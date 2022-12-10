from discord.ext import commands
import re
from discord.ext import commands

def Index(arg: str):
    n = int(arg)
    if n <= 0:
        raise commands.BadArgument('Index must be a positive integer.')
    return n

class RegexConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        try: re.compile(argument)
        except re.error: 
            raise commands.BadArgument("The regex pattern provided is invalid.")
        return argument