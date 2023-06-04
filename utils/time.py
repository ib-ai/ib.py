import re
import asyncio
from datetime import datetime, timedelta

from tortoise import timezone

DEGENERACY_DELAY = timedelta(seconds=1)  # when datetime is in the past, a small amount of time is slept for regardless
MAX_DELTA = timedelta(days=40)  # asyncio.sleep is faulty for longer periods of time
async def long_sleep_until(terminus: datetime):
    """
    Sleep until the datetime object given.
    If in the past, a DEGENERACY_DELAY amount is slept.
    """
    now = timezone.now()
    if terminus < now:
        terminus = now + DEGENERACY_DELAY
    while terminus - now > MAX_DELTA:
        await asyncio.sleep(MAX_DELTA.total_seconds())
        now = timezone.now()
    await asyncio.sleep((terminus - now).total_seconds())


ENDMONTH_BUFFER = timedelta(days=5)
CODES = {'w': 'weeks', 'd': 'days', 'h': 'hours', 'm': 'minutes', 's': 'seconds'}
def parse_time(s: str) -> timedelta:
    """
    Convert short-hand duration time string into a python timedelta object.
    """
    if not re.fullmatch('(?:\d+\D+)*', s):
        raise ValueError()
    total_delta = timedelta()
    for value, key in re.findall('(\d+)(\D+)', s):
        value = int(value)
        if key.startswith('y'):
            # python timedelta objects don't work with years
            # implemented this way to preserve day and month of year
            now = timezone.now() + total_delta
            if now.month == 2 and now.day == 29:  # for when you add 1 year to the 29th of February
                now -= ENDMONTH_BUFFER            # subtract a few days so datetime initialization doesn't throw errors
            for i in range(value):
                next = datetime(
                    year = now.year + 1,
                    month = now.month,
                    day = now.day,
                    hour = now.hour,
                    minute = now.minute,
                    second = now.second,
                    microsecond = now.microsecond,
                    tzinfo = timezone.get_default_timezone(),
                )
                total_delta += next - now
                now = next
        elif key.startswith('mo'):
            # python timedelta objects don't work with months
            # implemented this way to preserve the day of month
            now = timezone.now() + total_delta
            if now.day >= 28:           # for when you add 1 month to the 31st of January, and similar
                now -= ENDMONTH_BUFFER  # subtract a few days so datetime initialization doesn't throw errors
            for i in range(value):
                year = now.year
                month = now.month
                if month == 12:
                    month = 0
                    year += 1
                next = datetime(
                    year = year,
                    month = month + 1,
                    day = now.day,
                    hour = now.hour,
                    minute = now.minute,
                    second = now.second,
                    microsecond = now.microsecond,
                    tzinfo = timezone.get_default_timezone(),
                )
                total_delta += next - now
                now = next
        else:
            # remaining cases are handled with "codes" dictionary
            total_delta += timedelta(**{CODES[key[0]]: value})
    return total_delta