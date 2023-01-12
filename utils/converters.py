import re
import logging
from datetime import datetime
from tortoise import timezone

from discord.ext import commands

from utils.misc import parse_time

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

def TimestampConverter(arg: str):
    """
    Convert string into a POSIX timestamp.
    """
    print(arg)
    now = timezone.now()
    now_timestamp = now.timestamp()
    try:
        match = re.search('<t:([0-9]*)(?::.)?>', arg)
        if match is None:
            timestamp = int(arg)
        else:
            timestamp = match.group(1)
        if timestamp < now_timestamp:
            raise commands.BadArgument("Timestamp cannot correspond to a time in the past.")
        if timestamp > 8640000000000:  # for some reason this is the maximum??
            raise commands.BadArgument("Timestamp value is too large.")
        return datetime.fromtimestamp(timestamp, tz=timezone.get_timezone())
    except ValueError as e:
        logging.debug('Direct timestamp conversion failed.')
    
    try:
        delta = parse_time(arg)
        return now + delta
    except ValueError as e:
        raise commands.BadArgument(e)
