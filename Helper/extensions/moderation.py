from datetime import datetime, timedelta
from typing import Optional, Union

import discord
import humanfriendly
from discord.ext import commands, tasks

from ..main import HelperBot
from ..utils import DurationCoverter


class Moderation(
    commands.Cog,
    description="Used to manage server and punish misdeeds.\n`<input>` are mandatory and `[input]` are optional.",
):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot

    @commands.command(
        help="Mute a member so they cannot type",
    )
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def mute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        time: Optional[DurationCoverter] = None,
        *,
        reason: Optional[str] = None,
    ) -> None:
        time: Union[timedelta, None] = time
        if (ctx.author.top_role > member.top_role) or (member != ctx.guild.owner):
            if time:
                if time.total_seconds() <= 2160000:
                    embed1 = discord.Embed(
                        description=f"<:tick:1001136782508826777> Muted {member} for `{humanfriendly.format_timespan(time.total_seconds())}`.\n**Reason:** {reason}",
                        color=discord.Color.green(),
                    )
                    embed1.timestamp = discord.utils.utcnow()
                    await member.timeout(
                        time, reason=f"{reason if reason else ctx.author.id}"
                    )
                    await self.bot.logs.send(embed=embed1)
                    await ctx.send(embed=embed1)
                else:
                    embed2 = discord.Embed(
                        description="<:no:1001136828738453514> Maximum mute duration is `25 days`.",
                        color=discord.Color.red(),
                    )
                    await ctx.send(embed=embed2)
            else:
                unmute_time = discord.utils.utcnow() + timedelta(seconds=2160000)
                embed3 = discord.Embed(
                    description=f"<:tick:1001136782508826777> Muted {member} for `25d`.\n**Reason:** {reason}",
                    color=discord.Color.green(),
                )
                embed3.timestamp = discord.utils.utcnow()
                await member.timeout(
                    unmute_time, reason=f"{reason if reason else ctx.author.id}"
                )
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
        reason: Optional[str] = None,
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
        member: Union[discord.Member, discord.User],
        *,
        reason: Optional[str] = None,
    ) -> None:
        if isinstance(member, discord.User) or (
            isinstance(member, discord.Member)
            and (ctx.author.top_role > member.top_role or member != ctx.guild.owner)
        ):
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
        member: Union[discord.User, discord.Member],
        *,
        reason: Optional[str] = None,
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
        time: DurationCoverter,
        *,
        reason: Optional[str] = None,
    ) -> None:
        time: timedelta = time  # type: ignore
        if time:
            if time.total_seconds() <= 21600:
                embed1 = discord.Embed(
                    description=f"<:tick:1001136782508826777> Slowmode of `{humanfriendly.format_timespan(time.total_seconds())}` has been started in {ctx.channel.mention}.\n**Reason:** {reason}",
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
                description=f"<:tick:1001136782508826777> Slowmode has been terminated in {ctx.channel.mention}.\n**Reason:** {reason}",
                color=discord.Color.green(),
            )
            embed3.timestamp = discord.utils.utcnow()
            await ctx.channel.edit(
                slowmode_delay=0, reason=f"{reason if reason else ctx.author.id}"
            )
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
        reason: Optional[str] = None,
    ) -> None:
        if (
            member == ctx.author or member == ctx.guild.owner or member == self.bot.user
        ) or (ctx.author.top_role <= member.top_role):
            embed = discord.Embed(
                description="<:no:1001136828738453514> You can't warn this user.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
        else:
            await self.bot.db.warn_db.warn_entry(
                ctx.guild.id, member.id, reason, ctx.message.created_at.timestamp()
            )
            embed1 = discord.Embed(
                description=f"<:tick:1001136782508826777> {ctx.author.name} has warned {member.name}.\n**Reason:** {reason}",
                color=discord.Color.green(),
            )
            embed1.timestamp = discord.utils.utcnow()
            await ctx.send(embed=embed1)
            await self.bot.logs.send(embed=embed1)
            data = await self.bot.db.warn_db.warn_log(ctx.guild.id, member.id)
            count = len(data[3])
            embed2 = discord.Embed(
                title=f"Warned by {ctx.author.name} in {ctx.guild.name}",
                description=f"Total warn(s) -> [{count}]"
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
    async def warns(
        self, ctx: commands.Context, member: discord.Member
    ) -> Optional[discord.Message]:
        data = await self.bot.db.warn_db.warn_log(ctx.guild.id, member.id)
        if not data or not data[3]:
            embed3 = discord.Embed(
                description=f"<:bullet:1014583675184230511> {member.mention} has a clean record.",
                color=discord.Color.blue(),
            )
            return await ctx.send(embed=embed3)
        embed = discord.Embed(
            title=f"{member.name}'s Misdeeds",
            description=f"Total Warns: `{len(data[2])}`",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=member.display_avatar)
        for i in range(len(data[2])):
            timestamp = datetime.fromtimestamp(float(data[3][i]))
            reason = data[2][i]
            embed.add_field(
                name=f"On {discord.utils.format_dt(timestamp, style='D')}",
                value=f"<:bullet:1014583675184230511> Reason: {reason}\n<:bullet:1014583675184230511> Warn ID: `{data[3][i]}`",
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
    ) -> Optional[discord.Message]:
        data = await self.bot.db.warn_db.warn_log(ctx.guild.id, member.id)
        if not data:
            embed3 = discord.Embed(
                description=f"<:bullet:1014583675184230511> {member.mention} has a clean record.",
                color=discord.Color.blue(),
            )
            return await ctx.send(embed=embed3)
        if data[3] and warn_id in data[3]:
            index = data[3].index(warn_id)
            embed1 = discord.Embed(
                description=f"<:tick:1001136782508826777> Deleted warn entry.",
                color=discord.Color.green(),
            )
            embed1.timestamp = discord.utils.utcnow()
            await self.bot.db.warn_db.remove_warn(ctx.guild.id, member.id, index)
            await self.bot.logs.send(embed=embed1)
            return await ctx.send(embed=embed1)
        else:
            embed2 = discord.Embed(
                description="<:no:1001136828738453514> No warn entry corresponding user found.",
                color=discord.Color.red(),
            )
            return await ctx.send(embed=embed2)

    @tasks.loop(hours=24)
    async def clean_warns(self) -> None:
        data = await self.bot.db.warn_db.get_all()
        for raw in data:
            if not raw[3]:
                await self.bot.db.warn_db.remove_record(raw[0], raw[1])
                continue
            for time in raw[3]:
                diff = datetime.now() - datetime.fromtimestamp(float(time))
                clear_after = 5260000 - round(diff.total_seconds())
                clear_at = datetime.now() + timedelta(seconds=clear_after)
                if datetime.now() >= clear_at:
                    index = raw[3].index(time)
                    if len(raw[3]) > 1:
                        await self.bot.db.warn_db.remove_warn(raw[0], raw[1])
                    else:
                        raw[2].remove(raw[2][index])
                        raw[3].remove(raw[3][index])
                        await self.bot.db.warn_db.update_warn(raw)

    @clean_warns.before_loop
    async def before_clear_warns(self):
        await self.bot.wait_until_ready()
        print("🔃 Started Clear Warns loop.")

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")
        self.clean_warns.start()


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Moderation(bot))
