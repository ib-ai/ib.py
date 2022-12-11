import logging
from discord.ext import commands

async def available_subcommands(ctx: commands.Context):
    """
    Send a list of available subcommands in a group command.
    """
    subcmds = []
    for cmd in ctx.command.commands:
        try:
            usable = await cmd.can_run(ctx)
            if usable:
                subcmds.append('`'+cmd.name+'`')
        except commands.CommandError:
            logging.exception(f'Command "{cmd.name}" check threw error, discarded in {ctx.command.name} group subcommand list.')
    await ctx.send(f'Available subcommands: {", ".join(subcmds)}.')