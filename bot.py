from datetime import datetime
import json
import os

import discord
from discord.ext import commands
import logging
from cogs.commands.reminder import schedule_reminder

from db.models import MemberReminder, db_main

with open('./config.json', 'r') as config_json:
    config = json.load(config_json)

    # Load from environment variable overrides
    if "TOKEN" in os.environ:
        config['token'] = os.getenv("TOKEN")
    if "PREFIX" in os.environ:
        config['prefix'] = os.getenv("PREFIX")
    if "DESCRIPTION" in os.environ:
        config['description'] = os.getenv("DESCRIPTION")
    if "APPLICATION_ID" in os.environ:
        config['application_id'] = os.getenv("APPLICATION_ID")
    if "DB_HOST" in os.environ:
        config['db_host'] = os.getenv("DB_HOST")
    if "DB_USER" in os.environ:
        config['db_user'] = os.getenv("DB_USER")
    if "DB_DATABASE" in os.environ:
        config['db_database'] = os.getenv("DB_DATABASE")
    if "DB_PASSWORD" in os.environ:
        config['db_password'] = os.getenv("DB_PASSWORD")

logger = logging.getLogger()

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
logger.setLevel(logging.INFO)
logging.getLogger('gino.engine._SAEngine').setLevel(logging.ERROR)

intents = discord.Intents.all()

class IBpy(commands.Bot):
    def __init__(self):
        super().__init__(
            intents=intents, 
            command_prefix=config['prefix'],
            description=config['description'],
            application_id=config['application_id']
        )
    
    async def on_ready(self):
        await bot.change_presence(activity=discord.Game(name="{}help".format(config['prefix'])), status=discord.Status.do_not_disturb)
        await db_main()

        bot_name = bot.user.name
        bot_description = bot.description
        guild_number = len(bot.guilds)

        logger.info("Bot \"{}\" is now connected.".format(bot_name))
        logger.info("Currently serving {} guilds.".format(guild_number))
        logger.info("Described as \"{}\".".format(bot_description))
        
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

        date_now = datetime.utcnow()
        reminders_list = await MemberReminder.query.where(MemberReminder.time > date_now).gino.all()

        for reminder in reminders_list:
            user = bot.get_user(reminder.user_id)
            await schedule_reminder(user, reminder.time, reminder.text)
        
        logger.info("Scheduled all reminders.")

bot = IBpy()

bot.run(config['token'])