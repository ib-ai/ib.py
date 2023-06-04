import asyncio
from typing import Mapping

from tortoise import timezone
import discord
from discord import app_commands
from discord.ext import commands
from db.models import MemberReminder

from utils.commands import available_subcommands
from utils.converters import DatetimeConverter
from utils.time import DEGENERACY_DELAY, long_sleep_until
from discord.utils import format_dt
from utils.pagination import paginated_embed_menus, PaginationView

import logging
logger = logging.getLogger(__name__)

class Reminder(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.active: Mapping[int, asyncio.Task] = {}
    
    async def handle_reminder(self, user: discord.User, reminder: MemberReminder):
        """
        Sleep until reminder's timestamp, then send the message to the user and delete the timer.
        If cancelled, reminder deletion must be handled elsewhere.
        """
        message = reminder.message
        terminus = reminder.timestamp
        await long_sleep_until(terminus)
        await user.send(f'You asked me to remind you: {message}')
        await reminder.delete()
    
    def removal_callback(self, id: int):
        """
        Create callback for removing reminder's task from the internal mapping of active tasks.
        To be used in asyncio.Task.add_done_callback when scheduling a timer.
        """
        def callback(task: asyncio.Task):
            del self.active[id]
        return callback
    
    async def schedule_existing_reminders(self):
        """
        Schedule all timers existing in the database. To be used on bot start-up.
        If a reminder's time has passed, it is scheduled to send with DEGENERACY_DELAY (to avoid rate-limiting).
        """
        reminders = await MemberReminder.all()
        if not reminders:
            logger.debug('No existing reminders found.')
        
        # on bot start-up, add a bit of delay between scheduled reminders (to avoid rate-limiting)
        dormant = asyncio.create_task(
            asyncio.sleep(DEGENERACY_DELAY.total_seconds())
        )
        async def schedule_once_completed(last: asyncio.Task, user: discord.User, reminder: MemberReminder):
            await asyncio.wait_for(last, timeout=None)
            await self.handle_reminder(user, reminder)

        async with asyncio.TaskGroup() as tg:
            for reminder in reminders:
                if reminder.reminder_id in self.active:
                    logger.debug('Reminder already active. (skipping)')
                    continue
                user = self.bot.get_user(reminder.user_id)
                if not user:
                    logger.warning(f'User {reminder.user_id} not found. (skipping)')
                    continue

                if reminder.timestamp <= timezone.now():
                    dormant = tg.create_task(schedule_once_completed(dormant, user, reminder))
                    logger.debug(f'Dormant timer running: {reminder.reminder_id}')
                else:
                    task = asyncio.create_task(self.handle_reminder(user, reminder))
                    self.active[reminder.reminder_id] = task
                    task.add_done_callback(self.removal_callback(reminder.reminder_id))
                    logger.debug(f'Active timer running: {reminder.reminder_id}')

                logger.debug(f'Active reminders: {len(self.active)}')

    @commands.hybrid_group()
    async def reminder(self, ctx: commands.Context):
        """
        Commands for handling reminders.
        """
        await available_subcommands(ctx)
    
    @reminder.command(aliases=['add'])
    @app_commands.rename(terminus='duration')
    async def create(self, ctx: commands.Context, terminus: DatetimeConverter, *, message):
        """
        Create a reminder.
        """
        values = dict(
            user_id = ctx.author.id,
            message = message,
            timestamp = terminus
        )
        reminder = await MemberReminder.create(**values)
        logger.debug(f"User {ctx.author.id} scheduled a reminder for {terminus}.")
        task = asyncio.create_task(self.handle_reminder(ctx.author, reminder))
        self.active[reminder.reminder_id] = task
        task.add_done_callback(self.removal_callback(reminder.reminder_id))
        await ctx.send(f'Reminder set for {format_dt(terminus.timestamp())} ({format_dt(terminus.timestamp(), "R")}).')

    @reminder.command(aliases=['remove'])
    async def delete(self, ctx: commands.Context, id: int):
        """
        Delete a reminder.
        """
        reminder = await MemberReminder.get_or_none(reminder_id = id)
        if not reminder:
            await ctx.send(f'Invalid reminder ID!')
            return
        task = self.active[id]
        task.cancel()
        
        await reminder.delete()
        await ctx.send(f'Reminder with ID {id} has been deleted.')
    
    @reminder.command()
    async def list(self, ctx: commands.Context):
        """
        List your active reminders.
        """ 
        user_reminders = await MemberReminder.filter(user_id=ctx.author.id)

        embed_dict = dict(
            title = f'Reminders for {ctx.author.name}#{ctx.author.discriminator}.',
            description = f'Here is a list of your active reminders.',
        )
        if ctx.author.accent_color: embed_dict['color'] = ctx.author.accent_color.value
        names = [f'[ID: {reminder.reminder_id}] {format_dt(reminder.timestamp)}' for reminder in user_reminders]
        values = [reminder.message for reminder in user_reminders]

        embeds = paginated_embed_menus(names, values, embed_dict=embed_dict)
        embed, view = await PaginationView(ctx, embeds).return_paginated_embed_view()
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))