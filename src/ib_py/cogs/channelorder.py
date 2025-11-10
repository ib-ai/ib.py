import discord
from discord.ext import commands


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
    async def snapshot(self, ctx: commands.Context, *, category_input: str):
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

        if text_channels:
            await self.save_snapshot(guild.id, category.id, "text", [ch.id for ch in text_channels])
            embed.add_field(
                name="Text Channels",
                value=", ".join(ch.name for ch in text_channels),
                inline=False
            )

        if voice_channels:
            await self.save_snapshot(guild.id, category.id, "voice", [ch.id for ch in voice_channels])
            embed.add_field(
                name="Voice Channels",
                value=", ".join(ch.name for ch in voice_channels),
                inline=False
            )

        if forum_channels:
            await self.save_snapshot(guild.id, category.id, "forum", [ch.id for ch in forum_channels])
            embed.add_field(
                name="Forum Channels",
                value=", ".join(ch.name for ch in forum_channels),
                inline=False
            )

        await ctx.reply(embed=embed, ephemeral=True)

    @channelorder.command(aliases=["r"])
    async def rollback(self, ctx: commands.Context, category_input: str):
        guild = ctx.guild
        category = self.get_cateogry(guild, category_input)
        raise NotImplementedError("Command requires implementation and permission set-up.")
    
    async def setup(bot: commands.Bot):
        await bot.add_cog(ChannelOrder(bot))