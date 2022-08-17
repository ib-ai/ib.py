import json
import os

import discord
from discord.ext import commands
import logging

from db.models import db_main

with open('./config.json', 'r') as config_json:
    config = json.load(config_json)

logger = logging.getLogger()

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
logger.setLevel(logging.INFO)

intents = discord.Intents.all()

bot = commands.Bot(intents=intents, command_prefix=config['prefix'], description=config['description'])

@bot.event
async def on_ready():
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
                await bot.load_extension(os.path.join(folder, filename).replace('\\', '.').replace('/', '.')[2:-3])
    
    logger.info("Loaded all cogs.")

bot.run(config['token'])