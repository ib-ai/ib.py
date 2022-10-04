import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Credits to @AlphartDev on GitHub for this pattern.
TIME_PATTERN = re.compile(
    "(?:([0-9]+)\\s*y[a-z]*[,\\s]*)?" \
    + "(?:([0-9]+)\\s*mo[a-z]*[,\\s]*)?" \
    + "(?:([0-9]+)\\s*w[a-z]*[,\\s]*)?" \
    + "(?:([0-9]+)\\s*d[a-z]*[,\\s]*)?" \
    + "(?:([0-9]+)\\s*h[a-z]*[,\\s]*)?" \
    + "(?:([0-9]+)\\s*m[a-z]*[,\\s]*)?" \
    + "(?:([0-9]+)\\s*(?:s[a-z]*)?)?"
)

def parse_duration(duration: str, seconds: bool = False):
    matcher = TIME_PATTERN.match(duration)

    years = 0
    months = 0
    weeks = 0
    days = 0
    hours = 0
    minutes = 0
    seconds = 0

    if matcher.groups()[0]: years += int(matcher.groups()[0])
    if matcher.groups()[1]: months += int(matcher.groups()[1])
    if matcher.groups()[2]: weeks += int(matcher.groups()[2])
    if matcher.groups()[3]: days += int(matcher.groups()[3])
    if matcher.groups()[4]: hours += int(matcher.groups()[4])
    if matcher.groups()[5]: minutes += int(matcher.groups()[5])
    if matcher.groups()[6]: seconds += int(matcher.groups()[6])

    if not any((years, months, weeks, days, hours, minutes, seconds)):
        raise RuntimeError("Invalid time specified.")
    
    if seconds:
        time = relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds).seconds
    else:
        time = datetime.utcnow() + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)

    return time