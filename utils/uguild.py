import discord
from discord.ext import commands
from db.models import GuildData

async def get_guild_data(guild: discord.Guild, prop: str = None) -> GuildData:
    guild_data = await GuildData.query.where(GuildData.guild_id == guild.id).gino.first()

    if guild_data is None:
        await GuildData.create(guild_id=guild.id)
    
    return getattr(guild_data, prop) if prop else guild_data

def mods_or_manage_guild():
    def predicate(ctx):
        moderator_role_id = get_guild_data(ctx.guild, "moderator_id")
        return commands.check_any(commands.has_guild_permissions(manage_guild=True), commands.has_role(moderator_role_id))
    return commands.check(predicate)