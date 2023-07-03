import discord
from discord.ext import commands

from db.db import db_init
from utils import config


import logging
logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)  # TODO: Change back to logging.INFO

cogs_logger = logging.getLogger('cogs')
cogs_logger.setLevel(logging.DEBUG)  # TODO: Change back to logging.INFO

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


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
        await db_init()

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

        bot_name = bot.user.name
        bot_description = bot.description
        guild_number = len(bot.guilds)

        logger.info(f"Bot \"{bot_name}\" is now connected.")
        logger.info(f"Currently serving {guild_number} guilds.")
        logger.info(f"Described as \"{bot_description}\".")

        await self.get_cog('Reminder').schedule_existing_reminders()
        logger.info(f'Existing reminders queued.')
    
    async def on_command_error(self, ctx: commands.Context, exception) -> None:
        # sends the error message as a discord message
        # uesful for debugging, TODO: remove/edit before pushing to production
        await super().on_command_error(ctx, exception)
        await ctx.send(exception)

bot = IBpy()
bot.run(config.token)
