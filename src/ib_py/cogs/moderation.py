import asyncio
import logging
from collections.abc import Callable, Mapping
from datetime import timedelta
from typing import Optional

import discord
from discord import app_commands
from discord.app_commands import describe
from discord.ext import commands
from discord.utils import format_dt
from tortoise import timezone

from ..config import IBPyConfig
from ..db.cached import get_guild_data
from ..db.models import MemberRole, PunishmentType, StaffNote, StaffPunishment
from ..utils.commands import available_subcommands
from ..utils.converters import DatetimeConverter
from ..utils.time import long_sleep_until

CHAT_MOD_CHANNEL_ID = 1530943314386485428

config = IBPyConfig()
config.requires("prefix", "sticky_roles")

logger = logging.getLogger(__name__)

UNKNOWN = "???"
punishment_format = {
    PunishmentType.WARN: "Warn :warning:",
    PunishmentType.KICK: "Kick :boot:",
    PunishmentType.TIMEOUT: "Timeout :hourglass_flowing_sand:",
    PunishmentType.MUTE: "Mute :zipper_mouth:",
    PunishmentType.BAN: "Ban :hammer:",
    PunishmentType.UNKNOWN: UNKNOWN,
}
revocation_format = {
    PunishmentType.WARN: UNKNOWN,
    PunishmentType.KICK: UNKNOWN,
    PunishmentType.TIMEOUT: "Untimeout :hourglass:",
    PunishmentType.MUTE: "Unmute :speaking_head:",
    PunishmentType.BAN: "Unban :angel:",
    PunishmentType.UNKNOWN: UNKNOWN,
}

APPEALS_SERVER_INVITE = "https://discord.gg/qSdu3Z4JfJ"
REJOIN_SERVER_INVITE = "https://discord.gg/ibo"

MESSAGE_DELETE_WINDOW = timedelta(hours=1)

BAN_REASON_PRESETS: Mapping[str, str] = {
    "compromised": "Account compromised.",
    "r5": "Rule 5. Academic Dishonesty is strictly prohibited.",
    "banevasion": "Ban evasion is strictly prohibited.",
    "spam": "Spam or unsolicited advertising is not allowed.",
    "nsfw": "Rule 4. Posting NSFW content in violation of server rules.",
}

reasonflags: Mapping[str, Callable] = {}


def reasonflag(*flags: str):
    def decorator(f):
        for flag in flags:
            reasonflags[flag] = f
        return f

    return decorator


@reasonflag("-redact", "-redacted")
def redact(reason: str) -> tuple[str, bool]:
    return reason.replace("-redacted", "").replace("-redact", "").strip(), True


@reasonflag("-r5")
def rule_5(reason: str) -> tuple[str, bool]:
    return "Rule 5. Academic Dishonesty is strictly prohibited.", False


@reasonflag("-banevasion")
def ban_evasion(reason: str) -> tuple[str, bool]:
    return "Ban evasion is strictly prohibited.", False


def punishment_message(punishment: StaffPunishment, redact: bool):
    user_mention = f"<@{punishment.user_id}>"
    user_display = punishment.user_display
    user_id = punishment.user_id
    if redact and punishment.redacted:
        user_mention = "[REDACTED]"
        user_display = "[REDACTED]"
        user_id = "[REDACTED]"

    notified_line = "Yes :white_check_mark:" if punishment.user_notified else "No :x:"
    return (
        f"**Case: #{punishment.punishment_id} | {punishment_format[punishment.punishment_type]}**\n"
        + f"**Offender: **{user_mention} (User: {user_display}, ID: {user_id})\n"
        + f"**Moderator: **{punishment.staff_display} (ID: {punishment.staff_id})\n"
        + f"**Reason: **{punishment.reason}"
        + f"**User notified: **{notified_line}"
    )


def _reason_autocomplete_choices(
    current: str, presets: Mapping[str, str]
) -> list[app_commands.Choice[str]]:
    current_lower = current.lower()
    choices = [
        app_commands.Choice(name=f"{label} \u2014 {text}", value=text)
        for label, text in presets.items()
        if current_lower in text.lower() or current_lower in label.lower()
    ]

    # let typed text through as its own choice so staff can select what they typed if preset not matched
    if current and not any(choice.value == current for choice in choices):
        choices.insert(0, app_commands.Choice(name=current, value=current))
    return choices[:25]


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.sticky_role_ids = config.sticky_roles

        self.active = {}
        self.incomplete_unmutes = {}

    async def cog_load(self) -> None:
        if not self.bot.is_ready():
            return

        await self.update_sticky_roles()
        await self.schedule_existing_punishment_expirations()
        logger.info("Existing punishment expirations queued.")
        await self.check_reapply_active_mutes()
        logger.info("Active mutes checked.")

    async def handle_punishment_expiration(self, punishment: StaffPunishment):
        await long_sleep_until(punishment.expiry)

        punishment_type = punishment.punishment_type
        if punishment_type == PunishmentType.BAN:
            guild = self.bot.get_guild(punishment.guild_id)
            user = await self.bot.fetch_user(punishment.user_id)
            await guild.unban(
                user, reason=f"Punishment case no. {punishment.punishment_id} expired."
            )
        elif punishment_type == PunishmentType.MUTE:
            guild = self.bot.get_guild(punishment.guild_id)
            member = guild.get_member(punishment.user_id)
            if not member:
                self.incomplete_unmutes[(punishment.guild_id, punishment.user_id)] = (
                    punishment.punishment_id
                )
                return  # user left the guild before unmute could be processed

            guild_data = await get_guild_data(guild_id=punishment.guild_id)
            mute_role = guild.get_role(guild_data.mute_id)
            if mute_role not in member.roles:
                return  # user was manually unmuted before expiration

            await member.remove_roles(
                mute_role, reason=f"Punishment case no. {punishment.punishment_id} expired."
            )

    def removal_callback(self, id: int):
        def callback(task: asyncio.Task):
            del self.active[id]

        return callback

    async def update_sticky_roles(self):
        updated_sticky_roles = []
        for role_id in config.sticky_roles:
            for guild in self.bot.guilds:
                role = discord.utils.get(guild.roles, id=role_id)
                if role:
                    break
            else:
                logger.warning(f"Sticky role with ID {role_id} not found in any guild.")
                continue

            bot_top_role = guild.me.top_role
            if role.position >= bot_top_role.position:
                logger.warning(
                    f'Sticky role "{role.name}" in guild "{guild.name}" '
                    f"is above or equal to the bot's top role in the hierarchy; "
                    f"role will not be sticky."
                )
                continue

            updated_sticky_roles.append(role_id)
        self.sticky_role_ids = updated_sticky_roles

    async def schedule_existing_punishment_expirations(self):
        # address punishments that expired in the past while the bot was offline
        punishments = await StaffPunishment.filter(
            expiry__isnull=False, expiry__lt=timezone.now(), expiry_complete=False
        )
        if not punishments:
            logger.debug("No existing punishments with expirations in the past.")

        async with asyncio.TaskGroup():
            for punishment in punishments:
                task = asyncio.create_task(self.handle_punishment_expiration(punishment))
                self.active[punishment.punishment_id] = task
                task.add_done_callback(self.removal_callback(punishment.punishment_id))

                punishment.expiry_complete = True
                await punishment.save()
                logger.debug(
                    f"Punishment expiration marked complete: id={punishment.punishment_id}"
                )

        # address punishments that are still pending expiration
        punishments = await StaffPunishment.filter(
            expiry__isnull=False, expiry__gte=timezone.now()
        )
        if not punishments:
            logger.debug("No existing punishments with expirations in the future.")
            return

        async with asyncio.TaskGroup():
            for punishment in punishments:
                if punishment.punishment_id in self.active:
                    logger.debug("Punishment expiration already scheduled. (skipping)")
                    continue

                user = self.bot.get_user(punishment.user_id) or await self.bot.fetch_user(
                    punishment.user_id
                )
                if not user:
                    logger.warning(f"User {punishment.user_id} not found. (skipping)")
                    continue

                task = asyncio.create_task(self.handle_punishment_expiration(punishment))
                self.active[punishment.punishment_id] = task
                task.add_done_callback(self.removal_callback(punishment.punishment_id))
                logger.debug(f"Punishment expiration scheduled: id={punishment.punishment_id}")
            logger.debug(f"Total punishment expirations scheduled: {len(self.active)}")

    async def check_reapply_active_mutes(self):
        active_mutes = await StaffPunishment.filter(
            punishment_type=PunishmentType.MUTE, expiry_complete=False
        ).all()
        for punishment in active_mutes:
            guild = self.bot.get_guild(punishment.guild_id)
            if not guild:
                continue

            member = guild.get_member(punishment.user_id)
            if not member:
                continue

            guild_data = await get_guild_data(guild_id=punishment.guild_id)
            if not guild_data or not guild_data.mute_id:
                continue

            mute_role = guild.get_role(guild_data.mute_id)
            if mute_role in member.roles:
                continue  # mute still active

            await member.add_roles(mute_role, reason="Reapplying active mute.")
            task = asyncio.create_task(self.handle_punishment_expiration(punishment))
            self.active[punishment.punishment_id] = task
            task.add_done_callback(self.removal_callback(punishment.punishment_id))

    async def publish_punishment_log(
        self, punishment_type: PunishmentType, entry: discord.AuditLogEntry
    ):
        guild_data = await get_guild_data(guild_id=entry.guild.id)
        if not guild_data:
            return

        public_log = guild_data.modlog_id
        internal_log = guild_data.modlog_staff_id
        if not public_log and not internal_log:
            return  # nowhere to publish

        # if bot itself performed underlying action, don't double log it
        if entry.user and entry.user.id == self.bot.user.id:
            return

        reason, redact = self.parse_reason_redact(entry.reason or "")
        offender = (
            entry.target
            if isinstance(entry.target, discord.User)
            else await self.bot.fetch_user(entry.target.id)
        )
        punishment = await StaffPunishment.create(
            punishment_type=punishment_type,
            guild_id=entry.guild.id,
            user_display=f"{offender.name}",
            user_id=offender.id,
            staff_display=f"{entry.user.name}",
            staff_id=entry.user.id,
            reason=reason,
            redacted=redact,
            user_notified=False,
        )

        if not reason:
            prefix = guild_data.prefix or config.prefix
            punishment.reason = f"Use `{prefix}reason {punishment.punishment_id} <reason>` to specify a reason."
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

    async def create_and_publish_punishment(
        self,
        *,
        punishment_type: PunishmentType,
        guild: discord.Guild,
        offender: discord.abc.User,
        moderator: discord.abc.User,
        reason: str,
        user_notified: bool,
    ) -> StaffPunishment:
        """
        used by slash command-driven punishments where the bot itself performs the action, rather than relying on audit log entries.
        publish_punishment_log() will see the resulting audit log entry but skip re-publishing it, since entry.user will be the bot.
        """
        guild_data = await get_guild_data(guild_id=guild.id)

        parsed_reason, redact = self.parse_reason_redact(reason or "")

        punishment = await StaffPunishment.create(
            punishment_type=punishment_type,
            guild_id=guild.id,
            user_display=f"{offender.name}",
            user_id=offender.id,
            staff_display=f"{moderator.name}",
            staff_id=moderator.id,
            reason=parsed_reason,
            redacted=redact,
            user_notified=user_notified,
        )

        if not parsed_reason:
            prefix = (guild_data.prefix if guild_data else None) or config.prefix
            punishment.reason = f"Use `{prefix}reason {punishment.punishment_id} <reason>` to specify a reason."
            await punishment.save()

        if not guild_data:
            return punishment

        internal_log = guild_data.modlog_staff_id
        public_log = guild_data.modlog_id

        if internal_log:
            log_message = punishment_message(punishment, redact=False)
            channel = self.bot.get_channel(internal_log)
            if channel:
                message_staff = await channel.send(log_message)
                punishment.message_staff_id = message_staff.id
                await punishment.save()

        if public_log:
            log_message = punishment_message(punishment, redact=True)
            channel = self.bot.get_channel(public_log)
            if channel:
                message = await channel.send(log_message)
                punishment.message_id = message.id
                await punishment.save()

        return punishment

    async def publish_revocation_log(
        self, punishment_type: PunishmentType, entry: discord.AuditLogEntry
    ):
        guild_data = await get_guild_data(guild_id=entry.guild.id)
        if not guild_data:
            return

        public_log = guild_data.modlog_id
        internal_log = guild_data.modlog_staff_id
        if not public_log and not internal_log:
            return  # nowhere to publish

        pardoned = (
            entry.target
            if isinstance(entry.target, discord.User)
            else await self.bot.fetch_user(entry.target.id)
        )

        if internal_log:
            log_message = (
                f"**{revocation_format[punishment_type]}**\n"
                + f"**Pardoned: **<@{pardoned.id}> (User: {pardoned.name}, ID: {pardoned.id})\n"
                + f"**Moderator: **{entry.user.name} (ID: {entry.user.id})"
            )
            channel = self.bot.get_channel(internal_log)
            await channel.send(log_message)

        if public_log:
            log_message = (
                f"**{revocation_format[punishment_type]}**\n"
                + f"**Pardoned: **<@{pardoned.id}> (User: {pardoned.name}, ID: {pardoned.id})\n"
                + f"**Moderator: **{entry.user.name} (ID: {entry.user.id})"
            )
            channel = self.bot.get_channel(public_log)
            await channel.send(log_message)

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

    @staticmethod
    async def _try_dm(user: discord.abc.User, content: str) -> bool:
        # best-effort DM, returns whether it was actually delivered.
        try:
            await user.send(content)
            return True
        except (discord.Forbidden, discord.HTTPException):
            return False

    @staticmethod
    async def _purge_recent_messages(
        guild: discord.Guild, user_id: int, window: timedelta
    ) -> int:
        cutoff = discord.utils.utcnow() - window
        deleted_count = 0

        for channel in guild.text_channels:
            perms = channel.permissions_for(guild.me)
            if not perms.read_message_history or not perms.manage_messages:
                continue  # cannot read or delete messages in this channel

            try:
                deleted = await channel.purge(
                    after=cutoff,
                    check=lambda m: m.author.id == user_id,
                    bulk=True,
                )
                deleted_count += len(deleted)
            except discord.Forbidden:
                continue
            except discord.HTTPException:
                continue

        return deleted_count

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready. Ensures initialization on bot startup."""
        await self.update_sticky_roles()
        await self.schedule_existing_punishment_expirations()
        logger.info("Existing punishment expirations queued.")
        await self.check_reapply_active_mutes()
        logger.info("Active mutes checked.")

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        if entry.action == discord.AuditLogAction.kick:
            await self.publish_punishment_log(PunishmentType.KICK, entry)
        elif entry.action == discord.AuditLogAction.member_update:
            if entry.user.bot:
                return  # already handled via create_and_publish_punishment

            if not hasattr(entry.after, "timed_out_until"):
                return  # not a timeout-related change

            if not entry.after.timed_out_until:
                # timeout removed/expired
                await self.publish_revocation_log(PunishmentType.TIMEOUT, entry)
                return

            # timeout applied via native Discord UI
            reason = entry.reason or "No reason provided."
            dm_content = (
                f"You have been timed out in **{entry.guild.name}** until "
                f"{format_dt(entry.after.timed_out_until, 'F')} "
                f"({format_dt(entry.after.timed_out_until, 'R')}).\n"
                f"**Reason:** {reason}"
            )
            notified = await self._try_dm(entry.target, dm_content)

            await self.publish_punishment_log(PunishmentType.TIMEOUT, entry)

            status = (
                "was successfully DMed the reason"
                if notified
                else "could **not** be DMed (DMs closed or blocked the bot)"
            )
            staff_message = (
                f"{entry.user.mention} heads up — {entry.target.mention} {status} "
                f"regarding their timeout."
            )

            guild_data = await get_guild_data(guild_id=entry.guild.id)
            staff_channel_ids = []
            if guild_data and guild_data.modlog_staff_id:
                staff_channel_ids.append(guild_data.modlog_staff_id)
            staff_channel_ids.append(CHAT_MOD_CHANNEL_ID)

            for channel_id in set(staff_channel_ids):
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(staff_message)
        elif entry.action == discord.AuditLogAction.ban:
            await self.publish_punishment_log(PunishmentType.BAN, entry)
        elif entry.action == discord.AuditLogAction.unban:
            await self.publish_revocation_log(PunishmentType.BAN, entry)
            # update expirations
            punishment = (
                await StaffPunishment.filter(
                    user_id=entry.target.id,
                    guild_id=entry.guild.id,
                    punishment_type=PunishmentType.BAN,
                    expiry__isnull=False,
                )
                .order_by("-timestamp")
                .first()
            )
            if not punishment:
                return  # no matching punishment found

            punishment.expiry_complete = True
            await punishment.save()
        elif entry.action == discord.AuditLogAction.member_role_update:
            guild_data = await get_guild_data(guild_id=entry.guild.id)
            if not guild_data.mute_id:
                return  # no mute role set

            if not hasattr(entry.after, "roles"):
                return  # not a role change, cannot be a mute/unmute

            if any(guild_data.mute_id == role.id for role in entry.before.roles):
                # unmute
                await self.publish_revocation_log(PunishmentType.MUTE, entry)
            elif (
                any(guild_data.mute_id == role.id for role in entry.after.roles)
                and not entry.user.bot
            ):
                # mute
                await self.publish_punishment_log(PunishmentType.MUTE, entry)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        Log message edits.
        """
        guild_data = await get_guild_data(guild_id=after.guild.id)
        if not guild_data or not guild_data.logs_id:
            return  # no log channel set
        log_channel = self.bot.get_channel(guild_data.logs_id)

        if after.author.bot:
            return  # ignore bot messages

        embed = discord.Embed(
            color=discord.Colour.yellow(),
            description=before.content if before.content else "(no content)",
        )
        embed.set_author(
            name=f"{after.author.name} edited a message in #{after.channel.name}",
            icon_url=after.author.display_avatar.url,
            url=after.jump_url,
        )
        embed.add_field(
            name="Edited to",
            value=after.content if after.content else "(no content)",
            inline=False,
        )
        embed.add_field(
            name="Utilities",
            value="\n".join(
                [
                    f"User: {after.author.mention} (ID: {after.author.id})",
                    f"Message: [**Jump URL**]({after.jump_url}) (ID: {after.id})",
                ]
            ),
        )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """
        Log message deletes.
        """
        guild_data = await get_guild_data(guild_id=message.guild.id)
        if not guild_data or not guild_data.logs_id:
            return  # no log channel set
        log_channel = self.bot.get_channel(guild_data.logs_id)

        if message.author.bot:
            return  # ignore bot messages

        embed = discord.Embed(
            color=discord.Colour.red(),
            description=message.content if message.content else "(no content)",
        )
        embed.set_author(
            name=f"{message.author.name} deleted a message in #{message.channel.name}",
            icon_url=message.author.display_avatar.url,
            url=message.jump_url,
        )
        embed.add_field(
            name="Utilities",
            value="\n".join(
                [
                    f"User: {message.author.mention} (ID: {message.author.id})",
                    f"Message: [**Jump URL**]({message.jump_url}) (ID: {message.id})",
                ]
            ),
        )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Handle incomplete unmutes when a member rejoins.
        """
        sticky_roles = await MemberRole.get_or_none(
            guild_id=member.guild.id, user_id=member.id
        )
        if not sticky_roles:
            return
        roles = [
            role
            for role_id in sticky_roles.role_ids
            if (role := member.guild.get_role(role_id)) is not None
            and role.name != "@everyone"
        ]
        if roles:
            await member.add_roles(*roles)

        if (member.guild.id, member.id) in self.incomplete_unmutes:
            guild_data = await get_guild_data(guild_id=member.guild.id)
            mute_role = member.guild.get_role(guild_data.mute_id)
            if mute_role in member.roles:
                await member.remove_roles(
                    mute_role, reason="Punishment case expired while user was not in guild."
                )

            punishment_id = self.incomplete_unmutes[(member.guild.id, member.id)]
            punishment = await StaffPunishment.get(punishment_id=punishment_id)
            punishment.expiry_complete = True
            await punishment.save()

            del self.incomplete_unmutes[(member.guild.id, member.id)]

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Update sticky roles when a member's roles change.
        """
        # check for role update
        if set(before.roles) == set(after.roles):
            return

        # if bot gets roles updated, handle separately
        if after.id == self.bot.user.id:
            await self.update_sticky_roles()
            return

        member_roles = await MemberRole.get_or_none(guild_id=after.guild.id, user_id=after.id)
        sticky_roles = [role.id for role in after.roles if role.id in self.sticky_role_ids]

        # go case by case
        if not member_roles and not sticky_roles:
            return  # no sticky roles changes to manage

        if not sticky_roles:
            # delete existing entry
            await member_roles.delete()
            return

        if not member_roles:
            # create new entry
            member_roles = MemberRole(
                guild_id=after.guild.id,
                user_id=after.id,
                role_ids=sticky_roles,
            )
            await member_roles.save()
            return

        # update existing entry
        member_roles.role_ids = sticky_roles
        await member_roles.save()

    @commands.hybrid_command()
    @commands.has_permissions(ban_members=True)
    @describe(user="User to ban", reason="Reason for ban")
    async def blacklist(
        self,
        ctx: commands.Context,
        user: discord.User,
        *,
        reason: Optional[str] = None,
    ):
        """
        Blacklist a user that is not in the server.
        """
        if any(member.id == user.id for member in ctx.guild.members):
            await ctx.send(
                "User is in the server. Please use Discord's built-in moderation tools."
            )
            return

        await ctx.guild.ban(user, reason=reason)
        if not reason:
            await ctx.send(f"Banned {user}.")
            return
        await ctx.send(f"Banned {user} for `{reason}`.")

    @commands.hybrid_command(name="ban", description="Ban a user from the server.")
    @describe(
        user="The user to ban (ID or mention).",
        reason="Reason for the ban. Start typing for suggestions.",
    )
    @commands.has_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        user: discord.User,
        *,
        reason: str,
    ):
        """
        Ban a user from the server.
        """
        await ctx.defer(ephemeral=True)

        guild = ctx.guild
        if guild is None:
            await ctx.send("This command can only be used in a server.")
            return

        existing_member = guild.get_member(user.id)
        if existing_member is not None:
            top_role = guild.me.top_role
            if existing_member.top_role >= top_role and guild.owner_id != ctx.author.id:
                await ctx.send(
                    "I cannot ban this user because they have a higher or equal role than me."
                )
                return

        dm_content = (
            f"You have been banned from **{guild.name}**.\n"
            f"**Reason:** {reason}\n\n"
            f"If you believe this was a mistake, you may appeal here: {APPEALS_SERVER_INVITE}"
        )
        notified = await self._try_dm(user, dm_content)

        try:
            await guild.ban(
                user,
                reason=reason,
                delete_message_seconds=int(MESSAGE_DELETE_WINDOW.total_seconds()),
            )
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban this user.")
            return
        except discord.HTTPException as exc:
            await ctx.send(f"Failed to ban this user: {exc}")
            return

        await self.create_and_publish_punishment(
            punishment_type=PunishmentType.BAN,
            guild=guild,
            offender=user,
            moderator=ctx.author,
            reason=reason,
            user_notified=notified,
        )

        await ctx.send(
            f"Banned {user.mention} (`{user.id}`)."
            + ("User notified." if notified else "\n\u26a0\ufe0f Could not DM the user.")
        )

    @ban.autocomplete("reason")
    async def ban_reason_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return _reason_autocomplete_choices(current, BAN_REASON_PRESETS)

    @commands.hybrid_command(name="kick", description="Kick a user from the server.")
    @describe(
        user="The user to kick (ID or mention).",
        reason="Reason for the kick. Start typing for suggestions.",
    )
    @commands.has_permissions(kick_members=True)
    async def kick(
        self,
        ctx: commands.Context,
        user: discord.User,
        *,
        reason: str,
    ):
        """
        Kick a user from the server."""
        await ctx.defer(ephemeral=True)

        guild = ctx.guild
        if guild is None:
            await ctx.send("This command can only be used in a server.")
            return

        member = guild.get_member(user.id)
        if member is None:
            await ctx.send("That user is not in the server.")
            return

        top_role = guild.me.top_role
        if member.top_role >= top_role and guild.owner_id != ctx.author.id:
            await ctx.send("I can't kick this user due to role hierarchy.")
            return

        dm_content = (
            f"You have been kicked from **{guild.name}**.\n"
            f"**Reason**: {reason}\n\n"
            f"You're welcome to rejoin here: {REJOIN_SERVER_INVITE}"
        )
        notified = await self._try_dm(user, dm_content)

        try:
            await guild.kick(user, reason=reason)
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick this user.")
            return
        except discord.HTTPException as exc:
            await ctx.send(f"Failed to kick this user: {exc}")
            return

        await self.create_and_publish_punishment(
            punishment_type=PunishmentType.KICK,
            guild=guild,
            offender=user,
            moderator=ctx.author,
            reason=reason,
            user_notified=notified,
        )

        await ctx.send(
            f"Kicked {user.mention} (`{user.id}`)."
            + ("User notified." if notified else "\n\u26a0\ufe0f Could not DM the user.")
        )

    @commands.hybrid_command()
    async def expire(
        self, ctx: commands.Context, case_number: int, terminus: DatetimeConverter
    ):
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
            await ctx.send(
                f"Expiration is not supported for this punishment type: `{punishment.punishment_type.value}`."
            )
            return

        punishment.expiry = terminus
        punishment.expiry_complete = False
        await punishment.save()

        task = asyncio.create_task(self.handle_punishment_expiration(punishment))
        self.active[punishment.punishment_id] = task
        task.add_done_callback(self.removal_callback(punishment.punishment_id))
        await ctx.send(
            f"Punishment expiry set for {format_dt(terminus)} ({format_dt(terminus, 'R')})."
        )

    @commands.hybrid_command()
    @commands.has_permissions(kick_members=True)
    async def history(self, ctx: commands.Context, user: discord.User):
        """
        Display a user's punishment history.
        """
        guild_data = await get_guild_data(guild_id=ctx.guild.id)
        add_links = guild_data and guild_data.modlog_id

        embed = discord.Embed(description=f"History of {user.mention}.")
        punishments = await StaffPunishment.filter(user_id=user.id).order_by("timestamp").all()
        for punishment in punishments:
            timestamp_display = (
                format_dt(punishment.timestamp, "d") if punishment.timestamp else UNKNOWN
            )
            staff_display = punishment.staff_display if not punishment.redacted else UNKNOWN
            title = f"Case #{punishment.punishment_id} | {punishment_format[punishment.punishment_type]} (by {staff_display} on {timestamp_display})"
            body = f"{punishment.reason}"
            if add_links and punishment.message_id:
                body += f"\n-# [*Jump to modlog entry.*](https://discord.com/channels/{punishment.guild_id}/{guild_data.modlog_id}/{punishment.message_id})"
            embed.add_field(name=title, value=body, inline=False)
        if not punishments:
            embed.description = f"{user.mention} has no punishment history."
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

        guild_data = await get_guild_data(guild_id=punishment.guild_id)
        if guild_data and guild_data.modlog_id and punishment.message_id:
            content += f"\n-# [Go to message](https://discord.com/channels/{punishment.guild_id}/{guild_data.modlog_id}/{punishment.message_id})"
        await ctx.send(content)

    @commands.hybrid_command()
    @commands.has_permissions(moderate_members=True)
    async def note(
        self, ctx: commands.Context, user: discord.User, *, note: Optional[str] = None
    ):
        """
        Save a note on a user.
        """
        if note:
            await StaffNote.create(user_id=user.id, author_id=ctx.author.id, note=note)
            await ctx.send("The note has been added.")
        embed = discord.Embed(description=f"Notes for {user.mention}.")
        notes = await StaffNote.filter(user_id=user.id).order_by("timestamp").all()
        for note in notes:
            author = self.bot.get_user(note.author_id)
            author_display = author.name if author else UNKNOWN
            time_display = format_dt(note.timestamp, "d") if note.timestamp else UNKNOWN
            embed.add_field(
                name=f"#{note.note_id} — Entry by {author_display} (on {time_display}):",
                value=note.note,
                inline=False,
            )
        if not notes:
            embed.description = f"{user.mention} has no notes."
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def delnote(self, ctx: commands.Context, note_id: int):
        """
        Delete a staff note by its ID. Administrator only.
        """
        note = await StaffNote.filter(note_id=note_id).get_or_none()
        if not note:
            await ctx.send(f"Note #{note_id} does not exist.")
            return

        await note.delete()
        await ctx.send(f"Note #{note_id} deleted.")

    @delnote.error
    async def delnote_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need administrator permissions to delete notes.")
            return
        raise error

    @commands.hybrid_command()
    @commands.has_permissions(moderate_members=True)
    @describe(user="User to warn", reason="Reason for the warning")
    async def warn(
        self,
        ctx: commands.Context,
        user: discord.User,
        *,
        reason: str,
    ):
        """
        Warn a user.
        """
        dm_content = f"You have been warned in **{ctx.guild.name}**.\n**Reason:** {reason}"
        notified = await self._try_dm(user, dm_content)

        await self.create_and_publish_punishment(
            punishment_type=PunishmentType.WARN,
            guild=ctx.guild,
            offender=user,
            moderator=ctx.author,
            reason=reason,
            user_notified=notified,
        )

        await ctx.send(
            f"Warned {user.mention} (`{user.id}`)."
            + ("User notified." if notified else "\n\u26a0\ufe0f Could not DM the user.")
        )

    @warn.error
    async def warn_error(self, ctx: commands.Context, error: commands.CommandError):
        if (
            isinstance(error, commands.MissingRequiredArgument)
            and error.param.name == "reason"
        ):
            await ctx.send("You need to provide a reason: `&warn <user> <reason>`.")
            return
        raise error

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(moderate_members=True)
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
        if number < 1 or number > 100:
            await ctx.send("Please specify a number between 1 and 100.")
            return
        deleted = await ctx.channel.purge(limit=number)
        await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=5)

    @purge.command()
    async def reaction(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        message_id: int,
        emoji: discord.Emoji,
    ):
        """
        Bulk delete reactions.
        """
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send("Message not found.")
            return
        except discord.Forbidden:
            await ctx.send("I do not have permission to read messages in that channel.")
            return
        except discord.HTTPException:
            await ctx.send("An error occurred while fetching the message.")
            return

        try:
            await message.clear_reaction(emoji)
        except discord.Forbidden:
            await ctx.send("I do not have permission to delete reactions.")
            return
        except discord.NotFound:
            await ctx.send("The emoji you specifiied was not found.")
            return
        except TypeError:
            await ctx.send("The emoji you specified is invalid.")
            return
        except discord.HTTPException:
            await ctx.send("An error occurred while deleting reactions.")
            return

        await ctx.send(f"Deleted reactions to {message_id} with emoji {emoji}.")

    @commands.hybrid_command()
    @commands.has_permissions(kick_members=True)
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
            try:
                modlog_message = await modlog.fetch_message(punishment.message_id)
                await modlog_message.edit(content=new_message)
            except discord.NotFound:
                pass  # message was deleted

        new_message = punishment_message(punishment, redact=False)
        guild_data = await get_guild_data(guild_id=ctx.guild.id)
        modlog_staff = self.bot.get_channel(guild_data.modlog_staff_id)
        if modlog_staff:
            try:
                modlog_staff_message = await modlog_staff.fetch_message(
                    punishment.message_staff_id
                )
                await modlog_staff_message.edit(content=new_message)
            except discord.NotFound:
                pass  # message was deleted

        await ctx.send(f'Case #{case_number} reason updated: "{reason}"')


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
