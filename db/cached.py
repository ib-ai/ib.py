from typing import Optional
from async_lru import alru_cache
from db.models import GuildData, StaffFilter, StaffMonitorMessage, StaffMonitorUser, StaffTag


def model_cache_factory(Model):

    @alru_cache
    async def model_cache() -> list[Model]:
        return await Model.all()

    return model_cache


@alru_cache
async def get_guild_data(guild_id: int) -> GuildData:
    return (await GuildData.get_or_create(guild_id=guild_id))[0]


get_all_monitor_users = model_cache_factory(StaffMonitorUser)
get_all_monitor_messages = model_cache_factory(StaffMonitorMessage)
get_all_filters = model_cache_factory(StaffFilter)
get_all_tags = model_cache_factory(StaffTag)
