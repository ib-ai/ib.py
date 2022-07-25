from discord.ext import commands
from discord.utils import get
import discord

from db.models import StaffMonitorMessage, StaffMonitorUser
from utils.ucommand import reply_unknown_syntax
from utils.uguild import get_guild_data, mods_or_manage_guild

class Monitor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.group(invoke_without_command=True)
    @mods_or_manage_guild()
    @commands.guild_only()
    async def monitor(self, ctx: commands.Context):
        await ctx.send(reply_unknown_syntax(ctx.command))
    
    @monitor.command()
    @commands.has_guild_permissions(manage_guild=True)
    @commands.guild_only()
    async def toggle(self, ctx: commands.Context):
        guild_data = await get_guild_data(ctx.guild)

        try:
            await guild_data.update(monitoring = not guild_data.monitoring).apply()
        except Exception as e:
            print(e)
            return

        success_message = "disabled" if not guild_data.monitoring else "enabled"
        
        await ctx.send("`monitoring` has been successfully {}.".format(success_message))
    
    @monitor.group(invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def channel(self, ctx: commands.Context):
        await ctx.send(reply_unknown_syntax(ctx.command))
    
    @channel.command(name='user')
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def channel_user(self, ctx: commands.Context, channel: discord.TextChannel):
        guild_data = await get_guild_data(ctx.guild)

        try:
            await guild_data.update(monitor_user_log_id=channel.id if channel else None).apply()
        except Exception as e:
            print(e)
            return

        success_message = "removed" if not channel else "set as <#{}>".format(channel.id)
        
        await ctx.send("`monitor-user` has been successfully {}.".format(success_message))
    
    @channel.command(name='message')
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def channel_message(self, ctx: commands.Context, channel: discord.TextChannel):
        guild_data = await get_guild_data(ctx.guild)

        try:
            await guild_data.update(monitor_message_log_id=channel.id if channel else None).apply()
        except Exception as e:
            print(e)
            return

        success_message = "removed" if not channel else "set as <#{}>".format(channel.id)
        
        await ctx.send("`monitor-message` has been successfully {}.".format(success_message))
    
    @monitor.group(invoke_without_command=True)
    @mods_or_manage_guild()
    @commands.guild_only()
    async def user(self, ctx: commands.Context):
        await ctx.send(reply_unknown_syntax(ctx.command))
    
    @user.command(name='create', aliases=['add'])
    @commands.guild_only()
    async def user_create(self, ctx: commands.Context, user: discord.Member):
        try:
            monitored_user = await StaffMonitorUser.query.where(StaffMonitorUser.user_id == user.id).gino.first()

            if monitored_user is not None:
                await ctx.send("{} is already being monitored.".format(user.mention))
                return

            monitored_user = StaffMonitorUser(user_id=user.id)
            await monitored_user.create()
        except Exception as e:
            print(e)

        await ctx.send("{} has been successfully added to monitor.".format(user.mention))
    
    @user.command(name='remove', aliases=['delete'])
    @commands.guild_only()
    async def user_remove(self, ctx: commands.Context, user: discord.Member):
        try:
            monitored_user = await StaffMonitorUser.query.where(StaffMonitorUser.user_id == user.id).gino.first()

            if monitored_user is None:
                await ctx.send("{} is not being monitored.".format(user.mention))
                return

            await monitored_user.delete()
        except Exception as e:
            print(e)

        await ctx.send("{} has been successfully removed from monitor.".format(user.mention))
    
    @monitor.group(invoke_without_command=True)
    @mods_or_manage_guild()
    @commands.guild_only()
    async def message(self, ctx: commands.Context):
        await ctx.send(reply_unknown_syntax(ctx.command))
    
    @message.command(name='create', aliases=['add'])
    @commands.guild_only()
    async def message_create(self, ctx: commands.Context, *, pattern: str):
        try:
            monitored_message = await StaffMonitorMessage.query.where(StaffMonitorMessage.message == pattern).gino.first()

            if monitored_message is not None:
                await ctx.send("The pattern (`{}`) is already being monitored.".format(pattern))
                return

            monitored_message = StaffMonitorMessage(message=pattern)
            await monitored_message.create()
        except Exception as e:
            print(e)
            
        await ctx.send("The pattern (`{}`) has been successfully added to monitor.".format(pattern))
    
    @message.command(name='remove', aliases=['delete'])
    @commands.guild_only()
    async def message_remove(self, ctx: commands.Context, *, pattern: str):
        try:
            monitored_message = await StaffMonitorMessage.query.where(StaffMonitorMessage.message == pattern).gino.first()

            if monitored_message is None:
                await ctx.send("The pattern (`{}`) is not being monitored.".format(pattern))
                return

            await monitored_message.delete()
        except Exception as e:
            print(e)

        await ctx.send("The pattern (`{}`) has been successfully removed from monitor.".format(pattern))
    
    async def cog_command_error(self, ctx, error: commands.CommandError):
        # ! More robust error checking
        await ctx.send(error)

def setup(bot: commands.Bot):
    bot.add_cog(Monitor(bot))