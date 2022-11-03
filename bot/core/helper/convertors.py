import datetime

import time_str
from discord.ext import commands


class DurationConvertor(commands.Converter, datetime.timedelta):
    async def convert(self, ctx: commands.Context, args: str) -> datetime.timedelta:
        args = args.strip()
        time = time_str.IntervalConverter(args)
        return time.timedelta_precise()
