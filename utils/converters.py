import discord
from discord.ext import commands

def Index(arg: str):
    n = int(arg)
    if n <= 0:
        raise commands.BadArgument('Index must be a positive integer.')
    return n