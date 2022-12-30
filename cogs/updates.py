import logging
from typing import Optional
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

from db.models import GuildData
from utils.misc import ordinal
from utils.checks import admin_command, staff_command, cogify
from utils.converters import Index

# updates operates by UTC dates
UTC = timezone(offset=timedelta(), name='UTC')

class UpdatesMessage(commands.Converter):
    async def convert(self, ctx: commands.Context, message_id: str) -> discord.Message:
        guild_data = await GuildData.get(guild_id = ctx.guild.id)
        updates_channel = ctx.bot.get_channel(guild_data.updates_id)
        update_message = await updates_channel.fetch_message(message_id)
        return update_message


class Updates(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    cog_check = cogify(staff_command())
    
    @commands.hybrid_group()
    async def update(self, ctx: commands.Context):
        """
        Commands for handling updates.
        """
        subcmds = []
        for cmd in ctx.command.commands:
            try:
                usable = await cmd.can_run(ctx)
                if usable:
                    subcmds.append('`'+cmd.name+'`')
            except commands.CommandError as e:
                logging.debug(f'Command "{cmd.name}" check threw error, discarded in {ctx.command.name} group subcommand list.')
        await ctx.send(f'Available subcommands: {", ".join(subcmds)}.')
    
    @update.command()
    @admin_command()
    async def set(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """
        Set an updates channel.
        """
        values = dict(updates_id = channel.id if channel else None)
        await GuildData.update_or_create(values, guild_id = ctx.guild.id)
        if channel:
            await ctx.send(f'Updates channel set to <#{channel.id}> for this guild.')
        else:
            await ctx.send(f'Updates channel removed for this guild.')
    
    @update.command(aliases=['add'])
    async def create(self, ctx: commands.Context, update1: str, update2: Optional[str] = None, update3: Optional[str] = None):
        """
        Create (up to 3) update entries.
        """
        logging.debug(f'Update create - {update1}, {update2}, {update3}')

        # note: currently, discord does not support variable-length arguments in hybrid commands
        updates = [update1]
        if update2: updates.append(update2)
        if update3: updates.append(update3)

        guild_data = await GuildData.get(guild_id = ctx.guild.id)
        updates_channel = self.bot.get_channel(guild_data.updates_id)
        
        # updates operates by UTC dates
        last_midnight = datetime.now(tz=UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        async for message in updates_channel.history(limit=5, after=last_midnight):
            if message.author == self.bot.user:
                update_content = '\n- '.join([message.content, *updates])
                await message.edit(content=update_content)
                break
        else:
            # if no message was found:
            d = last_midnight.date()
            fmt = f"**{ordinal(d.day)} of %B, %Y**"
            update_date = d.strftime(fmt)
            update_content = '\n- '.join([update_date, *updates])
            await updates_channel.send(content=update_content)

        await ctx.send(f'Added update(s): `{"`,`".join(updates)}`')
    
    @update.command(aliases=['remove'])
    async def delete(self, ctx: commands.Context, message: UpdatesMessage, entries: commands.Greedy[Index]):
        """
        Delete update entries.
        """
        if not entries:
            raise commands.BadArgument('Please provide a valid update entry. (Updates entries must be a positive integer.)')
        logging.debug(f'Update delete - {entries}, {message.content}')

        # note: the zeroth entry is always the date
        # update entry indices are supplied with 1-based indexing
        updates = message.content.split('\n- ')
        try:
            removed = [updates[i] for i in entries]
        except IndexError as e:
            raise commands.BadArgument('Updates entries provided go out of range.')
        remaining = [updates[i] for i in range(len(updates)) if i not in entries]

        # if no updates remain, delete message
        if len(remaining) < 2:
            await message.delete()
        else:
            new = '\n- '.join(remaining)
            await message.edit(content=new)

        await ctx.send(f'Removed update(s): `{"`,`".join(removed)}`')


async def setup(bot: commands.Bot):
    await bot.add_cog(Updates(bot))