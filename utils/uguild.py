import discord
from discord.ext import commands
from db.models import GuildData
import re

async def get_guild_data(guild: discord.Guild, prop: str = None) -> GuildData:
    guild_data = await GuildData.query.where(GuildData.guild_id == guild.id).gino.first()

    if guild_data is None:
        guild_data = await GuildData.create(guild_id=guild.id)
    
    return getattr(guild_data, prop) if prop else guild_data

def mods_or_manage_guild():
    async def predicate(ctx):
        moderator_role_id = await get_guild_data(ctx.guild, "moderator_id")
        return commands.check_any(commands.has_guild_permissions(manage_guild=True), commands.has_role(moderator_role_id))
    return commands.check(predicate)

def truncate(input: str, length: int):
    if len(input) <= length:
        return input
    symbol = "..."
    cut_down = len(symbol) + 1
    return input[0:length - cut_down] + symbol

def assert_regex(pattern: str):
    try: re.compile(pattern)
    except re.error: raise RuntimeError("The regex pattern provided is invalid.")

def assert_length(value: str, length: int, error: str):
    if len(value) > length:
        raise RuntimeError(error)
