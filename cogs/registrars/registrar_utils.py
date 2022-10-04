from typing import Union
from discord.ext import commands
import discord
from discord import app_commands

from db.models import MemberOpt

class RegistrarUtils(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name = "ping", description="Pong!")
    @app_commands.guild_only()
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong! Latency is currently {}ms for WebSocket.".format(round(self.bot.latency * 1000)))

    @app_commands.command(name = "serverinfo", description="Retrieves current server information.")
    @app_commands.guild_only()
    async def serverinfo(self, interaction: discord.Interaction):
        embed = discord.Embed() \
            .set_author(name=interaction.guild.name) \
            .set_thumbnail(url=str(interaction.guild.icon_url))

        embed.add_field(name="Owner",  value=interaction.guild.owner.mention, inline=True) \
            .add_field(name="Creation Date", value="<t:{}>".format(round(interaction.guild.created_at.timestamp())), inline=True) \
            .add_field(name="Voice Region", value=interaction.guild.region, inline=True) \
            .add_field(name="# of Members", value=interaction.guild.member_count, inline=True) \
            .add_field(name="# of Bots", value=len(list(filter(lambda member: member.bot, interaction.guild.members))), inline=True) \
            .add_field(name="Currently Online", value=len(list(filter(lambda member: member.status != discord.Status.offline, interaction.guild.members))), inline=True) \
            .add_field(name="# of Roles", value=len(interaction.guild.roles), inline=True) \
            .add_field(name="# of Channels", value=len(interaction.guild.channels), inline=True) 

        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name = "avatar", description="Retrieves avatar of user.")
    @app_commands.choices(type = [
        app_commands.Choice(name = "Global", value = "global"),
        app_commands.Choice(name = "Server", value = "server")
    ])
    @app_commands.guild_only()
    async def user_avatar(self, interaction: discord.Interaction, type: str, member: discord.Member = None):
        if not member:
            member = interaction.user
        
        avatar = member.display_avatar.with_size(1024).url
        
        if type == "server":
            if not member.guild_avatar:
                await interaction.response.send_message("This user does not have a server avatar.")
                return
            avatar = member.guild_avatar.with_size(1024).url

        await interaction.response.send_message(avatar)
    
    @app_commands.command(name = "banner", description="Retrieves banner of user (if available).")
    @app_commands.guild_only()
    async def user_banner(self, interaction: discord.Interaction, member: discord.Member = None):
        if not member:
            member = interaction.user
        
        if not member.banner:
            await interaction.response.send_message("This user does not have a banner set.")
            return

        await interaction.response.send_message(member.banner.with_size(1024).url)
    
    @app_commands.command(name = "opt", description="Opts in/out of specified channel.")
    @app_commands.guild_only()
    async def user_opt(self, interaction: discord.Interaction, channel: Union[discord.TextChannel, discord.VoiceChannel]):
        # TODO Check for opt only in spam
        # TODO Opt blacklist

        if not channel:
            opt_list = await MemberOpt.query.where(MemberOpt.user_id == interaction.user.id).gino.all()
            channel_names = [interaction.guild.get_channel(opt.channel_id) for opt in opt_list]
            await interaction.response.send_message("You currently have opt-outs for the following channels: `{}`. Please mention a channel in order to toggle an opt-out for it.".format(
                ", ".join([chan for chan in channel_names if chan])
            ))
            return
        
        channel_opt = await MemberOpt.query.where(user_id = interaction.user.id).where(channel_id = channel.id).gino.first()
        
        if channel_opt:
            await channel.set_permissions(interaction.user, overwrite=None)
            await channel_opt.delete()
            await interaction.response.send_message("You will now be able to see the channel.")
        else:
            if not channel.permissions_for(interaction.user).read_messages:
                await interaction.response.send_message("You cannot opt in/out of channels you do not have permission to view.")
                return
            
            if not channel.overwrites_for(interaction.user).is_empty():
                await interaction.response.send_message("For security reasons, opting in/out of channels where you have an existing user override is disabled. Please contact staff.")
                return
            
            await channel.set_permissions(interaction.user, read_messages=False)
            await MemberOpt.create(user_id=interaction.user.id, channel_id=channel.id)
            await interaction.response.send_message("You will no longer be able to see the channel.")

        
async def setup(bot: commands.Bot):
    await bot.add_cog(RegistrarUtils(bot))