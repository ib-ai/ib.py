import asyncio
from typing import Union, Optional
from collections.abc import Callable, Mapping

import discord
from discord.ext import commands
from discord.app_commands import describe

from tortoise import timezone
from tortoise.functions import Max
from db.models import PunishmentType, StaffPunishment, StaffNote
from db.cached import get_guild_data

from utils.commands import available_subcommands
from utils.converters import DatetimeConverter
from utils.time import long_sleep_until, format_timestamp

import logging
logger = logging.getLogger(__name__)

UNKNOWN = "???"
punishment_format = {
    PunishmentType.KICK: "Kick :boot:",
    PunishmentType.MUTE: "Mute :zipper_mouth:",
    PunishmentType.BAN: "Ban :hammer:",
    PunishmentType.UNKNOWN: UNKNOWN,
}
revocation_format = {
    PunishmentType.KICK: UNKNOWN,
    PunishmentType.MUTE: "Unmute :speaking_head:",
    PunishmentType.BAN: "Unban :angel:",
    PunishmentType.UNKNOWN: UNKNOWN,
}


reasonflags: Mapping[str, Callable] = {}
def reasonflag(*flags: str):
    def decorator(f):
        for flag in flags:
            reasonflags[flag] = f
        return f
    return decorator

@reasonflag('-redact', '-redacted')
def redact(reason: str) -> tuple[str, bool]:
    return reason.replace('-redact', '').strip(), True

@reasonflag('-r5')
def rule_5(reason: str) -> tuple[str, bool]:
    return "Rule 5. Academic Dishonesty is strictly prohibited.", True

@reasonflag('-banevasion')
def ban_evasion(reason: str) -> tuple[str, bool]:
    return "Ban evasion is strictly prohibited.", True


def punishment_message(punishment: StaffPunishment, redact: bool):
    user_mention = f'<@{punishment.user_id}>'
    user_display = punishment.user_display
    user_id      = punishment.user_id
    if redact and punishment.redacted:
        user_mention = '[REDACTED]'
        user_display = '[REDACTED]'
        user_id      = '[REDACTED]'
    return f'**Case: #{punishment.punishment_id} | {punishment_format[punishment.punishment_type]}**\n' \
         + f'**Offender: **{user_mention} (User: {user_display}, ID: {user_id})\n' \
         + f'**Moderator: **{punishment.staff_display} (ID: {punishment.staff_id})\n' \
         + f'**Reason: **{punishment.reason}'

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.active = {}
    
    async def handle_punishment_expiration(self, punishment: StaffPunishment):
        punishment_type = punishment.punishment_type
        await long_sleep_until(punishment.expiry)
        if punishment_type == PunishmentType.BAN:
            guild = self.bot.get_guild(punishment.guild_id)
            user = await self.bot.fetch_user(punishment.user_id)
            await guild.unban(user, reason=f'Punishment case no. {punishment.punishment_id} expired.')
        elif punishment_type == PunishmentType.MUTE:
            pass  # leaving this for now
    
    def removal_callback(self, id: int):
        def callback(task: asyncio.Task):
            del self.active[id]
        return callback

    async def schedule_existing_punishment_expirations(self):
        pass  # TODO: implement this
    
    async def publish_punishment_log(self, punishment_type: PunishmentType, entry: discord.AuditLogEntry):
        guild_data = await get_guild_data(guild_id=entry.guild.id)
        if not guild_data:
            return

        public_log = guild_data.modlog_id
        internal_log = guild_data.modlog_staff_id
        if not public_log and not internal_log:
            return  # nowhere to publish

        reason, redact = self.parse_reason_redact(entry.reason or '')
        offender = entry.target if isinstance(entry.target, discord.User) else await self.bot.fetch_user(entry.target.id)
        punishment = await StaffPunishment.create(
            punishment_type = punishment_type,
            guild_id = entry.guild.id,
            user_display = f'{offender.name}#{offender.discriminator}',
            user_id = offender.id,
            staff_display = f'{entry.user.name}#{entry.user.discriminator}',
            staff_id = entry.user.id,
            reason = reason,
            redacted = redact,
        )

        if not reason:
            punishment.reason = f'Use `{guild_data.prefix}reason {punishment.punishment_id} <reason>` to specify a reason.'
            await punishment.save()

        if internal_log:
            log_message = punishment_message(punishment, redact=False)
            channel = self.bot.get_channel(internal_log)
            message_staff = await channel.send(log_message)
            punishment.message_staff_id = message_staff.id
            await punishment.save()

        if public_log:
            log_message = punishment_message(punishment, redact=True)
            channel = self.bot.get_channel(public_log)
            message = await channel.send(log_message)
            punishment.message_id = message.id
            await punishment.save()
    
    async def publish_revocation_log(self, punishment_type: PunishmentType, entry: discord.AuditLogEntry):
        guild_data = await get_guild_data(guild_id=entry.guild.id)
        if not guild_data:
            return

        public_log = guild_data.modlog_id
        internal_log = guild_data.modlog_staff_id
        if not public_log and not internal_log:
            return  # nowhere to publish

        pardoned = entry.target if isinstance(entry.target, discord.User) else await self.bot.fetch_user(entry.target.id)
        if public_log:
            log_message = f'**{revocation_format[punishment_type]}**\n' \
                        + f'**Pardoned: **<@{pardoned.id}> (User: {pardoned.name}#{pardoned.discriminator}, ID: {pardoned.id})\n' \
                        + f'**Moderator: **{entry.user.name}#{entry.user.discriminator} (ID: {entry.user.id})'
            channel = self.bot.get_channel(public_log)
            message = await channel.send(log_message)

    @staticmethod
    def parse_reason_redact(reason: str):
        reason = reason.strip()
        if not reason:
            return reason, False

        end_token = reason.split()[-1]
        for flag, updated in reasonflags.items():
            if end_token == flag:
                return updated(reason)
        return reason, False

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        if entry.action == discord.AuditLogAction.kick:
            await self.publish_punishment_log(PunishmentType.KICK, entry)
        elif entry.action == discord.AuditLogAction.ban:
            await self.publish_punishment_log(PunishmentType.BAN, entry)
        elif entry.action == discord.AuditLogAction.unban:
            await self.publish_revocation_log(PunishmentType.BAN, entry)
        elif entry.action == discord.AuditLogAction.member_role_update:
            pass  # leave this for now, TODO: look into timeouts

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        Log message edits.
        """
        utilities = f"[21 Jump Street]({after.jump_url})\n" \
                  + f"User: {after.author.mention}"
        embed_data = dict(
            author = dict(
                name = f'{after.author.name}#{after.author.discriminator} (ID: {after.author.id}) edited in #{after.channel.name}',
            ),
            color = discord.Colour.yellow().value,
            fields = [
                dict(name="From", value=before.content),
                dict(name="To", value=after.content),
                dict(name="Utilities", value=utilities)
            ]
        )
        embed = discord.Embed.from_dict(embed_data)

        guild_data = await get_guild_data(guild_id=after.guild.id)
        if not guild_data:
            return
        
        log_channel = self.bot.get_channel(guild_data.logs_id)
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """
        Log message deletes.
        """
        utilities = f"User: {message.author.mention}"
        embed_data = dict(
            author = dict(
                name = f'{message.author.name}#{message.author.discriminator} (ID: {message.author.id}) edited in #{message.channel.name}',
            ),
            color = discord.Colour.red().value,
            description = message.content,
            fields = [
                dict(name="Utilities", value=utilities)
            ]
        )
        embed = discord.Embed.from_dict(embed_data)

        guild_data = await get_guild_data(guild_id=message.guild.id)
        if not guild_data:
            return
        
        log_channel = self.bot.get_channel(guild_data.logs_id)
        await log_channel.send(embed=embed)


    @commands.hybrid_command()
    @describe(user='User to ban', reason='Reason for ban')
    async def blacklist(self, ctx: commands.Context, user: discord.User, *, reason: str):
        """
        Blacklist a user that is not in the server.
        """ 
        if user in ctx.guild.members:
            await ctx.send("User is in the server. Please use Discord's built-in moderation tools.")
            return

        await ctx.guild.ban(user, reason=reason)
        await ctx.send(f'Banned {user} for `{reason}`.')
    
    @commands.hybrid_command()
    async def expire(self, ctx: commands.Context, case_number: int, terminus: DatetimeConverter):
        """
        Set a duration for a punishment. Equivalently, schedule the revokement of a punishment.
        """
        punishment = await StaffPunishment.filter(punishment_id=case_number).get_or_none()
        if not punishment:
            await ctx.send(f"Case #{case_number} does not exist.")
            return

        if punishment.punishment_type not in (
                PunishmentType.BAN,
                PunishmentType.MUTE,
            ):
            await ctx.send(f'Expiration is not supported for this punishment type: `{punishment.punishment_type}`.')
            return

        punishment.expiry = terminus
        await punishment.save()

        task = asyncio.create_task(self.handle_punishment_expiration(punishment))
        self.active[punishment.punishment_id] = task
        task.add_done_callback(self.removal_callback(punishment.punishment_id))
        await ctx.send(f'Punishment expiry set for {format_timestamp(terminus)} ({format_timestamp(terminus, "R")}).')

    
    @commands.hybrid_command()
    async def history(self, ctx: commands.Context, user_id: int):
        """
        Display a user's punishment history.
        """
        guild_data = await get_guild_data(guild_id=ctx.guild.id)
        modlog = self.bot.get_channel(guild_data.modlog_id)
        if not modlog:
            # TODO: do some logging
            return

        embed = discord.Embed(description=f"History of <@{user_id}>.")
        punishments = await StaffPunishment.all()
        for punishment in punishments:
            if punishment.user_id == user_id:
                timestamp = UNKNOWN
                try:
                    modlog_message = await modlog.fetch_message(punishment.message_id)
                    timestamp = format_timestamp(modlog_message.created_at, 'd')
                except discord.NotFound:
                    logger.error(f'Message ({punishment.message_id}) not found in modlog ({modlog.id}).')
                except discord.Forbidden:
                    logger.error(f'Permission denied to read messages in modlog.')
                except discord.HTTPException:
                    logger.error('An error occurred while fetching the message.')

                embed.add_field(
                    name = f"Case #{punishment.punishment_id} ({timestamp}) - By {punishment.staff_display}",
                    value = f"{punishment_format[punishment.punishment_type]} - {punishment.reason}",
                    inline = False
                )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command()
    async def lookup(self, ctx: commands.Context, case_number: int):
        """
        Retrieve punishment case by case number.
        """
        punishment = await StaffPunishment.filter(punishment_id=case_number).get_or_none()
        if not punishment:
            await ctx.send(f"Case #{case_number} does not exist.")
            return
        content = punishment_message(punishment, redact=False)
        await ctx.send(content)
    
    @commands.hybrid_command()
    async def note(self, ctx: commands.Context, user: discord.User, note: Optional[str] = None):
        """
        Save a note on a user.
        """
        if note:
            await StaffNote.create(
                user_id = user.id,
                author_id = ctx.author.id,
                note = note
            )
            await ctx.send(f"The note has been added.")
        else:
            embed = discord.Embed(description=f"Notes for {user.mention}.")
            notes = await StaffNote.all()
            for note in notes:
                if note.user_id == user.id:
                    author = self.bot.get_user(note.author_id)
                    author_display = f'{author.name}#{author.discriminator}' if author else UNKNOWN
                    time_display = format_timestamp(note.timestamp, 'd') if note.timestamp else UNKNOWN
                    embed.add_field(
                        name = f"Entry by {author_display} (on {time_display}):",
                        value = note.note,
                        inline = False
                    )
            await ctx.send(embed=embed)
    
    @commands.group(invoke_without_command=True)
    async def purge(self, ctx: commands.Context):
        """
        Commands for bulk deletion.
        """
        await available_subcommands(ctx)
    
    @purge.command()
    async def message(self, ctx: commands.Context, number: int):
        """
        Bulk delete messages.
        """
        async for message in ctx.channel.history(limit=number):
            try:
                await message.delete()
            except discord.Forbidden:
                await ctx.send('I do not have permission to delete messages.')
                return
            except discord.HTTPException:
                await ctx.send('An error occurred while deleting messages.')
                return
        await ctx.send(f'Deleted {number} messages.', delete_after=5)
    
    @purge.command()
    async def reaction(self, ctx: commands.Context, channel: discord.TextChannel, message_id: int, emoji: discord.Emoji):
        """
        Bulk delete reactions.
        """ 
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send('Message not found.')
            return
        except discord.Forbidden:
            await ctx.send('I do not have permission to read messages in that channel.')
            return
        except discord.HTTPException:
            await ctx.send('An error occurred while fetching the message.')
            return

        try:
            await message.clear_reaction(emoji)
        except discord.Forbidden:
            await ctx.send('I do not have permission to delete reactions.')
            return
        except discord.NotFound:
            await ctx.send('The emoji you specifiied was not found.')
            return
        except TypeError:
            await ctx.send('The emoji you specified is invalid.')
            return
        except discord.HTTPException:
            await ctx.send('An error occurred while deleting reactions.')
            return
        
        await ctx.send(f'Deleted reactions to {message_id} with emoji {emoji}.')

    @commands.hybrid_command()
    async def reason(self, ctx: commands.Context, case_number: int, *, reason: str):
        """
        Set a reason for a punishment case.
        """
        punishment = await StaffPunishment.filter(punishment_id=case_number).get_or_none()
        if not punishment:
            await ctx.send(f"Case #{case_number} does not exist.")
            return
        
        reason, redact = self.parse_reason_redact(reason)
        punishment.reason = reason
        punishment.redacted = redact
        await punishment.save()

        new_message = punishment_message(punishment, redact=True)
        guild_data = await get_guild_data(guild_id=ctx.guild.id)
        modlog = self.bot.get_channel(guild_data.modlog_id)
        if modlog:
            modlog_message = await modlog.fetch_message(punishment.message_id)
            await modlog_message.edit(content=new_message)

        new_message = punishment_message(punishment, redact=False)
        guild_data = await get_guild_data(guild_id=ctx.guild.id)
        modlog_staff = self.bot.get_channel(guild_data.modlog_staff_id)
        if modlog_staff:
            modlog_staff_message = await modlog_staff.fetch_message(punishment.message_staff_id)
            await modlog_staff_message.edit(content=new_message)

        await ctx.send(f'Case #{case_number} reason updated: "{reason}"')


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))