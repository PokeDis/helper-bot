from datetime import timedelta
from typing import Optional

import discord
from discord.ext import commands

from ..main import HelperBot


class Management(commands.Cog, description="Management commands."):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx: commands.Context, count: int) -> None:
        await ctx.message.delete()
        delete_from = discord.utils.utcnow() - timedelta(days=13)
        await ctx.channel.purge(
            limit=count,
            check=lambda message: not message.pinned,
            after=delete_from,
            oldest_first=False,
        )

    @commands.command()
    @commands.guild_only()
    async def suggest(self, ctx: commands.Context, *, suggestion: str) -> None:
        suggestion_channel = discord.utils.get(
            ctx.guild.text_channels, name="suggestions"
        )
        suggestion_embed = discord.Embed(
            description=f"**Suggestion**\n\n{suggestion}", colour=0x2F3136
        )
        suggestion_embed.set_author(
            name=f"{str(ctx.author)} - {ctx.author.id}",
            icon_url=ctx.author.display_avatar,
        )
        suggestion_embed.set_footer(text=f"{ctx.guild.name} | Submitted at")
        suggestion_embed.timestamp = discord.utils.utcnow()
        message = await suggestion_channel.send(embed=suggestion_embed)
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        feedback_embed = discord.Embed(
            title="<a:_:1000859478217994410>  Success",
            description=f"> Your suggestion has been sent to {suggestion_channel.mention}.",
            colour=0x2F3136,
        )
        feedback_embed.set_footer(
            text="The staff team will review your suggestion as soon as possible."
        )
        await ctx.send(embed=feedback_embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def lock(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel]
    ) -> None:
        channel = channel or ctx.channel
        for role in ctx.guild.roles:
            if not role.permissions.administrator and not role.is_bot_managed():
                await channel.set_permissions(role, send_messages=False)
        await ctx.send(f"Locked {channel.mention}.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def unlock(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel]
    ) -> None:
        channel = channel or ctx.channel
        for role in ctx.guild.roles:
            if not role.permissions.administrator and not role.is_bot_managed():
                await channel.set_permissions(role, send_messages=True)
        await ctx.send(f"Unlocked {channel.mention}.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def poll(self, ctx: commands.Context, question: str, *options: str):
        if len(options) <= 1:
            return await ctx.send("You need more than one option to make a poll!")
        elif len(options) > 10:
            return await ctx.send("You cannot make a poll for more than ten options!")
        else:
            reactions = [
                "1️⃣",
                "2️⃣",
                "3️⃣",
                "4️⃣",
                "5️⃣",
                "6️⃣",
                "7️⃣",
                "8️⃣",
                "9️⃣",
                "🔟",
            ]
            description = [f"{reactions[i]} {j}" for i, j in enumerate(options)]
            poll_embed = discord.Embed(
                title=f"{question}", description="\n".join(description), colour=0x2F3136
            )
            poll_embed.set_footer(text=f"Poll by {str(ctx.author)}")
            poll_embed.timestamp = discord.utils.utcnow()
            poll_message = await ctx.send(embed=poll_embed)
            for reaction in reactions[: len(options)]:
                await poll_message.add_reaction(reaction)


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Management(bot))
