from discord.ext import commands
from db.models import GuildData

def cogify(check):
    return lambda self, ctx: check.predicate(ctx)


async def is_moderator(ctx: commands.Context):
    assert await commands.guild_only().predicate(ctx)
    guild_data = await GuildData.get_or_none(guild_id=ctx.guild.id)
    moderator_role_id = guild_data.moderator_id if guild_data else None
    return any(role.id == moderator_role_id for role in ctx.author.roles) if moderator_role_id else False


def admin_command():
    return commands.has_guild_permissions(manage_guild=True)

def staff_command():
    return commands.check_any(
        commands.check(is_moderator),
        admin_command()
    )
