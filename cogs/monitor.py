import logging
import re
from typing import List, Optional
import discord
from discord.ext import commands
from db.cached import get_all_monitor_messages, get_all_monitor_users, get_guild_data
from db.models import GuildData, StaffMonitorMessage, StaffMonitorUser

from utils.checks import admin_command, cogify, staff_command
from utils.commands import available_subcommands
from utils.converters import RegexConverter
from utils.embeds import EmbedGenerator
from utils.pagination import Pagination

class Monitor(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Log messages that:
        - are from a monitored user.
        - match a monitor's pattern.
        """
        # If DM, return
        if message.guild is None:
            return

        # If bot, return
        if message.author.bot:
            return
        
        # TODO Add check for config for NSA Deny List

        guild_data = await get_guild_data(guild_id=message.guild.id)

        # If no guild data, or no monitoring enabled, return
        if not guild_data or not guild_data.monitoring:
            return
        
        # Monitored Users
        if guild_data.monitor_user_log_id:
            monitor_users = [user.user_id for user in await get_all_monitor_users()]
            if message.author.id in monitor_users:
                await log_suspicious_message(guild_data.monitor_user_log_id, message)
                return
        
        # Monitored Messages
        if guild_data.monitor_message_log_id:
            monitor_messages = [pattern.message for pattern in await get_all_monitor_messages()]
            for pattern in monitor_messages:
                if re.search(pattern, message.content, re.IGNORECASE):
                    await log_suspicious_message(guild_data.monitor_message_log_id, message)
                    return

    cog_check = cogify(staff_command())

    @commands.hybrid_group()
    async def monitor(self, ctx: commands.Context):
        """
        Commands for monitoring problematic message patterns and users.
        """
        await available_subcommands(ctx)

    @monitor.group()
    @admin_command()
    async def channel(self, ctx: commands.Context):
        """
        Commands for setting up channels to log problematic messages to.
        """
        await available_subcommands(ctx)

    @channel.command(name='user')
    @admin_command()
    async def channel_user(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """
        Set logging channel for monitored users.
        """
        values = dict(monitor_user_log_id = channel.id if channel else None)
        await GuildData.update_or_create(values, guild_id=ctx.guild.id)
        get_guild_data.cache_clear()

        if channel:
            await ctx.send(f'Log channel for monitored users set to <#{channel.id}> for this guild.')
        else:
            await ctx.send('Log channel for monitored users removed for this guild.')
    
    @channel.command(name='message')
    @admin_command()
    async def channel_message(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """
        Set logging channel for monitored message patterns.
        """
        values = dict(monitor_message_log_id = channel.id if channel else None)
        await GuildData.update_or_create(values, guild_id=ctx.guild.id)
        get_guild_data.cache_clear()

        if channel:
            await ctx.send(f'Log channel for monitored messages set to <#{channel.id}> for this guild.')
        else:
            await ctx.send('Log channel for monitored messages removed for this guild.')

    @monitor.command()
    async def cleanup(self, ctx: commands.Context):
        """
        Remove users that are no longer in the server.
        """
        monitor_users = await get_all_monitor_users()
        users_removed = 0

        for monitor_user in monitor_users:
            if not ctx.guild.get_member(monitor_user.user_id):
                await monitor_user.delete()
                users_removed += 1

        get_all_monitor_users.cache_clear()
        
        logging.debug(f"{users_removed} user(s) were removed from monitor.")
        await ctx.send(f"{users_removed} user(s) were removed from monitor.")
    
    @monitor.command()
    async def list(self, ctx: commands.Context):
        """
        List of monitored message patterns and monitored users.
        """
        monitor_users = await get_all_monitor_users()
        monitor_messages = await get_all_monitor_messages()

        formatted_users = await formatted_user_monitor(ctx.guild, [user.user_id for user in monitor_users])
        formatted_messages = [f"Regex: `{pattern.message}`" for pattern in monitor_messages]

        embeds = EmbedGenerator(entries=formatted_users + formatted_messages, description="Here is a list of entries.", step=10).build_embed()
        monitor_embed, monitor_view = await Pagination(ctx, embeds).return_paginated_embed_view()

        await ctx.send(embed=monitor_embed, view=monitor_view)

    @monitor.group()
    async def message(self, ctx: commands.Context):
        """
        Commands for monitoring problematic message patterns.
        """
        await available_subcommands(ctx)
    
    @message.command(aliases=['add'], name='create')
    async def message_create(self, ctx: commands.Context, pattern: RegexConverter):
        """
        Create a monitor for a message pattern.
        """
        monitored_message = await StaffMonitorMessage.filter(message=pattern).exists()

        if monitored_message:
            await ctx.send(f"The pattern (`{pattern}`) is already being monitored.")
            return

        await StaffMonitorMessage.create(message=pattern)
        get_all_monitor_messages.cache_clear()

        logging.debug(f"Added pattern {pattern} to monitor.")
        await ctx.send(f"The pattern (`{pattern}`) has been successfully added to monitor.")
    
    @message.command(aliases=['remove'], name='delete')
    async def message_delete(self, ctx: commands.Context, *, pattern: RegexConverter):
        """
        Delete a monitor for a message pattern.
        """
        monitored_message = await StaffMonitorMessage.filter(message=pattern).get_or_none()

        if not monitored_message:
            await ctx.send(f"The pattern (`{pattern}`) is not being monitored.")
            return

        await monitored_message.delete()
        get_all_monitor_messages.cache_clear()

        logging.debug(f"Removed pattern {pattern} from monitor.")
        await ctx.send(f"The pattern (`{pattern}`) has been successfully removed from monitor.")

    @monitor.group()
    async def user(self, ctx: commands.Context):
        """
        Commands for monitoring problematic users.
        """
        await available_subcommands(ctx)
    
    @user.command(aliases=['add'], name='create')
    async def user_create(self, ctx: commands.Context, member: discord.Member):
        """
        Create a monitor for a user.
        """
        monitored_user = await StaffMonitorUser.filter(user_id=member.id).exists()

        if monitored_user:
            await ctx.send(f"{member.mention} is already being monitored.")
            return

        await StaffMonitorUser.create(user_id=member.id)
        get_all_monitor_users.cache_clear()

        logging.debug(f"Added user with id {member.id} to monitor.")
        await ctx.send(f"{member.mention} has been successfully added to monitor.")
    
    @user.command(aliases=['remove'], name='delete')
    async def user_delete(self, ctx: commands.Context, member: discord.Member):
        """
        Delete a monitor for a user.
        """
        monitored_user = await StaffMonitorUser.filter(user_id=member.id).get_or_none()

        if not monitored_user:
            await ctx.send(f"{member.mention} is not being monitored.")
            return

        await monitored_user.delete()
        get_all_monitor_users.cache_clear()

        logging.debug(f"Removed user with id {member.id} from monitor.")
        await ctx.send(f"{member.mention} has been successfully removed from monitor.")
    
    @monitor.command()
    @admin_command()
    async def toggle(self, ctx: commands.Context):
        """
        Toggle if monitoring is active for the guild.
        """ 
        guild_data = (await GuildData.get_or_create(guild_id=ctx.guild.id))[0]
        guild_data.monitoring = not guild_data.monitoring
        await guild_data.save()
        get_guild_data.cache_clear()

        await ctx.send(f"Monitoring is now {'enabled' if guild_data.monitoring else 'disabled'} for this guild.")

async def log_suspicious_message(channel: int, message: discord.Message):
    monitor_channel = message.guild.get_channel(channel)

    if not monitor_channel:
        return

    author = f"{message.author.name} (ID: {message.author.id})"

    embed = discord.Embed(title=author, description=message.content, color=discord.Colour.red())

    embed.set_author(name="Monitor Trigger", icon_url=message.author.display_avatar.url) \
        .add_field(name="Utilities", value=f"[21 Jump Street]({message.jump_url})\nUser: {message.author.mention}  • Channel: <#{message.channel.id}>", inline=False)

    await monitor_channel.send(embed=embed)

async def formatted_user_monitor(guild: discord.Guild, user_ids: List[int]) -> List[str]:
    formatted_users = []

    for id in user_ids:
        member = await guild.fetch_member(id)
        formatted = f"User: {id}" + f" ({member.mention})" if member else ""
        
        formatted_users.append(formatted)
    
    return formatted_users

async def setup(bot: commands.Bot):
    await bot.add_cog(Monitor(bot))
