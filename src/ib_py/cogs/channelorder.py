import discord
from discord.ext import commands

from ..db.models import GuildSnapshot

TEXT_CHANNEL_TYPES = {
    discord.ChannelType.text,
    discord.ChannelType.news,
    discord.ChannelType.forum,
}

VOICE_CHANNEL_TYPES = {discord.ChannelType.voice, discord.ChannelType.stage_voice}


class ChannelCategory(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> discord.CategoryChannel:
        guild = ctx.guild

        # Try ID first
        if argument.isdigit():
            category = discord.utils.get(guild.categories, id=int(argument))
            if category:
                return category

        # Try name (case-insensitive)
        category = discord.utils.find(
            lambda c: c.name.lower() == argument.lower(), guild.categories
        )

        if category:
            return category

        raise commands.BadArgument(f"Category `{argument}` not found.")


class ChannelOrder(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def create_snapshot_embed(self, category, channels):
        """
        Helper function to create a snapshot embed for a given category.
        Channels are listed on separate lines and mentioned using <#id>.
        """
        embed = discord.Embed(
            title=f"📸 Snapshot for {category.name}",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="Channels",
            value="\n".join(f"<#{ch.id}>" for ch in channels) or "None",
            inline=False,
        )
        embed.set_footer(text=f"Category ID: {category.id} | Total channels: {len(channels)}")
        return embed

    @commands.hybrid_group(aliases=["co"])
    async def channelorder(self, ctx: commands.Context):
        """
        Commands for discord channel arrangement within categories.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @channelorder.command(name="snapshot")
    @commands.has_permissions(administrator=True)
    async def snapshot(self, ctx: commands.Context, *, category: ChannelCategory):
        """
        Take a snapshot of all channels (text, voice, forum) in the given category.
        """
        # Sort all channels by position
        all_channels_sorted = sorted(category.channels, key=lambda c: (c.position, c.id))

        # Separate and recombine: text+forum first, then voice (voices keep relative order)
        text_forum_channels = [
            ch for ch in all_channels_sorted if ch.type in TEXT_CHANNEL_TYPES
        ]
        voice_channels = [ch for ch in all_channels_sorted if ch.type in VOICE_CHANNEL_TYPES]

        # Combine: text+forum first, then voice (voice order preserved among themselves)
        all_channels = text_forum_channels + voice_channels

        embed = self.create_snapshot_embed(category, all_channels)

        # Upsert snapshot
        channel_ids = [ch.id for ch in all_channels]
        snapshot, created = await GuildSnapshot.get_or_create(category_id=category.id)
        snapshot.channel_list = channel_ids
        await snapshot.save()

        msg = "Created new snapshot." if created else "Updated existing snapshot."
        await ctx.reply(msg, embed=embed)

    @channelorder.command(aliases=["r"])
    @commands.has_permissions(manage_channels=True)
    async def rollback(self, ctx: commands.Context, *, category: ChannelCategory):
        """
        Rollback channels in a category to the saved snapshot order.
        Also restores channels that were moved out of the category.
        """
        guild = ctx.guild

        snapshot = await GuildSnapshot.get_or_none(category_id=category.id)
        if not snapshot:
            await ctx.reply("No snapshot exists for this category.")
            return

        # ensure all snapshot channels are back in the category
        for pos, ch_id in enumerate(snapshot.channel_list):
            ch = guild.get_channel(ch_id)
            if not ch:
                continue  # channel deleted

            try:
                # If channel is in wrong category, move it back
                if ch.category_id != category.id:
                    await ch.edit(category=category)
                    moved_back = ch.name
            except discord.Forbidden:
                await ctx.reply(f"Missing permission to move {ch.name}.")
                return
            except discord.HTTPException as e:
                await ctx.reply(f"Failed moving {ch.name}: {e}")
                return

        # reorder channels inside the category
        for new_pos, ch_id in enumerate(snapshot.channel_list):
            ch = guild.get_channel(ch_id)
            if not ch:
                continue

            try:
                if ch.position != new_pos:
                    await ch.edit(position=new_pos)
                    reordered = ch.name
            except discord.Forbidden:
                await ctx.reply(f"Missing permission to reorder {ch.name}.")
                return
            except discord.HTTPException as e:
                await ctx.reply(f"Failed reordering {ch.name}: {e}")
                return

        if not moved_back and not reordered:
            await ctx.reply("Channels are already in the snapshot order.")
            return

        await ctx.reply(
            f"`{category.name}` channels have been reordered to match the snapshot."
        )

    @channelorder.command(name="view")
    @commands.has_permissions(manage_channels=True)
    async def list_snapshot(self, ctx: commands.Context, *, category: ChannelCategory):
        """
        List the stored snapshot for a given category (by ID or name).
        Staff-only command.
        """
        guild = ctx.guild

        # Fetch snapshot from DB
        snapshot = await GuildSnapshot.get_or_none(category_id=category.id)
        if not snapshot:
            await ctx.reply("No snapshot stored for this category.")
            return

        # Retrieve channels from snapshot (if still exist)
        snapshot_channels = [guild.get_channel(ch_id) for ch_id in snapshot.channel_list]

        # Filter and group
        embed = self.create_snapshot_embed(category, snapshot_channels)

        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelOrder(bot))
