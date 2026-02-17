import io
import json
import logging
from typing import Callable, Optional

import discord
from discord import app_commands
from discord.ext import commands

from ib_py.utils.checks import cogify, is_moderator_member, staff_command

EMBED_DESCRIPTION_CHAR_LIMIT = 4096
EMBED_FIELD_NAME_CHAR_LIMIT = 256
EMBED_FIELD_VALUE_CHAR_LIMIT = 1024
EMBED_FIELD_COUNT_LIMIT = 25
EMBED_COUNT_LIMIT = 10
EMBED_CHAR_LIMIT = 6000  # Total characters across all embed components
MESSAGE_CHAR_LIMIT = 2000  # For content outside of embeds

JSON_OUTPUT_INDENT = 2  # Number of spaces for JSON indentation in outputs


logger = logging.getLogger(__name__)


class BotMessages(commands.Cog):
    # use Glitchii's GUI for building embeds to get raw JSON
    EMBED_GUI_URL = "https://glitchii.github.io/embedbuilder/"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ctx_menu_commands = []

    async def cog_load(self):
        # Register context menu commands & set permissions + checks
        ctx_menu_get_json = app_commands.context_menu(name="Get Message JSON")(
            self.ctx_menu_get_json
        )
        ctx_menu_get_json.default_permissions = discord.Permissions(manage_messages=True)
        ctx_menu_get_json.add_check(self.staff_interaction)
        self.ctx_menu_commands.append(ctx_menu_get_json)

        ctx_menu_edit_message = app_commands.context_menu(name="Edit Message")(
            self.ctx_menu_edit_message
        )
        ctx_menu_edit_message.default_permissions = discord.Permissions(manage_messages=True)
        ctx_menu_edit_message.add_check(self.staff_interaction_on_self_message)
        self.ctx_menu_commands.append(ctx_menu_edit_message)

        ctx_menu_add_embeds = app_commands.context_menu(name="Add Embeds")(
            self.ctx_menu_add_embeds
        )
        ctx_menu_add_embeds.default_permissions = discord.Permissions(manage_messages=True)
        ctx_menu_add_embeds.add_check(self.staff_interaction_on_self_message)
        self.ctx_menu_commands.append(ctx_menu_add_embeds)

        logger.debug(
            f"Registering {len(self.ctx_menu_commands)} context menu commands for BotMessages cog."
        )

    async def cog_unload(self):
        for cmd in self.ctx_menu_commands:
            self.bot.tree.remove_command(cmd.name, type=cmd.type)

        logger.debug(
            f"Unloaded {len(self.ctx_menu_commands)} context menu commands from BotMessages cog."
        )

    @staticmethod
    def parse_json_or_text(input_str: str):
        """
        Helper function to parse input as JSON or plain text.
        Returns dict of arguments to pass into send/edit methods.
        """
        input_str = input_str.strip()
        if not (input_str.startswith("{") and input_str.endswith("}")):
            # If it doesn't look like JSON, treat it as plain text content
            return dict(content=input_str)

        json_data = json.loads(input_str)
        content = json_data.pop("content", None)  # Optional plain text content
        embeds = []

        # validation checks for embeds and fields to prevent hitting Discord limits or missing required keys
        if content and len(content) > MESSAGE_CHAR_LIMIT:
            raise ValueError(
                f"Content exceeds character limit of {MESSAGE_CHAR_LIMIT} characters.\n{content[:100]}..."
            )

        char_total = 0
        if len(json_data.get("embeds", [])) > EMBED_COUNT_LIMIT:
            raise ValueError(
                f"Input has {len(json_data.get('embeds', []))} embeds, which exceeds the limit of {EMBED_COUNT_LIMIT}."
            )
        for i, embed_data in enumerate(json_data.get("embeds", [])):
            if len(embed_data.get("description", "")) > EMBED_DESCRIPTION_CHAR_LIMIT:
                raise ValueError(
                    f"Embed {i + 1} description exceeds character limit of {EMBED_DESCRIPTION_CHAR_LIMIT} characters.\n{embed_data.get('description')[:100]}..."
                )
            if len(embed_data.get("fields", [])) > EMBED_FIELD_COUNT_LIMIT:
                raise ValueError(
                    f"Embed {i + 1} has {len(embed_data.get('fields', []))} fields, which exceeds the limit of {EMBED_FIELD_COUNT_LIMIT}."
                )
            for j, field in enumerate(embed_data.get("fields", [])):
                if "name" not in field:
                    raise ValueError(f"Embed {i + 1} field {j + 1} is missing a 'name' key.")
                if "value" not in field:
                    raise ValueError(f"Embed {i + 1} field {j + 1} is missing a 'value' key.")
                if len(field["name"]) > EMBED_FIELD_NAME_CHAR_LIMIT:
                    raise ValueError(
                        f"Embed {i + 1} field {j + 1} name exceeds character limit of {EMBED_FIELD_NAME_CHAR_LIMIT} characters.\n{field['name'][:100]}..."
                    )
                if len(field["value"]) > EMBED_FIELD_VALUE_CHAR_LIMIT:
                    raise ValueError(
                        f"Embed {i + 1} field {j + 1} value exceeds character limit of {EMBED_FIELD_VALUE_CHAR_LIMIT} characters.\n{field['value'][:100]}..."
                    )
            embed = discord.Embed.from_dict(embed_data)
            char_total += len(embed)
            embeds.append(embed)
        if char_total > EMBED_CHAR_LIMIT:
            raise ValueError(
                f"Total embed characters exceed the limit of {EMBED_CHAR_LIMIT} characters."
            )

        return dict(content=content, embeds=embeds)

    # Checks

    cog_check = cogify(staff_command())

    async def staff_interaction(self, interaction: discord.Interaction) -> bool:
        # Admin bypass
        if interaction.user.guild_permissions.manage_guild:
            return True

        return await is_moderator_member(interaction.user)

    async def staff_interaction_on_self_message(
        self, interaction: discord.Interaction
    ) -> bool:
        # Must be called on a message from this bot
        if not interaction.message or interaction.message.author.id != self.bot.user.id:
            await interaction.response.send_message(
                "This command can only be used on messages sent by this bot.", ephemeral=True
            )
            return False
        return await self.staff_interaction(interaction)

    # Interactions Classes

    # See: https://github.com/ib-ai/modmail.py/blob/main/utils/ticket_embed.py#L19
    class ConfirmationView(discord.ui.View):
        """Confirmation view for yes/no operations."""

        def __init__(self, timeout: int = 60):
            super().__init__(timeout=timeout)
            self.value = None

        @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
        async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.value = True
            self.stop()

        @discord.ui.button(label="No", style=discord.ButtonStyle.red)
        async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.value = False
            self.stop()

    class ContentModal(discord.ui.Modal, title="Edit Message Content"):
        content = discord.ui.TextInput(
            label="Message Content or JSON", style=discord.TextStyle.paragraph
        )

        def __init__(self, message: discord.Message, action: Callable):
            super().__init__()
            self.message = message
            self.action = action

        async def on_submit(self, interaction: discord.Interaction):
            args = BotMessages.parse_json_or_text(self.content.value)
            await self.action(interaction, self.message, **args)

    # Context Menu Commands

    async def ctx_menu_get_json(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        """
        Context menu for getting the raw JSON of a message.
        """
        embed_json = [embed.to_dict() for embed in message.embeds]
        result = {
            "content": message.content,
            "embeds": embed_json,
        }
        output = f"```json\n{json.dumps(result, indent=JSON_OUTPUT_INDENT)}\n```"
        if len(output) > 2000:
            # write to a file if too long for a message
            file = discord.File(
                fp=io.StringIO(json.dumps(result, indent=JSON_OUTPUT_INDENT)),
                filename="message.json",
            )
            await interaction.response.send_message(
                "Message JSON is too long, sending as a file:", file=file, ephemeral=True
            )
        else:
            await interaction.response.send_message(output, ephemeral=True)

    async def ctx_menu_edit_message(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        """
        Context menu for editing a message.
        """

        async def edit_action(interaction: discord.Interaction, m: discord.Message, **args):
            await m.edit(**args)
            await interaction.response.send_message("Message edited!", ephemeral=True)

        await interaction.response.send_modal(
            self.ContentModal(message=message, action=edit_action)
        )

    async def ctx_menu_add_embeds(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        """
        Context menu for adding embeds to a message.
        """

        async def add_embeds_action(
            interaction: discord.Interaction, m: discord.Message, **args
        ):
            if "content" in args and args["content"] is not None:
                await interaction.response.send_message(
                    "You cannot change the content of the message when using the Add Embeds context menu. Please use the Edit Message context menu for that.",
                    ephemeral=True,
                )
                return

            existing_embeds = m.embeds
            new_embeds = args.get("embeds", [])
            if not new_embeds:
                await interaction.response.send_message("No embeds added.", ephemeral=True)
                return

            await m.edit(embeds=existing_embeds + new_embeds)
            await interaction.response.send_message(
                f"{len(new_embeds)} embed(s) added to the message!", ephemeral=True
            )

        await interaction.response.send_modal(
            self.ContentModal(
                message=message,
                action=add_embeds_action,
            )
        )

    # Text & Slash Commands

    @commands.hybrid_command(name="send")
    async def send(
        self,
        ctx: commands.Context,
        channel: Optional[discord.TextChannel] = None,
        *,
        json_or_text: Optional[str] = None,
    ):
        """
        Commands for sending messages with the bot.
        """
        if not json_or_text:
            await ctx.send(
                f"Please provide message content or JSON input. Use [{self.EMBED_GUI_URL}]({self.EMBED_GUI_URL}) to construct embeds."
            )
            return

        args = BotMessages.parse_json_or_text(json_or_text)

        if channel is None:
            await ctx.send(**args)
            return  # early return since no confirmation needed for sending in the same channel

        view = self.ConfirmationView()
        preview_message = await ctx.send(**args)
        confirm_message = await ctx.send(f"Send this message to {channel.mention}?", view=view)

        await view.wait()
        if view.value is True:
            await channel.send(**args)
            await ctx.send("Message sent!")
        else:
            await ctx.send("Message sending cancelled.")

        # Cleanup preview and confirmation messages
        await preview_message.delete()
        await confirm_message.delete()

    @commands.hybrid_command(name="edit")
    async def edit(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        message_id: int,
        *,
        json_or_text: Optional[str] = None,
    ):
        """
        Commands for editing messages with the bot.
        """
        if not json_or_text:
            await ctx.send(
                f"Please provide message content or JSON input. Use [{self.EMBED_GUI_URL}]({self.EMBED_GUI_URL}) to construct embeds."
            )
            return

        args = BotMessages.parse_json_or_text(json_or_text)
        original_message = await channel.fetch_message(message_id)
        if original_message.author.id != self.bot.user.id:
            await ctx.send("You can only edit messages sent by this bot.")
            return

        view = self.ConfirmationView()
        preview_message = await ctx.send(**args)
        confirm_message = await ctx.send(
            f"Edit message to the above in {channel.mention}?", view=view
        )

        await view.wait()
        if view.value is True:
            await original_message.edit(**args)
            await ctx.send("Message edited!")
        else:
            await ctx.send("Message editing cancelled.")

        # Cleanup preview and confirmation messages
        await preview_message.delete()
        await confirm_message.delete()

    # legacy command, for backwards compatibility, but should send a warning
    @commands.command()
    async def embedraw(
        self, ctx: commands.Context, channel: discord.TextChannel, *, json_input: str
    ):
        """
        Create a Discord embed via raw JSON input.
        """
        json_data = json.loads(
            json_input, strict=False
        )  # Allow trailing commas and other non-standard JSON features
        embed = discord.Embed(
            description=json_data.get("description", None),
            color=discord.Color(int(json_data.get("color", 0))),
            url=json_data.get("image_url", None),
        )
        for name, value in json_data.get("fields", []):
            embed.add_field(name=name, value=value, inline=False)

        payload = dict(embeds=[embed.to_dict()])
        discord_json = json.dumps(payload, indent=JSON_OUTPUT_INDENT)
        warning_msg = "⚠️ This command is deprecated. From now on, please use the /send or /edit commands with the new JSON input instead. (To get a message's raw JSON, right click -> Apps -> Get Message JSON.) ⚠️"
        output_str = f"```json\n{discord_json}\n```"
        full_str = warning_msg + "\n" + output_str
        if len(full_str) > 2000:
            file = discord.File(fp=io.StringIO(discord_json), filename="embed.json")
            await ctx.send(warning_msg, file=file)
        else:
            await ctx.send(full_str)

        if channel is None:
            await ctx.send(embed=embed)
        else:
            await channel.send(embed=embed)
            await ctx.send("Embed sent!")


async def setup(bot: commands.Bot):
    await bot.add_cog(BotMessages(bot))
