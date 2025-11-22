from async_lru import alru_cache

from ..config import IBPyConfig
from .models import (
    GuildData,
    StaffFilter,
    StaffMonitorMessage,
    StaffMonitorUser,
    StaffTag,
)

config = IBPyConfig()

def cache(func):
    if config.testing_env:
        func.cache_clear = lambda: None
        return func
    return alru_cache(func)


def model_cache_factory(Model):
    @cache
    async def model_cache() -> list[Model]:
        return await Model.all()
    return model_cache


@cache
async def get_guild_data(guild_id: int) -> GuildData:
    return (await GuildData.get_or_create(guild_id=guild_id))[0]


get_all_monitor_users = model_cache_factory(StaffMonitorUser)
get_all_monitor_messages = model_cache_factory(StaffMonitorMessage)
get_all_filters = model_cache_factory(StaffFilter)
get_all_tags = model_cache_factory(StaffTag)
