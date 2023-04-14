import re
import discord
from discord.ext import commands
from db.cached import get_all_filters, get_guild_data
from db.models import GuildData, StaffFilter
from utils.checks import cogify, staff_command

from utils.commands import available_subcommands
from utils.converters import RegexConverter
from utils.misc import truncate
from utils.pagination import PaginationView, paginated_embed_menus

import logging
logger = logging.getLogger(__name__)

class Filter(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Delete messages that match a filter's pattern.
        """
        # If DM, return
        if message.guild is None:
            return

        # If bot, return
        if message.author.bot:
            return

        guild_data = await get_guild_data(guild_id=message.guild.id)

        # If no guild data return
        if not guild_data:
            return

        if guild_data.filtering and guild_data.monitor_message_log_id:
            filter_messages = await get_all_filters()
            for filter in filter_messages:
                match = re.search(filter.trigger, message.content, re.IGNORECASE)

                if match:
                    formatted_filter = f"{message.content[:match.start()]}**{message.content[match.start():match.end()]}**{message.content[match.end():]}"

                    await log_filtered_message(guild_data.monitor_message_log_id, message, formatted_filter, filter.notify)
                    await message.delete()

                    dm_filter_message = "The following message has been flagged and deleted for potentially " \
                            f"breaking the rules on {message.guild} (offending phrase bolded):\n\n{formatted_filter}" \
                            + "\n\nIf you believe you haven't broken any rules, or have any other questions or concerns " \
                            "regarding this, you can contact the staff team for clarification by DMing the ModMail bot, " \
                            "at the top of the sidebar on the server."

                    await message.author.send(truncate(dm_filter_message))
                    return

    cog_check = cogify(staff_command())

    @commands.hybrid_group()
    async def filter(self, ctx: commands.Context):
        """
        Commands for filtering unwanted message patterns.
        """
        await available_subcommands(ctx)

    @filter.command(aliases=['add'])
    async def create(self, ctx: commands.Context, *, pattern: RegexConverter):
        """
        Create a filter.
        """
        filtered_message = await StaffFilter.filter(trigger=pattern).exists()

        if filtered_message:
            await ctx.send(f"The pattern (`{pattern}`) has already being filtered.")
            return

        if len(pattern) > 1024:
            await ctx.send(f"The pattern provided is longer than 1024 characters.")
            return

        await StaffFilter.create(trigger=pattern)
        get_all_filters.cache_clear()

        logger.debug(f"Added pattern {pattern} to filters.")
        await ctx.send(f"The pattern (`{pattern}`) has been successfully added to filtered messages.")

    @filter.command(aliases=['remove'])
    async def delete(self, ctx: commands.Context, filter_id: int):
        """
        Delete a filter.
        """
        filtered_message = await StaffFilter.filter(filter_id=filter_id).get_or_none()

        if not filtered_message:
            await ctx.send(f"The filter with ID `{filter_id}` does not exist.")
            return

        await filtered_message.delete()
        get_all_filters.cache_clear()

        logger.debug(f"Removed {filtered_message.trigger} from filters.")
        await ctx.send(f"The pattern (`{filtered_message.trigger}`) has been successfully removed from filtered messages.")

    @filter.command()
    async def list(self, ctx: commands.Context):
        """
        List all filters.
        """
        filtered_messages = sorted(await get_all_filters(), key=lambda x: x.filter_id)

        names = [f"{'[Notify] ' if filter.notify else ''}Filter (ID: `{filter.filter_id}`)" for filter in filtered_messages]
        entries =[f"```{filter.trigger}```" for filter in filtered_messages]

        embeds = paginated_embed_menus(names, entries)
        filter_embed, filter_view = await PaginationView(ctx, embeds).return_paginated_embed_view()

        await ctx.send(embed=filter_embed, view=filter_view)

    @filter.command()
    async def notify(self, ctx: commands.Context, filter_id: int):
        """
        Toggle if a filter triggers a ping.
        """
        filtered_message = await StaffFilter.filter(filter_id=filter_id).get_or_none()

        if not filtered_message:
            await ctx.send(f"Filter with ID `{filter_id}` does not exist.")
            return

        filtered_message.notify = not filtered_message.notify

        await filtered_message.save()
        get_all_filters.cache_clear()

        logger.debug(f"{'Enabled' if filtered_message.notify else 'Disabled'} notify for filter with ID {filtered_message.filter_id}.")
        await ctx.send(f"The ping notification for filter (`{filtered_message.trigger}`) [ID: {filtered_message.filter_id}] has been successfully {'enabled' if filtered_message.notify else 'disabled'}.")

    @filter.command()
    async def toggle(self, ctx: commands.Context):
        """
        Toggle if filtering is active for guild.
        """
        guild_data = (await GuildData.get_or_create(guild_id=ctx.guild.id))[0]

        guild_data.filtering = not guild_data.filtering

        await guild_data.save()
        get_guild_data.cache_clear()

        await ctx.send(f"Message filtering {'`enabled`' if guild_data.filtering else '`disabled`'} for this guild.")

async def log_filtered_message(channel: int, message: discord.Message, formatted_message: str, notify: bool):
    filter_channel = message.guild.get_channel(channel)

    if not filter_channel:
        return

    author = f"{message.author.name}#{message.author.discriminator} (ID: {message.author.id})"

    description = f"\"{formatted_message}\", sent in **<#{message.channel.id}>** by <@{message.author.id}>"
    description = truncate(description, 950) # Accounts for above characters and a lenient snowflake value

    embed = discord.Embed(title=author, description=description, color=discord.Colour.magenta())

    embed.set_author(name="Filter was triggered!", icon_url=message.author.display_avatar.url)

    await filter_channel.send(embed=embed)

    if notify:
        await filter_channel.send("@here")

async def setup(bot: commands.Bot):
    await bot.add_cog(Filter(bot))
