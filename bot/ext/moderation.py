import datetime
import typing

import discord
import humanfriendly
from discord.ext import commands, tasks

from bot.core.helper import DurationConvertor

if typing.TYPE_CHECKING:
    from bot.core import PokeHelper


class Moderation(commands.Cog):

    """Moderation commands to help you moderate your server."""

    def __init__(self, bot: "PokeHelper") -> None:
        self.bot = bot

    @tasks.loop(hours=24)
    async def clean_warns(self) -> None:
        data = await self.bot.db.warns.get_all_warns
        for warn in data:
            for record in warn.logs:
                if (datetime.datetime.utcnow() - record.time).days >= 30:
                    await self.bot.db.warns.remove_warn(warn.guild_id, warn.user_id, warn.logs.index(record))

    @clean_warns.before_loop
    async def before_clear_warns(self):
        await self.bot.wait_until_ready()
        print("🔃 Started Clear Warns loop.")

    @commands.command(help="Mute a member so they cannot type")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def mute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        time: DurationConvertor | None = None,
        *,
        reason: str = "No reason provided",
    ) -> None:
        if (ctx.author.top_role > member.top_role) or (member != ctx.guild.owner):
            if time is not None:
                if time.total_seconds() <= 2160000:
                    embed1 = discord.Embed(
                        description=f"<:tick:1001136782508826777> Muted {member} for "
                        f"`{humanfriendly.format_timespan(time.total_seconds())}`.\n**Reason:** {reason}",
                        color=discord.Color.green(),
                    )
                    embed1.timestamp = discord.utils.utcnow()
                    await member.timeout(time, reason=f"{reason if reason else ctx.author.id}")
                    await self.bot.logs.send(embed=embed1)
                    await ctx.send(embed=embed1)
                else:
                    embed2 = discord.Embed(
                        description="<:no:1001136828738453514> Maximum mute duration is `25 days`.",
                        color=discord.Color.red(),
                    )
                    await ctx.send(embed=embed2)
            else:
                unmute_time = discord.utils.utcnow() + datetime.timedelta(seconds=2160000)
                embed3 = discord.Embed(
                    description=f"<:tick:1001136782508826777> Muted {member} for `25d`.\n**Reason:** {reason}",
                    color=discord.Color.green(),
                )
                embed3.timestamp = discord.utils.utcnow()
                await member.timeout(unmute_time, reason=f"{reason if reason else ctx.author.id}")
                await self.bot.logs.send(embed=embed3)
                await ctx.send(embed=embed3)
        else:
            embed4 = discord.Embed(
                description="<:no:1001136828738453514> You can't mute this user.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed4)

    @commands.command(help="Unmute a member")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def unmute(self, ctx: commands.Context, member: discord.Member) -> None:
        if member.is_timed_out():
            embed = discord.Embed(
                description=f"<:tick:1001136782508826777> Unmuted {member}.",
                color=discord.Color.green(),
            )
            embed.timestamp = discord.utils.utcnow()
            await member.timeout(None)
            await self.bot.logs.send(embed=embed)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description=f"<:no:1001136828738453514> {member} is not muted.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @commands.command(help="Kick a member")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ) -> None:
        embed1 = discord.Embed(
            description=f"<:tick:1001136782508826777> Kicked {member}.\n**Reason:** {reason}",
            color=discord.Color.green(),
        )
        embed1.timestamp = discord.utils.utcnow()
        if (ctx.author.top_role > member.top_role) or (member != ctx.guild.owner):
            await member.kick(reason=f"{reason if reason else ctx.author.id}")
            await ctx.send(embed=embed1)
        else:
            embed2 = discord.Embed(
                description="<:no:1001136828738453514> You can't kick this user.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed2)

    @commands.command(help="Ban a member")
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ) -> None:
        if ctx.author.top_role > member.top_role or member != ctx.guild.owner:
            embed = discord.Embed(
                description=f"<:tick:1001136782508826777> Banned {member}.\n**Reason:** {reason}",
                color=discord.Color.green(),
            )
            embed.timestamp = discord.utils.utcnow()
            await ctx.guild.ban(member, reason=f"{reason if reason else ctx.author.id}")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description="<:no:1001136828738453514> You can't ban this user.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @commands.command(help="Unban a member")
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(
        self,
        ctx: commands.Context,
        member: discord.User,
        *,
        reason: str = "No reason provided",
    ) -> None:
        embed1 = discord.Embed(
            description=f"<:tick:1001136782508826777> Unbanned {member}.\n**Reason:** {reason}",
            color=discord.Color.green(),
        )
        embed1.timestamp = discord.utils.utcnow()
        await ctx.guild.unban(member, reason=f"{reason if reason else ctx.author.id}")
        await ctx.send(embed=embed1)

    @commands.command(
        help="Enable or disable slowmode on a channel",
    )
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def slowmode(
        self,
        ctx: commands.Context,
        time: DurationConvertor,
        *,
        reason: str = "No reason provided",
    ) -> None:
        if time:
            if time.total_seconds() <= 21600:
                embed1 = discord.Embed(
                    description=f"<:tick:1001136782508826777> Slowmode of "
                    f"`{humanfriendly.format_timespan(time.total_seconds())}` has been started in "
                    f"{ctx.channel.mention}.\n**Reason:** {reason}",
                    color=discord.Color.green(),
                )
                embed1.timestamp = discord.utils.utcnow()
                await ctx.channel.edit(
                    slowmode_delay=int(time.total_seconds()),
                    reason=f"{reason if reason else ctx.author.id}",
                )
                await self.bot.logs.send(embed=embed1)
                await ctx.send(embed=embed1)
            else:
                embed2 = discord.Embed(
                    description="<:no:1001136828738453514> Maximum slowmode duration is `6 hours`.",
                    color=discord.Color.red(),
                )
                await ctx.send(embed=embed2)
        else:
            embed3 = discord.Embed(
                description=f"<:tick:1001136782508826777> Slowmode has been terminated in "
                f"{ctx.channel.mention}.\n**Reason:** {reason}",
                color=discord.Color.green(),
            )
            embed3.timestamp = discord.utils.utcnow()
            await ctx.channel.edit(slowmode_delay=0, reason=f"{reason if reason else ctx.author.id}")
            await self.bot.logs.send(embed=embed3)
            await ctx.send(embed=embed3)

    @commands.command(help="Warn a member")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def warn(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ) -> None:
        if (member == ctx.author or member == ctx.guild.owner or member == self.bot.user) or (
            ctx.author.top_role <= member.top_role
        ):
            embed = discord.Embed(
                description="<:no:1001136828738453514> You can't warn this user.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
        else:
            data = await self.bot.db.warns.update_warn(ctx.guild.id, member.id, reason)
            embed1 = discord.Embed(
                description=f"<:tick:1001136782508826777> {ctx.author.name} has warned {member.name}."
                f"\n**Reason:** {reason}",
                color=discord.Color.green(),
            )
            embed1.timestamp = discord.utils.utcnow()
            await ctx.send(embed=embed1)
            await self.bot.logs.send(embed=embed1)
            embed2 = discord.Embed(
                title=f"Warned by {ctx.author.name} in {ctx.guild.name}",
                description=f"Total warn(s) -> [{len(data.logs)}]"
                "\nWarns reset per 2 months. More than 3 warns per 2 months can have serious consequences.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow(),
            )
            embed2.add_field(name="Reason", value=reason)
            embed2.set_thumbnail(url=ctx.author.display_avatar)
            try:
                await self.bot.logs.send(embed=embed2)
                await member.send(embed=embed2)
            except discord.HTTPException:
                pass

    @commands.command(help="Get warnings for a member")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def warns(self, ctx: commands.Context, member: discord.Member) -> None | discord.Message:
        data = await self.bot.db.warns.get_warn(ctx.guild.id, member.id)
        if data is None:
            embed3 = discord.Embed(
                description=f"<:bullet:1014583675184230511> {member.mention} has a clean record.",
                color=discord.Color.blue(),
            )
            return await ctx.send(embed=embed3)
        embed = discord.Embed(
            title=f"{member.name}'s Misdeeds",
            description=f"Total Warns: `{len(data.logs)}`",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=member.display_avatar)
        for i in data.logs:
            embed.add_field(
                name=f"On {discord.utils.format_dt(i.time, style='D')}",
                value=f"<:bullet:1014583675184230511> Reason: {i.reason}\n<:bullet:1014583675184230511>"
                f" Warn ID: `{i.time.timestamp()}`",
                inline=False,
            )
        return await ctx.send(embed=embed)

    @commands.command(
        help="Clear a single warning from a member",
        aliases=["dw", "rw", "removewarn"],
    )
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def deletewarn(
        self, ctx: commands.Context, member: discord.Member, warn_id: float
    ) -> discord.Message | None:
        data = await self.bot.db.warns.get_warn(ctx.guild.id, member.id)
        if data is None:
            embed3 = discord.Embed(
                description=f"<:bullet:1014583675184230511> {member.mention} has a clean record.",
                color=discord.Color.blue(),
            )
            return await ctx.send(embed=embed3)
        ids = [i.time.timestamp() for i in data.logs]
        if warn_id not in ids:
            embed4 = discord.Embed(
                description=f"<:no:1001136828738453514> {warn_id} is not a valid warn ID.",
                color=discord.Color.red(),
            )
            return await ctx.send(embed=embed4)
        await self.bot.db.warns.remove_warn(ctx.guild.id, member.id, ids.index(warn_id))
        embed = discord.Embed(
            description=f"<:tick:1001136782508826777> Warn ID `{warn_id}` has been removed from {member.mention}.",
            color=discord.Color.green(),
        )
        embed.timestamp = discord.utils.utcnow()
        await self.bot.logs.send(embed=embed)
        await ctx.send(embed=embed)

    @commands.command(help="Displays bot stats")
    @commands.guild_only()
    async def info(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title="Bot Stats",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Servers", value=f"{len(self.bot.guilds)}")
        embed.add_field(name="Users", value=f"{len(self.bot.users)}")
        embed.add_field(name="Bot latency", value=f"{round(self.bot.latency * 1000)}ms")
        embed.set_thumbnail(url=self.bot.user.display_avatar)
        await ctx.send(embed=embed)

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")
        self.clean_warns.start()


async def setup(bot: "PokeHelper") -> None:
    await bot.add_cog(Moderation(bot))
