import discord
from discord.ext import commands

from ..main import HelperBot


class Management(commands.Cog, description="Tag related commands."):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot


    @commands.command()
    async def droptags(self, ctx: commands.Context) -> None:
        await self.bot.tag_db.exec_write_query("DROP TABLE tags")
        await ctx.send("done")


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Management(bot))
