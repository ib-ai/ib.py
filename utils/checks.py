import discord
from discord.ext import commands

def is_moderator(ctx: commands.Context):
    role_id = None  # TODO: retrieve moderator role ID
    return commands.has_role(role_id)


def admin_command():
    return commands.has_guild_permissions(manage_guild=True)

def staff_command():
    return commands.check_any(
        commands.check(is_moderator),
        admin_command()
    )
