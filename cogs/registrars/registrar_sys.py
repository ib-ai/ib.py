from discord.ext import commands
import discord

from utils.ucommand import reply_unknown_syntax
from utils.uguild import get_guild_data

class RegistrarSys(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    # Channels
    
    @commands.group(invoke_without_command=True)
    @commands.has_guild_permissions(manage_guild=True)
    @commands.guild_only()
    async def modlog(self, ctx: commands.Context):
        await ctx.send(reply_unknown_syntax(ctx.command))
    
    @modlog.command()
    @commands.guild_only()
    async def staff(self, ctx: commands.Context, channel: discord.TextChannel=None):
        guild_data = await get_guild_data(ctx.guild)

        try:
            await guild_data.update(modlog_staff_id=channel.id if channel else None).apply()
        except Exception as e:
            print(e)
            return

        success_message = "removed" if not channel else "set as <#{}>".format(channel.id)
        
        await ctx.send("`modlog-staff` has been successfully {}.".format(success_message))
    
    @modlog.command()
    @commands.guild_only()
    async def server(self, ctx: commands.Context, channel: discord.TextChannel=None):
        guild_data = await get_guild_data(ctx.guild)

        try:
            await guild_data.update(modlog_id=channel.id if channel else None).apply()
        except Exception as e:
            print(e)
            return

        success_message = "removed" if not channel else "set as <#{}>".format(channel.id)
        
        await ctx.send("`modlog` has been successfully {}.".format(success_message))
    
    @commands.command()
    @commands.has_guild_permissions(manage_guild=True)
    @commands.guild_only()
    async def logs(self, ctx: commands.Context, channel: discord.TextChannel=None):
        guild_data = await get_guild_data(ctx.guild)

        try:
            await guild_data.update(logs_id=channel.id if channel else None).apply()
        except Exception as e:
            print(e)
            return

        success_message = "removed" if not channel else "set as <#{}>".format(channel.id)
        
        await ctx.send("`logs` has been successfully {}.".format(success_message))

    # Roles
    
    @commands.command()
    @commands.has_guild_permissions(manage_guild=True)
    @commands.guild_only()
    async def muterole(self, ctx: commands.Context, role: discord.Role=None):
        guild_data = await get_guild_data(ctx.guild)

        try:
            await guild_data.update(mute_id=role.id if role else None).apply()
        except Exception as e:
            print(e)
            return

        success_message = "removed" if not role else "set as {}".format(role.name)
        
        await ctx.send("`muterole` has been successfully {}.".format(success_message))
    
    @commands.command()
    @commands.has_guild_permissions(manage_guild=True)
    @commands.guild_only()
    async def moderators(self, ctx: commands.Context, role: discord.Role=None):
        guild_data = await get_guild_data(ctx.guild)

        try:
            await guild_data.update(moderator_id=role.id if role else None).apply()
        except Exception as e:
            print(e)
            return

        success_message = "removed" if not role else "set as {}".format(role.name)
        
        await ctx.send("`moderators` has been successfully {}.".format(success_message))

    @commands.command()
    @commands.has_guild_permissions(manage_guild=True)
    @commands.guild_only()
    async def guilddata(self, ctx: commands.Context):
        guild_data = await get_guild_data(ctx.guild)

        prefix = guild_data.prefix if guild_data.prefix else "`None`"

        modlog_channel = f"<#{guild_data.modlog_id}>" if guild_data.modlog_id else "`None`"
        modlog_staff_channel = f"<#{guild_data.modlog_staff_id}>" if guild_data.modlog_staff_id else "`None`"
        updates_channel = f"<#{guild_data.updates_id}>" if guild_data.updates_id else "`None`"
        logs_channel = f"<#{guild_data.logs_id}>" if guild_data.logs_id else "`None`"
        monitor_user_channel = f"<#{guild_data.monitor_user_log_id}>" if guild_data.monitor_user_log_id else "`None`"
        monitor_message_channel = f"<#{guild_data.monitor_message_log_id}>" if guild_data.monitor_message_log_id else "`None`"

        mute_role = f"`{ctx.guild.get_role(guild_data.mute_id).name}`" if guild_data.mute_id else "`None`"
        mod_role = f"`{ctx.guild.get_role(guild_data.moderator_id).name}`" if guild_data.moderator_id else "`None`"
        helper_role = f"`{ctx.guild.get_role(guild_data.helper_id).name}`" if guild_data.helper_id else "`None`"

        guild_value_message = """**Guild Data for {}**

        **Prefix:** {}
        **Server Modlog:** {}
        **Staff Modlog:** {}
        **Updates:** {}
        **Logs:** {}
        **Mute:** {}
        **Moderator Role:** {}
        **Helper Role:** {}
        **Monitor User Channel:** {}
        **Monitor Message Channel:** {}
        """.format(ctx.guild, prefix, modlog_channel, modlog_staff_channel, updates_channel, logs_channel, mute_role, mod_role, helper_role, monitor_user_channel, monitor_message_channel)

        await ctx.send(guild_value_message)        

    
    async def cog_command_error(self, ctx, error: commands.CommandError):
        # ! More robust error checking
        if isinstance(error, commands.ChannelNotFound):
            await ctx.send(error)
        else:
            await ctx.send(error)
        
async def setup(bot: commands.Bot):
    await bot.add_cog(RegistrarSys(bot))