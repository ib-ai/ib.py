from datetime import timedelta
from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest
from tortoise import timezone

from ib_py.cogs.moderation import Moderation, punishment_format, revocation_format
from ib_py.db.models import (
    GuildData,
    MemberRole,
    PunishmentType,
    StaffNote,
    StaffPunishment,
)

from .db import cleanup_tables
from .mocks import (
    MockAuditLogEntry,
    MockBot,
    MockChannel,
    MockGuild,
    MockMember,
    MockMessage,
    MockReaction,
    MockRole,
    MockUser,
)
from .scenarios import scenario_class, scenario_fixture
from .utils import patch_cog_commands


@pytest.fixture
def moderation_cog():
    bot = MockBot()
    cog = Moderation(bot)
    return patch_cog_commands(cog)


@scenario_class
@cleanup_tables(StaffPunishment, GuildData)
class TestReason:
    """Tests for the reason command."""

    @scenario_fixture(["punishment", "modlog_message", "modlog_staff_message"])
    async def reason_setup(self, moderation_cog, ctx):
        modlog_channel = MockChannel(id=12345, guild=ctx.guild)
        modlog_staff_channel = MockChannel(id=12346, guild=ctx.guild)

        ctx.guild.channels = [modlog_channel, modlog_staff_channel]

        await GuildData.create(
            prefix="&",
            guild_id=ctx.guild.id,
            modlog_id=modlog_channel.id,
            modlog_staff_id=modlog_staff_channel.id,
        )
        moderation_cog.bot.guilds = [ctx.guild]

        modlog_channel.messages.append(
            (
                modlog_message := MockMessage(
                    id=1000000000, content="Original modlog message", channel=modlog_channel
                )
            )
        )
        modlog_staff_channel.messages.append(
            (
                modlog_staff_message := MockMessage(
                    id=1000000001,
                    content="Original staff message",
                    channel=modlog_staff_channel,
                )
            )
        )

        punishment = await StaffPunishment.create(
            punishment_type=PunishmentType.WARN,
            guild_id=ctx.guild.id,
            user_display="TestUser",
            user_id=111111111,
            staff_display="Moderator",
            staff_id=999999999,
            reason="Old reason",
            message_id=modlog_message.id,
            message_staff_id=modlog_staff_message.id,
        )

        return locals()

    async def test_case_does_not_exist(self, moderation_cog, ctx):
        """Test updating reason for a non-existent case."""
        await moderation_cog.reason(ctx, -1, reason="Test reason")

        assert len(ctx.messages_sent) == 1
        assert "does not exist" in ctx.messages_sent[0].content

    async def test_case_exists(
        self, moderation_cog, ctx, punishment, modlog_message, modlog_staff_message
    ):
        """Test updating reason for an existing case."""
        await moderation_cog.reason(ctx, punishment.punishment_id, reason="New test reason")

        # Check confirmation message
        assert len(ctx.messages_sent) == 1
        assert (
            f"Case #{punishment.punishment_id} reason updated" in ctx.messages_sent[0].content
        )
        assert "New test reason" in ctx.messages_sent[0].content

        # Check database update
        updated_punishment = await StaffPunishment.get(punishment_id=punishment.punishment_id)
        assert updated_punishment.reason == "New test reason"
        assert updated_punishment.redacted is False

        # Check that modlog messages were edited
        assert "New test reason" in modlog_message.content
        assert "New test reason" in modlog_staff_message.content


class TestReasonFlags:
    """Tests for reason parsing and redacting."""

    @pytest.mark.parametrize(
        "input_reason,expected_reason,expected_redacted",
        [
            ("", "", False),  # blank reason
            ("   ", "", False),  # whitespace reason
            ("asdf", "asdf", False),  # normal reason
            ("-redact", "", True),  # redact flag
            ("-redacted", "", True),  # redacted flag
            ("asdf -redact", "asdf", True),  # reason with redact
            (
                "asdf -redacted",
                "asdf",
                True,
            ),  # reason with redacted
            (
                "-r5",
                "Rule 5. Academic Dishonesty is strictly prohibited.",
                True,
            ),  # r5 flag
            (
                "asdf -r5",
                "Rule 5. Academic Dishonesty is strictly prohibited.",
                True,
            ),  # reason with r5
            (
                "-banevasion",
                "Ban evasion is strictly prohibited.",
                True,
            ),  # banevasion flag
            (
                "asdf -banevasion",
                "Ban evasion is strictly prohibited.",
                True,
            ),  # reason with banevasion
        ],
        ids=[
            "blank_reason",
            "whitespace_reason",
            "normal_reason",
            "redact_flag",
            "redacted_flag",
            "reason_with_redact",
            "reason_with_redacted",
            "r5_flag",
            "reason_with_r5",
            "banevasion_flag",
            "reason_with_banevasion",
        ],
    )
    async def test_reason_flags(
        self,
        moderation_cog,
        input_reason,
        expected_reason,
        expected_redacted,
    ):
        """Test reason parsing and redacting."""
        reason, redacted = moderation_cog.parse_reason_redact(input_reason)
        assert reason == expected_reason
        assert redacted == expected_redacted


@scenario_class
@cleanup_tables(StaffPunishment, GuildData)
class TestAuditLog:
    """Tests for audit log event handling."""

    @scenario_fixture(["user", "staff", "mute_role", "modlog_channel", "modlog_staff_channel"])
    async def audit_log_setup(self, moderation_cog, ctx):
        user = MockUser(id=111111111, name="TestUser")
        staff = MockMember(id=999999999, name="Moderator", guild=ctx.guild)
        mute_role = MockRole(id=55555, name="Muted", guild=ctx.guild)
        modlog_channel = MockChannel(id=12345, guild=ctx.guild)
        modlog_staff_channel = MockChannel(id=12346, guild=ctx.guild)
        ctx.guild.members = [staff]
        ctx.guild.roles = [mute_role]
        ctx.guild.channels = [modlog_channel, modlog_staff_channel]

        await GuildData.create(
            prefix="&",
            guild_id=ctx.guild.id,
            modlog_id=modlog_channel.id,
            modlog_staff_id=modlog_staff_channel.id,
            mute_id=mute_role.id,
        )
        moderation_cog.bot.guilds = [ctx.guild]

        return locals()

    @staticmethod
    def check_punishment_message(message, punishment):
        assert f"Case: #{punishment.punishment_id}" in message.content
        assert punishment_format[punishment.punishment_type] in message.content
        assert punishment.user_display in message.content
        assert str(punishment.user_id) in message.content
        assert punishment.staff_display in message.content
        assert str(punishment.staff_id) in message.content
        assert punishment.reason in message.content

    @staticmethod
    def check_revocation_message(message, ptype, pardoned, moderator):
        assert revocation_format[ptype] in message.content
        assert pardoned.name in message.content
        assert str(pardoned.id) in message.content
        assert moderator.name in message.content
        assert str(moderator.id) in message.content

    @pytest.mark.parametrize(
        "action,ptype,reason",
        [
            (discord.AuditLogAction.kick, PunishmentType.KICK, None),
            (discord.AuditLogAction.kick, PunishmentType.KICK, "kick reason"),
            (discord.AuditLogAction.ban, PunishmentType.BAN, None),
            (discord.AuditLogAction.ban, PunishmentType.BAN, "ban reason"),
        ],
        ids=["kick_no_reason", "kick_with_reason", "ban_no_reason", "ban_with_reason"],
    )
    async def test_punishment_audit_log(
        self,
        moderation_cog,
        ctx,
        user,
        staff,
        modlog_channel,
        modlog_staff_channel,
        action,
        ptype,
        reason,
    ):
        """Test kick/ban."""
        entry = MockAuditLogEntry(
            action=action,
            target=user,
            user=staff,
            guild=ctx.guild,
            reason=reason,
        )

        await moderation_cog.on_audit_log_entry_create(entry)

        punishment = await StaffPunishment.filter(
            user_id=user.id, punishment_type=ptype
        ).first()
        assert punishment is not None
        assert (reason if reason else "&reason") in punishment.reason
        assert len(modlog_channel.messages) == 1
        assert len(modlog_staff_channel.messages) == 1
        self.check_punishment_message(modlog_channel.messages[0], punishment)
        self.check_punishment_message(modlog_staff_channel.messages[0], punishment)

    async def test_unban(
        self, moderation_cog, ctx, user, staff, modlog_channel, modlog_staff_channel
    ):
        """Test unban."""
        entry = MockAuditLogEntry(
            action=discord.AuditLogAction.unban,
            target=user,
            user=staff,
            guild=ctx.guild,
            reason="unban reason",
        )

        await moderation_cog.on_audit_log_entry_create(entry)

        assert len(modlog_channel.messages) == 1
        assert len(modlog_staff_channel.messages) == 1
        self.check_revocation_message(
            modlog_channel.messages[0], PunishmentType.BAN, user, staff
        )
        self.check_revocation_message(
            modlog_staff_channel.messages[0], PunishmentType.BAN, user, staff
        )

    async def test_mute_role_added(
        self, moderation_cog, ctx, user, staff, mute_role, modlog_channel, modlog_staff_channel
    ):
        """Test mute."""
        member = MockMember(id=user.id, name=user.name, guild=ctx.guild)
        entry = MockAuditLogEntry(
            action=discord.AuditLogAction.member_role_update,
            target=member,
            user=staff,
            guild=ctx.guild,
            reason="mute reason",
        )
        entry.before.roles = []
        entry.after.roles = [mute_role]

        await moderation_cog.on_audit_log_entry_create(entry)

        punishment = await StaffPunishment.filter(
            user_id=member.id, punishment_type=PunishmentType.MUTE
        ).first()
        assert punishment is not None
        assert punishment.reason == "mute reason"
        assert len(modlog_channel.messages) == 1
        assert len(modlog_staff_channel.messages) == 1
        self.check_punishment_message(modlog_channel.messages[0], punishment)
        self.check_punishment_message(modlog_staff_channel.messages[0], punishment)

    async def test_mute_role_removed(
        self, moderation_cog, ctx, user, staff, mute_role, modlog_channel, modlog_staff_channel
    ):
        """Test unmute."""
        entry = MockAuditLogEntry(
            action=discord.AuditLogAction.member_role_update,
            target=user,
            user=staff,
            guild=ctx.guild,
            reason="unmute reason",
        )
        entry.before.roles = [mute_role]
        entry.after.roles = []

        await moderation_cog.on_audit_log_entry_create(entry)

        assert len(modlog_channel.messages) == 1
        assert len(modlog_staff_channel.messages) == 1
        self.check_revocation_message(
            modlog_channel.messages[0], PunishmentType.MUTE, user, staff
        )
        self.check_revocation_message(
            modlog_staff_channel.messages[0], PunishmentType.MUTE, user, staff
        )


@scenario_class
@cleanup_tables(StaffPunishment, GuildData)
class TestPunishmentLogs:
    """Tests for punishment logging in modlog and modlog_staff channels."""

    @scenario_fixture(["entry", "modlog_channel", "modlog_staff_channel"])
    async def punishment_log_setup(self, moderation_cog, ctx):
        modlog_channel = MockChannel(id=12345, guild=ctx.guild)
        modlog_staff_channel = MockChannel(id=12346, guild=ctx.guild)
        ctx.guild.channels = [modlog_channel, modlog_staff_channel]
        moderation_cog.bot.guilds = [ctx.guild]

        user = MockUser(id=111111111, name="TestUser")
        staff = MockUser(id=999999999, name="Moderator")
        entry = MockAuditLogEntry(
            action=discord.AuditLogAction.ban,
            target=user,
            user=staff,
            guild=ctx.guild,
            reason="test reason",
        )
        return locals()

    async def test_publish_punishment_log_no_guild_data(
        self, moderation_cog, entry, modlog_channel, modlog_staff_channel
    ):
        """Test publishing punishment log when no log channels are set."""

        await moderation_cog.publish_punishment_log(PunishmentType.BAN, entry)

        # No messages sent in log channels
        assert len(modlog_channel.messages) == 0
        assert len(modlog_staff_channel.messages) == 0

        # Should not create punishment record
        punishments = await StaffPunishment.all()
        assert len(punishments) == 0

    async def test_publish_punishment_log_no_channels_configured(
        self, moderation_cog, ctx, entry, modlog_channel, modlog_staff_channel
    ):
        """Test publishing punishment log when no log channels are configured."""
        await GuildData.create(prefix="&", guild_id=ctx.guild.id)
        await moderation_cog.publish_punishment_log(PunishmentType.BAN, entry)

        # No messages sent in log channels
        assert len(modlog_channel.messages) == 0
        assert len(modlog_staff_channel.messages) == 0

        # Should not create punishment record
        punishments = await StaffPunishment.all()
        assert len(punishments) == 0

    async def test_publish_punishment_log_only_public_channel(
        self, moderation_cog, ctx, entry, modlog_channel, modlog_staff_channel
    ):
        """Test publishing punishment log to public channel only."""
        await GuildData.create(prefix="&", guild_id=ctx.guild.id, modlog_id=modlog_channel.id)
        await moderation_cog.publish_punishment_log(PunishmentType.BAN, entry)

        # Should send message to public channel only
        assert len(modlog_channel.messages) == 1
        assert len(modlog_staff_channel.messages) == 0

        # Should create punishment record with message ID
        punishments = await StaffPunishment.all()
        assert len(punishments) == 1
        punishment = punishments[0]
        assert punishment.message_id == modlog_channel.messages[0].id

    async def test_publish_punishment_log_only_public_channel_redacted(
        self, moderation_cog, ctx, entry, modlog_channel, modlog_staff_channel
    ):
        """Test publishing punishment log to public channel only with redacted reason."""
        await GuildData.create(prefix="&", guild_id=ctx.guild.id, modlog_id=modlog_channel.id)
        entry.reason += " -redact"
        await moderation_cog.publish_punishment_log(PunishmentType.BAN, entry)

        # Should send message to public channel only
        assert len(modlog_channel.messages) == 1
        assert len(modlog_staff_channel.messages) == 0

        # Should create punishment record with message ID
        punishments = await StaffPunishment.all()
        assert len(punishments) == 1
        punishment = punishments[0]
        assert punishment.message_id == modlog_channel.messages[0].id

        # Check that user details are redacted in public log
        public_message = modlog_channel.messages[0]
        assert "TestUser" not in public_message.content
        assert str(entry.target.id) not in public_message.content

    async def test_publish_punishment_log_only_staff_channel(
        self, moderation_cog, ctx, entry, modlog_channel, modlog_staff_channel
    ):
        """Test publishing punishment log to staff channel only."""
        await GuildData.create(
            prefix="&", guild_id=ctx.guild.id, modlog_staff_id=modlog_staff_channel.id
        )
        await moderation_cog.publish_punishment_log(PunishmentType.KICK, entry)

        # Should send message to staff channel only
        assert len(modlog_channel.messages) == 0
        assert len(modlog_staff_channel.messages) == 1

        # Should create punishment record with message ID
        punishments = await StaffPunishment.all()
        assert len(punishments) == 1
        punishment = punishments[0]
        assert punishment.message_staff_id == modlog_staff_channel.messages[0].id

    async def test_publish_punishment_log_only_staff_channel_redacted(
        self, moderation_cog, ctx, entry, modlog_channel, modlog_staff_channel
    ):
        """Test publishing punishment log to staff channel only with redacted reason."""
        await GuildData.create(
            prefix="&", guild_id=ctx.guild.id, modlog_staff_id=modlog_staff_channel.id
        )
        entry.reason += " -redact"
        await moderation_cog.publish_punishment_log(PunishmentType.KICK, entry)

        # Should send message to staff channel only
        assert len(modlog_channel.messages) == 0
        assert len(modlog_staff_channel.messages) == 1

        # Should create punishment record with message ID
        punishments = await StaffPunishment.all()
        assert len(punishments) == 1
        punishment = punishments[0]
        assert punishment.message_staff_id == modlog_staff_channel.messages[0].id

        # Check that user details are not redacted in staff log
        staff_message = modlog_staff_channel.messages[0]
        assert "TestUser" in staff_message.content
        assert str(entry.target.id) in staff_message.content

    async def test_publish_punishment_log_both_channels(
        self, moderation_cog, ctx, entry, modlog_channel, modlog_staff_channel
    ):
        """Test publishing punishment log to both channels."""
        await GuildData.create(
            prefix="&",
            guild_id=ctx.guild.id,
            modlog_id=modlog_channel.id,
            modlog_staff_id=modlog_staff_channel.id,
        )
        await moderation_cog.publish_punishment_log(PunishmentType.KICK, entry)

        # Should send to both channels
        assert len(modlog_channel.messages) == 1
        assert len(modlog_staff_channel.messages) == 1
        assert modlog_channel.messages[0].content == modlog_staff_channel.messages[0].content

        # Should create punishment record with both message IDs
        punishments = await StaffPunishment.all()
        assert len(punishments) == 1
        punishment = punishments[0]
        assert punishment.message_id == modlog_channel.messages[0].id
        assert punishment.message_staff_id == modlog_staff_channel.messages[0].id

    async def test_publish_punishment_log_both_channels_redacted(
        self, moderation_cog, ctx, entry, modlog_channel, modlog_staff_channel
    ):
        """Test publishing punishment log to both channels with redacted reason."""
        await GuildData.create(
            prefix="&",
            guild_id=ctx.guild.id,
            modlog_id=modlog_channel.id,
            modlog_staff_id=modlog_staff_channel.id,
        )
        entry.reason += " -redact"
        await moderation_cog.publish_punishment_log(PunishmentType.KICK, entry)

        # Should send to both channels
        assert len(modlog_channel.messages) == 1
        assert len(modlog_staff_channel.messages) == 1

        # Should create punishment record with both message IDs
        punishments = await StaffPunishment.all()
        assert len(punishments) == 1
        punishment = punishments[0]
        assert punishment.message_id == modlog_channel.messages[0].id
        assert punishment.message_staff_id == modlog_staff_channel.messages[0].id

        # Check that user details are redacted in public log
        public_message = modlog_channel.messages[0]
        assert "TestUser" not in public_message.content
        assert str(entry.target.id) not in public_message.content

        # Check that user details are not redacted in staff log
        staff_message = modlog_staff_channel.messages[0]
        assert "TestUser" in staff_message.content
        assert str(entry.target.id) in staff_message.content

    async def test_publish_revocation_log_no_guild_data(
        self, moderation_cog, entry, modlog_channel, modlog_staff_channel
    ):
        """Test publishing revocation log when no guild data exists."""
        await moderation_cog.publish_revocation_log(PunishmentType.BAN, entry)

        # Should not send any messages
        assert len(modlog_channel.messages) == 0
        assert len(modlog_staff_channel.messages) == 0

    async def test_publish_revocation_log_no_channels_configured(
        self, moderation_cog, ctx, entry, modlog_channel, modlog_staff_channel
    ):
        """Test publishing revocation log when no log channels are configured."""
        await GuildData.create(prefix="&", guild_id=ctx.guild.id)
        await moderation_cog.publish_revocation_log(PunishmentType.BAN, entry)

        # Should not send any messages
        assert len(modlog_channel.messages) == 0
        assert len(modlog_staff_channel.messages) == 0

    async def test_publish_revocation_log_only_public_channel(
        self, moderation_cog, ctx, entry, modlog_channel, modlog_staff_channel
    ):
        """Test publishing revocation log to public channel only."""
        await GuildData.create(prefix="&", guild_id=ctx.guild.id, modlog_id=modlog_channel.id)
        await moderation_cog.publish_revocation_log(PunishmentType.BAN, entry)

        # Should send message to public channel only
        assert len(modlog_channel.messages) == 1
        assert len(modlog_staff_channel.messages) == 0

    async def test_publish_revocation_log_only_staff_channel(
        self, moderation_cog, ctx, entry, modlog_channel, modlog_staff_channel
    ):
        """Test publishing revocation log to staff channel only."""
        await GuildData.create(
            prefix="&", guild_id=ctx.guild.id, modlog_staff_id=modlog_staff_channel.id
        )
        await moderation_cog.publish_revocation_log(PunishmentType.MUTE, entry)

        # Should send message to staff channel only
        assert len(modlog_channel.messages) == 0
        assert len(modlog_staff_channel.messages) == 1

    async def test_publish_revocation_log_both_channels(
        self, moderation_cog, ctx, entry, modlog_channel, modlog_staff_channel
    ):
        """Test publishing revocation log to both channels."""
        await GuildData.create(
            prefix="&",
            guild_id=ctx.guild.id,
            modlog_id=modlog_channel.id,
            modlog_staff_id=modlog_staff_channel.id,
        )
        await moderation_cog.publish_revocation_log(PunishmentType.BAN, entry)

        # Should send to both channels
        assert len(modlog_channel.messages) == 1
        assert len(modlog_staff_channel.messages) == 1
        assert modlog_channel.messages[0].content == modlog_staff_channel.messages[0].content


@scenario_class
@cleanup_tables(GuildData)
class TestMessageLogs:
    """Tests for logging of message edits and deletions in logs channel."""

    @scenario_fixture(["user", "message", "logs_channel"])
    async def message_log_setup(self, moderation_cog, ctx):
        logs_channel = MockChannel(id=12345, guild=ctx.guild)
        user = MockUser(id=111111111, name="TestUser")
        message = MockMessage(id=1000000000, content="message content", channel=ctx.channel)
        message.author = user
        message.guild = ctx.guild
        ctx.guild.channels = [logs_channel, ctx.channel]
        moderation_cog.bot.guilds = [ctx.guild]
        return locals()

    @staticmethod
    def check_edited_log_message(log_message, user, before_message, after_message):
        assert log_message.embed is not None
        embed_text = str(log_message.embed.to_dict())
        assert "edited a message" in embed_text
        assert (
            before_message.content if before_message.content else "(no content)" in embed_text
        )
        assert after_message.content if after_message.content else "(no content)" in embed_text
        assert str(user.id) in embed_text
        assert after_message.jump_url in embed_text

    @staticmethod
    def check_deleted_log_message(log_message, user, deleted_message):
        assert log_message.embed is not None
        embed_text = str(log_message.embed.to_dict())
        assert "deleted a message" in embed_text
        assert (
            deleted_message.content
            if deleted_message.content
            else "(no content)" in embed_text
        )
        assert str(user.id) in embed_text
        assert deleted_message.jump_url in embed_text

    async def test_message_edit_no_guild_data(
        self, moderation_cog, ctx, user, message, logs_channel
    ):
        """Test message edit logging when no guild data exists."""
        edited = MockMessage(id=1000000000, content="edited content", channel=ctx.channel)
        edited.author = user
        edited.guild = ctx.guild

        await moderation_cog.on_message_edit(message, edited)

        # Should not log anything
        assert len(logs_channel.messages) == 0

    async def test_message_edit_no_logs_channel_configured(
        self, moderation_cog, ctx, user, message, logs_channel
    ):
        """Test message edit logging when no logs channel is configured."""
        await GuildData.create(prefix="&", guild_id=ctx.guild.id)
        edited = MockMessage(id=1000000000, content="edited content", channel=ctx.channel)
        edited.author = user
        edited.guild = ctx.guild

        await moderation_cog.on_message_edit(message, edited)

        # Should not log anything
        assert len(logs_channel.messages) == 0

    async def test_message_edit_ignores_bot_messages(
        self, moderation_cog, ctx, user, message, logs_channel
    ):
        """Test that bot message edits are ignored."""
        await GuildData.create(prefix="&", guild_id=ctx.guild.id, logs_id=logs_channel.id)
        edited = MockMessage(id=1000000000, content="edited content", channel=ctx.channel)
        edited.author = user
        edited.guild = ctx.guild
        user.bot = True

        await moderation_cog.on_message_edit(message, edited)

        # Should not log bot messages
        assert len(logs_channel.messages) == 0

    async def test_message_edit_with_content(
        self, moderation_cog, ctx, user, message, logs_channel
    ):
        """Test logging message edit with both before and after content."""
        await GuildData.create(prefix="&", guild_id=ctx.guild.id, logs_id=logs_channel.id)
        edited = MockMessage(id=1000000000, content="edited content", channel=ctx.channel)
        edited.author = user
        edited.guild = ctx.guild

        await moderation_cog.on_message_edit(message, edited)

        # Should log the edit
        assert len(logs_channel.messages) == 1
        self.check_edited_log_message(logs_channel.messages[0], user, message, edited)

    async def test_message_edit_no_content_before(
        self, moderation_cog, ctx, logs_channel, user, message
    ):
        """Test logging message edit when before content is empty (e.g., embed only)."""
        await GuildData.create(prefix="&", guild_id=ctx.guild.id, logs_id=logs_channel.id)

        before = MockMessage(id=message.id, content="", channel=ctx.channel)
        before.author = user
        before.guild = ctx.guild
        after = MockMessage(id=message.id, content="New content added", channel=ctx.channel)
        after.author = user
        after.guild = ctx.guild

        await moderation_cog.on_message_edit(before, after)

        # Should log the edit with "(no content)" for before
        assert len(logs_channel.messages) == 1
        self.check_edited_log_message(logs_channel.messages[0], user, before, after)

    async def test_message_delete_no_guild_data(self, moderation_cog, message, logs_channel):
        """Test message delete logging when no guild data exists."""
        await moderation_cog.on_message_delete(message)

        # Should not log anything
        assert len(logs_channel.messages) == 0

    async def test_message_delete_no_logs_channel_configured(
        self, moderation_cog, ctx, message, logs_channel
    ):
        """Test message delete logging when no logs channel is configured."""
        await GuildData.create(prefix="&", guild_id=ctx.guild.id)
        await moderation_cog.on_message_delete(message)

        # Should not log anything
        assert len(logs_channel.messages) == 0

    async def test_message_delete_ignores_bot_messages(
        self, moderation_cog, ctx, user, message, logs_channel
    ):
        """Test that bot message deletions are ignored."""
        await GuildData.create(prefix="&", guild_id=ctx.guild.id, logs_id=logs_channel.id)
        user.bot = True
        await moderation_cog.on_message_delete(message)

        # Should not log bot messages
        assert len(logs_channel.messages) == 0

    async def test_message_delete_with_content(
        self, moderation_cog, ctx, user, message, logs_channel
    ):
        """Test logging message deletion with content."""
        await GuildData.create(prefix="&", guild_id=ctx.guild.id, logs_id=logs_channel.id)
        await moderation_cog.on_message_delete(message)

        # Should log the deletion
        assert len(logs_channel.messages) == 1
        self.check_deleted_log_message(logs_channel.messages[0], user, message)

    async def test_message_delete_no_content(
        self, moderation_cog, ctx, user, message, logs_channel
    ):
        """Test logging message deletion when content is empty (e.g., embed only)."""
        await GuildData.create(prefix="&", guild_id=ctx.guild.id, logs_id=logs_channel.id)
        await moderation_cog.on_message_delete(message)

        # Should log the deletion
        assert len(logs_channel.messages) == 1
        self.check_deleted_log_message(logs_channel.messages[0], user, message)


@scenario_class
@cleanup_tables(MemberRole)
class TestStickyRoles:
    """Tests for sticky roles functionality."""

    @scenario_fixture(["guild", "member", "above_bot_role", "sticky_role", "non_sticky_role"])
    async def sticky_roles_setup(self, moderation_cog):
        guild = MockGuild()
        above_bot_role = MockRole(id=99999, name="AboveBot", position=4, guild=guild)
        bot_role = MockRole(id=88888, name="BotRole", position=3, guild=guild)
        sticky_role = MockRole(id=11111, name="StickyRole", position=2, guild=guild)
        non_sticky_role = MockRole(id=22222, name="NonStickyRole", position=1, guild=guild)
        bot_member = MockMember(id=222222222, name="TestBot", guild=guild, roles=[bot_role])
        member = MockMember(id=111111111, name="TestUser", guild=guild, roles=[])

        guild.roles = [above_bot_role, sticky_role, bot_role, non_sticky_role]
        guild.me = bot_member

        moderation_cog.sticky_role_ids = [sticky_role.id, above_bot_role.id]
        moderation_cog.bot.guilds = [guild]
        await moderation_cog.on_ready()

        return locals()

    async def test_member_join_no_data(self, moderation_cog, member):
        """Test member joining with no sticky roles data."""
        # Member joins
        await moderation_cog.on_member_join(member)

        # Should have no roles added
        assert len(member.roles) == 0

    async def test_member_join_no_sticky_roles(self, moderation_cog, guild, member):
        """Test member joining with sticky roles data but no roles saved."""
        # Create sticky roles record
        await MemberRole.create(
            guild_id=guild.id,
            user_id=member.id,
            role_ids=[],
        )

        # Member rejoins
        await moderation_cog.on_member_join(member)

        # Should have both roles
        assert len(member.roles) == 0

    async def test_member_join_with_sticky_roles(
        self, moderation_cog, guild, member, sticky_role
    ):
        """Test member joining with sticky roles data and roles saved."""
        # Create sticky roles record
        await MemberRole.create(
            guild_id=guild.id,
            user_id=member.id,
            role_ids=[sticky_role.id],
        )

        # Member rejoins
        await moderation_cog.on_member_join(member)

        # Should have both roles
        assert sticky_role in member.roles
        assert len(member.roles) == 1

    async def test_member_update_add_sticky_role(self, moderation_cog, member, sticky_role):
        """Test member getting a sticky role added."""
        # Member gets a sticky role added
        before = MockMember(id=member.id, name=member.name, guild=member.guild, roles=[])
        after = MockMember(
            id=member.id, name=member.name, guild=member.guild, roles=[sticky_role]
        )

        await moderation_cog.on_member_update(before, after)

        # Verify sticky roles saved
        sticky_roles = await MemberRole.get_or_none(
            guild_id=member.guild.id, user_id=member.id
        )
        assert sticky_roles is not None
        assert sticky_role.id in sticky_roles.role_ids

    async def test_member_update_remove_sticky_role(self, moderation_cog, member, sticky_role):
        """Test member getting a sticky role removed."""
        # Pre-create sticky roles record
        await MemberRole.create(
            guild_id=member.guild.id,
            user_id=member.id,
            role_ids=[sticky_role.id],
        )

        # Member gets a sticky role removed
        before = MockMember(
            id=member.id, name=member.name, guild=member.guild, roles=[sticky_role]
        )
        after = MockMember(id=member.id, name=member.name, guild=member.guild, roles=[])

        await moderation_cog.on_member_update(before, after)

        # Verify sticky roles updated
        sticky_roles = await MemberRole.get_or_none(
            guild_id=member.guild.id, user_id=member.id
        )
        assert sticky_roles is None

    async def test_member_update_add_non_sticky_role(
        self, moderation_cog, member, non_sticky_role
    ):
        """Test member getting a non-sticky role added."""
        # Member gets a non-sticky role added
        before = MockMember(id=member.id, name=member.name, guild=member.guild, roles=[])
        after = MockMember(
            id=member.id, name=member.name, guild=member.guild, roles=[non_sticky_role]
        )

        await moderation_cog.on_member_update(before, after)

        # Verify no sticky roles saved
        sticky_roles = await MemberRole.get_or_none(
            guild_id=member.guild.id, user_id=member.id
        )
        assert sticky_roles is None

    async def test_member_update_remove_non_sticky_role(
        self, moderation_cog, member, sticky_role, non_sticky_role
    ):
        """Test member getting a non-sticky role removed."""

        # Pre-create sticky roles record
        await MemberRole.create(
            guild_id=member.guild.id,
            user_id=member.id,
            role_ids=[sticky_role.id],
        )

        # Member gets a non-sticky role removed
        before = MockMember(
            id=member.id,
            name=member.name,
            guild=member.guild,
            roles=[sticky_role, non_sticky_role],
        )
        after = MockMember(
            id=member.id, name=member.name, guild=member.guild, roles=[sticky_role]
        )

        await moderation_cog.on_member_update(before, after)

        # Verify sticky roles unchanged
        sticky_roles = await MemberRole.get_or_none(
            guild_id=member.guild.id, user_id=member.id
        )
        assert sticky_roles is not None
        assert sticky_role.id in sticky_roles.role_ids

    async def test_member_update_add_above_bot_role(
        self, moderation_cog, member, above_bot_role
    ):
        """Test member getting a role above bot's role added."""
        # Member gets a role above bot's role added
        before = MockMember(id=member.id, name=member.name, guild=member.guild, roles=[])
        after = MockMember(
            id=member.id, name=member.name, guild=member.guild, roles=[above_bot_role]
        )

        await moderation_cog.on_member_update(before, after)

        # Verify no sticky roles saved
        sticky_roles = await MemberRole.get_or_none(
            guild_id=member.guild.id, user_id=member.id
        )
        assert sticky_roles is None

    async def test_member_update_remove_above_bot_role(
        self, moderation_cog, member, above_bot_role, sticky_role
    ):
        """Test member getting a role above bot's role removed."""

        # Pre-create sticky roles record
        await MemberRole.create(
            guild_id=member.guild.id,
            user_id=member.id,
            role_ids=[sticky_role.id],
        )

        # Member gets a role above bot's role removed
        before = MockMember(
            id=member.id,
            name=member.name,
            guild=member.guild,
            roles=[above_bot_role, sticky_role],
        )
        after = MockMember(
            id=member.id, name=member.name, guild=member.guild, roles=[sticky_role]
        )

        await moderation_cog.on_member_update(before, after)

        # Verify sticky roles unchanged
        sticky_roles = await MemberRole.get_or_none(
            guild_id=member.guild.id, user_id=member.id
        )
        assert sticky_roles is not None
        assert sticky_role.id in sticky_roles.role_ids


@scenario_class
@cleanup_tables(StaffPunishment, GuildData)
class TestBlacklist:
    """Tests for the blacklist command."""

    @scenario_fixture(["modlog_channel", "modlog_staff_channel", "user"])
    async def blacklist_setup(self, moderation_cog, ctx):
        modlog_channel = MockChannel(id=12345, guild=ctx.guild)
        modlog_staff_channel = MockChannel(id=12346, guild=ctx.guild)
        ctx.guild.channels = [modlog_channel, modlog_staff_channel]

        user = MockUser(id=111111111, name="BadUser")
        ctx.guild.members = []
        moderation_cog.bot.users[user.id] = user

        await GuildData.create(
            guild_id=ctx.guild.id,
            prefix="&",
            modlog_id=modlog_channel.id,
            modlog_staff_id=modlog_staff_channel.id,
        )
        moderation_cog.bot.guilds = [ctx.guild]

        return locals()  # Return locals so the decorator can extract variables

    async def test_user_already_in_server(
        self, moderation_cog, ctx, modlog_channel, modlog_staff_channel, user
    ):
        """Test blacklist when user is already in server."""
        member = MockMember(id=user.id, name=user.name, guild=ctx.guild)
        ctx.guild.members = [member]
        await moderation_cog.blacklist(ctx, user, reason="Test")

        assert len(ctx.messages_sent) == 1
        assert "User is in the server" in ctx.messages_sent[0].content

        assert len(modlog_channel.messages) == 0
        assert len(modlog_staff_channel.messages) == 0

    async def test_blacklist_without_reason(
        self,
        bot,
        moderation_cog,
        ctx,
        modlog_channel,
        modlog_staff_channel,
        user,
    ):
        """Test blacklist without reason provided."""
        with patch.object(ctx.guild, "ban", new_callable=AsyncMock) as mock_ban:
            await moderation_cog.blacklist(ctx, user)

            mock_ban.assert_called_once()
            assert len(ctx.messages_sent) == 1
            assert "Banned" in ctx.messages_sent[0].content

    async def test_blacklist_with_reason(
        self,
        bot,
        moderation_cog,
        ctx,
        modlog_channel,
        modlog_staff_channel,
        user,
    ):
        """Test blacklist with reason provided."""
        with patch.object(ctx.guild, "ban", new_callable=AsyncMock) as mock_ban:
            await moderation_cog.blacklist(ctx, user, reason="blacklist reason")

            mock_ban.assert_called_once_with(user, reason="blacklist reason")
            assert len(ctx.messages_sent) == 1
            assert "Banned" in ctx.messages_sent[0].content
            assert "blacklist reason" in ctx.messages_sent[0].content


@scenario_class
@cleanup_tables(StaffPunishment)
class TestExpire:
    """Tests for the expire command."""

    @scenario_fixture(["user"])
    async def expire_setup(self, moderation_cog, ctx):
        user = MockUser(id=111111111, name="TestUser")
        moderation_cog.bot.users[user.id] = user
        return locals()

    async def test_expire_non_existent_case(self, moderation_cog, ctx):
        """Test expire with non_existent case number."""
        future_date = timezone.now() + timedelta(days=1)
        await moderation_cog.expire(ctx, -1, future_date)

        assert len(ctx.messages_sent) == 1
        assert "does not exist" in ctx.messages_sent[0].content

    async def test_expire_kick_not_supported(self, moderation_cog, ctx, user):
        """Test expire on kick."""
        punishment = await StaffPunishment.create(
            punishment_type=PunishmentType.KICK,
            guild_id=ctx.guild.id,
            user_display=user.name,
            user_id=user.id,
            staff_display="Moderator",
            staff_id=999999999,
            reason="kick reason",
        )
        future_date = timezone.now() + timedelta(days=1)
        await moderation_cog.expire(ctx, punishment.punishment_id, future_date)

        assert len(ctx.messages_sent) == 1
        assert "not supported" in ctx.messages_sent[0].content

    @pytest.mark.parametrize(
        "punishment_type,reason,timedelta_seconds",
        [
            (PunishmentType.MUTE, "mute reason", 1200),
            (PunishmentType.BAN, "ban reason", 2400),
        ],
        ids=["expire_mute", "expire_ban"],
    )
    async def test_expire_punishment(
        self, moderation_cog, ctx, user, punishment_type, reason, timedelta_seconds
    ):
        """Test expire on mute and ban punishments."""
        punishment = await StaffPunishment.create(
            punishment_type=punishment_type,
            guild_id=ctx.guild.id,
            user_display=user.name,
            user_id=user.id,
            staff_display="Moderator",
            staff_id=999999999,
            reason=reason,
        )
        future_date = timezone.now() + timedelta(seconds=timedelta_seconds)
        await moderation_cog.expire(ctx, punishment.punishment_id, future_date)

        assert len(ctx.messages_sent) == 1
        assert "Punishment expiry set" in ctx.messages_sent[0].content
        assert str(int(future_date.timestamp())) in ctx.messages_sent[0].content

        # Verify the punishment was updated
        updated_punishment = await StaffPunishment.get(punishment_id=punishment.punishment_id)
        assert updated_punishment.expiry is not None
        assert updated_punishment.expiry_complete is False

        # Verify punishment expiration is queued
        assert punishment.punishment_id in moderation_cog.active

    # testing startup behavior here, not necessarily the expire command itself

    @pytest.mark.parametrize(
        "punishment_type",
        [PunishmentType.MUTE, PunishmentType.BAN],
        ids=["mute", "ban"],
    )
    async def test_expire_existing_punishment_future_date(
        self, moderation_cog, ctx, user, punishment_type
    ):
        """Test scheduling of expiration on punishment with a future date."""
        punishment = await StaffPunishment.create(
            punishment_type=punishment_type,
            guild_id=ctx.guild.id,
            user_display=user.name,
            user_id=user.id,
            staff_display="Moderator",
            staff_id=999999999,
            reason="future reason",
            expiry=timezone.now() + timedelta(days=1),
            expiry_complete=False,
        )
        await moderation_cog.schedule_existing_punishment_expirations()

        assert punishment.punishment_id in moderation_cog.active

    @pytest.mark.parametrize(
        "punishment_type",
        [PunishmentType.MUTE, PunishmentType.BAN],
        ids=["mute", "ban"],
    )
    async def test_expire_existing_punishment_past_date(
        self, moderation_cog, ctx, user, punishment_type
    ):
        """Test scheduling of expiration on punishment with a past date."""
        punishment = await StaffPunishment.create(
            punishment_type=punishment_type,
            guild_id=ctx.guild.id,
            user_display=user.name,
            user_id=user.id,
            staff_display="Moderator",
            staff_id=999999999,
            reason="past reason",
            expiry=timezone.now() - timedelta(days=1),
            expiry_complete=False,
        )
        await moderation_cog.schedule_existing_punishment_expirations()

        assert punishment.punishment_id in moderation_cog.active

    async def test_reapply_mutes_on_startup(self, moderation_cog, ctx):
        """Test active mutes are reapplied on startup to muted users without mute role."""
        moderation_cog.bot.guilds = [ctx.guild]
        mute_role = MockRole(id=55555, name="Muted", guild=ctx.guild)
        member = MockMember(id=111111111, name="MutedUser", guild=ctx.guild, roles=[])
        ctx.guild.roles = [mute_role]
        ctx.guild.members = [member]
        await GuildData.create(
            guild_id=ctx.guild.id,
            mute_id=mute_role.id,
        )
        mute_punishment = await StaffPunishment.create(
            punishment_type=PunishmentType.MUTE,
            guild_id=ctx.guild.id,
            user_display=member.name,
            user_id=member.id,
            staff_display="Moderator",
            staff_id=999999999,
            reason="active mute",
            expiry=timezone.now() + timedelta(hours=1),
            expiry_complete=False,
        )
        await moderation_cog.on_ready()

        assert mute_role in member.roles
        assert mute_punishment.punishment_id in moderation_cog.active


@scenario_class
@cleanup_tables(StaffPunishment, GuildData)
class TestHistory:
    """Tests for the history command."""

    @scenario_fixture(["user"])
    async def history_setup(self, moderation_cog):
        user = MockUser(id=111111111, name="TestUser")
        moderation_cog.bot.users[user.id] = user
        return locals()

    @staticmethod
    def check_history_embed(embed, punishments):
        for punishment in punishments:
            found = False
            for field in embed.fields:
                field_text = field.name + "\n" + field.value
                if f"Case #{punishment.punishment_id}" in field.name:
                    assert str(punishment.punishment_id) in field_text
                    assert punishment_format[punishment.punishment_type] in field_text
                    assert punishment.staff_display in field_text
                    assert punishment.reason in field_text
                    found = True
                    break
            assert found, f"Punishment Case #{punishment.punishment_id} not found in embed."

    async def test_no_cases(self, moderation_cog, ctx, user):
        """Test history when user has no punishment history."""
        await moderation_cog.history(ctx, user)

        assert len(ctx.messages_sent) == 1
        assert ctx.messages_sent[0].embed is not None
        assert "no punishment history" in ctx.messages_sent[0].embed.description

    async def test_single_case(self, moderation_cog, ctx, user):
        """Test history when user has a single punishment."""
        punishment = await StaffPunishment.create(
            punishment_type=PunishmentType.WARN,
            guild_id=ctx.guild.id,
            user_display=user.name,
            user_id=user.id,
            staff_display="Moderator",
            staff_id=999999999,
            reason="first offense",
            message_id=1000000000,
        )

        await moderation_cog.history(ctx, user)

        assert len(ctx.messages_sent) == 1
        assert ctx.messages_sent[0].embed is not None
        self.check_history_embed(ctx.messages_sent[0].embed, [punishment])

    async def test_multiple_cases(self, moderation_cog, ctx, user):
        """Test history when user has multiple punishments."""
        punishment1 = await StaffPunishment.create(
            punishment_type=PunishmentType.WARN,
            guild_id=ctx.guild.id,
            user_display=user.name,
            user_id=user.id,
            staff_display="Moderator",
            staff_id=999999999,
            reason="first offense",
            message_id=1000000000,
        )
        punishment2 = await StaffPunishment.create(
            punishment_type=PunishmentType.KICK,
            guild_id=ctx.guild.id,
            user_display=user.name,
            user_id=user.id,
            staff_display="Moderator",
            staff_id=999999999,
            reason="second offense",
            message_id=1000000001,
        )

        await moderation_cog.history(ctx, user)

        assert len(ctx.messages_sent) == 1
        assert ctx.messages_sent[0].embed is not None
        self.check_history_embed(ctx.messages_sent[0].embed, [punishment1, punishment2])


@cleanup_tables(StaffPunishment, GuildData)
class TestLookup:
    """Tests for the lookup command."""

    async def test_lookup_non_existent_case(self, moderation_cog, ctx):
        """Test lookup with non_existent case number."""
        await moderation_cog.lookup(ctx, -1)

        assert len(ctx.messages_sent) == 1
        assert "does not exist" in ctx.messages_sent[0].content

    @pytest.mark.parametrize(
        "is_redacted,has_message_id,reason",
        [
            (False, True, "unredacted reason"),
            (True, True, "redacted reason"),
            (False, False, ""),
        ],
        ids=["normal_entry", "redacted_entry", "missing_message_id"],
    )
    async def test_lookup_valid_case(
        self, moderation_cog, ctx, is_redacted, has_message_id, reason
    ):
        """Test lookup with valid case numbers."""
        await GuildData.create(
            guild_id=ctx.guild.id,
            modlog_id=12345,
        )

        punishment = await StaffPunishment.create(
            punishment_type=PunishmentType.WARN,
            guild_id=ctx.guild.id,
            user_display="TestUser",
            user_id=111111111,
            staff_display="Moderator",
            staff_id=999999999,
            reason=reason,
            redacted=is_redacted,
            message_id=1000000000 if has_message_id else None,
        )
        await moderation_cog.lookup(ctx, punishment.punishment_id)

        assert len(ctx.messages_sent) == 1
        assert reason in ctx.messages_sent[0].content
        if not has_message_id:
            assert "Go to message" not in ctx.messages_sent[0].content
        else:
            assert "Go to message" in ctx.messages_sent[0].content


@scenario_class
@cleanup_tables(StaffNote)
class TestNote:
    """Tests for the note command."""

    @scenario_fixture(["user"])
    async def history_setup(self, moderation_cog):
        user = MockUser(id=111111111, name="TestUser")
        moderation_cog.bot.users[user.id] = user
        return locals()

    async def test_view_notes_empty(self, moderation_cog, ctx, user):
        """Test viewing notes when user has no notes."""
        await moderation_cog.note(ctx, user, note=None)

        assert len(ctx.messages_sent) == 1
        assert "no notes" in ctx.messages_sent[0].embed.description

    async def test_view_notes_with_notes(self, moderation_cog, ctx, user):
        """Test viewing notes when user has notes."""
        await StaffNote.create(
            user_id=user.id,
            author_id=ctx.author.id,
            note="note 1",
        )
        await StaffNote.create(
            user_id=user.id,
            author_id=ctx.author.id,
            note="note 2",
        )
        await moderation_cog.note(ctx, user, note=None)

        assert len(ctx.messages_sent) == 1
        embed = ctx.messages_sent[0].embed
        assert embed is not None
        assert len(embed.fields) == 2
        assert "note 1" in embed.fields[0].value
        assert "note 2" in embed.fields[1].value

    async def test_add_note(self, moderation_cog, ctx, user):
        """Test adding a note to a user with no existing notes."""
        await moderation_cog.note(ctx, user, note="test note")

        # Should send confirmation and notes embed
        assert len(ctx.messages_sent) == 2
        assert "added" in ctx.messages_sent[0].content
        assert ctx.messages_sent[1].embed is not None
        assert "test note" in ctx.messages_sent[1].embed.fields[0].value

        # Verify note was created
        notes = await StaffNote.filter(user_id=user.id).all()
        assert len(notes) == 1
        assert notes[0].note == "test note"

    async def test_add_note_to_existing_notes(self, moderation_cog, ctx, user):
        """Test adding a note to a user with existing notes."""
        await StaffNote.create(
            user_id=user.id,
            author_id=ctx.author.id,
            note="existing note",
        )

        await moderation_cog.note(ctx, user, note="new note")

        # Should send confirmation and notes embed
        assert len(ctx.messages_sent) == 2
        assert "added" in ctx.messages_sent[0].content
        assert ctx.messages_sent[1].embed is not None
        assert "existing note" in ctx.messages_sent[1].embed.fields[0].value
        assert "new note" in ctx.messages_sent[1].embed.fields[1].value

        # Verify notes were created
        notes = await StaffNote.filter(user_id=user.id).order_by("timestamp").all()
        assert len(notes) == 2
        assert notes[0].note == "existing note"
        assert notes[1].note == "new note"


class TestPurge:
    """Tests for the purge command."""

    @pytest.mark.parametrize(
        "number",
        [0, -5, 101],
        ids=["zero", "negative", "above_max"],
    )
    async def test_purge_message_invalid_number(self, moderation_cog, ctx, number):
        """Test purging invalid number of messages."""
        # Access the subcommand from the group
        purge_message = moderation_cog.purge.get_command("message")
        await purge_message(ctx, number)

        # Should get error message
        assert len(ctx.messages_sent) == 1
        assert "between 1 and 100" in ctx.messages_sent[0].content.lower()

    @pytest.mark.parametrize(
        "number,expected_message",
        [
            (5, "Deleted 5 messages"),
            (10, "Deleted 10 messages"),
            (15, "Deleted 10 messages"),
        ],
        ids=["purge_5", "purge_10", "purge_15"],
    )
    async def test_purge_message_valid_number(
        self, moderation_cog, ctx, number, expected_message
    ):
        """Test purging messages from a channel."""
        # Add some messages to the channel
        for i in range(10):
            ctx.channel.messages.append(
                MockMessage(id=1000000000 + i, content=f"Message {i}", channel=ctx.channel)
            )
        # Access the subcommand from the group
        purge_message = moderation_cog.purge.get_command("message")
        await purge_message(ctx, number)

        # Should send confirmation
        assert len(ctx.messages_sent) == 1
        assert expected_message in ctx.messages_sent[0].content

        # Check number of messages in channel
        remaining_messages = len(ctx.channel.messages)
        assert remaining_messages == max(0, 10 - min(number, 10))

    async def test_message_does_not_exist(self, moderation_cog, ctx):
        """Test purging reactions from message that doesn't exist."""
        channel = MockChannel(id=12345, guild=ctx.guild)
        emoji = Mock(spec=discord.Emoji)
        emoji.name = "test_emoji"

        # Access the subcommand from the group
        reaction_cmd = moderation_cog.purge.get_command("reaction")
        await reaction_cmd(ctx, channel, 99999999, emoji)

        # Should get error message
        assert len(ctx.messages_sent) == 1
        assert "not found" in ctx.messages_sent[0].content.lower()

    async def test_message_with_reactions(self, moderation_cog, ctx):
        """Test purging reactions from message with reactions of given emoji."""
        channel = MockChannel(id=12345, guild=ctx.guild)
        emoji = Mock(spec=discord.Emoji)
        emoji.name = "test_emoji"

        message = MockMessage(id=1000000000, content="Test Message", channel=channel)
        reaction = MockReaction(emoji=emoji, message=message)
        message.reactions.append(reaction)
        channel.messages.append(message)

        # Access the subcommand from the group
        reaction_cmd = moderation_cog.purge.get_command("reaction")
        await reaction_cmd(ctx, channel, message.id, emoji)

        # Should send confirmation
        assert len(ctx.messages_sent) == 1
        assert "Deleted reactions" in ctx.messages_sent[0].content
