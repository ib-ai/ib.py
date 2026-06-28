"""
Comprehensive test suite for the BotMessages cog.

Covers:
- parse_json_or_text: valid text, valid JSON, invalid JSON, malicious/gamified inputs,
  Discord API limit violations
- ConfirmationView: button callbacks, timeout, initial state
- ContentModal: submission with plain text, JSON, and invalid JSON
- interaction_check: admin, moderator, and regular user permissions
  (staff_interaction + staff_interaction_on_self_message)
- Context menu commands: get_json, edit_message, add_embeds
- Hybrid commands: send, edit
- Legacy command: embedraw
- Cog lifecycle: cog_load, cog_unload
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from ib_py.cogs.botmessage import (
    EMBED_CHAR_LIMIT,
    EMBED_COUNT_LIMIT,
    EMBED_DESCRIPTION_CHAR_LIMIT,
    EMBED_FIELD_COUNT_LIMIT,
    EMBED_FIELD_NAME_CHAR_LIMIT,
    EMBED_FIELD_VALUE_CHAR_LIMIT,
    JSON_OUTPUT_INDENT,
    MESSAGE_CHAR_LIMIT,
    BotMessages,
)

from .mocks import MockChannel, MockMessage
from .utils import patch_cog_commands

# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def botmessage_cog(bot):
    cog = BotMessages(bot)
    return patch_cog_commands(cog)


@pytest.fixture
def target_channel(ctx):
    """A secondary channel for cross-channel send/edit tests."""
    ch = MockChannel(id=111222333, name="target-channel", guild=ctx.guild)
    ch.mention = f"<#{ch.id}>"
    ctx.guild.channels.append(ch)
    return ch


# ── Helpers ──────────────────────────────────────────────────


def _make_confirmation_side_effect(value: bool | None):
    """Return an async side-effect for ConfirmationView.wait that sets value."""

    async def _side_effect(self):
        self.value = value

    return _side_effect


# ============================================================
# 1.  parse_json_or_text
# ============================================================


class TestParseJsonOrText:
    """Tests for the static parse_json_or_text helper."""

    # ── Plain-text inputs (parametrized) ─────────────────────

    @pytest.mark.parametrize(
        "input_str,expected",
        [
            ("hello world", dict(content="hello world")),
            ("  padded  ", dict(content="padded")),
            ("", dict(content="")),
            ("   ", dict(content="")),
            ("not { json", dict(content="not { json")),
            ("not json }", dict(content="not json }")),
            ("こんにちは世界", dict(content="こんにちは世界")),
            ("🎉 party 🎉", dict(content="🎉 party 🎉")),
            (
                "**bold** __underline__ ~~strike~~",
                dict(content="**bold** __underline__ ~~strike~~"),
            ),
            ("@everyone @here", dict(content="@everyone @here")),
            ("<@123456789> <@&999>", dict(content="<@123456789> <@&999>")),
            ("line1\nline2\nline3", dict(content="line1\nline2\nline3")),
            ("https://example.com", dict(content="https://example.com")),
        ],
        ids=[
            "plain_text",
            "whitespace_padded",
            "empty_string",
            "whitespace_only",
            "brace_mid_text",
            "closing_brace_only",
            "unicode_japanese",
            "emoji",
            "markdown_formatting",
            "everyone_here_mention",
            "user_role_mention",
            "multiline",
            "url",
        ],
    )
    def test_plain_text_inputs(self, input_str, expected):
        assert BotMessages.parse_json_or_text(input_str) == expected

    # ── Valid JSON inputs (parametrized) ─────────────────────

    @pytest.mark.parametrize(
        "input_str,expected_content,expected_embed_count",
        [
            ('{"content": "hello"}', "hello", 0),
            (
                '{"embeds": [{"title": "T", "description": "D"}]}',
                None,
                1,
            ),
            ('{"content": "hi", "embeds": [{"title": "T"}]}', "hi", 1),
            (
                '{"embeds": [{"title": "A"}, {"title": "B"}, {"title": "C"}]}',
                None,
                3,
            ),
            ('{"embeds": []}', None, 0),
            ('{"unrelated_key": 42}', None, 0),
            ('  {"content": "padded"}  ', "padded", 0),
            ('{"content": null, "embeds": []}', None, 0),
            ('{"content": ""}', "", 0),
        ],
        ids=[
            "json_content_only",
            "json_embed_only",
            "json_content_and_embed",
            "json_multiple_embeds",
            "json_empty_embeds",
            "json_no_recognized_keys",
            "json_whitespace_padded",
            "json_null_content",
            "json_empty_content_string",
        ],
    )
    def test_valid_json_inputs(self, input_str, expected_content, expected_embed_count):
        result = BotMessages.parse_json_or_text(input_str)
        assert result["content"] == expected_content
        assert len(result.get("embeds", [])) == expected_embed_count

    # ── Invalid JSON inputs (parametrized) ───────────────────

    @pytest.mark.parametrize(
        "input_str",
        [
            "{invalid json}",
            '{"content": "unclosed}',
            '{"embeds": [{"title": }]}',
            '{"content": undefined}',
            "{,}",
            "{'single_quotes': 'value'}",
        ],
        ids=[
            "invalid_syntax",
            "unclosed_string",
            "malformed_embed",
            "js_undefined",
            "leading_comma",
            "single_quotes",
        ],
    )
    def test_invalid_json_raises_valueerror(self, input_str):
        with pytest.raises(json.JSONDecodeError):
            BotMessages.parse_json_or_text(input_str)

    # ── Discord API limit violations ──────────────────────────

    @pytest.mark.parametrize(
        "input_str",
        [
            '{"content": "' + "A" * (MESSAGE_CHAR_LIMIT + 1) + '"}',
            '{"embeds": [{"description": "'
            + "D" * (EMBED_DESCRIPTION_CHAR_LIMIT + 1)
            + '"}]}',
            '{"embeds": [{"fields": [{"name": "'
            + "N" * (EMBED_FIELD_NAME_CHAR_LIMIT + 1)
            + '", "value": "V"}]}]}',
            '{"embeds": [{"fields": [{"name": "N", "value": "'
            + "V" * (EMBED_FIELD_VALUE_CHAR_LIMIT + 1)
            + '"}]}]}',
            '{"embeds": [{"fields": ['
            + ",".join(['{"name": "N", "value": "V"}'] * (EMBED_FIELD_COUNT_LIMIT + 1))
            + "]}]}",
            '{"embeds": [' + ",".join(['{"title": "E"}'] * (EMBED_COUNT_LIMIT + 1)) + "]}",
            '{"embeds": [{"title": "' + "T" * (EMBED_CHAR_LIMIT + 1) + '"}]}',
            '{"embeds": [{"description": "'
            + "D" * (EMBED_CHAR_LIMIT // 2 + 1)
            + '"}, {"description": "'
            + "D" * (EMBED_CHAR_LIMIT // 2 + 1)
            + '"}]}',
        ],
        ids=[
            "content_over_limit",
            "embed_description_over_limit",
            "embed_field_name_over_limit",
            "embed_field_value_over_limit",
            "embed_field_count_over_limit",
            "embed_count_over_limit",
            "embed_total_char_over_limit",
            "embed_combined_char_over_limit",
        ],
    )
    def test_inputs_over_discord_limits(self, input_str):
        """Inputs that exceed Discord limits and would be rejected by the API later."""
        with pytest.raises(ValueError):
            BotMessages.parse_json_or_text(input_str)

    # ── Embed construction fidelity ──────────────────────────

    def test_embed_from_dict_preserves_fields(self):
        input_str = json.dumps(
            {
                "embeds": [
                    {
                        "title": "Title",
                        "description": "Desc",
                        "color": 0xFF0000,
                        "fields": [{"name": "F1", "value": "V1", "inline": True}],
                        "footer": {"text": "foot"},
                    }
                ]
            }
        )
        result = BotMessages.parse_json_or_text(input_str)
        embed = result["embeds"][0]
        assert isinstance(embed, discord.Embed)
        assert embed.title == "Title"
        assert embed.description == "Desc"
        assert embed.color.value == 0xFF0000
        assert embed.fields[0].name == "F1"
        assert embed.footer.text == "foot"

    # ── Missing required keys in embed fields ─────────────

    @pytest.mark.parametrize(
        "input_str,match",
        [
            ('{"embeds": [{"fields": [{"value": "V"}]}]}', "missing a 'name' key"),
            ('{"embeds": [{"fields": [{"name": "N"}]}]}', "missing a 'value' key"),
        ],
        ids=["field_missing_name", "field_missing_value"],
    )
    def test_fields_missing_required_keys(self, input_str, match):
        with pytest.raises(ValueError, match=match):
            BotMessages.parse_json_or_text(input_str)

    def test_empty_json_object(self):
        result = BotMessages.parse_json_or_text("{}")
        assert result == dict(content=None, embeds=[])

    def test_json_with_extra_keys_ignored(self):
        """Extra top-level keys besides content/embeds should not cause errors."""
        input_str = '{"content": "hi", "components": [], "tts": true}'
        result = BotMessages.parse_json_or_text(input_str)
        assert result["content"] == "hi"
        assert result["embeds"] == []
        assert "components" not in result
        assert "tts" not in result


# ============================================================
# 2.  ConfirmationView
# ============================================================


class TestConfirmationView:
    """Tests for the ConfirmationView UI component."""

    def _find_button(self, view, label):
        for child in view.children:
            if getattr(child, "label", None) == label:
                return child
        return None

    async def test_initial_value_is_none(self):
        view = BotMessages.ConfirmationView()
        assert view.value is None

    async def test_yes_button_sets_true(self):
        view = BotMessages.ConfirmationView()
        btn = self._find_button(view, "Yes")
        assert btn is not None
        assert btn.style == discord.ButtonStyle.green
        await btn.callback(AsyncMock())
        assert view.value is True

    async def test_no_button_sets_false(self):
        view = BotMessages.ConfirmationView()
        btn = self._find_button(view, "No")
        assert btn is not None
        assert btn.style == discord.ButtonStyle.red
        await btn.callback(AsyncMock())
        assert view.value is False

    async def test_default_timeout(self):
        assert BotMessages.ConfirmationView().timeout == 60

    async def test_custom_timeout(self):
        assert BotMessages.ConfirmationView(timeout=300).timeout == 300

    async def test_pressing_button_stops_view(self):
        view = BotMessages.ConfirmationView()
        view.stop = MagicMock()
        btn = self._find_button(view, "Yes")
        await btn.callback(AsyncMock())
        view.stop.assert_called_once()


# ============================================================
# 3.  ContentModal
# ============================================================


class TestContentModal:
    """Tests for the ContentModal UI component."""

    async def test_submit_plain_text(self):
        message = MagicMock()
        action = AsyncMock()
        modal = BotMessages.ContentModal(message=message, action=action)
        modal.content = MagicMock(value="Hello world")
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        await modal.on_submit(interaction)

        # Action now receives (interaction, message, **parsed_args)
        action.assert_awaited_once_with(interaction, message, content="Hello world")

    async def test_submit_valid_json(self):
        message = MagicMock()
        action = AsyncMock()
        modal = BotMessages.ContentModal(message=message, action=action)
        modal.content = MagicMock(value='{"content": "hi", "embeds": [{"title": "T"}]}')
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        await modal.on_submit(interaction)

        action.assert_awaited_once()
        call_args = action.call_args
        assert call_args.args == (interaction, message)
        assert call_args.kwargs["content"] == "hi"
        assert len(call_args.kwargs["embeds"]) == 1
        assert isinstance(call_args.kwargs["embeds"][0], discord.Embed)

    async def test_submit_invalid_json_raises(self):
        message = MagicMock()
        action = AsyncMock()
        modal = BotMessages.ContentModal(message=message, action=action)
        modal.content = MagicMock(value="{invalid json}")
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        with pytest.raises(json.JSONDecodeError):
            await modal.on_submit(interaction)

        action.assert_not_awaited()

    async def test_modal_stores_message_reference(self):
        msg = MagicMock()
        modal = BotMessages.ContentModal(message=msg, action=AsyncMock())
        assert modal.message is msg


# ============================================================
# 4.  interaction_check
# ============================================================


class TestStaffInteraction:
    """Tests for the staff_interaction permission gate."""

    async def test_admin_bypass(self, botmessage_cog):
        interaction = MagicMock()
        interaction.user.guild_permissions.manage_guild = True
        assert (await botmessage_cog.staff_interaction(interaction)) is True

    @patch(
        "ib_py.cogs.botmessage.is_moderator_member",
        new_callable=AsyncMock,
        return_value=True,
    )
    async def test_moderator_passes(self, mock_is_mod, botmessage_cog):
        interaction = MagicMock()
        interaction.user.guild_permissions.manage_guild = False
        assert await botmessage_cog.staff_interaction(interaction) is True
        mock_is_mod.assert_awaited_once_with(interaction.user)

    @patch(
        "ib_py.cogs.botmessage.is_moderator_member",
        new_callable=AsyncMock,
        return_value=False,
    )
    async def test_regular_user_fails(self, mock_is_mod, botmessage_cog):
        interaction = MagicMock()
        interaction.user.guild_permissions.manage_guild = False
        assert await botmessage_cog.staff_interaction(interaction) is False

    async def test_admin_check_short_circuits(self, botmessage_cog):
        """Admin bypass should not call is_moderator_member at all."""
        interaction = MagicMock()
        interaction.user.guild_permissions.manage_guild = True
        with patch(
            "ib_py.cogs.botmessage.is_moderator_member", new_callable=AsyncMock
        ) as mock_is_mod:
            await botmessage_cog.staff_interaction(interaction)
            mock_is_mod.assert_not_awaited()


# ============================================================
# 5.  Context Menu: Get Message JSON
# ============================================================


class TestCtxMenuGetJson:
    """Tests for the 'Get Message JSON' context-menu command."""

    async def test_plain_message_no_embeds(self, botmessage_cog):
        message = MockMessage(content="Hello")
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        await botmessage_cog.ctx_menu_get_json(interaction, message)

        output = interaction.response.send_message.call_args[0][0]
        parsed = json.loads(output.replace("```json\n", "").replace("\n```", ""))
        assert parsed == {"content": "Hello", "embeds": []}

    async def test_message_with_single_embed(self, botmessage_cog):
        embed = discord.Embed(title="Title", description="Desc")
        message = MockMessage(content="txt", embed=embed)
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        await botmessage_cog.ctx_menu_get_json(interaction, message)

        output = interaction.response.send_message.call_args[0][0]
        parsed = json.loads(output.replace("```json\n", "").replace("\n```", ""))
        assert parsed["content"] == "txt"
        assert len(parsed["embeds"]) == 1
        assert parsed["embeds"][0]["title"] == "Title"

    async def test_message_with_multiple_embeds(self, botmessage_cog):
        e1 = discord.Embed(title="A")
        e2 = discord.Embed(title="B")
        message = MockMessage(content="")
        message.embeds = [e1, e2]
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        await botmessage_cog.ctx_menu_get_json(interaction, message)

        output = interaction.response.send_message.call_args[0][0]
        parsed = json.loads(output.replace("```json\n", "").replace("\n```", ""))
        assert len(parsed["embeds"]) == 2

    async def test_long_output_sent_as_file(self, botmessage_cog):
        long_content = "X" * 2000
        message = MockMessage(content=long_content)
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        await botmessage_cog.ctx_menu_get_json(interaction, message)

        kwargs = interaction.response.send_message.call_args.kwargs
        assert "file" in kwargs
        f = kwargs["file"]
        assert isinstance(f, discord.File)
        assert f.filename == "message.json"

    async def test_response_is_ephemeral(self, botmessage_cog):
        message = MockMessage(content="hi")
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        await botmessage_cog.ctx_menu_get_json(interaction, message)

        assert interaction.response.send_message.call_args.kwargs["ephemeral"] is True

    async def test_empty_content_message(self, botmessage_cog):
        message = MockMessage(content="")
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        await botmessage_cog.ctx_menu_get_json(interaction, message)

        output = interaction.response.send_message.call_args[0][0]
        parsed = json.loads(output.replace("```json\n", "").replace("\n```", ""))
        assert parsed["content"] == ""

    async def test_output_uses_configured_indent(self, botmessage_cog):
        message = MockMessage(content="test")
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        await botmessage_cog.ctx_menu_get_json(interaction, message)

        output = interaction.response.send_message.call_args[0][0]
        raw_json = output.replace("```json\n", "").replace("\n```", "")
        # Re-dump with the expected indent and compare
        parsed = json.loads(raw_json)
        expected = json.dumps(parsed, indent=JSON_OUTPUT_INDENT)
        assert raw_json == expected

    async def test_unicode_content_preserved(self, botmessage_cog):
        message = MockMessage(content="日本語テスト 🎉")
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        await botmessage_cog.ctx_menu_get_json(interaction, message)

        output = interaction.response.send_message.call_args[0][0]
        parsed = json.loads(output.replace("```json\n", "").replace("\n```", ""))
        assert parsed["content"] == "日本語テスト 🎉"


# ============================================================
# 6.  Context Menu: Edit Message
# ============================================================


class TestCtxMenuEditMessage:
    """Tests for the 'Edit Message' context-menu command."""

    async def test_sends_modal(self, botmessage_cog):
        message = MockMessage(content="Original")
        message.author = botmessage_cog.bot.user  # Must be from this bot to edit
        interaction = MagicMock()
        interaction.response.send_modal = AsyncMock()

        await botmessage_cog.ctx_menu_edit_message(interaction, message)

        interaction.response.send_modal.assert_awaited_once()
        modal = interaction.response.send_modal.call_args[0][0]
        assert isinstance(modal, BotMessages.ContentModal)

    async def test_modal_action_edits_and_responds(self, botmessage_cog):
        """The edit action should edit the message and send an ephemeral response."""
        message = MagicMock()
        message.author = botmessage_cog.bot.user  # Must be from this bot to edit
        message.edit = AsyncMock()
        interaction = MagicMock()
        interaction.response.send_modal = AsyncMock()

        await botmessage_cog.ctx_menu_edit_message(interaction, message)

        modal = interaction.response.send_modal.call_args[0][0]
        # Action now takes (interaction, message, **args)
        action_interaction = MagicMock()
        action_interaction.response.send_message = AsyncMock()
        await modal.action(action_interaction, message, content="new content")
        message.edit.assert_awaited_once_with(content="new content")
        action_interaction.response.send_message.assert_awaited_once_with(
            "Message edited!", ephemeral=True
        )

    async def test_non_bot_message_rejected(self, botmessage_cog):
        """Trying to edit a message not sent by this bot should send an error."""
        message = MockMessage(content="Original")
        message.author = MagicMock(id=999999)  # Not the bot's user ID
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        await botmessage_cog.ctx_menu_edit_message(interaction, message)

        interaction.response.send_message.assert_awaited_once()
        resp = interaction.response.send_message.call_args.args[0]
        assert "only edit messages sent by this bot" in resp.lower()


# ============================================================
# 7.  Context Menu: Add Embeds
# ============================================================


class TestCtxMenuAddEmbeds:
    """Tests for the 'Add Embeds' context-menu command."""

    async def test_sends_modal(self, botmessage_cog):
        message = MockMessage(content="Original")
        message.author = botmessage_cog.bot.user  # Must be from this bot to edit
        interaction = MagicMock()
        interaction.response.send_modal = AsyncMock()

        await botmessage_cog.ctx_menu_add_embeds(interaction, message)

        interaction.response.send_modal.assert_awaited_once()
        modal = interaction.response.send_modal.call_args[0][0]
        assert isinstance(modal, BotMessages.ContentModal)

    async def test_action_appends_embeds_to_existing(self, botmessage_cog):
        """The action should merge existing + new embeds and respond with count."""
        existing = discord.Embed(title="Old")
        new_embed = discord.Embed(title="New")
        message = MagicMock()
        message.author = botmessage_cog.bot.user  # Must be from this bot to edit
        message.embeds = [existing]
        message.edit = AsyncMock()
        interaction = MagicMock()
        interaction.response.send_modal = AsyncMock()

        await botmessage_cog.ctx_menu_add_embeds(interaction, message)

        modal = interaction.response.send_modal.call_args[0][0]
        action_interaction = MagicMock()
        action_interaction.response.send_message = AsyncMock()
        await modal.action(action_interaction, message, embeds=[new_embed])
        message.edit.assert_awaited_once()
        combined = message.edit.call_args.kwargs["embeds"]
        assert len(combined) == 2
        assert combined[0].title == "Old"
        assert combined[1].title == "New"
        # Should report how many embeds were added
        assert "1 embed(s) added" in action_interaction.response.send_message.call_args.args[0]

    async def test_action_rejects_content_change(self, botmessage_cog):
        """Setting content via Add Embeds should be rejected with an error."""
        message = MagicMock()
        message.author = botmessage_cog.bot.user  # Must be from this bot to edit
        message.embeds = []
        message.edit = AsyncMock()
        interaction = MagicMock()
        interaction.response.send_modal = AsyncMock()

        await botmessage_cog.ctx_menu_add_embeds(interaction, message)

        modal = interaction.response.send_modal.call_args[0][0]
        action_interaction = MagicMock()
        action_interaction.response.send_message = AsyncMock()
        await modal.action(action_interaction, message, content="text", embeds=[])
        message.edit.assert_not_awaited()
        resp = action_interaction.response.send_message.call_args.args[0]
        assert "cannot change the content" in resp.lower()

    async def test_action_with_no_new_embeds_sends_notice(self, botmessage_cog):
        """Submitting without any embeds should send 'No embeds added.'"""
        message = MagicMock()
        message.author = botmessage_cog.bot.user  # Must be from this bot to edit
        message.embeds = [discord.Embed(title="Keep")]
        message.edit = AsyncMock()
        interaction = MagicMock()
        interaction.response.send_modal = AsyncMock()

        await botmessage_cog.ctx_menu_add_embeds(interaction, message)

        modal = interaction.response.send_modal.call_args[0][0]
        action_interaction = MagicMock()
        action_interaction.response.send_message = AsyncMock()
        await modal.action(action_interaction, message, embeds=[])
        message.edit.assert_not_awaited()
        action_interaction.response.send_message.assert_awaited_once_with(
            "No embeds added.", ephemeral=True
        )

    async def test_action_multiple_embeds_reports_count(self, botmessage_cog):
        """Adding multiple embeds should report the correct count."""
        message = MagicMock()
        message.author = botmessage_cog.bot.user  # Must be from this bot to edit
        message.embeds = []
        message.edit = AsyncMock()
        interaction = MagicMock()
        interaction.response.send_modal = AsyncMock()

        await botmessage_cog.ctx_menu_add_embeds(interaction, message)

        modal = interaction.response.send_modal.call_args[0][0]
        action_interaction = MagicMock()
        action_interaction.response.send_message = AsyncMock()
        new_embeds = [
            discord.Embed(title="A"),
            discord.Embed(title="B"),
            discord.Embed(title="C"),
        ]
        await modal.action(action_interaction, message, embeds=new_embeds)
        message.edit.assert_awaited_once()
        assert "3 embed(s) added" in action_interaction.response.send_message.call_args.args[0]

    async def test_non_bot_message_rejected(self, botmessage_cog):
        """Trying to add embeds to a message not sent by this bot should send an error."""
        message = MockMessage(content="Original")
        message.author = MagicMock(id=999999)  # Not the bot's user ID
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        await botmessage_cog.ctx_menu_add_embeds(interaction, message)

        interaction.response.send_message.assert_awaited_once()
        resp = interaction.response.send_message.call_args.args[0]
        assert "only edit messages sent by this bot" in resp.lower()


# ============================================================
# 8.  /send hybrid command
# ============================================================


class TestSendCommand:
    """Tests for the /send hybrid command."""

    async def test_no_input_shows_embed_gui_url(self, botmessage_cog, ctx):
        await botmessage_cog.send(ctx, channel=None, json_or_text=None)
        assert len(ctx.messages_sent) == 1
        assert BotMessages.EMBED_GUI_URL in ctx.messages_sent[0].content

    async def test_plain_text_same_channel_no_confirmation(self, botmessage_cog, ctx):
        await botmessage_cog.send(ctx, channel=None, json_or_text="Hello!")
        assert len(ctx.messages_sent) == 1
        assert ctx.messages_sent[0].content == "Hello!"

    async def test_plain_text_other_channel_confirmed(
        self, botmessage_cog, ctx, target_channel
    ):
        with patch.object(
            BotMessages.ConfirmationView,
            "wait",
            _make_confirmation_side_effect(True),
        ):
            await botmessage_cog.send(ctx, channel=target_channel, json_or_text="Cross-post")

        # Target channel received the message
        assert any(m.content == "Cross-post" for m in target_channel.messages)
        # Confirmation reply present
        assert any("Message sent!" in m.content for m in ctx.messages_sent)

    async def test_plain_text_other_channel_declined(
        self, botmessage_cog, ctx, target_channel
    ):
        with patch.object(
            BotMessages.ConfirmationView,
            "wait",
            _make_confirmation_side_effect(False),
        ):
            await botmessage_cog.send(ctx, channel=target_channel, json_or_text="Declined msg")

        assert len(target_channel.messages) == 0
        assert any("cancelled" in m.content for m in ctx.messages_sent)

    async def test_timeout_treated_as_cancel(self, botmessage_cog, ctx, target_channel):
        """When the view times out (value stays None) the else branch runs."""
        with patch.object(
            BotMessages.ConfirmationView,
            "wait",
            _make_confirmation_side_effect(None),
        ):
            await botmessage_cog.send(ctx, channel=target_channel, json_or_text="Timed out")

        assert len(target_channel.messages) == 0
        assert any("cancelled" in m.content for m in ctx.messages_sent)

    async def test_invalid_json_raises(self, botmessage_cog, ctx):
        with pytest.raises(json.JSONDecodeError):
            await botmessage_cog.send(ctx, channel=None, json_or_text="{bad}")

    async def test_json_input_same_channel(self, botmessage_cog, ctx):
        """JSON input to same channel should send without confirmation."""
        ctx.send = AsyncMock(return_value=MagicMock())
        await botmessage_cog.send(ctx, channel=None, json_or_text='{"content": "via json"}')
        ctx.send.assert_awaited_once()
        call_kwargs = ctx.send.call_args.kwargs
        assert call_kwargs["content"] == "via json"

    async def test_json_with_embeds_same_channel(self, botmessage_cog, ctx):
        ctx.send = AsyncMock(return_value=MagicMock())
        json_str = '{"content": "hi", "embeds": [{"title": "E"}]}'
        await botmessage_cog.send(ctx, channel=None, json_or_text=json_str)
        call_kwargs = ctx.send.call_args.kwargs
        assert len(call_kwargs["embeds"]) == 1

    async def test_preview_and_confirm_deleted_on_cross_send(
        self, botmessage_cog, ctx, target_channel
    ):
        """Preview and confirmation messages should be cleaned up."""
        deleted = []
        original_send = ctx.send

        async def tracking_send(*args, **kwargs):
            msg = await original_send(*args, **kwargs)
            original_delete = msg.delete

            async def tracked_delete():
                deleted.append(msg)
                await original_delete()

            msg.delete = tracked_delete
            return msg

        ctx.send = tracking_send
        with patch.object(
            BotMessages.ConfirmationView,
            "wait",
            _make_confirmation_side_effect(True),
        ):
            await botmessage_cog.send(ctx, channel=target_channel, json_or_text="cleanup test")

        # Two messages should be deleted: preview and confirmation
        assert len(deleted) == 2


# ============================================================
# 9.  /edit hybrid command
# ============================================================


class TestEditCommand:
    """Tests for the /edit hybrid command."""

    async def test_no_input_shows_embed_gui_url(self, botmessage_cog, ctx):
        channel = MockChannel(id=555, guild=ctx.guild)
        await botmessage_cog.edit(ctx, channel, 1, json_or_text=None)
        assert len(ctx.messages_sent) == 1
        assert BotMessages.EMBED_GUI_URL in ctx.messages_sent[0].content

    async def test_invalid_json_raises(self, botmessage_cog, ctx):
        channel = MockChannel(id=555, guild=ctx.guild)
        with pytest.raises(json.JSONDecodeError):
            await botmessage_cog.edit(ctx, channel, 1, json_or_text="{bad}")

    async def test_message_not_found_raises(self, botmessage_cog, ctx):
        channel = MockChannel(id=555, guild=ctx.guild)
        with pytest.raises(discord.NotFound):
            await botmessage_cog.edit(ctx, channel, 999999, json_or_text="hello")

    async def test_edit_confirmed(self, botmessage_cog, ctx):
        channel = MockChannel(id=555, guild=ctx.guild)
        channel.mention = f"<#{channel.id}>"
        original = MockMessage(id=42, content="old", channel=channel)
        original.author = botmessage_cog.bot.user  # Simulate a message sent by the bot
        channel.messages.append(original)

        with patch.object(
            BotMessages.ConfirmationView,
            "wait",
            _make_confirmation_side_effect(True),
        ):
            await botmessage_cog.edit(ctx, channel, 42, json_or_text="new content")

        assert original.content == "new content"
        assert any("edited" in m.content.lower() for m in ctx.messages_sent)

    async def test_edit_declined(self, botmessage_cog, ctx):
        channel = MockChannel(id=555, guild=ctx.guild)
        channel.mention = f"<#{channel.id}>"
        original = MockMessage(id=42, content="old", channel=channel)
        original.author = botmessage_cog.bot.user  # Simulate a message sent by the bot
        channel.messages.append(original)

        with patch.object(
            BotMessages.ConfirmationView,
            "wait",
            _make_confirmation_side_effect(False),
        ):
            await botmessage_cog.edit(ctx, channel, 42, json_or_text="new content")

        assert original.content == "old"
        assert any("cancelled" in m.content for m in ctx.messages_sent)

    async def test_edit_timeout(self, botmessage_cog, ctx):
        channel = MockChannel(id=555, guild=ctx.guild)
        channel.mention = f"<#{channel.id}>"
        original = MockMessage(id=42, content="old", channel=channel)
        original.author = botmessage_cog.bot.user  # Simulate a message sent by the bot
        channel.messages.append(original)

        with patch.object(
            BotMessages.ConfirmationView,
            "wait",
            _make_confirmation_side_effect(None),
        ):
            await botmessage_cog.edit(ctx, channel, 42, json_or_text="timeout")

        assert original.content == "old"
        assert any("cancelled" in m.content for m in ctx.messages_sent)

    async def test_preview_and_confirm_messages_cleaned_up(self, botmessage_cog, ctx):
        channel = MockChannel(id=555, guild=ctx.guild)
        channel.mention = f"<#{channel.id}>"
        original = MockMessage(id=42, content="old", channel=channel)
        original.author = botmessage_cog.bot.user  # Simulate a message sent by the bot
        channel.messages.append(original)

        deleted = []
        original_send = ctx.send

        async def tracking_send(*args, **kwargs):
            msg = await original_send(*args, **kwargs)
            original_delete = msg.delete

            async def tracked_delete():
                deleted.append(msg)
                await original_delete()

            msg.delete = tracked_delete
            return msg

        ctx.send = tracking_send
        with patch.object(
            BotMessages.ConfirmationView,
            "wait",
            _make_confirmation_side_effect(True),
        ):
            await botmessage_cog.edit(ctx, channel, 42, json_or_text="new")

        assert len(deleted) == 2


# ============================================================
# 10. embedraw (legacy command)
# ============================================================


class TestEmbedrawCommand:
    """Tests for the deprecated embedraw command."""

    async def test_basic_embed_sends_deprecation_warning(self, botmessage_cog, ctx):
        channel = MockChannel(id=777, guild=ctx.guild)
        json_input = '{"description": "Test embed"}'
        await botmessage_cog.embedraw(ctx, channel, json_input=json_input)
        assert any("deprecated" in m.content.lower() for m in ctx.messages_sent)

    async def test_embed_with_color(self, botmessage_cog, ctx):
        channel = MockChannel(id=777, guild=ctx.guild)
        json_input = '{"description": "Colored", "color": 16711680}'
        await botmessage_cog.embedraw(ctx, channel, json_input=json_input)
        # The embed should be sent to the channel
        assert len(channel.messages) > 0

    async def test_embed_with_fields(self, botmessage_cog, ctx):
        """Fields are expected as [name, value] pairs."""
        channel = MockChannel(id=777, guild=ctx.guild)
        json_input = '{"description": "D", "fields": [["Name", "Value"]]}'
        await botmessage_cog.embedraw(ctx, channel, json_input=json_input)
        assert len(channel.messages) > 0

    async def test_embed_sent_to_specified_channel(self, botmessage_cog, ctx):
        channel = MockChannel(id=777, guild=ctx.guild)
        json_input = '{"description": "Target"}'
        await botmessage_cog.embedraw(ctx, channel, json_input=json_input)
        assert len(channel.messages) > 0
        # Also sends confirmation
        assert any("sent" in m.content.lower() for m in ctx.messages_sent)

    async def test_invalid_json_raises_decode_error(self, botmessage_cog, ctx):
        channel = MockChannel(id=777, guild=ctx.guild)
        with pytest.raises(json.JSONDecodeError):
            await botmessage_cog.embedraw(ctx, channel, json_input="not json")

    @pytest.mark.parametrize(
        "json_input",
        [
            '{"description": "D", "fields": [["a", "b", "c"]]}',
        ],
        ids=["three_element_tuple"],
    )
    async def test_non_pair_fields_raise(self, botmessage_cog, ctx, json_input):
        """Fields with more than 2 elements should fail to unpack."""
        channel = MockChannel(id=777, guild=ctx.guild)
        with pytest.raises((ValueError, TypeError)):
            await botmessage_cog.embedraw(ctx, channel, json_input=json_input)

    async def test_dict_fields_produce_wrong_output(self, botmessage_cog, ctx):
        """
        Fields as dicts (Discord API format) don't crash but silently produce
        wrong field names — the cog iterates dict keys instead of values.
        This documents the bug.
        """
        channel = MockChannel(id=777, guild=ctx.guild)
        json_input = '{"description": "D", "fields": [{"name": "N", "value": "V"}]}'
        await botmessage_cog.embedraw(ctx, channel, json_input=json_input)
        # Cog doesn't crash but field name/value are dict keys, not the intended values
        assert len(channel.messages) > 0

    async def test_long_output_sent_as_file(self, botmessage_cog, ctx):
        channel = MockChannel(id=777, guild=ctx.guild)
        long_desc = "A" * 3000
        json_input = json.dumps({"description": long_desc})

        # Need to mock ctx.send to accept file=
        sent_files = []
        original_send = ctx.send

        async def extended_send(content=None, embed=None, file=None, **kwargs):
            if file is not None:
                sent_files.append(file)
            return await original_send(content=content, embed=embed, **kwargs)

        ctx.send = extended_send

        await botmessage_cog.embedraw(ctx, channel, json_input=json_input)

        assert len(sent_files) == 1
        assert sent_files[0].filename == "embed.json"

    async def test_missing_description_defaults_to_none(self, botmessage_cog, ctx):
        channel = MockChannel(id=777, guild=ctx.guild)
        json_input = '{"color": 0}'
        await botmessage_cog.embedraw(ctx, channel, json_input=json_input)
        assert len(channel.messages) > 0

    async def test_missing_color_defaults_to_zero(self, botmessage_cog, ctx):
        channel = MockChannel(id=777, guild=ctx.guild)
        json_input = '{"description": "no color"}'
        await botmessage_cog.embedraw(ctx, channel, json_input=json_input)
        assert len(channel.messages) > 0

    async def test_channel_is_never_none_bug(self, botmessage_cog, ctx):
        """
        `channel` is a required parameter, so the `if channel is None` branch
        in embedraw is dead code. This test documents that the branch is
        unreachable through normal invocation.
        """
        channel = MockChannel(id=777, guild=ctx.guild)
        json_input = '{"description": "test"}'
        await botmessage_cog.embedraw(ctx, channel, json_input=json_input)
        # The embed is sent to the channel AND "Embed sent!" is returned
        assert len(channel.messages) > 0
        assert any("sent" in m.content.lower() for m in ctx.messages_sent)


# ============================================================
# 11. Cog lifecycle (cog_load / cog_unload)
# ============================================================


class TestCogLifecycle:
    """Tests for cog_load and cog_unload registering / removing commands."""

    async def test_cog_load_registers_stored_commands(self, bot):
        cog = BotMessages(bot)
        bot.tree = MagicMock()
        bot.tree.add_command = MagicMock()

        await cog.cog_load()

        # Should register all commands in ctx_menu_commands
        assert bot.tree.add_command.call_count == len(cog.ctx_menu_commands)
        for cmd in cog.ctx_menu_commands:
            bot.tree.add_command.assert_any_call(cmd)

    async def test_cog_unload_removes_stored_commands(self, bot):
        cog = BotMessages(bot)
        bot.tree = MagicMock()
        bot.tree.remove_command = MagicMock()

        await cog.cog_load()
        await cog.cog_unload()

        # Only removes commands in ctx_menu_commands (just get_json due to bug)
        assert bot.tree.remove_command.call_count == len(cog.ctx_menu_commands)
        for cmd in cog.ctx_menu_commands:
            bot.tree.remove_command.assert_any_call(cmd.name, type=cmd.type)
