from typing import List
from async_lru import alru_cache
from db.models import GuildData, StaffMonitorMessage, StaffMonitorUser

@alru_cache
async def get_guild_data(guild_id: int) -> GuildData | None:
    return await GuildData.get_or_none(guild_id=guild_id)

@alru_cache
async def get_all_monitor_users() -> List[StaffMonitorUser]:
    return await StaffMonitorUser.all()

@alru_cache
async def get_all_monitor_messages() -> List[StaffMonitorMessage]:
    return await StaffMonitorMessage.all()
