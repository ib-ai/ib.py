"""
Simplified tests for the guilddata cog that work around command framework complexities.
"""

import pytest

from ib_py.cogs.guildconfig import GuildConfig
from ib_py.config import IBPyConfig
from ib_py.db.models import GuildData

from .db import cleanup_tables
from .mocks import MockChannel, MockRole

config = IBPyConfig()
config.requires("prefix")


@pytest.fixture
def guilddata_cog(bot):
    cog = GuildConfig(bot)
    return cog


@cleanup_tables(GuildData)
class TestGuildDataCommand:
    """Tests for the guilddata command."""

    async def test_guilddata_no_data(self, guilddata_cog, ctx):
        """Test guilddata command when no data exists for the guild."""
        await guilddata_cog.guilddata.callback(guilddata_cog, ctx)

        assert len(ctx.messages_sent) == 1
        msg = ctx.messages_sent[0]
        assert msg.embed is not None
        assert ctx.guild.name in msg.embed.title
        assert str(ctx.guild.id) in msg.embed.title

    @pytest.mark.parametrize(
        "name,field,value",
        [
            ("prefix", "prefix", "&"),
            ("modlog", "modlog_id", 12345),
            ("staffmodlog", "modlog_staff_id", 12346),
            ("updates", "updates_id", 12347),
            ("logs", "logs_id", 12348),
            ("mute", "mute_id", 55555),
            ("moderator", "moderator_id", 55556),
            ("helper", "helper_id", 55557),
            ("filtering", "filtering", True),
            # ("removal", "removal", True),  # not sure what this is for?
            # ("suppressed_channels", "suppressed_channels", [11111, 22222]),  # not sure what this is for?
            ("monitoring_user", "monitoring_user", True),
            ("monitoring_message", "monitoring_message", True),
            ("usermonitor", "monitor_user_log_id", 12349),
            ("messagemonitor", "monitor_message_log_id", 12350),
        ],
    )
    async def test_guilddata_with_data(self, guilddata_cog, ctx, name, field, value):
        """Test guilddata command with specific configuration field set."""
        create_kwargs = {field: value}
        await GuildData.create(guild_id=ctx.guild.id, **create_kwargs)
        await guilddata_cog.guilddata.callback(guilddata_cog, ctx)

        # Should send an embed
        assert len(ctx.messages_sent) == 1
        message = ctx.messages_sent[0]
        assert message.embed is not None

        # The embed should contain the configuration data
        assert any(
            name in line
            and (
                ("enabled" if value else "disabled") if isinstance(value, bool) else str(value)
            )
            in line
            for data in message.embed.fields
            for line in data.value.split("\n")
        )

    async def test_guilddata_with_full_data(self, guilddata_cog, ctx):
        """Test guilddata command with all configuration data set."""
        create_kwargs = dict(
            prefix="!",
            modlog_id=12345,
            modlog_staff_id=12346,
            updates_id=12347,
            logs_id=12348,
            mute_id=55555,
            moderator_id=55556,
            helper_id=55557,
            # suppressed_channels=[11111, 22222],  # not sure what this is for?
            monitor_user_log_id=12349,
            monitor_message_log_id=12350,
        )
        await GuildData.create(guild_id=ctx.guild.id, **create_kwargs)
        await guilddata_cog.guilddata.callback(guilddata_cog, ctx)

        # Should send an embed with all data
        assert len(ctx.messages_sent) == 1
        message = ctx.messages_sent[0]
        assert message.embed is not None

        # The embed should contain all configuration data
        for value in create_kwargs.values():
            assert any(
                str(value) in line
                for data in message.embed.fields
                for line in data.value.split("\n")
            )


@cleanup_tables(GuildData)
class TestSetToggle:
    """Tests for setting field of guild configuration data."""

    async def test_set_prefix(self, guilddata_cog, ctx):
        """Test setting the prefix field."""
        prefix_cmd = guilddata_cog.set.get_command("prefix")
        await prefix_cmd.callback(guilddata_cog, ctx, prefix="!")

        # Should confirm the change
        assert len(ctx.messages_sent) == 1
        assert "prefix" in ctx.messages_sent[0].content
        assert "!" in ctx.messages_sent[0].content

        # Verify database was updated
        guild_data = await GuildData.get(guild_id=ctx.guild.id)
        assert guild_data.prefix == "!"

    @pytest.mark.parametrize(
        "field,db_field",
        [
            ("modlog", "modlog_id"),
            ("staffmodlog", "modlog_staff_id"),
            ("updates", "updates_id"),
            ("logs", "logs_id"),
            ("messagemonitor", "monitor_message_log_id"),
            ("usermonitor", "monitor_user_log_id"),
        ],
        ids=lambda x: x[0],
    )
    async def test_set_channel_field(self, guilddata_cog, ctx, field, db_field):
        """Test setting channel configuration fields."""
        channel = MockChannel(id=12345, guild=ctx.guild)
        ctx.guild.channels.append(channel)

        cmd = guilddata_cog.set.get_command(field)
        await cmd.callback(ctx, channel)

        # Should confirm the change
        assert len(ctx.messages_sent) == 1
        assert str(channel.id) in ctx.messages_sent[0].content

        # Verify database was updated
        guild_data = await GuildData.get(guild_id=ctx.guild.id)
        assert getattr(guild_data, db_field) == channel.id

    @pytest.mark.parametrize(
        "field,db_field",
        [
            ("mute", "mute_id"),
            ("moderator", "moderator_id"),
            ("helper", "helper_id"),
        ],
        ids=["mute", "moderator", "helper"],
    )
    async def test_set_role_field(self, guilddata_cog, ctx, field, db_field):
        """Test setting role configuration fields."""
        role = MockRole(id=55555, name="TestRole", guild=ctx.guild)
        ctx.guild.roles.append(role)

        cmd = guilddata_cog.set.get_command(field)
        await cmd.callback(ctx, role)

        # Should confirm the change
        assert len(ctx.messages_sent) == 1
        assert str(role.id) in ctx.messages_sent[0].content

        # Verify database was updated
        guild_data = await GuildData.get(guild_id=ctx.guild.id)
        assert getattr(guild_data, db_field) == role.id

    async def test_unset_prefix(self, guilddata_cog, ctx):
        """Test unsetting the prefix field."""
        await GuildData.create(guild_id=ctx.guild.id, prefix="!")
        prefix_cmd = guilddata_cog.set.get_command("prefix")
        await prefix_cmd.callback(guilddata_cog, ctx, prefix=None)

        # Should confirm the change
        assert len(ctx.messages_sent) == 1
        assert "prefix" in ctx.messages_sent[0].content

        # Verify database was updated (should be None now)
        guild_data = await GuildData.get(guild_id=ctx.guild.id)
        assert guild_data.prefix is None

    @pytest.mark.parametrize(
        "field,db_field",
        [
            ("modlog", "modlog_id"),
            ("staffmodlog", "modlog_staff_id"),
            ("updates", "updates_id"),
            ("logs", "logs_id"),
            ("messagemonitor", "monitor_message_log_id"),
            ("usermonitor", "monitor_user_log_id"),
        ],
        ids=lambda x: x[0],
    )
    async def test_unset_channel_field(self, guilddata_cog, ctx, field, db_field):
        """Test unsetting channel configuration fields."""
        await GuildData.create(guild_id=ctx.guild.id, **{db_field: 12345})

        cmd = guilddata_cog.set.get_command(field)
        await cmd.callback(ctx, None)

        # Should confirm the change
        assert len(ctx.messages_sent) == 1
        assert "None" in ctx.messages_sent[0].content

        # Verify database was updated
        guild_data = await GuildData.get(guild_id=ctx.guild.id)
        assert getattr(guild_data, db_field) is None

    @pytest.mark.parametrize(
        "field,db_field",
        [
            ("mute", "mute_id"),
            ("moderator", "moderator_id"),
            ("helper", "helper_id"),
        ],
        ids=["mute", "moderator", "helper"],
    )
    async def test_unset_role_field(self, guilddata_cog, ctx, field, db_field):
        """Test unsetting role configuration fields."""
        await GuildData.create(guild_id=ctx.guild.id, prefix="&", **{db_field: 55555})

        # Now unset it by passing None
        cmd = guilddata_cog.set.get_command(field)
        await cmd.callback(ctx, None)

        # Should confirm the change
        assert len(ctx.messages_sent) == 1
        assert "None" in ctx.messages_sent[0].content

        # Verify database was updated
        guild_data = await GuildData.get(guild_id=ctx.guild.id)
        assert getattr(guild_data, db_field) is None

    @pytest.mark.parametrize(
        "toggle_name,fields",
        [
            ("filtering", ("filtering",)),
            ("usermonitor", ("monitoring_user",)),
            ("messagemonitor", ("monitoring_message",)),
            ("monitor", ("monitoring_user", "monitoring_message")),
        ],
        ids=["filtering", "usermonitor", "messagemonitor", "monitor"],
    )
    async def test_toggle(self, guilddata_cog, ctx, toggle_name, fields):
        """Test toggling boolean configuration fields."""
        await GuildData.create(guild_id=ctx.guild.id)

        cmd = guilddata_cog.toggle.get_command(toggle_name)
        await cmd.callback(ctx)

        # Should confirm the change
        assert len(ctx.messages_sent) == 1
        for field in fields:
            assert field in ctx.messages_sent[0].content

        # Verify database was updated to True
        guild_data = await GuildData.get(guild_id=ctx.guild.id)
        for field in fields:
            assert getattr(guild_data, field) is True
