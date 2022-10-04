from discord.ext import commands
import discord

from db.models import GuildVote

class ReactionListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        self.reaction_checks(payload)

        # Get unicode emoji
        emoji = payload.emoji.name

        match emoji:
            # Thumbs Up
            case "\uD83D\uDC4D":
                vote_entry = await GuildVote.query.where(GuildVote.message_id == payload.message_id).gino.first()
                await vote_entry.update(positive = vote_entry.positive + 1).apply()
            # Thumbs Down
            case "\uD83D\uDC4E":
                vote_entry = await GuildVote.query.where(GuildVote.message_id == payload.message_id).gino.first()
                await vote_entry.update(negative = vote_entry.negative + 1).apply()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        self.reaction_checks(payload)

        # Get unicode emoji
        emoji = payload.emoji.name

        match emoji:
            # Thumbs Up
            case "\uD83D\uDC4D":
                vote_entry = await GuildVote.query.where(GuildVote.message_id == payload.message_id).gino.first()
                await vote_entry.update(positive = vote_entry.positive - 1).apply()
            # Thumbs Down
            case "\uD83D\uDC4E":
                vote_entry = await GuildVote.query.where(GuildVote.message_id == payload.message_id).gino.first()
                await vote_entry.update(negative = vote_entry.negative - 1).apply()
    
    def reaction_checks(self, payload: discord.RawReactionActionEvent):
        # Ignore if self
        if payload.user_id == self.bot.user.id:
            return

        # Ignore if not in guild
        if not payload.guild_id:
            return
        
        # Ignore if not unicode emoji
        if not payload.emoji.is_unicode_emoji():
            return

        # Get member object
        reaction_user = payload.member

        # Ignore if bot
        if reaction_user.bot:
            return

async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionListener(bot))