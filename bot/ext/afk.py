import datetime
import re
import typing as t

import discord
import humanfriendly
from discord.ext import commands

from bot.database.models import UserAfk

if t.TYPE_CHECKING:
    from bot.core import PokeHelper


class Afk(commands.Cog):
    a

    def __init__(self, bot: "PokeHelper") -> None:
        self.bot = bot
        self.afks: list[UserAfk] = []

    @commands.command(help="Set your afk status")
    @commands.guild_only()
    @commands.has_role("Server Booster")
    async def afk(self, ctx: commands.Context, *, reason: str = "No reason provided") -> None:
        await self.bot.db.afk.add_afk(UserAfk(user_id=ctx.author.id, reason=reason, time=discord.utils.utcnow()))
        await ctx.send(
            embed=discord.Embed(
                title="You are now afk.", description=f"**Reason:** *{reason}*", color=discord.Color.random()
            )
        )
        try:
            await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not self.afks or len(self.afks) != await self.bot.db.afk.get_total_afk():
            self.afks = await self.bot.db.afk.get_all_afk()
        if message.author.bot:
            return
        for user in self.afks:
            if message.author.id == user.user_id:
                await self.bot.db.afk.delete_afk(user.user_id)
                await message.reply(
                    embed=discord.Embed(
                        title="You are no longer afk.",
                        description=f"**Time:** {humanfriendly.format_timespan(datetime.datetime.utcnow() - user.time)}",
                        color=discord.Color.random(),
                    )
                )
                try:
                    await message.author.edit(nick=re.sub(r"\[AFK\]", "", message.author.display_name, count=1))
                except discord.Forbidden:
                    pass
                return
            if member := [x for x in message.mentions if x.id == user.user_id]:
                author = member[0]
                await message.channel.send(
                    embed=discord.Embed(
                        title=f"{author.display_name} is afk.",
                        description=f"**Reason:** *{user.reason}*\n**Time:** *{discord.utils.format_dt(user.time, 'R')}*",
                    )
                )


async def setup(bot: "PokeHelper") -> None:
    await bot.add_cog(Afk(bot))
