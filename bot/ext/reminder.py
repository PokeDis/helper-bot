import asyncio
import datetime
import typing

import discord
import humanfriendly
from discord.ext import commands, tasks

from bot.core.helper import DurationConvertor
from bot.core.views.paginators import ClassicPaginator
from bot.database.models import Reminder as ReminderModel

if typing.TYPE_CHECKING:
    from bot.core import PokeHelper


class Reminder(commands.Cog):

    """Reminders to keep you in check with your tasks."""

    def __init__(self, bot: "PokeHelper") -> None:
        self.bot = bot

    @commands.group(
        name="reminder",
        aliases=["remindme", "remind"],
        help="Reminds you of something",
        invoke_without_command=True,
    )
    @commands.guild_only()
    async def reminder(
        self,
        ctx: commands.Context,
        duration: DurationConvertor,
        *,
        about: str,
    ) -> None:
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                description=f"<:tick:1001136782508826777> I will remind you in "
                f"{humanfriendly.format_timespan(duration.total_seconds())} about `{about}`.",
                color=discord.Color.green(),
            )
            msg = await ctx.send(embed=embed)
            await self.bot.db.reminders.add_reminder(
                ReminderModel(msg.id, datetime.datetime.now() + duration, ctx.guild.id, ctx.channel.id, ctx.author.id)
            )
            await asyncio.sleep(duration.total_seconds())
            data = await self.bot.db.reminders.get_reminder(msg.id)
            if data is not None:
                embed = discord.Embed(
                    description=f"<:tick:1001136782508826777> You asked me to remind you about"
                    f" [message]({msg.jump_url}).",
                    color=discord.Color.green(),
                )
                await msg.reply(content=ctx.author.mention, embed=embed)
                await self.bot.db.reminders.delete_reminder(msg.id)

    @reminder.command(name="delete", help="Delete a reminder")
    @commands.guild_only()
    async def _delete(self, ctx: commands.Context, reminder_id: int) -> None | discord.Message:
        data = await self.bot.db.reminders.get_reminder(reminder_id)
        if data is None:
            embed = discord.Embed(
                description=f"<:tick:1001136782508826777> I could not find a reminder with id {reminder_id}",
                color=discord.Color.green(),
            )
            return await ctx.send(embed=embed)
        if data.user_id != ctx.author.id:
            embed = discord.Embed(
                description=f"<:tick:1001136782508826777> You can only delete your own reminders",
                color=discord.Color.green(),
            )
            return await ctx.send(embed=embed)
        await self.bot.db.reminders.delete_reminder(reminder_id)
        embed = discord.Embed(
            description=f"<:tick:1001136782508826777> I have deleted your reminder with id {reminder_id}",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @reminder.command(name="all", help="Get a list of all your reminders")
    @commands.guild_only()
    async def _all(self, ctx: commands.Context) -> discord.Message | None:
        data = await self.bot.db.reminders.get_all_reminder(ctx.author.id)
        if not data:
            embed = discord.Embed(
                description=f"<:tick:1001136782508826777> You have no reminders",
                color=discord.Color.green(),
            )
            return await ctx.send(embed=embed)
        embeds = []
        chunked = [data[i : i + 10] for i in range(0, len(data), 10)]
        for chunk in chunked:
            embed = discord.Embed(
                description=f"Total Reminders: `{len(data)}`",
                color=discord.Color.blue(),
            )
            embed.set_thumbnail(url=ctx.author.display_avatar)
            embed.set_author(name=f"{ctx.author.name}'s Reminders", icon_url=ctx.author.display_avatar)
            for reminder in chunk:
                embed.add_field(
                    name=f"ID: {reminder.message_id}",
                    value=f"<:bullet:1014583675184230511>Reminder in: "
                    f"{discord.utils.format_dt(reminder.end_time, style='R')}\n"
                    f"[Jump to message]"
                    f"(https://discord.com/channels/{reminder.guild_id}/{reminder.channel_id}/{reminder.message_id})",
                    inline=False,
                )
            embeds.append(embed)
        paginator = ClassicPaginator(ctx, embeds)
        return await paginator.start()

    @tasks.loop(seconds=10)
    async def check_reminders(self) -> None:
        reminders = await self.bot.db.reminders.get_reminder_by_time
        for reminder in reminders:
            channel = self.bot.get_channel(reminder.channel_id) or await self.bot.fetch_channel(reminder.channel_id)
            if channel is None:
                continue
            message = await channel.fetch_message(reminder.message_id)
            if message is None:
                continue
            embed = discord.Embed(
                description=f"<:tick:1001136782508826777> You asked me to remind you about"
                f" [message]({message.jump_url})",
                color=discord.Color.green(),
            )
            await message.reply(embed=embed)
            await self.bot.db.reminders.delete_reminder(reminder.message_id)

    @check_reminders.before_loop
    async def before_check_reminders(self) -> None:
        await self.bot.wait_until_ready()
        print("🔃 Started Check Reminders loop.")

    async def cog_load(self) -> None:
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")
        self.check_reminders.start()


async def setup(bot: "PokeHelper") -> None:
    await bot.add_cog(Reminder(bot))
