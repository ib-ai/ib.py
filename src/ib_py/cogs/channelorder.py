import discord
from discord.ext import commands

from ..db.models import GuildSnapshot


class ChannelOrder(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_group(aliases=["co"])
    async def channelorder(self, ctx: commands.Context):
        """
        Commands for discord channel arrangement within categories.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
    
    @channelorder.command(name="snapshot")
    @commands.has_permissions(administrator=True)
    async def snapshot(self, ctx: commands.Context, *, category_input: int):
        """
        Take a snapshot of all channels (text, voice, forum) in the given category.
        Admin-only command.
        """
        guild = ctx.guild
        category = self.get_category(guild, category_input)

        if not category:
            await ctx.reply("Invalid category ID or name.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📸 Snapshot for {category.name}",
            color=discord.Color.blue()
        )

        # Get all types of channels
        text_channels = category.text_channels
        voice_channels = category.voice_channels
        forum_channels = getattr(category, "forums", [])
        # Sort all channels by position
        all_channels_sorted = sorted(category.channels, key=lambda c: (c.position, c.id))

        # Separate by type
        text_forum_channels = [ch for ch in all_channels_sorted if ch.type in (discord.ChannelType.text, discord.ChannelType.forum)]
        voice_channels = [ch for ch in all_channels_sorted if ch.type == discord.ChannelType.voice]

        # Combine: text+forum first, then voice (voice order preserved among themselves)
        all_channels = text_forum_channels + voice_channels

        if text_channels:
            embed.add_field(
                name="Text Channels",
                value=", ".join(ch.name for ch in text_channels),
                inline=False
            )

        if voice_channels:
            embed.add_field(
                name="Voice Channels",
                value=", ".join(ch.name for ch in voice_channels),
                inline=False
            )

        if forum_channels:
            embed.add_field(
                name="Forum Channels",
                value=", ".join(ch.name for ch in forum_channels),
                inline=False
            )

        # Upsert snapshot
        existing_snapshot = await GuildSnapshot.get_or_none(category_id=category_input)
        channel_ids = [ch.id for ch in all_channels]

        if existing_snapshot:
            # Update the existing snapshot
            existing_snapshot.channel_list = channel_ids
            await existing_snapshot.save()
        else:
            # Create a new snapshot
            await self.save_snapshot(category.id, channel_ids)

        await ctx.reply(embed=embed, ephemeral=True)

    def get_category(self, guild: discord.Guild, category_input: int) -> discord.CategoryChannel | None:
        """
        Retrieves a category from a guild by name or ID.
        """
        category = discord.utils.get(guild.categories, id=int(category_input))
        if category:
            return category
        
        # if not category return message with error
    
    async def save_snapshot(self, category_id: int, channel_ids: list[int]):
        await GuildSnapshot.create(
            category_id=category_id,
            channel_list=channel_ids,
        )

    @channelorder.command(aliases=["r"])
    @commands.has_permissions(administrator=True)
    async def rollback(self, ctx: commands.Context, *, category_input: int):
        """
        Rollback channels in a category to the saved snapshot order.
        """
        guild = ctx.guild
        category = self.get_category(guild, category_input)
        
        if not category:
            await ctx.reply("Invalid category ID or name.", ephemeral=True)
            return

        # Fetch snapshot
        snapshot = await GuildSnapshot.get_or_none(category_id=category.id)
        if not snapshot:
            await ctx.reply("No snapshot exists for this category.", ephemeral=True)
            return

        # Map current channels
        channels_map = {ch.id: ch for ch in category.channels}
        new_order = [channels_map.get(ch_id) for ch_id in snapshot.channel_list if channels_map.get(ch_id)]

        if not new_order:
            await ctx.reply("Snapshot channel IDs do not match current channels.", ephemeral=True)
            return

        # Check if already in order
         # Get all types of channels
        voice_channels = category.voice_channels
        # Sort all channels by position
        all_channels_sorted = sorted(category.channels, key=lambda c: (c.position, c.id))

        # Separate by type
        text_forum_channels = [ch for ch in all_channels_sorted if ch.type in (discord.ChannelType.text, discord.ChannelType.forum)]
        voice_channels = [ch for ch in all_channels_sorted if ch.type == discord.ChannelType.voice]

        # Combine: text+forum first, then voice (voice order preserved among themselves)
        all_channels = text_forum_channels + voice_channels

        # Compare current positions to snapshot
        moves_needed = []
        for new_pos, ch in enumerate(new_order):
            if ch.position != new_pos:
                moves_needed.append((ch, new_pos))

        # Check if already in order
        current_order_ids = [ch.id for ch in all_channels]
        new_order_ids = [ch.id for ch in new_order]

        if current_order_ids[:len(new_order_ids)] == new_order_ids:
            await ctx.reply("Channels are already in the snapshot order. No changes needed.", ephemeral=True)
            return

        # Move only out-of-position channels
        for ch, new_pos in moves_needed:
            try:
                await ch.edit(position=new_pos)
            except discord.Forbidden:
                await ctx.reply(f"Missing permission to edit {ch.name}.", ephemeral=True)
                return
            except discord.HTTPException as e:
                await ctx.reply(f"Failed to reorder {ch.name}: {e}", ephemeral=True)
                return

        await ctx.reply(f"`{category.name}` channels have been reordered to match the snapshot.", ephemeral=True)



async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelOrder(bot))