import asyncio
import re
from datetime import datetime
from typing import Dict, Optional

import discord
from discord.ext import commands

from ib_py.db.models import GuildVote, GuildVoteLadder

# permission helper functions


def is_staff(member: discord.Member) -> bool:
    return member.guild_permissions.administrator


def member_has_ladder_role(member: discord.Member, ladder: GuildVoteLadder) -> bool:
    role_ids = ladder.vote_ladder_roles or []
    return any(role.id in role_ids for role in member.roles)


def can_create_vote(member: discord.Member, ladder: GuildVoteLadder) -> bool:
    if ladder.vote_ladder_label == "public":
        return is_staff(member)
    return member_has_ladder_role(member, ladder)


def can_vote(member: discord.Member, ladder: GuildVoteLadder) -> bool:
    if ladder.vote_ladder_label == "public":
        return True
    return member_has_ladder_role(member, ladder)


def compute_result(
    options: list[str], totals: list[int], minimum: int
) -> tuple[str, str, Optional[int]]:
    if not totals or sum(totals) == 0:
        return "failed", "No votes were cast.", None

    highest = max(totals)
    leaders = [i for i, t in enumerate(totals) if t == highest]

    if len(leaders) > 1:
        return "drew", "Tie between: " + ", ".join(options[i] for i in leaders), None

    winner = leaders[0]
    if highest < minimum:
        return "failed", f"Did not meet the upvote threshold of {minimum}.", winner

    return "passed", f"`{options[winner]}` won with {highest} votes.", winner


class VoteButtons(discord.ui.View):
    def __init__(self, vote_entry: "VoteEntry", timeout: int):
        super().__init__(timeout=timeout)
        self.vote_entry = vote_entry
        vote_entry.view = self
        self._rebuild_buttons()

    def _rebuild_buttons(self):
        self.clear_items()
        for index, option in enumerate(self.vote_entry.vote.options):
            self.add_item(VoteButton(option, index))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        try:
            await self.vote_entry.message.edit(view=self)
        except discord.HTTPException:
            pass  # Message might have been deleted
        await self.vote_entry.check_final_criteria()


class VoteButton(discord.ui.Button):
    def __init__(self, label: str, index: int):
        super().__init__(style=discord.ButtonStyle.primary, label=label[:80])
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view: VoteButtons = self.view
        entry = view.vote_entry

        if entry.vote.finished:
            await interaction.response.send_message(
                content="This vote has already finished.", ephemeral=True
            )
            return

        ladder = entry.vote.vote_ladder_id
        member = interaction.user
        if not isinstance(member, discord.Member) or not can_vote(member, ladder):
            await interaction.response.send_message(
                content="You do not have permission to vote in this voteladder.",
                ephemeral=True,
            )
            return

        await entry.cast_vote(user_id=member.id, option_index=self.index)

        await interaction.response.send_message(
            content=f"You voted for `{entry.vote.options[self.index]}`.", ephemeral=True
        )

        await entry.update_message()


class VoteEntry:
    def __init__(self, bot: commands.Bot, vote: GuildVote, message: discord.Message):
        self.bot = bot
        self.vote = vote
        self.message = message
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self.view: Optional["VoteButtons"] = None

    async def cast_vote(self, user_id: int, option_index: int):
        async with self._lock:
            if self.vote.finished:
                return

            key = str(user_id)

            # Remove old vote if exists
            if key in self.vote.voters:
                old_index = self.vote.voters[key]
                self.vote.totals[old_index] -= 1

            # Add new vote
            self.vote.voters[key] = option_index
            self.vote.totals[option_index] += 1

            await self.vote.save()
        await self.check_final_criteria()

    async def update_message(self):
        total_votes = sum(self.vote.totals)

        lines = [
            f"**{option}** - {count}"
            for option, count in zip(self.vote.options, self.vote.totals)
        ]

        embed = discord.Embed(
            title="Vote",
            description=(
                f"{self.vote.message}\n\n"
                + "\n".join(lines)
                + f"\n\nTotal Votes: **{total_votes}**"
            ),
            color=discord.Color.blurple(),
        )

        footer = f"Vote ID: {self.vote.vote_id}"
        if self.vote.finished:
            footer += " | Voting has ended."
        embed.set_footer(text=footer)

        try:
            await self.message.edit(embed=embed)
        except discord.HTTPException:
            pass

    async def check_final_criteria(self):
        async with self._lock:
            if self.vote.finished:
                return

            now = int(datetime.utcnow().timestamp())
            ladder = self.vote.vote_ladder_id

            leading = max(self.vote.totals) if self.vote.totals else 0
            met_threshold = leading >= ladder.threshold
            expired = now >= self.vote.expiry

            if not (met_threshold or expired):
                return

            self.vote.finished = True
            await self.vote.save()

        await self._disable_buttons()
        await self.update_message()
        await self._announce_result()

        if self._task:
            self._task.cancel()

    async def _disable_buttons(self):
        if self.view is None:
            return
        for item in self.view.children:
            item.disabled = True
        try:
            await self.message.edit(view=self.view)
        except discord.HTTPException:
            pass  # Message might have been deleted

    async def _announce_result(self, ladder: GuildVoteLadder = None):
        channel = self.bot.get_channel(ladder.channel_id)
        if not channel:
            return

        result, reason, _winner = compute_result(
            self.vote.options, self.vote.totals, ladder.minimum
        )

        await channel.send(f"Update on vote `{self.vote.vote_id}`:\n**{result}**. {reason}")

    def start_scheduler(self):
        delay = max(0, self.vote.expiry - int(datetime.utcnow().timestamp() * 1000)) / 1000
        self._task = asyncio.create_task(self.__expire_after(delay))

    async def __expire_after(self, delay: float):
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return
        await self.check_final_criteria()


class VoteCache:
    def __init__(self):
        self.votes: Dict[int, VoteEntry] = {}

    def register(self, message_id: int, vote_entry: VoteEntry):
        self.votes[message_id] = vote_entry

    def get(self, message_id: int) -> Optional[VoteEntry]:
        return self.votes.get(message_id)

    def remove(self, message_id: int):
        self.votes.pop(message_id, None)


class Voting(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cache = VoteCache()

    async def cog_load(self):
        unfinished = await GuildVote.filter(finished=False).prefetch_related("vote_ladder_id")

        for vote in unfinished:
            ladder = vote.vote_ladder_id

            channel = self.bot.get_channel(ladder.channel_id)
            if not channel:
                continue

            try:
                message = await channel.fetch_message(vote.message_id)
            except (discord.NotFound, discord.HTTPException):
                # if message is gone, vote can never resolve so mark as finished
                vote.finished = True
                await vote.save()
                continue

            vote_entry = VoteEntry(self.bot, vote, message)
            view = VoteButtons(vote_entry, timeout=None)
            try:
                await message.edit(view=view)
            except discord.HTTPException:
                pass

            vote_entry.start_scheduler()
            self.cache.register(message.id, vote_entry)

    @staticmethod
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

        return {
            "d": value * 86400,
            "h": value * 3600,
            "m": value * 60,
            "s": value,
        }[unit]

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

        roles = ladder.vote_ladder_roles or []
        if role.id in roles:
            await ctx.send(f"Role {role.mention} is already assigned to `{ladder_name}`.")
            return

        roles.append(role.id)
        ladder.vote_ladder_roles = roles
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
                value=(
                    f"Channel: {channel_mention}\n"
                    f"Roles: {roles_display}\n"
                    f"Threshold: {ladder.threshold}\n"
                    f"Minimum: {ladder.minimum}\n"
                    f"Timeout: {ladder.timeout} seconds"
                ),
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def vote(self, ctx: commands.Context, ladder_name: str, *, text: str):
        # start a new yes/no vote on a ladder. use `voteoptions` to chnage to custom options
        ladder = await GuildVoteLadder.get_or_none(vote_ladder_label=ladder_name)

        if not ladder:
            await ctx.send("Vote ladder not found.")
            return

        if not isinstance(ctx.author, discord.Member) or not can_create_vote(
            ctx.author, ladder
        ):
            await ctx.send("You do not have permission to create a vote in this voteladder.")
            return

        target_channel = ctx.guild.get_channel(ladder.channel_id)

        expiry = int(datetime.utcnow().timestamp()) + ladder.timeout

        embed = discord.Embed(title="Vote", description=text, color=discord.Color.blurple())

        # send message
        message = await target_channel.send(embed=embed)

        # create vote with message_id
        vote = await GuildVote.create(
            message=text,
            message_id=message.id,  # ← THIS FIXES IT
            options=["Yes", "No"],
            totals=[0, 0],
            voters={},
            expiry=expiry,
            finished=False,
            vote_ladder_id=ladder,
        )

        vote_entry = VoteEntry(self.bot, vote, message)
        view = VoteButtons(vote_entry, timeout=ladder.timeout)

        await message.edit(view=view)
        await vote_entry.update_message()

        vote_entry.start_scheduler()
        self.cache.register(message.id, vote_entry)

        confirmation = f"Vote `{vote.vote_id}` started in {target_channel.mention}."
        await ctx.send(confirmation)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def voteoptions(self, ctx, ladder_name: str, vote_id: int, *options):
        # replace the options on an existing, unfinished vote and reset its timer.
        vote = await GuildVote.get_or_none(vote_id=vote_id).prefetch_related("vote_ladder_id")

        if not vote:
            await ctx.send("Vote not found.")
            return

        if vote.finished:
            await ctx.send("This vote has already finished.")
            return

        ladder = vote.vote_ladder_id
        if not isinstance(ctx.author, discord.Member) or not can_create_vote(
            ctx.author, ladder
        ):
            await ctx.send("You do not have permission to modify this vote.")
            return

        if len(options) < 2:
            await ctx.send("You must provide at least 2 options.")
            return

        # Replace options
        vote.options = list(options)
        vote.totals = [0] * len(options)
        vote.voters = {}
        vote.expiry = int(datetime.utcnow().timestamp()) + ladder.timeout
        vote.finished = False

        await vote.save()

        entry = self.cache.get(vote.message_id)
        if entry is None:
            await ctx.send(
                "Vote entry not found in cache. Please restart the bot to refresh the cache."
            )
            return

        if entry._task:
            entry._task.cancel()

        entry.vote = vote
        new_view = VoteButtons(entry, timeout=None)

        try:
            await entry.message.edit(view=new_view)
        except discord.HTTPException:
            pass

        await entry.update_message()
        entry.start_scheduler()

        await ctx.send(f"Vote {vote_id} updated with new options and timer reset.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Voting(bot))
