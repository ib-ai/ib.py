import discord
from discord.ext import commands
import logging
import os

from db.db import db_init
from utils import settings

settings.init()

logger = logging.getLogger()

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

# TODO: Change back to logging.INFO
logger.setLevel(logging.DEBUG)

intents = discord.Intents.all()

class IBpy(commands.Bot):
    def __init__(self):
        super().__init__(
            intents=intents, 
            command_prefix=settings.config.prefix,
            description=settings.config.description,
            application_id=settings.config.application_id
        )
    
    async def on_ready(self):
        await bot.change_presence(activity=discord.Game(name=f"{settings.config.prefix}help"), status=discord.Status.do_not_disturb)
        await db_init()

        bot_name = bot.user.name
        bot_description = bot.description
        guild_number = len(bot.guilds)

        logger.info(f"Bot \"{bot_name}\" is now connected.")
        logger.info(f"Currently serving {guild_number} guilds.")
        logger.info(f"Described as \"{bot_description}\".")
        
        for folder, _, files in os.walk('./cogs'):
            for filename in files:
                if filename.endswith('.py'):
                    try:
                        await bot.load_extension(os.path.join(folder, filename).replace('\\', '.').replace('/', '.')[2:-3])
                    except commands.errors.NoEntryPointError as e:
                        # ! Remove before push
                        print(e)
                        pass
        
        logger.info("Loaded all cogs.")

bot = IBpy()

bot.run(settings.config.token)