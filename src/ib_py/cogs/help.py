from typing import List, Mapping, Optional

import discord
from discord.ext import commands

EMBED_COLOUR = discord.Color.blurple()


class IBpyHelp(commands.HelpCommand):
    def __init__(self) -> None:
        super().__init__(
            command_attrs={"help": "Shows help for the bot, a category, or a command."}
        )

    def get_command_signature(self, command):
        return f"{self.context.clean_prefix}{command.qualified_name} {command.signature}"

    async def send_bot_help(
        self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]
    ):
        """
        Send help menu for the bot.
        """
        embed = discord.Embed(
            title="Help",
            description=(
                f"Use `{self.context.clean_prefix}help <command>`  or "
                f"`{self.context.clean_prefix}help <category>` for more details."
            ),
            color=EMBED_COLOUR,
        )

        for cog, cog_commands in mapping.items():
            filtered = await self.filter_commands(cog_commands, sort=True)
            if not filtered:
                continue

            cog_name = cog.qualified_name if cog else "No Category"
            value = ", ".join(f"`{c.name}`" for c in filtered)
            embed.add_field(name=cog_name, value=value, inline=False)

        if bot_user := self.context.bot.user:
            embed.set_thumbnail(url=bot_user.display_avatar.url)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        """
        Send help menu for a cog.
        """
        embed = discord.Embed(
            title=f"{cog.qualified_name} Commands",
            description=cog.description or "No description provided.",
            color=EMBED_COLOUR,
        )

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(
                name=self.get_command_signature(command),
                value=command.short_doc or "No description provided.",
                inline=False,
            )

        if not filtered:
            embed.description = "No commands available."

    async def send_group_help(self, group: commands.Group):
        """
        Send help menu for a command group.
        """
        embed = discord.Embed(
            title=self.get_command_signature(group),
            description=group.help or "No description provided.",
            color=EMBED_COLOUR,
        )

        filtered = await self.filter_commands(group.commands, sort=True)
        for command in filtered:
            embed.add_field(
                name=self.get_command_signature(command),
                value=command.short_doc or "No description provided.",
                inline=False,
            )

        if group.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in group.aliases),
                inline=False,
            )

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        """
        Send help menu for a command.
        """
        embed = discord.Embed(
            title=self.get_command_signature(command),
            description=command.help or "No description provided.",
            color=EMBED_COLOUR,
        )

        if command.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in command.aliases),
                inline=False,
            )

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_error_message(self, error: str):
        """
        Send message when an error is thrown.
        """
        # raise NotImplementedError('Command requires implementation and permission set-up.')
        channel = self.get_destination()  # this defaults to the command context channel
        await channel.send(error)


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.old_help_command = bot.help_command
        bot.help_command = IBpyHelp()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self.old_help_command


async def setup(bot):
    await bot.add_cog(Help(bot))
