import asyncio
import re
from datetime import datetime
from typing import Dict, Optional

import discord
from discord.ext import commands

from ib_py.db.models import GuildVote, GuildVoteLadder


class VoteEntry:
    def __init__(self, bot: commands.Bot, vote: GuildVote):
        self.bot = bot
        self.vote = vote
        self._task = Optional[asyncio.Task] = None

    async def vote_yes(self):
        self.vote.positive += 1
        self.vote.save()
        await self.check_final_criteria()

    async def unvote_yes(self):
        self.vote.positive -= 1
        self.vote.save()
        await self.check_final_criteria()

    async def vote_no(self):
        self.vote.negative += 1
        self.vote.save()
        await self.check_final_criteria()

    async def unvote_no(self):
        self.vote.negative -= 1
        self.vote.save()
        await self.check_final_criteria()

    async def check_final_criteria(self):
        """
        Check if the vote has met the criteria for passing or failing and mark as finished if so.
        """
        if self.vote.finished:
            return
        now = int(datetime.utcnow().timestamp() * 1000)

        if (
            self.vote.positive >= self.vote.vote_ladder_id.threshold
            or self.vote.negative >= self.vote.vote_ladder_id.threshold
            or now >= self.expiry
        ):
            self.vote.finished = True
            await self.vote.save()

            guild = self.bot.get_guild(self.vote.vote_ladder_id.vote_ladder_id)
            if guild:
                channel = guild.get_channel(self.vote.vote_ladder_id.channel_id)
                if channel:
                    result, reason = "drew", ""
                    if self.vote.positive > self.vote.negative:
                        if self.vote.positive < self.vote.vote_ladder_id.minimum:
                            result = "failed"
                            reason = "Did not meet the upvote threshold."
                        else:
                            result = "passed"
                    elif self.vote.negative > self.vote.positive:
                        result = "failed"
                        reason = "More downvotes than upvotes."
                    await channel.send(
                        f"Update on vote `{self.vote.vote_ladder.vote_ladder_label}/{self.vote.message_id}`: "
                        f"{result}.{reason}"
                    )

            if self._task:
                self._task.cancel()

    def start_scheduler(self):
        delay = max(0, self.vote.expiry - int(datetime.utcnow().timestamp() * 1000)) / 1000
        self._task = asyncio.create_task(self.__expire_after(delay))

    async def __expire_after(self, delay: float):
        await asyncio.sleep(delay)
        await self.check_final_criteria()


class VoteCache:
    def __init__(
        self,
    ):
        self.votes: Dict[int, VoteEntry] = {}

    def register(self, message_id: int, vote_entry: VoteEntry):
        self.votes[message_id] = vote_entry

    def get(self, message_id: int) -> Optional[VoteEntry]:
        return self.votes.get(message_id)


class Voting(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cache = VoteCache()

    async def react(self, message_id: int, action: int):
        """
        React to a message with a thumbs up or thumbs down.
        """
        entry = self.cache.get(message_id)

        if not entry:
            return

        if action == 0:
            await entry.vote_yes()
        elif action == 1:
            await entry.unvote_yes()
        elif action == 2:
            await entry.vote_no()
        elif action == 3:
            await entry.unvote_no()

    def parse_duration(duration: str) -> int:
        """
        Convert a human-readable duration string into seconds.
        Examples:
            3d -> 259200
            12h -> 43200
            30m -> 1800
        """
        match = re.fullmatch(r"(\d+)([dhms])", duration.lower())
        if not match:
            raise ValueError("Invalid duration format. Use Nd, Nh, Nm, or Ns.")

        value, unit = match.groups()
        value = int(value)

        if unit == "d":
            return value * 86400
        elif unit == "h":
            return value * 3600
        elif unit == "m":
            return value * 60
        elif unit == "s":
            return value

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        Increment vote count when reaction is added.
        """
        if payload.user_id == self.bot.user.id:
            return

        if payload.emoji.name == "\ud83d\udc4d":
            await self.react(payload.message_id, 0)
        elif payload.emoji.name == "\ud83d\udc4e":
            await self.react(payload.message_id, 2)

    @commands.Cog.listener()
    async def on_raw_reaction_delete(self, payload: discord.RawReactionActionEvent):
        """
        Decrement vote count when reaction is deleted.
        """
        if payload.user_id == self.bot.user.id:
            return

        if payload.emoji.name == "\ud83d\udc4d":
            await self.react(payload.message_id, 1)
        elif payload.emoji.name == "\ud83d\udc4e":
            await self.react(payload.message_id, 3)

    @commands.hybrid_group()
    @commands.has_permissions(administrator=True)
    async def voteladder(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @voteladder.command()
    async def channel(
        self, ctx: commands.Context, ladder_name: str, channel: discord.TextChannel
    ):
        """
        Assign a channel to a voteladder.
        """
        if channel is None:
            await ctx.send("You must specify a valid text channel.")
            return

        ladder = await GuildVoteLadder.get_or_none(vote_ladder_label=ladder_name)
        if not ladder:
            await ctx.send(f"Vote ladder `{ladder_name}` does not exist.")
            return

        guild_channels = ctx.guild.text_channels
        if channel not in guild_channels:
            await ctx.send(f"The channel `{channel}` does not exist in this server.")
            return

        ladder.channel_id = channel.id
        await ladder.save()
        await ctx.send(f"Channel for `{ladder_name}` set to {channel.mention}.")

    @voteladder.command(aliases=["add"])
    async def create(self, ctx: commands.Context, ladder_name: str):
        """
        Create a voteladder.
        """
        existing = await GuildVoteLadder.get_or_none(vote_ladder_label=ladder_name)
        if existing:
            await ctx.send(f"Vote ladder `{ladder_name}` already exists.")
            return

        ladder = await GuildVoteLadder.create(
            vote_ladder_label=ladder_name,
            vote_ladder_roles=[],
            channel_id=ctx.channel.id,
            threshold=9999,
            minimum=0,
            timeout=24 * 7 * 3600,
        )

        await ladder.save()

        await ctx.send(f"Vote ladder `{ladder_name}` has been created.")

    @voteladder.command(aliases=["remove"])
    async def delete(self, ctx: commands.Context, ladder_name: str):
        """
        Delete a voteladder.
        """
        ladder = await GuildVoteLadder.get_or_none(vote_ladder_label=ladder_name)
        if not ladder:
            await ctx.send(f"Vote ladder `{ladder_name}` not found.")
            return

        await ladder.delete()
        await ctx.send(f"Vote ladder `{ladder_name}` deleted.")

    @voteladder.command()
    async def duration(self, ctx: commands.Context, ladder_name: str, duration: str):
        """
        Assign a vote duration to a voteladder.
        """
        ladder = await GuildVoteLadder.get_or_none(vote_ladder_label=ladder_name)
        if not ladder:
            await ctx.send(f"Vote ladder `{ladder_name}` not found.")
            return

        try:
            seconds = self.parse_duration(duration)
        except ValueError:
            await ctx.send("Invalid duration format. Use something like `3d`, `12h`, `30m`.")
            return

        ladder.timeout = seconds
        await ladder.save()
        await ctx.send(f"Vote duration for `{ladder_name}` set to {duration}.")

    @voteladder.command()
    async def minimum(self, ctx: commands.Context, ladder_name: str, minimum: int):
        """
        Assign a minimum upvote count for passing to a voteladder.
        """
        ladder = await GuildVoteLadder.get_or_none(vote_ladder_label=ladder_name)
        if not ladder:
            await ctx.send(f"Vote ladder `{ladder_name}` not found.")
            return

        if minimum < 0:
            await ctx.send("Minimum upvotes must be a positive integer.")
            return

        ladder.minimum = minimum
        await ladder.save()
        await ctx.send(f"Minimum upvotes for `{ladder_name}` set to {minimum}.")

    @voteladder.command()
    async def role(self, ctx: commands.Context, ladder_name: str, role: discord.Role):
        """
        Assign a role to the voteladder.
        """
        ladder = await GuildVoteLadder.get_or_none(vote_ladder_label=ladder_name)
        if not ladder:
            await ctx.send(f"Vote ladder `{ladder_name}` not found.")
            return

        if role not in ctx.guild.roles:
            await ctx.send(f"Role `{role.name}` does not exist in this server.")
            return

        if role.id in ladder.vote_ladder_roles:
            await ctx.send(f"Role {role.mention} is already assigned to `{ladder_name}`.")
            return

        ladder.vote_ladder_roles.append(role)
        await ladder.save()
        await ctx.send(f"Role {role.mention} added to `{ladder_name}`.")

    @voteladder.command()
    async def threshold(self, ctx: commands.Context, ladder_name: str, threshold: int):
        """
        Assign a vote passing theshold to a voteladder.
        """
        ladder = await GuildVoteLadder.get_or_none(vote_ladder_label=ladder_name)
        if not ladder:
            await ctx.send(f"Vote ladder `{ladder_name}` not found.")
            return

        if threshold < 0:
            await ctx.send("Threshold must be a positive integer.")
            return

        ladder.threshold = threshold
        await ladder.save()
        await ctx.send(f"Threshold for `{ladder_name}` set to {threshold}.")

    @voteladder.command()
    async def list(self, ctx: commands.Context):
        """List all voteladders with their roles."""
        ladders = await GuildVoteLadder.all()
        if not ladders:
            await ctx.send("No vote ladders found.")
            return

        embed = discord.Embed(title="Vote Ladders", color=discord.Color.blurple())

        for ladder in ladders:
            # Channel mention
            channel_mention = (
                f"<#{ladder.channel_id}>" if ladder.channel_id else "No channel set"
            )

            # Roles mentions
            role_mentions = []
            for role_id in ladder.vote_ladder_roles or []:
                role = ctx.guild.get_role(role_id)
                if role:
                    role_mentions.append(role.mention)
            roles_display = ", ".join(role_mentions) if role_mentions else "No roles assigned"

            embed.add_field(
                name=ladder.vote_ladder_label,
                value=f"Channel: {channel_mention}\nRoles: {roles_display}\nThreshold: {ladder.threshold}\nMinimum: {ladder.minimum}\nTimeout: {ladder.timeout} seconds",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command()
    async def vote(self, ctx: commands.Context):
        """
        Hold a vote within a particular voteladder.
        """
        raise NotImplementedError("Command requires implementation and permission set-up.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Voting(bot))
