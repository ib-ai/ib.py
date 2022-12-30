import discord
from discord.ext import commands

def cogify(check):
    return lambda self, ctx: check.predicate(ctx)


def is_moderator(ctx: commands.Context):
    moderator_role_id = None  # TODO: retrieve moderator role ID
    return any(role.id == moderator_role_id for role in ctx.author.roles)


def admin_command():
    return commands.has_guild_permissions(manage_guild=True)

def staff_command():
    return commands.check_any(
        commands.check(is_moderator),
        admin_command()
    )
