import discord
from discord.ext import commands

def Index(arg: str):
    n = int(arg)
    if n > 0:
        return n
    raise commands.BadArgument('Index must be a positive integer.')