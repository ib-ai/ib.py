import discord
from discord.ext import commands

from ..db.models import GuildSnapshot


class ChannelOrder(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_group(aliases=["co"])
    async def channelorder(self, ctx: commands.Context):
        """Commands for discord channel arrangement within categories."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    def get_category(self, guild: discord.Guild, category_input: str | int) -> discord.CategoryChannel | None:
        """
        Retrieves a category from a guild by name or ID.
        """
        # Try ID
        try:
            category_id = int(category_input)
            category = discord.utils.get(guild.categories, id=category_id)
            if category:
                return category
        except ValueError:
            pass  # Not an ID, so treat as name

        # Try by name (case-insensitive)
        category = discord.utils.find(lambda c: c.name.lower() == str(category_input).lower(), guild.categories)
        return category

    def draw_embed(self, title: str, fields: list[tuple[str, str, bool]], color=discord.Color.blue()):
        """
        Helper function to draw an embed with the given title, fields, and color.
        
        Args:
            title (str): The title of the embed.
            fields (list[tuple[str, str, bool]]): A list of fields where each field is a tuple (name, value, inline).
            color (discord.Color, optional): The color of the embed. Defaults to discord.Color.blue().

        Returns:
            discord.Embed: The constructed embed object.
        """
        embed = discord.Embed(title=title, color=color)
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
        return embed

    def create_snapshot_embed(self, category, channels):
        """
        Helper function to create a snapshot embed for a given category.
        Channels are listed on separate lines and mentioned using <#id>.
        """
        fields = []
        if channels:
            # Mention each channel on a new line
            channel_mentions = "\n".join(f"<#{ch.id}>" for ch in channels)
        else:
            channel_mentions = "None"

        fields.append(("Channels", channel_mentions, False))
        return self.draw_embed(title=f"📸 Snapshot for {category.name}", fields=fields)


    @channelorder.command(name="snapshot")
    @commands.has_permissions(administrator=True)
    async def snapshot(self, ctx: commands.Context, *, category_input: str):
        """Take a snapshot of all channels (text, voice, forum) in the given category."""
        guild = ctx.guild
        category = self.get_category(guild, category_input)

        if not category:
            await ctx.reply("Invalid category ID or name.", ephemeral=True)
            return

                # Get all types of channels
        voice_channels = category.voice_channels
        # Sort all channels by position
        all_channels_sorted = sorted(category.channels, key=lambda c: (c.position, c.id))

        # Separate and recombine: text+forum first, then voice (voices keep relative order)
        text_forum_channels = [ch for ch in all_channels_sorted if ch.type in (discord.ChannelType.text, discord.ChannelType.forum)]
        voice_channels = [ch for ch in all_channels_sorted if ch.type == discord.ChannelType.voice]

        # Combine: text+forum first, then voice (voice order preserved among themselves)
        all_channels = text_forum_channels + voice_channels

        embed = self.create_snapshot_embed(category, all_channels)

        # Upsert snapshot
        channel_ids = [ch.id for ch in all_channels]
        existing_snapshot = await GuildSnapshot.get_or_none(category_id=category.id)

        if existing_snapshot:
            existing_snapshot.channel_list = channel_ids
            await existing_snapshot.save()
            msg = "Updated existing snapshot."
        else:
            await GuildSnapshot.create(category_id=category.id, channel_list=channel_ids)
            msg = "Created new snapshot."

        embed.set_footer(text=f"Category ID: {category.id} | Total channels: {len(channel_ids)}")

        await ctx.reply(f"{msg}", embed=embed, ephemeral=True)

    @channelorder.command(aliases=["r"])
    @commands.has_permissions(manage_channels=True)
    async def rollback(self, ctx: commands.Context, *, category_input: str):
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


    @channelorder.command(name="view")
    @commands.has_permissions(manage_channels=True)
    async def list_snapshot(self, ctx: commands.Context, *, category_input: str):
        """
        List the stored snapshot for a given category (by ID or name).
        Staff-only command.
        """
        guild = ctx.guild
        category = self.get_category(guild, category_input)

        if not category:
            await ctx.reply("Invalid category ID or name.", ephemeral=True)
            return

        # Fetch snapshot from DB
        snapshot = await GuildSnapshot.get_or_none(category_id=category.id)
        if not snapshot:
            await ctx.reply("No snapshot stored for this category.", ephemeral=True)
            return

        # Retrieve channels from snapshot (if still exist)
        snapshot_channels = [guild.get_channel(ch_id) for ch_id in snapshot.channel_list]

        # Filter and group
        embed = self.create_snapshot_embed(category, snapshot_channels)

        embed.set_footer(text=f"Category ID: {category.id} | Total channels: {len(snapshot.channel_list)}")

        await ctx.reply(embed=embed, ephemeral=True)



async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelOrder(bot))