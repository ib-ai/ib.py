from discord.ext import commands
import discord

from utils.uguild import get_guild_data

class MessageListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listener for both DM and server messages.
        Args:
            message (discord.Message): The current message.
        """

        # No handling for DMs right now
        if message.guild is None and not message.author.bot:
            return
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        # Ignore embeds
        if not after.content:
            return

        author = "{} edited in #{}".format(before.author, before.channel)

        log_channel = before.guild.get_channel(await get_guild_data(before.guild, "logs_id"))

        if not log_channel:
            return

        embed = discord.Embed(color=discord.Colour.gold())

        embed.set_author(name=author, icon_url=before.author.avatar_url) \
            .add_field(name="From", value=before.content, inline=False) \
            .add_field(name="To", value=after.content, inline=False) \
            .add_field(name="Utilities", value="[21 Jump Street]({})\nUser: {} • ID: {}".format(after.jump_url, before.author.mention, before.author.id), inline=False)

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        author = "{} deleted in #{}".format(message.author, message.channel)

        log_channel = message.guild.get_channel(await get_guild_data(message.guild, "logs_id"))

        if not log_channel:
            return

        embed = discord.Embed(description=message.content, color=discord.Colour.red())

        embed.set_author(name=author, icon_url=message.author.avatar_url) \
            .add_field(name="Utilities", value="User: {} • ID: {}".format(message.author.mention, message.author.id), inline=False)

        await log_channel.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(MessageListener(bot))