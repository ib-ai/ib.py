import re
from typing import Optional
import discord
from discord.ext import commands
from db.cached import get_all_tags, get_guild_data
from db.models import StaffTag

from utils.commands import available_subcommands
from utils.converters import RegexConverter

import logging

from utils.pagination import NAME_SIZE_LIMIT, VALUE_SIZE_LIMIT, PaginationView, paginated_embed_menus

logger = logging.getLogger(__name__)


class Tags(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Respond to tags.
        """
        # If DM, return
        if not message.guild:
            return

        # If bot, return
        if message.author.bot:
            return

        guild_data = await get_guild_data(guild_id=message.guild.id)

        # If bot replies are disabled for channel, return
        if message.channel.id in guild_data.suppressed_channels:
            return

        tags = await get_all_tags()

        for tag in tags:
            if tag.disabled:
                continue

            if re.fullmatch(tag.trigger, message.content, re.IGNORECASE):
                await message.channel.send(tag.output)
                return

    @commands.hybrid_group()
    async def tag(self, ctx: commands.Context):
        """
        Commands for handling tags.
        """
        await available_subcommands(ctx)

    @tag.command(name="create", aliases=['add'])
    async def tag_create(self, ctx: commands.Context, trigger: RegexConverter,
                         output: str):
        """
        Create a tag.
        """
        if len(
                trigger
        ) > NAME_SIZE_LIMIT - 13:  # 2 for backticks and 11 for [Disabled] with trailing whitespace
            await ctx.send(
                f"The tag trigger is too long (should not exceed {NAME_SIZE_LIMIT - 13} characters)."
            )
            return

        if len(output) > VALUE_SIZE_LIMIT:
            await ctx.send(
                f"The tag output is too long (should not exceed {VALUE_SIZE_LIMIT} characters)."
            )
            return

        values = dict(output=output)
        await StaffTag.update_or_create(values, trigger=trigger)

        get_all_tags.cache_clear()

        logger.debug(f"Created tag {trigger} with output {output}.")
        await ctx.send(f"Created tag `{trigger}` with output `{output}`.")

    @tag.command(name="delete", aliases=['remove'])
    async def tag_delete(self, ctx: commands.Context, trigger: RegexConverter):
        """
        Delete a tag.
        """
        tag = await StaffTag.filter(trigger=trigger).get_or_none()

        if not tag:
            await ctx.send(f"Tag `{trigger}` does not exist.")
            return

        await tag.delete()
        get_all_tags.cache_clear()

        logger.debug(f"Deleted tag {trigger} with output {tag.output}.")
        await ctx.send(f"Deleted tag `{trigger}` with output `{tag.output}`.")

    @tag.command(name="list")
    async def tag_list(self,
                       ctx: commands.Context,
                       trigger: Optional[RegexConverter] = None):
        """
        List of tags with specified filter, or all tags if none specified.
        """
        tags = await get_all_tags()

        if trigger:
            tags = [
                tag for tag in tags if trigger.lower() in tag.trigger.lower()
            ]

        names = [
            f"{'[Disabled] ' if tag.disabled else ''}`{tag.trigger}`"
            for tag in tags
        ]
        values = [tag.output for tag in tags]

        embeds = paginated_embed_menus(names, values)
        tag_embed, tag_view = await PaginationView(
            ctx, embeds).return_paginated_embed_view()

        await ctx.send(embed=tag_embed, view=tag_view)

    @tag.command(name="toggle")
    async def tag_toggle(self, ctx: commands.Context, trigger: RegexConverter):
        """
        Toggle if a tag is active.
        """
        tag = await StaffTag.filter(trigger=trigger).get_or_none()

        if not tag:
            await ctx.send(f"Tag `{trigger}` does not exist.")
            return

        tag.disabled = not tag.disabled
        await tag.save()
        get_all_tags.cache_clear()

        logger.debug(
            f"Tag {trigger} is now {'disabled' if tag.disabled else 'enabled'}."
        )
        await ctx.send(
            f"Tag `{trigger}` is now {'disabled' if tag.disabled else 'enabled'}."
        )

    @commands.hybrid_group()
    async def reply(self, ctx: commands.Context):
        """
        Commands for handling channels where certain bot replies (e.g., tags) are disabled.
        """
        await available_subcommands(ctx)

    @reply.command(name="list")
    async def reply_list(self, ctx: commands.Context):
        """
        List of disabled reply channels.
        """
        suppressed_channels = (await get_guild_data(guild_id=ctx.guild.id
                                                    )).suppressed_channels
        channels = [f"<#{channel_id}>" for channel_id in suppressed_channels
                    ] if suppressed_channels else ["`None`"]

        await ctx.send(
            f"Replies for the following channels are disabled: {', '.join(channels)}"
        )

    @reply.command(name="toggle")
    async def reply_toggle(self, ctx: commands.Context,
                           channel: discord.TextChannel):
        """
        Toggle if bot replies are disabled for specified channel.
        """
        guild_data = await get_guild_data(guild_id=ctx.guild.id)

        disabled = channel.id in guild_data.suppressed_channels

        if disabled:
            guild_data.suppressed_channels.remove(channel.id)
        else:
            guild_data.suppressed_channels.append(channel.id)

        await guild_data.save()

        logger.debug(
            f"Channel {channel.id} replies are now {'disabled' if not disabled else 'enabled'}."
        )
        await ctx.send(
            f"Replies for <#{channel.id}> are now {'disabled' if not disabled else 'enabled'}."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Tags(bot))
