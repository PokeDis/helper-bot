import asyncio
import datetime
import humanfriendly

import discord
from discord.ext import commands, tasks

from ..utils import DurationCoverter

from ..main import HelperBot


class Reminder(commands.Cog, description="Reminders to keep you in check with your tasks.\n`<input>` are mandatory and `[input]` are optional."):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot

    @commands.group(
        name="reminder",
        aliases=["remindme", "remind"],
        help="Reminds you of something",
        invoke_without_command=True,
    )
    @commands.guild_only()
    async def reminder(
        self, ctx: commands.Context, duration: DurationCoverter, *, message: str = "None"
    ) -> None:
        duration: datetime.timedelta = duration  # type: ignore
        time = datetime.datetime.now() + duration
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                description=f"<:tick:1001136782508826777> I will remind you in {humanfriendly.format_timespan(duration.total_seconds())}.",
                color=discord.Color.green()
            )
            msg = await ctx.send(embed=embed)
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
        help="Delete a reminder"
    )
    @commands.guild_only()
    async def _delete(self, ctx: commands.Context, reminder_id: int) -> None:
        data = await self.bot.db.reminder_db.get_one(reminder_id)
        if len(data):
            embed = discord.Embed(
                description="<:tick:1001136782508826777> Reminder deleted.",
                color = discord.Color.green()
            )
            await ctx.send(embed=embed)
            await self.bot.db.reminder_db.remove_reminder(reminder_id)
            return
        await ctx.send("No such reminder found.")

    @reminder.command(
        name="all",
        help="Get a list of all your reminders"
    )
    @commands.guild_only()
    async def _all(self, ctx: commands.Context) -> None:
        data = await self.bot.db.reminder_db.get_by_user(ctx.author.id)
        embed = discord.Embed(
            title=f"{ctx.author.name}'s Reminders",
            description=f"Total Reminders: `{len(data)}`",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=ctx.author.display_avatar)
        for record in data:
            reminder_id = record[0]
            remind_after = discord.utils.format_dt(datetime.datetime.fromtimestamp(record[1]), style="R")
            channel = self.bot.get_channel(record[2]) or await self.bot.fetch_channel(record[2])
            message = record[4] if len(record[4]) <= 20 else record[4][0:17]+"..."
            embed.add_field(
                name=f"Reminder ID: {reminder_id}",
                value=f"<:bullet:1014583675184230511> Remind at: {remind_after}\n<:bullet:1014583675184230511> Message: {message}\n<:bullet:1014583675184230511> In: {channel.mention}",
                inline=False,
            )
        return await ctx.send(embed=embed)

    @tasks.loop(seconds=10)
    async def check_reminders(self) -> None:
        time = datetime.datetime.now().timestamp()
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

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()
        print("🔃 Started Check Reminders loop.")

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")
        self.check_reminders.start()


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Reminder(bot))
