from discord.ext import commands

def reply_unknown_syntax(command: commands.Command) -> str:
    message = ", ".join(['`{}`'.format(subcommand.name) for subcommand in command.walk_commands() if subcommand.parents[0] == command])
    return "Unknown syntax. Available subcommands: {}.".format(message)