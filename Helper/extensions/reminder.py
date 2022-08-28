import asyncio
import datetime

import humanfriendly
from discord.ext import commands, tasks

from ..utils import DurationCoverter

from ..main import HelperBot


class Reminder(commands.Cog):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot

    @commands.group(
        name="reminder",
        aliases=["remindme", "remind"],
        description="Reminds you of something.",
        invoke_without_command=True,
    )
    @commands.guild_only()
    async def reminder(
        self, ctx: commands.Context, duration: DurationCoverter, *, message: str = "None"
    ) -> None:
        duration: datetime.timedelta = duration  # type: ignore
        time = datetime.datetime.utcnow() + duration
        if ctx.invoked_subcommand is None:
            msg = await ctx.send(
                f"I will remind you in {humanfriendly.format_timespan(duration.total_seconds())}."
            )
            data = [
                msg.id,
                time.timestamp(),
                ctx.message.channel.id,
                ctx.author.id,
                message,
            ]
            await self.bot.db.reminder_db.add_reminder(data)
            await asyncio.sleep(duration.total_seconds())
            data = await self.bot.db.reminder_db.get_one(msg.id)
            if len(data):
                await msg.reply(f"{ctx.author.mention}\n**Reminder:** {message}")
                await self.bot.db.reminder_db.remove_reminder(msg.id)

    @reminder.command(
        name="delete",
        description="Delete a reminder."
    )
    @commands.guild_only()
    async def _delete(self, ctx: commands.Context, reminder_id: int) -> None:
        data = await self.bot.db.reminder_db.get_one(reminder_id)
        if len(data):
            await ctx.send("Reminder Deleted.")
            await self.bot.db.reminder_db.remove_reminder(reminder_id)
            return
        await ctx.send("No such reminder found.")

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
