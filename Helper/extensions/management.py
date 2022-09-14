from datetime import timedelta
from typing import Optional

import discord
from discord.ext import commands

from ..main import HelperBot


class Management(
    commands.Cog,
    description="Server management and utility tools.\n`<input>` are mandatory and `[input]` are optional.",
):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot

    @commands.command(help="Delete a number of messages from a channel")
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

    @commands.command(help="Change nickname of a member")
    @commands.has_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def nick(
        self, ctx: commands.Context, member: discord.Member, nick: Optional[str] = None
    ) -> None:
        nick = nick or member.name
        if len(nick) <= 32 and (
            ctx.author.top_role >= member.top_role or member != ctx.guild.owner
        ):
            embed1 = discord.Embed(
                description=f"<:tick:1001136782508826777> Nickname changed for {member.mention}.",
                color=discord.Color.green(),
            )
            await member.edit(nick=nick)
            await ctx.send(embed=embed1)
        else:
            embed2 = discord.Embed(
                description="<:no:1001136828738453514> You can't change nickname of this user.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed2)

    @commands.command(help="Suggest something to get public opinions")
    @commands.guild_only()
    async def suggest(self, ctx: commands.Context, *, suggestion: str) -> None:
        suggestion_channel = discord.utils.get(
            ctx.guild.text_channels, name="suggestions"
        )
        suggestion_embed = discord.Embed(
            description=f"**Suggestion**\n\n{suggestion}", color=discord.Color.blue()
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
            description=f"<:tick:1001136782508826777> Your suggestion has been sent to {suggestion_channel.mention}.",
            color=discord.Color.green(),
        )
        feedback_embed.set_footer(
            text="The staff team will review your suggestion as soon as possible."
        )
        await ctx.send(embed=feedback_embed)

    @commands.command(help="Lock mentioned or current channel")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def lock(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel]
    ) -> None:
        channel = channel or ctx.channel
        for role in ctx.guild.roles:
            if not role.permissions.administrator and not role.is_bot_managed():
                await channel.set_permissions(role, send_messages=False)
        embed = discord.Embed(
            description=f"<:tick:1001136782508826777> Locked {channel.mention}.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command(help="Unlock mentioned or current channel")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def unlock(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel]
    ) -> None:
        channel = channel or ctx.channel
        for role in ctx.guild.roles:
            if not role.permissions.administrator and not role.is_bot_managed():
                await channel.set_permissions(role, send_messages=True)
        embed = discord.Embed(
            description=f"<:tick:1001136782508826777> Unlocked {channel.mention}.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command(help="Start a poll for people to vote on")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def poll(self, ctx: commands.Context, question: str, *options: str):
        if len(options) <= 1:
            a_embed = discord.Embed(
                description="<:no:1001136828738453514> You need more than one option to make a poll!",
                color=discord.Color.red(),
            )
            return await ctx.send(embed=a_embed)
        elif len(options) > 10:
            b_embed = discord.Embed(
                description="<:no:1001136828738453514> You cannot make a poll for more than ten options!",
                color=discord.Color.red(),
            )
            return await ctx.send(embed=b_embed)
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
                title=f"{question}",
                description="\n".join(description),
                color=discord.Color.blue(),
            )
            poll_embed.set_footer(text=f"Poll by {str(ctx.author)}")
            poll_embed.timestamp = discord.utils.utcnow()
            poll_message = await ctx.send(embed=poll_embed)
            for reaction in reactions[: len(options)]:
                await poll_message.add_reaction(reaction)

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Management(bot))
