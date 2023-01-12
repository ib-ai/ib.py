import asyncio
import logging
from typing import Mapping, Union
from datetime import datetime, timedelta
from functools import partial

from tortoise import timezone
import discord
from discord.ext import commands
from db.models import MemberReminder

from utils.commands import available_subcommands
from utils.converters import TimestampConverter
from utils.misc import \
    discord_timestamp_string_format as dts_fmt
from utils.embeds import paginated_embed_menus
from utils.pagination import PaginationView


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # TODO: Change back to logging.INFO


class Reminder(commands.Cog):
    DORMANCY_DELAY = timedelta(seconds=1)  # on bot start-up, seconds of delay between scheduled reminders
    MAX_DELTA = timedelta(days=40)  # asyncio.sleep is faulty for longer periods of time

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.active: Mapping[int, asyncio.Task] = {}
    
    async def handle_reminder(self, user: discord.User, reminder: MemberReminder):
        """
        Sleep until reminder's timestamp, then send the message to the user and delete the timer.
        If cancelled, reminder deletion must be handled elsewhere.
        """
        id = reminder.reminder_id
        message = reminder.message
        terminus = reminder.timestamp
        now = timezone.now()
        if terminus < now:
            terminus = now + self.DORMANCY_DELAY
        while terminus - now > self.MAX_DELTA:
            logger.debug(f'Sleeping for MAX_DELTA: {id}')
            await asyncio.sleep(self.MAX_DELTA.total_seconds)
            now = timezone.now()
        logger.debug(f'Sleeping for {terminus - now}: {id}')
        await asyncio.sleep((terminus - now).total_seconds())
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
        If a reminder's time has passed, it is scheduled to send with DORMANCY_DELAY (to avoid rate-limiting).
        """
        reminders = await MemberReminder.all()
        if not reminders:
            logger.debug('No existing reminders found.')
        
        dormant = asyncio.create_task(
            asyncio.sleep(self.DORMANCY_DELAY.total_seconds())
        )
        async def schedule_once_completed(last: asyncio.Task, user: discord.User, reminder: MemberReminder):
            await asyncio.wait_for(last, timeout=None)
            await self.handle_reminder(user, reminder)

        async with asyncio.TaskGroup() as tg:
            for reminder in reminders:
                user = self.bot.get_user(reminder.user_id)
                if not user:
                    logger.warning(f'User {reminder.user_id} not found.')
                    continue

                if reminder.timestamp <= timezone.now():
                    dormant = tg.create_task(schedule_once_completed(dormant, user, reminder))
                    logger.debug(f'Dormant timer running: {reminder}')
                else:
                    task = asyncio.create_task(self.handle_reminder(user, reminder))
                    self.active[reminder.reminder_id] = task
                    task.add_done_callback(self.removal_callback(reminder.reminder_id))
                    logger.debug(f'Active timer running: {reminder}')

                logger.debug(f'Active: {len(self.active)}')

    @commands.hybrid_group()
    async def reminder(self, ctx: commands.Context):
        """
        Commands for handling reminders.
        """
        await available_subcommands(ctx)
    
    @reminder.command(aliases=['add'])
    async def create(self, ctx: commands.Context, terminus: TimestampConverter, *, message):
        """
        Create a reminder.
        """
        # NOTE: "timestamp" is a python datetime object
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
        await ctx.send(f'Reminder set for {dts_fmt(terminus)} ({dts_fmt(terminus, "R")}).')

    @reminder.command(aliases=['remove'])
    async def delete(self, ctx: commands.Context, id: int):
        """
        Delete a reminder.
        """
        reminder = await MemberReminder.get_or_none(reminder_id = id)
        if not reminder:
            await ctx.send(f'Invalid reminder ID!')
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
        names = [f'[ID: {reminder.reminder_id}] {dts_fmt(reminder.timestamp)}' for reminder in user_reminders]
        values = [reminder.message for reminder in user_reminders]
        embeds = paginated_embed_menus(names, values, embed_dict=embed_dict)
        # embeds = EmbedGenerator(entries=entries, description="Here is a list of your active reminders.", step=10).build_embed()

        embed, view = await PaginationView(ctx, embeds).return_paginated_embed_view()
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))