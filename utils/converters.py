from discord.ext import commands
import re
from discord.ext import commands

def Index(arg: str):
    """
    Checks if provided index is a valid and positive integer.
    """
    n = int(arg)
    if n <= 0:
        raise commands.BadArgument('Index must be a positive integer.')
    return n

def RegexConverter(arg: str):
    """
    Checks if provided regex pattern is valid.
    """
    try: re.compile(arg)
    except re.error: 
        raise commands.BadArgument("The regex pattern provided is invalid.")
    return arg