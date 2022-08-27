import asyncio
import datetime
import typing

import humanfriendly
from discord.ext import commands, tasks

from custom_durations import Duration

from ..main import HelperBot


class DurationCoverter(commands.Converter):

    total_seconds: typing.Callable[[], int]

    async def convert(self, ctx: commands.Context, args: str) -> datetime.timedelta:
        args = args.strip()
        time = Duration(args)
        return datetime.timedelta(seconds=time.to_seconds())


class Reminder(commands.Cog):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot

    @commands.command(
        name="remind",
        aliases=["reminder", "remindme"],
        description="Reminds you of something.",
    )
    async def remind(
        self, ctx: commands.Context, reminder: DurationCoverter, *, message: str = "None"
    ) -> None:
        time = datetime.datetime.utcnow() + reminder
        data = [
            ctx.message.id,
            time.timestamp(),
            ctx.message.channel.id,
            ctx.author.id,
            message,
        ]
        await self.bot.db.reminder_db.add_reminder(data)
        await ctx.reply(
            f"I will remind you in {humanfriendly.format_timespan(reminder.total_seconds())}."
        )
        await asyncio.sleep(reminder.total_seconds())
        await ctx.reply(f"{ctx.author.mention}\n**Reminder:** {message}")
        await self.bot.db.reminder_db.remove_reminder(ctx.message.id)

    @tasks.loop(seconds=20)
    async def check_reminders(self) -> None:
        time = datetime.datetime.utcnow().timestamp()
        reminders = await self.bot.db.reminder_db.get_by_time(time)
        for reminder in reminders:
            channel = self.bot.get_channel(reminder[2]) or await self.bot.fetch_channel(
                reminder[2]
            )
            user = self.bot.get_user(reminder[3]) or await self.bot.fetch_user(
                reminder[3]
            )
            await channel.send(f"{user.mention}\n**Reminder:** {reminder[4]}")
            await self.bot.db.reminder_db.remove_reminder(reminder[0])

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.check_reminders.start()


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Reminder(bot))
