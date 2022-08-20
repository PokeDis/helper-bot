from typing import Literal, Optional

import io
import chat_exporter
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

    @commands.command()
    @commands.guild_only()
    async def sync(
        self,
        ctx: commands.Context,
        guilds: commands.Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None,
    ) -> None:
        if not guilds:
            if spec == "~":
                synced = await self.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                self.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await self.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                self.bot.tree.clear_commands(guild=ctx.guild)
                await self.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await self.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await self.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


    @commands.command()
    async def archive(self, ctx: commands.Context, channel: discord.TextChannel, archive_channel: discord.TextChannel) -> None:
        if channel and archive_channel:
            transcript = await chat_exporter.export(channel, tz_info='UTC')
            transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                        filename=f"{channel.name}.html")

            await archive_channel.send(file=transcript_file)
            await channel.delete()


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Management(bot))
