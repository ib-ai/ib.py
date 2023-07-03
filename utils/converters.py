import re
from datetime import datetime
from tortoise import timezone

from discord.ext import commands

from utils.time import parse_time

import logging

logger = logging.getLogger(__name__)


class IndexConverter(commands.Converter):

    async def convert(self, ctx: commands.Context, arg: str) -> int:
        """
        Checks if provided index is a valid and positive integer.
        """
        n = int(arg)
        if n <= 0:
            raise commands.BadArgument('Index must be a positive integer.')
        return n


class DatetimeConverter(commands.Converter):

    async def convert(self, ctx: commands.Context, arg: str) -> datetime:
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
                raise commands.BadArgument(
                    "Timestamp cannot correspond to a time in the past.")
            return datetime.fromtimestamp(timestamp,
                                          tz=timezone.get_default_timezone())
        except (ValueError, OSError, OverflowError) as e:
            logger.debug('Direct timestamp conversion failed.')

        try:
            delta = parse_time(arg)
            return now + delta
        except (ValueError, KeyError) as e:
            raise commands.BadArgument('Invalid duration format.')


class RegexConverter(commands.Converter):

    async def convert(self, ctx: commands.Context, arg: str) -> str:
        """
        Checks if provided regex pattern is valid.
        """
        try:
            re.compile(arg)
        except re.error:
            raise commands.BadArgument(
                "The regex pattern provided is invalid.")
        return arg


class ListConverter(commands.Converter):

    async def convert(self, ctx: commands.Context,
                      argument: str) -> list[int] | str:
        """
        Checks if provided list can be separated and parsed.
        """
        if argument == '*':
            return '*'

        try:
            return list(map(int, re.split('\s*[,;\s]\s*', argument)))
        except ValueError:
            raise commands.BadArgument("The list provided is invalid.")
