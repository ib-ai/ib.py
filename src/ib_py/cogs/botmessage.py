import io
import json
from typing import Callable, Optional

import discord
from discord import app_commands
from discord.ext import commands

from ib_py.utils.checks import cogify, is_moderator_member, staff_command

JSON_OUTPUT_INDENT = 2  # Number of spaces for JSON indentation in outputs


class BotMessages(commands.Cog):
    # use the "discord utils" GUI for building embeds to get raw JSON
    EMBED_GUI_URL = "https://glitchii.github.io/embedbuilder/"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ctx_menu_commands = [
            ("Get Message JSON", self.ctx_menu_get_json),
            ("Edit Message", self.ctx_menu_edit_message),
            ("Add Embeds", self.ctx_menu_add_embeds),
        ]

    async def cog_load(self):
        for name, callback in self.ctx_menu_commands:
            cmd = app_commands.context_menu(name=name)(callback)
            cmd.default_permissions = discord.Permissions(manage_messages=True)
            cmd.add_check(self.interaction_check)
            self.bot.tree.add_command(cmd)

    async def cog_unload(self):
        for name, callback in self.ctx_menu_commands:
            self.bot.tree.remove_command(name, type=discord.AppCommandType.message)

    @staticmethod
    def parse_json_or_text(input_str: str):
        """
        Helper function to parse input as JSON or plain text.
        Returns dict of arguments to pass into send/edit methods.
        """
        input_str = input_str.strip()
        if input_str.startswith("{") and input_str.endswith("}"):
            try:
                json_data = json.loads(input_str)
                content = json_data.pop("content", None)  # Optional plain text content
                embeds = [
                    discord.Embed.from_dict(embed_data)
                    for embed_data in json_data.get("embeds", [])
                ]
                return dict(content=content, embeds=embeds)
            except (json.JSONDecodeError, KeyError) as e:
                raise ValueError(f"Failed to parse JSON: {e}")
        else:
            return dict(content=input_str)

    # Checks

    cog_check = cogify(staff_command())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Admin bypass
        if interaction.user.guild_permissions.manage_guild:
            return True

        return await is_moderator_member(interaction.user)

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
            await self.action(self.message, **args)
            await interaction.response.send_message("Done!", ephemeral=True)

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
        await interaction.response.send_modal(
            self.ContentModal(message=message, action=lambda m, **args: m.edit(**args))
        )

    async def ctx_menu_add_embeds(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        """
        Context menu for adding embeds to a message.
        """
        await interaction.response.send_modal(
            self.ContentModal(
                message=message,
                action=lambda m, **args: m.edit(embeds=m.embeds + args.get("embeds", [])),
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
