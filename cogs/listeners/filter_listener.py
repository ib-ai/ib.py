import re
from discord.ext import commands
import discord
from db.models import StaffFilter

from utils.uguild import get_guild_data

class FilterListener(commands.Cog):
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

        if not guild_data.filtering:
            return

        filtered_messages = [pattern for pattern in await StaffFilter.query.gino.all()]

        for pattern in filtered_messages:
            if not pattern.trigger:
                return
            
            match = re.search(pattern.trigger, message.content, re.IGNORECASE)
            
            if match:
                await log_filtered_message(guild_data.monitor_message_log_id, message, pattern.notify)

                await message.delete()

                formatted_filter = "{}**{}**{}".format(message.content[:match.start()], message.content[match.start():match.end()], message.content[match.end():])

                dm_filter_message = "The following message has been flagged and deleted for potentially " \
                    "breaking the rules on {} (offending phrase bolded):\n\n{}".format(message.guild, formatted_filter) \
                    + "\n\nIf you believe you haven't broken any rules, or have any other questions or concerns " \
                    "regarding this, you can contact the staff team for clarification by DMing the ModMail bot, " \
                    "at the top of the sidebar on the server."
                
                dm_filter_message = dm_filter_message if len(dm_filter_message) <= 2000 else dm_filter_message[0:2000]

                await message.author.send(dm_filter_message)

                return

async def log_filtered_message(channel: int, message: discord.Message, notify: bool):
    filter_channel = message.guild.get_channel(channel)

    if not filter_channel:
        # ! Add logger statement
        return

    author = "{} (ID: {})".format(message.author, message.author.id)

    description =  "\"{}\", sent in **<#{}>** by {}".format(message.content, message.channel.id, message.author.mention)
    description = description if len(description) <= 2000 else description[0:2000]

    embed = discord.Embed(title=author, description=description, color=discord.Colour.magenta())

    embed.set_author(name="Filter was triggered!", icon_url=message.author.avatar_url)

    await filter_channel.send(embed=embed)
    
    if notify:
        await filter_channel.send("@here")

async def setup(bot: commands.Bot):
    await bot.add_cog(FilterListener(bot))