from typing import Mapping, List, Optional

import discord
from discord.ext import commands


class IBpyHelp(commands.HelpCommand):
    def __init__(self) -> None:
        super().__init__()

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]):
        """
        Send help menu for the bot.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')

    async def send_cog_help(self, cog: commands.Cog):
        """
        Send help menu for a cog.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')

    async def send_group_help(self, group: commands.Group):
        """
        Send help menu for a command group.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')

    async def send_command_help(self, command: commands.Command):
        """
        Send help menu for a command.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')

    async def send_error_message(self, error: str):
        """
        Send message when an error is thrown.
        """
        # raise NotImplementedError('Command requires implementation and permission set-up.')
        channel = self.get_destination() # this defaults to the command context channel
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