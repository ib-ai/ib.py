import re
from discord.ext import commands
import discord
from db.models import StaffTag

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
        
        # TODO Disable Reply

        # TODO Repeat messages
        # ! Only get non-disabled ones

        tags = [tag for tag in await StaffTag.query.gino.all()]

        for tag in tags:
            if tag.disabled:
                pass

            if re.search(tag.trigger, message.content, re.IGNORECASE):
                try:
                    await message.channel.send(tag.output)
                except Exception as e:
                    await message.channel.send("Oh dear. Something went wrong. Ping a dev with this: {}".format(e))

    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        # TODO Include images/attachments

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
        # TODO Include images/attachments
        
        author = "{} deleted in #{}".format(message.author, message.channel)

        log_channel = message.guild.get_channel(await get_guild_data(message.guild, "logs_id"))

        if not log_channel:
            return

        embed = discord.Embed(description=message.content, color=discord.Colour.red())

        embed.set_author(name=author, icon_url=message.author.avatar_url) \
            .add_field(name="Utilities", value="User: {} • ID: {}".format(message.author.mention, message.author.id), inline=False)

        await log_channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(MessageListener(bot))