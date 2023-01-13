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

def DatetimeConverter(arg: str):
    """
    Convert string (timestamp or duration into the future) into a python datetime object.
    """
    now = timezone.now()
    now_timestamp = now.timestamp()
    try:
        match = re.search('<t:([0-9]*)(?::.)?>', arg)
        if match is None:
            timestamp = int(arg)
        else:
            timestamp = int(match.group(1))
        if timestamp < now_timestamp:
            raise commands.BadArgument("Timestamp cannot correspond to a time in the past.")
        return datetime.fromtimestamp(timestamp, tz=timezone.get_default_timezone())
    except (ValueError, OSError, OverflowError) as e:
        logging.debug('Direct timestamp conversion failed.')
    
    try:
        delta = parse_time(arg)
        return now + delta
    except (ValueError, KeyError) as e:
        raise commands.BadArgument('Invalid duration format.')
