import asyncio
from datetime import datetime
from discord.ext import commands
import discord
from discord import app_commands
from db.models import GuildVote, GuildVoteLadder
from pagination.pagination import Pagination

from utils.utime import parse_duration

class VoteLadderListPagination(Pagination):
    def build_field(self, embed: discord.Embed, index, value):
        embed.add_field(name="#{}".format(index), value=value, inline=False)

class VoteLadder(commands.GroupCog, name = "voteladder"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()
    
    @app_commands.command(name = "create", description="Creates a voteladder.")
    @commands.has_guild_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def voteladder_create(self, interaction: discord.Interaction, ladder_name: str):
        vote_ladder = await GuildVoteLadder.query.where(GuildVoteLadder.ladder_label == ladder_name.lower()).gino.first()

        if vote_ladder:
            await interaction.response.send_message("A voteladder with that name already exists.")
            return
        
        await GuildVoteLadder.create(ladder_label=ladder_name.lower())

        await interaction.response.send_message("The voteladder \" {} \" has been created.".format(ladder_name.lower()))
    
    @app_commands.command(name = "delete", description="Deletes a voteladder.")
    @commands.has_guild_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def voteladder_delete(self, interaction: discord.Interaction, ladder_name: str):
        vote_ladder = await GuildVoteLadder.query.where(GuildVoteLadder.ladder_label == ladder_name.lower()).gino.first()

        if not vote_ladder:
            await interaction.response.send_message("That ladder does not exist.")
            return

        await vote_ladder.delete()

        await interaction.response.send_message("The voteladder \" {} \" has been deleted.".format(ladder_name.lower()))

    @app_commands.command(name = "list", description="Lists your voteladders.")
    @commands.has_guild_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def voteladder_list(self, interaction: discord.Interaction):
        voteladders_list = await GuildVoteLadder.query.gino.all()

        voteladders = [voteladder.ladder_label for voteladder in voteladders_list]

        voteladders_embed, voteladders_view = VoteLadderListPagination(interaction, voteladders).return_paginated_embed()
        
        await interaction.response.send_message(embed=voteladders_embed, view=voteladders_view)

    @app_commands.command(name = "channel", description="Set channel for specified voteladder.")
    @commands.has_guild_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def voteladder_channel(self, interaction: discord.Interaction, ladder_name: str, channel: discord.TextChannel):
        vote_ladder = await GuildVoteLadder.query.where(GuildVoteLadder.ladder_label == ladder_name.lower()).gino.first()

        if not vote_ladder:
            await interaction.response.send_message("That ladder does not exist.")
            return
        
        await vote_ladder.update(channel_id=channel.id).apply()
        await interaction.response.send_message("The channel for voteladder \" {} \" has been set to {}.".format(ladder_name.lower(), channel.mention))
    
    @app_commands.command(name = "duration", description="Set duration for specified voteladder.")
    @commands.has_guild_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def voteladder_duration(self, interaction: discord.Interaction, ladder_name: str, duration: str):
        vote_ladder = await GuildVoteLadder.query.where(GuildVoteLadder.ladder_label == ladder_name.lower()).gino.first()

        if not vote_ladder:
            await interaction.response.send_message("That ladder does not exist.")
            return

        time = parse_duration(duration, seconds = True)
        
        await vote_ladder.update(timeout = time).apply()
        await interaction.response.send_message("The duration for voteladder \" {} \" has been set to {} seconds.".format(ladder_name.lower(), time))

    @app_commands.command(name = "threshold", description="Set threshold for specified voteladder.")
    @commands.has_guild_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def voteladder_threshold(self, interaction: discord.Interaction, ladder_name: str, threshold: int = None):
        vote_ladder = await GuildVoteLadder.query.where(GuildVoteLadder.ladder_label == ladder_name.lower()).gino.first()

        if not vote_ladder:
            await interaction.response.send_message("That ladder does not exist.")
            return
        
        await vote_ladder.update(threshold = threshold).apply()
        await interaction.response.send_message("The threshold for voteladder \" {} \" has been {}.".format(ladder_name.lower(), f"set to f{threshold}" if threshold else "removed"))

    @app_commands.command(name = "minimum", description="Set minimum for specified voteladder.")
    @commands.has_guild_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def voteladder_minimum(self, interaction: discord.Interaction, ladder_name: str, minimum: int = None):
        vote_ladder = await GuildVoteLadder.query.where(GuildVoteLadder.ladder_label == ladder_name.lower()).gino.first()

        if not vote_ladder:
            await interaction.response.send_message("That ladder does not exist.")
            return
        
        await vote_ladder.update(minimum = minimum).apply()
        await interaction.response.send_message("The minimum for voteladder \" {} \" has been {}.".format(ladder_name.lower(), f"set to f{minimum}" if minimum else "removed"))

    @app_commands.command(name = "role", description="Set alternate role for specified voteladder.")
    @commands.has_guild_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def voteladder_minimum(self, interaction: discord.Interaction, ladder_name: str, role: discord.Role = None):
        vote_ladder = await GuildVoteLadder.query.where(GuildVoteLadder.ladder_label == ladder_name.lower()).gino.first()

        if not vote_ladder:
            await interaction.response.send_message("That ladder does not exist.")
            return
        
        await vote_ladder.update(ladder_role = role.id).apply()
        await interaction.response.send_message("The role for voteladder \" {} \" has been {}.".format(ladder_name.lower(), f"set to f{role.name}" if role else "removed"))

async def create_vote(bot: commands.Bot, voteladder: GuildVoteLadder, vote: str) -> GuildVote | None:
    channel = bot.get_channel(voteladder.channel_id)

    if not channel: return None

    expiry = int(datetime.utcnow().timestamp()) + voteladder.timeout

    vote_entry = await GuildVote.create(message=vote, ladder_id=voteladder.ladder_id, expiry=expiry)

    message = await channel.send("{}) {}".format(vote.vote_id, vote_entry))

    await vote_entry.update(message_id = message.id).apply()
    await schedule_vote(bot, vote_entry)

    await message.add_reaction("\uD83D\uDC4D")
    await message.add_reaction("\uD83D\uDC4E")

    return vote_entry

async def schedule_vote(bot: commands.Bot, vote_entry: GuildVote):
    await asyncio.sleep(vote_entry.expiry - int(datetime.utcnow().timestamp()))
    await meets_final_criteria(bot, vote_entry)

async def meets_final_criteria(bot: commands.Bot, vote_entry: GuildVote):
    if vote_entry.finished:
        return
    
    voteladder: GuildVoteLadder = await GuildVoteLadder.get(vote_entry.ladder_id)

    yes = vote_entry.positive
    no = vote_entry.negative

    if yes >= voteladder.threshold or no >= voteladder.threshold or datetime.utcnow().timestamp() > vote_entry.expiry:
        channel = bot.get_channel(voteladder.channel_id)

        if yes > no:
            if yes < voteladder.minimum:
                text = "failed"
                reason = "Did not meet upvote threshold."
            else:
                text = "passed"
        elif no > yes:
            text = "failed"
            reason = "More downvotes than upvotes."
        else:
            text = "drew"
        
        if channel:
            await channel.send("Update on vote `{}/{}`: {}. {}".format(voteladder.ladder_label, vote_entry.vote_id, text, reason))

    await vote_entry.update(finished = True).apply()

async def setup(bot: commands.Bot):
    await bot.add_cog(VoteLadder(bot))