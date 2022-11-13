import datetime
import typing

import discord
import humanfriendly
from discord.ext import commands, tasks

from bot.core.views.paginators import ClassicPaginator

if typing.TYPE_CHECKING:
    from bot.core import PokeHelper


class Reputation(commands.Cog):

    """Reputation commands to give and take reputation from users."""

    def __init__(self, bot: "PokeHelper") -> None:
        self.bot = bot

    @commands.group(help="Check your/others rep")
    @commands.guild_only()
    async def rep(self, ctx: commands.Context, member: discord.Member | None = None) -> discord.Message | None:
        if ctx.invoked_subcommand is None:
            member = member or ctx.author
            embed = discord.Embed(color=discord.Color.blue())
            embed.set_author(name=f"{member.name}", icon_url=member.display_avatar)
            rep_data = await self.bot.db.rep.get_rep(member.id)
            if rep_data is None:
                embed.add_field(name="Reputation", value="0")
                return await ctx.send(embed=embed)
            embed.add_field(name="Reputation", value=f"{rep_data.reps}")
            return await ctx.send(embed=embed)
        return None

    @rep.command(help="Leaderboard for reputation")
    @commands.guild_only()
    async def leaderboard(self, ctx: commands.Context) -> None | discord.Message:
        leaderboard = await self.bot.db.rep.leaderboard
        if not leaderboard:
            embed = discord.Embed(
                description=f"<:no:998461229376999514> Leaderboard is empty.",
                color=discord.Color.red(),
            )
            return await ctx.reply(embed=embed)
        ranking = [i for i, x in enumerate(leaderboard) if x.user_id == ctx.author.id]
        ur_rank = ranking[0] + 1 if ranking else "N/A"
        ur_rep = await self.bot.db.rep.get_rep(ctx.author.id) or 0
        embeds = []
        chunks = [leaderboard[i : i + 10] for i in range(0, len(leaderboard), 10)]
        count = 0
        for chunk in chunks:
            embed = discord.Embed(
                color=discord.Color.blue(), description=f"**Your rank:** {ur_rank}\n**Your rep:** {ur_rep}\n\n"
            )
            embed.set_author(name=f"Reputation Leaderboard", icon_url=ctx.guild.icon)
            for user in chunk:
                count += 1
                embed.description += f"{count}. <@{user.user_id}>\nReputation: {user.reps}\n"
            embeds.append(embed)
        return await ClassicPaginator(ctx, embeds).start()

    @rep.command(help="Give +1 rep to a member")
    @commands.cooldown(1, 120, commands.BucketType.user)
    @commands.guild_only()
    async def give(self, ctx: commands.Context, member: discord.Member) -> discord.Message | None:
        embed = discord.Embed(
            description=f"<:tick:1001136782508826777> Gave +1 rep to {member.mention}.",
            color=discord.Color.green(),
        )
        data = await self.bot.db.rep.get_rep(member.id)
        if data is None:
            await self.bot.db.rep.update_rep(member.id, ctx.author.id)
            return await ctx.send(embed=embed)

        if ctx.author.id in [x.user_id for x in data.cooldown]:
            time = [x for x in data.cooldown if x.user_id == ctx.author.id][0].time
            diff = datetime.datetime.utcnow() - time

            if diff.seconds < 7200:
                embed = discord.Embed(
                    description=f"<:no:1001136828738453514> You can give them rep again in"
                    f" {humanfriendly.format_timespan(7200 - diff.seconds)}.",
                    color=discord.Color.red(),
                )
                return await ctx.send(embed=embed)
            else:
                await self.bot.db.rep.update_rep(member.id, ctx.author.id)
                return await ctx.send(embed=embed)
        else:
            await self.bot.db.rep.update_rep(member.id, ctx.author.id)
            return await ctx.send(embed=embed)

    @rep.command(help="Remove certain amount of rep from a member")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def take(self, ctx: commands.Context, member: discord.Member, amount: int) -> discord.Message:
        reps = await self.bot.db.rep.remove_rep(member.id, amount)
        embed1 = discord.Embed(
            title=f"<:tick:1001136782508826777> {ctx.author.name} took rep from {member.name}.",
            description=f"{member.mention} now has {reps} rep.",
            color=discord.Color.green(),
        )
        await self.bot.logs.send(embed=embed1)
        return await ctx.send(embed=embed1)

    @rep.command(help="Reset a members rep to 0")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def clear(self, ctx: commands.Context, member: discord.Member) -> discord.Message:
        embed = discord.Embed(
            title=f"<:tick:1001136782508826777> {ctx.author.name} cleared {member.name}'s rep.",
            description=f"{member.mention}'s rep reset to 0.",
            color=discord.Color.green(),
        )
        await self.bot.db.rep.clear_rep(member.id)
        await self.bot.logs.send(embed=embed)
        return await ctx.send(embed=embed)

    @tasks.loop(minutes=10)
    async def clean_rep_cd(self) -> None:
        cooldowns = await self.bot.db.rep.get_all_cooldown
        for user in cooldowns:
            for cooldown in user.cooldown:
                if cooldown.time + datetime.timedelta(hours=2) <= datetime.datetime.utcnow():
                    await self.bot.db.rep.remove_cooldown(user.user_id, cooldown.user_id)

    @clean_rep_cd.before_loop
    async def before_clean_rep_cd(self):
        await self.bot.wait_until_ready()
        print("🔃 Started Clean Reputation Cooldown loop.")

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")
        self.clean_rep_cd.start()


async def setup(bot: "PokeHelper") -> None:
    await bot.add_cog(Reputation(bot))
