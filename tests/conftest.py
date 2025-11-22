import builtins

import discord
import pytest
from discord.ext import commands
from tortoise import Tortoise

from .db import TORTOISE_ORM
from .mocks import (
    MockBot,
    MockChannel,
    MockContext,
    MockGuild,
    MockUser,
)

# database access


@pytest.fixture(scope="session", autouse=True)
async def db():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()

    yield Tortoise.get_connection("default")

    await Tortoise.close_connections()


# fixtures for common mock discord objects


@pytest.fixture
def bot():
    return MockBot()


@pytest.fixture
def ctx():
    guild = MockGuild()
    moderator = MockUser(id=999999999, name="Moderator")
    channel = MockChannel(guild=guild)
    guild.channels.append(channel)
    return MockContext(guild=guild, author=moderator, channel=channel)


# patch built-in isinstance to recognize mock classes as subclasses of discord.py classes
_original_isinstance = builtins.isinstance


def classinfo_check(classinfo, *classes):
    if not isinstance(classinfo, tuple):
        return any(classinfo is c for c in classes)
    for c in classinfo:
        if c in classes:
            return True
    return False


def patched_isinstance(obj, classinfo):
    if type(obj).__name__ == "MockMessage" and classinfo_check(classinfo, discord.Message):
        return True

    if type(obj).__name__ == "MockChannel" and classinfo_check(
        classinfo, discord.TextChannel, discord.abc.GuildChannel
    ):
        return True

    if type(obj).__name__ == "MockRole" and classinfo_check(classinfo, discord.Role):
        return True

    if type(obj).__name__ == "MockMember" and classinfo_check(
        classinfo, discord.User, discord.Member
    ):
        return True

    if type(obj).__name__ == "MockUser" and classinfo_check(classinfo, discord.User):
        return True

    if type(obj).__name__ == "MockGuild" and classinfo_check(classinfo, discord.Guild):
        return True

    if type(obj).__name__ == "MockContext" and classinfo_check(classinfo, commands.Context):
        return True

    if type(obj).__name__ == "MockBot" and classinfo_check(
        classinfo, discord.Client, commands.Bot
    ):
        return True

    if type(obj).__name__ == "MockAuditLogEntry" and classinfo_check(
        classinfo, discord.AuditLogEntry
    ):
        return True

    return _original_isinstance(obj, classinfo)


builtins.isinstance = patched_isinstance
