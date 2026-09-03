import logging

import discord
from discord.ext import commands

from .config import IBPyConfig
from .db.db import db_init

# setup config
config = IBPyConfig()
config.requires("prefix", "description", "application_id")

# setup logger
logger = logging.getLogger(__name__)

# setup bot
intents = discord.Intents.all()
INITIAL_COGS = (
    "botmessage",
    "channelorder",
    "dev",
    "filter",
    "guildconfig",
    "help",
    # "helper",
    "moderation",
    "monitor",
    "public",
    "reminder",
    "roles",
    "tags",
    "tickets",
    "updates",
    "voting",
)


class IBpy(commands.Bot):
    def __init__(self):
        super().__init__(
            intents=intents,
            command_prefix=config.prefix,
            description=config.description,
            application_id=config.application_id,
        )

    async def setup_hook(self):
        await db_init()

        for cog in INITIAL_COGS:
            try:
                await self.load_extension(f"ib_py.cogs.{cog}")
                logger.debug(f'Imported cog "{cog}".')
            except commands.errors.NoEntryPointError as e:
                # ! Remove before push
                logger.warning(e)
            except commands.errors.ExtensionNotFound as e:
                logger.warning(e)
            except commands.errors.ExtensionFailed as e:
                logger.error(e)
        logger.info("Loaded all cogs.")
        await self.tree.sync()

    async def on_ready(self):
        await self.change_presence(
            activity=discord.Game(name=f"{config.prefix}help"),
            status=discord.Status.do_not_disturb,
        )

        bot_name = self.user.name
        bot_description = self.description
        guild_number = len(self.guilds)

        logger.info(f'Bot "{bot_name}" is now connected.')
        logger.info(f"Currently serving {guild_number} guilds.")
        logger.info(f'Described as "{bot_description}".')

    async def on_command_error(self, ctx: commands.Context, exception) -> None:
        # sends the error message as a discord message
        # uesful for debugging, TODO: remove/edit before pushing to production
        await super().on_command_error(ctx, exception)
        await ctx.send(exception)
