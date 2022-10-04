import re
from discord.ext import commands
import discord
from db.models import StaffMonitorMessage, StaffMonitorUser

from utils.uguild import get_guild_data

class MonitorListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listener for both DM and server messages.
        Args:
            message (discord.Message): The current message.
        """

        if message.guild is None:
            return

        if message.author.bot:
            return
        
        # ! Add check for config for NSA Deny List

        # Do not trigger if command

        ctx = await self.bot.get_context(message)

        if ctx.valid:
            return

        guild_data = await get_guild_data(message.guild)

        if message.author.bot:
            return

        if not guild_data.monitoring:
            return
        
        monitor_users = [user.user_id for user in await StaffMonitorUser.query.gino.all()]
        monitor_messages = [pattern.message for pattern in await StaffMonitorMessage.query.gino.all()]

        if message.author.id in monitor_users:
            await log_suspicious_message(guild_data.monitor_user_log_id, message)
            return
        
        for pattern in monitor_messages:
            if not pattern:
                return
            
            if re.search(pattern, message.content, re.IGNORECASE):
                await log_suspicious_message(guild_data.monitor_message_log_id, message)
                return

async def log_suspicious_message(channel: int, message: discord.Message):
    monitor_channel = message.guild.get_channel(channel)

    if not monitor_channel:
        return

    author = "{} (ID: {})".format(message.author, message.author.id)

    embed = discord.Embed(title=author, description=message.content, color=discord.Colour.red())

    embed.set_author(name="Monitor Trigger", icon_url=message.author.avatar_url) \
        .add_field(name="Utilities", value="[21 Jump Street]({})\nUser: {}  • Channel: <#{}>".format(message.jump_url, message.author.mention, message.channel.id), inline=False)

    await monitor_channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(MonitorListener(bot))