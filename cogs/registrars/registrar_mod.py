import asyncio
from datetime import datetime
from discord.ext import commands
import discord
from cogs.commands.voteladder import create_vote
from cogs.listeners.punishment_listener import get_log_punishment, get_punishment_type_display
from db.models import GuildVote, GuildVoteLadder, PunishmentType, StaffNote, StaffPunishment

from utils.uguild import get_guild_data, mods_or_manage_guild
from utils.utime import parse_duration

class RegistrarMod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    # Updates

    @commands.command()
    @mods_or_manage_guild()
    @commands.guild_only()
    async def reason(self, ctx: commands.Context, case: int, reason: str):
        punishment = await StaffPunishment.get(case)

        if not punishment:
            await ctx.send("The case number provided does not exist.")
            return

        previous_reason = punishment.reason

        await punishment.update(reason = reason).apply()
        
        await ctx.send("The reason for case {} has been changed. `{}` -> `{}`".format(case, previous_reason, reason))
    
    @commands.command()
    @mods_or_manage_guild()
    @commands.guild_only()
    async def lookup(self, ctx: commands.Context, case: int):
        punishment = await StaffPunishment.get(case)

        if not punishment:
            await ctx.send("The case number provided does not exist.")
            return
        
        await ctx.send(get_log_punishment(punishment, False))

    @commands.command()
    @mods_or_manage_guild()
    @commands.guild_only()
    async def note(self, ctx: commands.Context, member: discord.Member, *, note: str = None):
        notes_list = await StaffNote.query.where(StaffNote.user_id == member.id).gino.all()

        if not note:
            notes_embed = discord.Embed(description="Here are the notes for {}.".format(member.mention))

            for note in notes_list:
                staff = ctx.guild.get_member(note.author_id)
                notes_embed.add_field(
                    name="Entry by {} (on {}):".format(str(staff) if staff else note.author_id, note.timestamp.strftime("%d/%m/%y")),
                    value=note.data,
                    inline=False
                )
            
            await ctx.send(embed=notes_embed)
            return

        if len(notes_list) >= 25:
            await ctx.send("There are already too many notes on this user (Discord limitation).")
            return
        
        if len(note) > 1024:
            await ctx.send("Your note is too long! Please make it less than 1024 characters (currently {} characters).".format(len(note)))
            return
        
        await StaffNote.create(user_id=member.id, author_id=ctx.author.id, data=note)
        await ctx.send("The note has been added.")
    
    @commands.command()
    @mods_or_manage_guild()
    @commands.guild_only()
    async def history(self, ctx: commands.Context, user: discord.User):
        punishments = await StaffPunishment.query.where(user_id = user.id).gino.all()
        modlog_channel = ctx.guild.get_channel(await get_guild_data(ctx.guild, "modlog_id"))

        history_embed = discord.Embed(title="History Of {}".format(str(user)))

        for punishment in punishments:
            message = modlog_channel.get_partial_message(punishment.message_id)
            history_embed.add_field(
                title="Case {} ({}) - By {}".format(punishment.punishment_id, message.created_at.strftime("%d/%m/%y") if message else "???", punishment.staff_display),
                value="{} - {}".format(get_punishment_type_display(punishment.punishment_type), punishment.reason),
                inline=False
            )
        
        await ctx.send(embed=history_embed)

    @commands.command()
    @commands.guild_only()
    async def vote(self, ctx: commands.Context, ladder_name: str, *, vote: str):
        vote_ladder = await GuildVoteLadder.query.where(GuildVoteLadder.ladder_label == ladder_name.lower()).gino.first()
        moderator_role_id = await get_guild_data(ctx.guild, "moderator_id")

        if vote_ladder:
            await ctx.send("A voteladder with that name already exists.")
            return
        
        if ctx.author.id != moderator_role_id or ctx.author.id != vote_ladder.ladder_role or not ctx.author.guild_permissions.manage_guild:
            await ctx.send("You do not have sufficient permissions to execute this command.")
            return
        
        vote_entry = await create_vote(ctx.bot, vote_ladder, vote)

        if not vote_entry:
            await ctx.send("Invalid or no channel specified for voteladder \" {} \".".format(vote_ladder.ladder_label))
            return

        await ctx.send("Created vote `{}:{}`.".format(vote_ladder.ladder_label, vote_entry.vote_id))

    @commands.command()
    @mods_or_manage_guild()
    @commands.guild_only()
    async def expire(self, ctx: commands.Context, case_id: int, duration: str):
        punishment: StaffPunishment = await StaffPunishment.get(case_id)

        if not punishment:
            await ctx.send("The case number provided does not exist.")
            return
        
        if punishment.punishment_type != PunishmentType.BAN or punishment.punishment_type != PunishmentType.MUTE:
            await ctx.send("The case number provided is not a ban or a mute.")
            return

        expiry = parse_duration(duration)

        await punishment.update(expiry = expiry).apply()
        await schedule_expiry(ctx.guild, punishment)
        await ctx.send("The expiration has been scheduled to <t:{}>.".format(int(expiry.timestamp())))

    async def cog_command_error(self, ctx, error: commands.CommandError):
        # ! More robust error checking
        if isinstance(error, commands.ChannelNotFound):
            await ctx.send(error)
        else:
            await ctx.send(error)

async def schedule_expiry(guild: discord.Guild, punishment: StaffPunishment):
    await asyncio.sleep(int(punishment.expiry.timestamp()) - int(datetime.utcnow().timestamp()))
    
    match punishment.punishment_type:
        case PunishmentType.BAN:
            await guild.unban(punishment.user_id)
        case PunishmentType.MUTE:
            user: discord.Member = await guild.get_member(punishment.user_id)

            if user:
                mute_role_id = await get_guild_data(guild, "mute_id")
                await user.remove_roles(mute_role_id)
    
        
async def setup(bot: commands.Bot):
    await bot.add_cog(RegistrarMod(bot))