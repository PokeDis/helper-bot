import discord
import humanfriendly

from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from typing import Optional, Union

from ..main import HelperBot
from ..utils.logistics import DurationCoverter


class Moderation(commands.Cog, description="Used to manage server and belt sinners.\n`<input>` are mandatory and `[input]` are optional."):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot
        self.clean_warns.start()

    # - - - - - Custom Errors - - - - -
    class HierarchyIssues(Exception):
        pass


    class PunishmentIssues(Exception):
        pass
    # - - - - - - - - - - - - - - - - -


    @commands.hybrid_command(
        brief="Mute a member so they cannot type",
        help="Mute a member so they cannot type."
        )
    @app_commands.default_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def mute(self, ctx: commands.Context, member: discord.Member, time: Optional[DurationCoverter] = None, *, reason: Optional[str] = None) -> None:
        if (ctx.author.top_role > member.top_role) or (member != ctx.guild.owner):
            if time:
                if time.total_seconds() <= 2160000:
                    embed1 = discord.Embed(
                        title="<a:_:1000859478217994410>  Success",
                        description=f"Muted {member} for `{humanfriendly.format_timespan(time.total_seconds())}`.\n**Reason:**\n> {reason}",
                        color=0x2F3136)
                    embed1.timestamp = discord.utils.utcnow()
                    await member.timeout(time, reason=f"{reason if reason else ctx.author.id}")
                    await ctx.send(embed=embed1)
                else:
                    embed2 = discord.Embed(
                        title="<a:_:1000851617182142535>  Nah Buddy...",
                        description="> Maximum mute duration is `25 days`.\n> If you want to get rid of them so bad, try using the ban command ¯\_(ツ)_/¯",
                        color=0x2F3136)
                    await ctx.send(embed=embed2)
            else:
                unmute_time = discord.utils.utcnow() + timedelta(seconds=2160000)
                embed3 = discord.Embed(
                    title="<a:_:1000859478217994410>  Success",
                    description=f"Muted {member} for `25d`.\n**Reason:**\n> {reason}",
                    color=0x2F3136)
                embed3.timestamp = discord.utils.utcnow()
                await member.timeout(unmute_time, reason=f"{reason if reason else ctx.author.id}")
                await ctx.send(embed=embed3)
        else:
            raise Moderation.HierarchyIssues("egg")


    @commands.hybrid_command(
        brief="Unmute a member",
        help="Unmute a member."
    )
    @app_commands.default_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def unmute(self, ctx: commands.Context, member: discord.Member) -> None:
        if member.is_timed_out():
            embed = discord.Embed(
                title="<a:_:1000859478217994410>  Success",
                description=f"> Unmuted {member}.",
                color=0x2F3136)
            embed.timestamp = discord.utils.utcnow()
            await member.timeout(None)
            await ctx.send(embed=embed)
        else:
            raise Moderation.PunishmentIssues("egg")

    
    @commands.hybrid_command(
        brief="Kick a member",
        help="Kick a member."
        )
    @app_commands.default_permissions(kick_members=True)
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None) -> None:
        embed1 = discord.Embed(
            title="<a:_:1000859478217994410>  Success",
            description=f"Kicked {member}.\n**Reason:**\n> {reason}",
            color=0x2F3136)
        embed1.timestamp = discord.utils.utcnow()
        if (ctx.author.top_role > member.top_role) or (member != ctx.guild.owner):
            await member.kick(reason=f"{reason if reason else ctx.author.id}")
            await ctx.send(embed=embed1)
        else:
            raise Moderation.HierarchyIssues("egg")


    @commands.hybrid_command(
        brief="Ban a member",
        help="Ban a member."
        )
    @app_commands.default_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx: commands.Context, member: Union[discord.Member, discord.User], *, reason: Optional[str] = None) -> None:
        if isinstance(member, discord.User) or (isinstance(member, discord.Member) and (ctx.author.top_role > member.top_role or member != ctx.guild.owner)):
            embed = discord.Embed(
                title="<a:_:1000859478217994410>  Success",
                description = f"Banned {member}.\n**Reason:**\n> {reason}",
                colour=0x2F3136)
            embed.timestamp = discord.utils.utcnow()
            await ctx.guild.ban(member, reason=f"{reason if reason else ctx.author.id}")
            await ctx.send(embed=embed)
        else:
            raise Moderation.HierarchyIssues("egg")


    @commands.hybrid_command(
        brief="Unban a member",
        help="Unban a member."
        )
    @app_commands.default_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, ctx: commands.Context, member: Union[discord.User, discord.Member], *, reason: Optional[str] = None) -> None:
        embed1 = discord.Embed(
            title="<a:_:1000859478217994410>  Success",
            description=f"Unbanned {member}.\n**Reason:**\n> {reason}",
            color=0x2F3136)
        embed1.timestamp = discord.utils.utcnow()
        await ctx.guild.unban(member, reason=f"{reason if reason else ctx.author.id}")
        await ctx.send(embed=embed1)


    @commands.hybrid_command(
        brief="Enable or disable slowmode on a channel",
        help="Enable or disable slowmode on a channel."
        )
    @app_commands.default_permissions(manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def slowmode(self, ctx: commands.Context, time: DurationCoverter, *, reason: Optional[str] = None) -> None:
        if time:
            if time.total_seconds() <= 21600:
                embed1 = discord.Embed(
                    title="<a:_:1000859478217994410>  Success",
                    description=f"Slowmode of `{humanfriendly.format_timespan(time.total_seconds())}` has been started in <#{ctx.channel.id}>.\n**Reason:**\n> {reason}",
                    color=0x2F3136)
                embed1.timestamp = discord.utils.utcnow()
                await ctx.channel.edit(slowmode_delay=time.total_seconds(), reason=f"{reason if reason else ctx.author.id}")
                await ctx.send(embed=embed1)
            else:
                embed2 = discord.Embed(
                    title="<a:_:1000851617182142535>  Nah Buddy...",
                    description="> Maximum slowmode duration is `6 hours`.\n> If you want people rattling on, try using the mute command ¯\_(ツ)_/¯",
                    color=0x2F3136)
                await ctx.send(embed=embed2)
        else:
            embed3 = discord.Embed(
                title="<a:_:1000859478217994410>  Success",
                description=f"Slowmode has been terminated.\n**Reason:**\n> {reason}",
                color=0x2F3136)
            embed3.timestamp = discord.utils.utcnow()
            await ctx.channel.edit(slowmode_delay=0, reason=f"{reason if reason else ctx.author.id}")
            await ctx.send(embed=embed3)


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~BETA TEST~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @commands.hybrid_command(
        brief="Warn a member",
        help="Warn a member."
        )
    @app_commands.default_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None) -> None:
        if (member == ctx.author or member == ctx.guild.owner or member == self.bot.user) or (ctx.author.top_role < member.top_role):
            raise Moderation.HierarchyIssues("egg")
        else:
            await self.bot.warn_db.warn_entry(ctx.guild.id, member.id, reason, ctx.message.created_at.timestamp())
            embed1 = discord.Embed(
                title="<a:_:1000859478217994410>  Success",
                description=f"{ctx.author.name} has warned {member.name}.\n**Reason:**\n> {reason}",
                color=0x2F3136)
            embed1.timestamp = discord.utils.utcnow()
            await ctx.send(embed=embed1)
            data = await self.bot.warn_db.warn_log(ctx.guild.id, member.id)
            count = len(data[3])
            embed2 = discord.Embed(
                title=f"Warned by {ctx.author.name} in {ctx.guild.name}",
                color=0x2F3136,
                timestamp=discord.utils.utcnow())
            embed2.add_field(name="Reason", value=reason, inline=False)
            embed2.add_field(name=f"Total warn(s) -> [{count}]", value="Warns reset per 2 months. More than 3 warns per 2 months can have serious consequences.", inline=False)
            embed2.set_thumbnail(url=ctx.author.display_avatar)
            try:
                await member.send(embed=embed2)
            except discord.HTTPException:
                pass


    @commands.hybrid_command(
        brief="Get warnings for a member",
        help="Get warnings for a member."
        )
    @app_commands.default_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def warns(self, ctx: commands.Context, member: discord.Member) -> None:
        data = await self.bot.warn_db.warn_log(ctx.guild.id, member.id)
        if not data or not data[3]:
            embed3 = discord.Embed(
                title=":mag:  Hmm...",
                description=f"> It seems the member has a clean record.",
                color=0x2F3136)
            return await ctx.send(embed=embed3)
        embed = discord.Embed(
            title=f"{member.name}'s Misdeeds",
            description=f"Total Warns: `{len(data[2])}`",
            color=0x2F3136)
        embed.set_thumbnail(url=member.display_avatar)
        for i in range(len(data[2])):
            timestamp = datetime.fromtimestamp(data[3][i])
            reason = data[2][i]
            embed.add_field(name=f"On {discord.utils.format_dt(timestamp, style='D')}", value=f"Reason: {reason}\nWarn ID: `{data[3][i]}`", inline=False)
        await ctx.send(embed=embed)


    @commands.hybrid_command(
        brief="Clear a single warning from a member",
        help="Clear a single warning from a member.",
        aliases=["dw", "rw", "removewarn"]
        )
    @app_commands.default_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def deletewarn(self, ctx: commands.Context, member: discord.Member, warn_id: float) -> None:
        data = await self.bot.warn_db.warn_log(ctx.guild.id, member.id)
        if not data:
            embed3 = discord.Embed(
                title=":mag:  Hmm...",
                description=f"> It seems the member has a clean record.",
                color=0x2F3136)
            return await ctx.send(embed=embed3)
        if data[3] and warn_id in data[3]:
            index = data[3].index(warn_id)
            embed1 = discord.Embed(
                title="<a:_:1000859478217994410>  Success",
                description=f"> Deleted warn entry.",
                color=0x2F3136)
            embed1.timestamp = discord.utils.utcnow()
            await self.bot.warn_db.remove_warn(ctx.guild.id, member.id, index)
            return await ctx.send(embed=embed1)
        else:
            embed2= discord.Embed(
                title="<a:_:1000851617182142535>  Error!",
                description="> No warn entry corresponding user found.",
                color=0x2F3136)
            return await ctx.send(embed=embed2)


    @tasks.loop(hours=24)
    async def clean_warns(self) -> None:
        data = await self.bot.warn_db.exec_fetchall("SELECT * FROM warnlogs")
        for raw in data:
            if not raw[3]:
                await self.bot.warn_db.exec_write_query("DELETE FROM warnlogs WHERE guild_id = $1 AND member_id = $2", (raw[0], raw[1],))
                continue
            for time in raw[3]:
                diff = datetime.now() - datetime.fromtimestamp(time)
                clear_after = 5260000 - round(diff.total_seconds())
                clear_at = datetime.now() + timedelta(seconds=clear_after)
                if datetime.now() >= clear_at:
                    index = raw[3].index(time)
                    if len(raw[3]) > 1:
                        await self.bot.warn_db.exec_write_query("DELETE FROM warnlogs WHERE guild_id = $1 AND member_id = $2", (raw[0], raw[1],))
                    else:
                        raw[2].remove(raw[2][index])
                        raw[3].remove(raw[3][index])
                        await self.bot.warn_db.exec_write_query("UPDATE warnlogs SET warns = $1, times = $2 WHERE member_id = $3 AND guild_id = $4", (raw[2], raw[3], raw[1], raw[0],))
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~BETA TEST~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    

    # - - - - - - - - - - - - - - - Local Error Handler - - - - - - - - - - - - - - -
    @mute.error
    @unmute.error
    @kick.error
    @ban.error
    @unban.error
    @warn.error
    async def local_errors(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            ctx.error_handled = True
            error = error.original
            if isinstance(error, (discord.errors.Forbidden, Moderation.HierarchyIssues)): # Handles hierarchy issues
                embed = discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description="> That user is a mod/admin",
                    color=0x2F3136)
                await ctx.send(embed=embed)
            elif isinstance(error, (discord.errors.NotFound, Moderation.PunishmentIssues)): # Handles punishment issues
                # if (error.code == 10026): # Unknown Ban # actually fuck it cos [or (str(error) == "egg")] no work
                    embed = discord.Embed(
                        title="<a:_:1000851617182142535>  Error!",
                        description="> Not a valid previously punished member.",
                        color=0x2F3136)
                    await ctx.send(embed=embed)
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Moderation(bot))
