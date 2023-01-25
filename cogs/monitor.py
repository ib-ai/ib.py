import re
from typing import Literal, Optional
import discord
from discord.ext import commands
from db.cached import get_all_monitor_messages, get_all_monitor_users, get_guild_data
from db.models import GuildData, StaffMonitorMessage, StaffMonitorUser, StaffMonitorMessageGroups

from utils.checks import admin_command, cogify, staff_command
from utils.commands import available_subcommands
from utils.converters import ListConverter, RegexConverter
from utils.pagination import paginated_embed_menus, PaginationView

import logging
logger = logging.getLogger(__name__)

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

        # If no guild data return
        if not guild_data:
            return
        
        # Monitored Users
        if guild_data.monitoring_user and guild_data.monitor_user_log_id:
            monitor_users = [user.user_id for user in await get_all_monitor_users()]
            if message.author.id in monitor_users:
                await log_suspicious_message(guild_data.monitor_user_log_id, message)
                return
        
        # Monitored Messages
        if guild_data.monitoring_message and guild_data.monitor_message_log_id:
            monitor_messages = [pattern.message for pattern in await get_all_monitor_messages() if not pattern.disabled]
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
        Set logger channel for monitored users.
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
        Set logger channel for monitored message patterns.
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
        bans = [entry.user.id async for entry in ctx.guild.bans()]
        users_removed = 0

        for monitor_user in monitor_users:
            if monitor_user.user_id in bans:
                await monitor_user.delete()
                users_removed += 1

        get_all_monitor_users.cache_clear()
        
        logger.debug(f"{users_removed} user(s) were removed from monitor.")
        await ctx.send(f"{users_removed} user(s) were removed from monitor.")
    
    @monitor.command()
    async def list(self, ctx: commands.Context, type: Optional[Literal['messages', 'users']] = None):
        """
        List of monitored message patterns and monitored users.
        """
        names = []
        entries = []

        if not type or type == "messages":
            monitor_messages = sorted(await get_all_monitor_messages(), key=lambda x: x.monitor_message_id)
            names += [f"{'[Disabled] ' if pattern.disabled else ''}Regex (ID: `{pattern.monitor_message_id}`)" for pattern in monitor_messages]
            entries += [f"```{pattern.message}```" for pattern in monitor_messages]

        if not type or type == "users":
            monitor_users = await get_all_monitor_users()
            names += [f"User (ID: `{user.user_id}`)" for user in monitor_users]
            entries += [f"<@{user.user_id}>" for user in monitor_users]

        embeds = paginated_embed_menus(names, entries)
        monitor_embed, monitor_view = await PaginationView(ctx, embeds).return_paginated_embed_view()

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

        logger.debug(f"Added pattern {pattern} to monitor.")
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

        logger.debug(f"Removed pattern {pattern} from monitor.")
        await ctx.send(f"The pattern (`{pattern}`) has been successfully removed from monitor.")

    @message.command(name='toggle')
    async def message_toggle(self, ctx: commands.Context, pattern_id: int):
        """
        Toggle a monitor for a message pattern.
        """
        monitored_message = await StaffMonitorMessage.filter(monitor_message_id=pattern_id).get_or_none()

        if not monitored_message:
            await ctx.send(f"Pattern with ID `{pattern_id}` does not exist.")
            return
        
        monitored_message.disabled = not monitored_message.disabled
        await monitored_message.save()
        get_all_monitor_messages.cache_clear()

        logger.debug(f"{'Disabled' if monitored_message.disabled else 'Enabled'} pattern with ID {monitored_message.monitor_message_id} in monitor.")
        await ctx.send(f"The pattern (`{monitored_message.message}`) [ID: {monitored_message.monitor_message_id}] has been successfully {'disabled' if monitored_message.disabled else 'enabled'}.")

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

        logger.debug(f"Added user with id {member.id} to monitor.")
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

        logger.debug(f"Removed user with id {member.id} from monitor.")
        await ctx.send(f"{member.mention} has been successfully removed from monitor.")
    
    @monitor.command()
    @admin_command()
    async def toggle(self, ctx: commands.Context, type: Optional[Literal['messages','users']] = None):
        """
        Toggle if monitoring is active for the guild.
        """ 
        guild_data = (await GuildData.get_or_create(guild_id=ctx.guild.id))[0]

        if not type or type == "messages":
            guild_data.monitoring_message = not guild_data.monitoring_message

        if not type or type == "users":
            guild_data.monitoring_user = not guild_data.monitoring_user

        await guild_data.save()
        get_guild_data.cache_clear()

        confirmation_message = f"Monitoring is now enabled for only {'messages' if guild_data.monitoring_message else 'users'} in this guild."

        if guild_data.monitoring_message == guild_data.monitoring_user:
            confirmation_message = f"Monitoring is now {'enabled' if guild_data.monitoring_message else 'disabled'} for both users and messages in this guild."
        elif not guild_data.monitoring_message and not guild_data.monitoring_user:
            confirmation_message = "Monitoring is now disabled for both users and messages in this guild."

        await ctx.send(confirmation_message)

    @monitor.group()
    async def group(self, ctx: commands.Context):
        """
        Commands for creating, modifying, and deleting group message monitors.
        """
        await available_subcommands(ctx)

    @group.command(name='add')
    async def group_add(self, ctx: commands.Context, name: str, monitor_messages: ListConverter):
        """
        Creates new/adds to existing group message monitor.
        """
        if len(monitor_messages) == 0:
            await ctx.send("You must provide at least one monitored message to add to a group.")
            return

        if monitor_messages == "*":
            await ctx.send("You cannot add all messages to a group. Please specify individual patterns to add to the group.")
            return
        
        db_monitor_messages = []

        for pattern_id in monitor_messages:
            db_monitor_message = await StaffMonitorMessage.filter(monitor_message_id=pattern_id).get_or_none()

            if not db_monitor_message:
                await ctx.send(f"The pattern with ID `{pattern_id}` could not be found.")
                return

            db_monitor_messages.append(db_monitor_message)
        
        monitor_group = await StaffMonitorMessageGroups.filter(name=name).get_or_none()

        if not monitor_group:
            monitor_group = await StaffMonitorMessageGroups.create(name=name)

        await monitor_group.monitor_messages.add(*db_monitor_messages)

        logger.debug(f"Added messages {monitor_messages} to group {name}.")
        await ctx.send(f"Messages `{monitor_messages}` have been successfully added to group `{name}`.")

    @group.command(name='delete')
    async def group_delete(self, ctx: commands.Context, name: str, monitor_messages: Optional[ListConverter] = None):
        """
        Deletes monitored messages from group message monitor, and if empty, deletes the entire group.
        """
        monitor_group = await StaffMonitorMessageGroups.filter(name=name).get_or_none()

        if not monitor_group:
            await ctx.send(f"The monitor group with name `{name}` could not be found.")
            return

        # Delete entire group
        if not monitor_messages:
            await monitor_group.delete()
            await ctx.send(f"Removed monitor group `{name}`.")
            logger.debug(f"Removed monitor group {name}.")
            return

        monitor_group_patterns = [pattern async for pattern in monitor_group.monitor_messages]

        # Delete specific entries from group
        if monitor_messages and monitor_messages != "*":
            db_monitor_messages = []

            for pattern_id in monitor_messages:
                db_monitor_message = await StaffMonitorMessage.filter(monitor_message_id=pattern_id).get_or_none()

                if not db_monitor_message:
                    await ctx.send(f"The pattern with ID `{pattern_id}` could not be found.")
                    return
                
                if db_monitor_message not in monitor_group_patterns:
                    await ctx.send(f"The pattern with ID `{pattern_id}` is not in the monitor group `{name}`.")
                    return

                db_monitor_messages.append(db_monitor_message)

            await monitor_group.monitor_messages.remove(*db_monitor_messages)

            logger.debug(f"Removed patterns {monitor_messages} from group {name}.")
            await ctx.send(f"Patterns `{monitor_messages}` have been successfully removed from group `{name}`.")
        else:
            # Delete all entries but keep group
            for pattern in monitor_group_patterns:
                await monitor_group.monitor_messages.remove(pattern)
            await ctx.send(f"Removed all patterns from monitor group `{name}`.")
            logger.debug(f"Removed all patterns from monitor group {name}.")

    @group.command(name='list')
    async def group_list(self, ctx: commands.Context):
        """
        List of monitored message pattern groups.
        """
        monitor_groups = await StaffMonitorMessageGroups.all()

        # chr(10) returns \n as backslashes cannot be used in f-string expressions
        names = [f"{'[Disabled]' if group.disabled else ''} {group.name}" for group in monitor_groups]
        values = await create_formatted_group_message(monitor_groups)

        embeds = paginated_embed_menus(names, values)
        monitor_embed, monitor_view = await PaginationView(ctx, embeds).return_paginated_embed_view()

        await ctx.send(embed=monitor_embed, view=monitor_view)
    
    @group.command(name='toggle')
    async def group_toggle(self, ctx: commands.Context, name: str):
        """
        Toggles a group message monitor on or off.
        """
        monitor_group = await StaffMonitorMessageGroups.filter(name=name).get_or_none()

        if not monitor_group:
            await ctx.send(f"The monitor group with name `{name}` could not be found.")
            return

        monitor_group.disabled = not monitor_group.disabled
        await monitor_group.save()

        async for pattern in monitor_group.monitor_messages:
            pattern.disabled = monitor_group.disabled
            print("pattern.disabled", pattern, pattern.disabled)
            await pattern.save()

        get_all_monitor_messages.cache_clear()
        
        logger.debug(f"Monitor group `{name}` (with {len(monitor_group.monitor_messages)} children) has been {'disabled' if monitor_group.disabled else 'enabled'}.")
        await ctx.send(f"Monitor group `{name}` (with {len(monitor_group.monitor_messages)} children) has been {'disabled' if monitor_group.disabled else 'enabled'}.")

async def log_suspicious_message(channel: int, message: discord.Message):
    monitor_channel = message.guild.get_channel(channel)

    if not monitor_channel:
        return

    author = f"{message.author.name}#{message.author.discriminator} (ID: {message.author.id})"

    embed = discord.Embed(title=author, description=message.content, color=discord.Colour.red())

    embed.set_author(name="Monitor Trigger", icon_url=message.author.display_avatar.url) \
        .add_field(name="Utilities", value=f"[21 Jump Street]({message.jump_url})\nUser: {message.author.mention}  • Channel: <#{message.channel.id}>", inline=False)

    await monitor_channel.send(embed=embed)

async def create_formatted_group_message(monitor_groups: list[StaffMonitorMessageGroups]):
    formatted_messages = []
    
    for group in monitor_groups:
        sorted_messages = sorted(await group.monitor_messages.all(), key=lambda x: x.monitor_message_id)
        message_lines = [f'[ID: {pattern.monitor_message_id}] {pattern.message}' for pattern in sorted_messages]
        formatted_messages.append(f"```{chr(10).join(message_lines)}```")

    return formatted_messages

async def setup(bot: commands.Bot):
    await bot.add_cog(Monitor(bot))
