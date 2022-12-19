from functools import cache
from db.models import GuildData

@cache
async def get_guild_data(guild_id: int) -> GuildData | None:
    return await GuildData.get_or_none(guild_id=guild_id)