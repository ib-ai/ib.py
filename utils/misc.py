from typing import Union

from datetime import datetime, timedelta
from tortoise import timezone
import discord

def discord_timestamp_string_format(dt: datetime, fmt: str = ''):
    return f'<t:{int(dt.timestamp())}{f":{fmt}" if fmt else ""}>'

ENDMONTH_BUFFER = timedelta(days=5)
def parse_time(s) -> timedelta:
    """
    Convert short-hand time string into a python timedelta object.
    """
    total_delta = timedelta()
    N = len(s)
    key = ''
    value = ''
    for i, c in enumerate(s):
        if not c.isnumeric():
            key += c
            if i < N-1:
                continue
        if not key:
            value += c
            continue
        value = int(value)
        if not value:
            continue
        if key.startswith('y'):  # implemented this way to preserve day and month of year
            now = timezone.now()
            if now.month == 2 and now.day == 29:  # for when you add 1 year to the 29th of February
                now -= ENDMONTH_BUFFER
            for i in range(value):
                next = datetime(
                    year = now.year + 1,
                    month = now.month,
                    day = now.day,
                    hour = now.hour,
                    minute = now.minute,
                    second = now.second,
                    microsecond = now.microsecond,
                    tzinfo = timezone.get_timezone(),
                )
                total_delta += next - now
                now = next
        elif key.startswith('mo'):  # implemented this way to preserve the day of month
            now = timezone.now()
            if now.day >= 28:
                now -= ENDMONTH_BUFFER  # for when you add 1 month to the 31st of January
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
                    tzinfo = timezone.get_timezone(),
                )
                total_delta += next - now
                now = next
        elif key.startswith('w'):
            total_delta += timedelta(weeks=value)
        elif key.startswith('d'):
            total_delta += timedelta(days=value)
        elif key.startswith('h'):
            total_delta += timedelta(hours=value)
        elif key.startswith('m'):
            total_delta += timedelta(minutes=value)
        elif key.startswith('s'):
            total_delta += timedelta(seconds=value)
        else:
            raise ValueError('Invalid time format.')
        key = ''
        value = c
    return total_delta


def ordinal(n: int) -> str:
    if n < 0:
        raise ValueError('Negative ordinal - ordinal must be passed a non-negative integer.')

    if n%100 in (11, 12, 13): return f'{n}th'
    if n%10 == 1: return f'{n}st'
    if n%10 == 2: return f'{n}nd'
    if n%10 == 3: return f'{n}rd'
    return f'{n}th'