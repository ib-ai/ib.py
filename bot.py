import discord
from discord.ext import commands
import logging
import os

from db.db import db_init
from utils import config

logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
logger.setLevel(logging.DEBUG)  # TODO: Change back to logging.INFO

intents = discord.Intents.all()

INITIAL_COGS = (
    'dev',
    'embeds',
    'filter',
    # 'help',
    'helper',
    'moderation',
    'monitor',
    'public',
    'reminder',
    'roles',
    'tags',
    'updates',
    'voting',
)

class IBpy(commands.Bot):
    def __init__(self):
        super().__init__(
            intents=intents, 
            command_prefix=config.prefix,
            description=config.description,
            application_id=config.application_id
        )
    
    async def setup_hook(self):
        for cog in INITIAL_COGS:
            try:
                await bot.load_extension(f'cogs.{cog}')
                logger.debug(f'Imported cog "{cog}".')
            except commands.errors.NoEntryPointError as e:
                # ! Remove before push
                logger.warning(e)
            except commands.errors.ExtensionNotFound as e:
                logger.warning(e)
            except commands.errors.ExtensionFailed as e:
                logger.error(e)
        
        logger.info("Loaded all cogs.")
    
    async def on_ready(self):
        await bot.change_presence(activity=discord.Game(name=f"{config.prefix}help"), status=discord.Status.do_not_disturb)
        await db_init()

        bot_name = bot.user.name
        bot_description = bot.description
        guild_number = len(bot.guilds)

        logger.info(f"Bot \"{bot_name}\" is now connected.")
        logger.info(f"Currently serving {guild_number} guilds.")
        logger.info(f"Described as \"{bot_description}\".")
    
    async def on_command_error(self, ctx: commands.Context, exception) -> None:
        # sends the error message as a discord message
        # uesful for debugging, TODO: remove/edit before pushing to production
        await super().on_command_error(ctx, exception)
        await ctx.send(exception)

bot = IBpy()
bot.run(config.token)