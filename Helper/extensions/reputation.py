import discord
import random
import humanfriendly

from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from typing import Optional

from ..main import HelperBot


async def can_manage_rep(ctx: commands.Context, member_id: int) -> bool:
    if (ctx.author.id != member_id) or (ctx.author.guild_permissions.manage_guild):
        return True

    else:
        embed = discord.Embed(
            title="<a:_:1000851617182142535>  Nu Uh!",
            description = f"> You cant mess with your own rep.",
            colour=0x2F3136
        )
        await ctx.send(embed=embed)
        return False


class Reputation(commands.Cog, description="Reputation may be used to determine trust factor.\n`<input>` are mandatory and `[input]` are optional."):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot
        self.clean_rep_cd.start()


    @commands.hybrid_command(
        brief="Check your/others rep",
        help="Check your/others rep."
        )
    @commands.guild_only()
    async def rep(self, ctx: commands.Context, member: Optional[discord.Member]) -> None:
        member = member or ctx.author
        embed = discord.Embed(
            colour=0x2F3136
        )
        embed.set_author(name=str(member.name), icon_url=f"{member.display_avatar}")

        if not (rep_data := await self.bot.rep_db.get_rep(member.id)):
            embed.add_field(name="Reputation", value="0")
            return await ctx.send(embed=embed)

        embed.add_field(name="Reputation", value=f"{rep_data[1]}")
        await ctx.send(embed=embed)


    @commands.hybrid_command(
        brief="Give +1 rep to a member",
        help="Give +1 rep to a member."
        )
    @commands.cooldown(1, 120, commands.BucketType.user)
    @commands.guild_only()
    async def giverep(self, ctx: commands.Context, member: discord.Member) -> None:
        embed = discord.Embed(
            title="<a:_:1000859478217994410>  Success",
            description = f"> Gave +1 rep to {member.mention}.",
            colour=0x2F3136
        )

        data = await self.bot.rep_cd_db.cd_log(ctx.author.id)
        if len(data) and member.id in data[1]:
            index = data[1].index(member.id)
            time = data[2][index]
            diff = datetime.now() - datetime.fromtimestamp(time)
            cooldown = 7200 - round(diff.total_seconds())
            cooldown_embed = discord.Embed(
                title=random.choice(
                    [
                        "<a:_:1000851617182142535>  Slow down!",
                        "<a:_:1000851617182142535>  You're going a little too fast bud...",
                        "<a:_:1000851617182142535>  Hold your horses!",
                        "<a:_:1000851617182142535>  Woah now, slow it down...",
                        "<a:_:1000851617182142535>  Take a breather...",
                        "<a:_:1000851617182142535>  NEGATORY.",
                    ]
                ),
                description=f"You can rep {member.mention} again in **{humanfriendly.format_timespan(cooldown)}**.",
                color=0x2F3136,
            )
            return await ctx.send(embed=cooldown_embed)

        if not await can_manage_rep(ctx, member.id):
            return

        data = await self.bot.rep_db.get_rep(member.id)
        if not data:
            await self.bot.rep_db.add_user(member.id, 1)
            await self.bot.rep_cd_db.cd_entry(ctx.author.id, member.id, ctx.message.created_at.timestamp())
            return await ctx.send(embed=embed)

        s = await self.bot.rep_db.get_rep(member.id)
        new_rep = s[1] + 1
        await self.bot.rep_db.update_rep(member.id, new_rep)
        await self.bot.rep_cd_db.cd_entry(ctx.author.id, member.id, ctx.message.created_at.timestamp())
        await ctx.send(embed=embed)


    @commands.hybrid_command(
        brief="Reset a members rep to 0",
        help="Reset a members rep to 0."
        )
    @app_commands.default_permissions(manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def repclear(self, ctx: commands.Context, member: discord.Member) -> None:
        embed = discord.Embed(
            title="<a:_:1000859478217994410>  Success",
            description = f"> {member.mention} rep reset to 0.",
            colour=0x2F3136
        )
        data = await self.bot.rep_db.get_rep(member.id)
        if not data:
            return await ctx.send(embed=embed)
        await self.bot.rep_db.clear_rep(member.id)
        await ctx.send(embed=embed)


    @commands.hybrid_command(
        brief="Remove -1 rep from a member",
        help="Remove -1 rep from a member."
        )
    @app_commands.default_permissions(manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def takerep(self, ctx: commands.Context, member: discord.Member) -> None:
        embed1 = discord.Embed(
            title="<a:_:1000859478217994410>  Success",
            description = f"> Removed -1 rep from {member.mention}.",
            colour=0x2F3136
        )
        embed2 = discord.Embed(
            title="<a:_:1000851617182142535>  L",
            description = f"> {member.mention}'s rep is already 0.",
            colour=0x2F3136
        )
        data = await self.bot.rep_db.get_rep(member.id)
        if not data:
            return await ctx.send(embed=embed2)
        s = await self.bot.rep_db.get_rep(member.id)
        if s[1] == 0:
            return await ctx.send(embed=embed2)
        new_rep = s[1] - 1
        await self.bot.rep_db.update_rep(member.id, new_rep)
        await ctx.send(embed=embed1)


    @tasks.loop(minutes=10)
    async def clean_rep_cd(self) -> None:
        data = await self.bot.rep_cd_db.exec_fetchall("SELECT * FROM repcooldown")
        for raw in data:
            if not raw[2]:
                await self.bot.rep_cd_db.exec_write_query("DELETE FROM repcooldown WHERE member_a_id = $1", (raw[0],))
                continue
            for time in raw[2]:
                diff = datetime.now() - datetime.fromtimestamp(time)
                clear_after = 6600 - round(diff.total_seconds())
                clear_at = datetime.now() + timedelta(seconds=clear_after)
                if datetime.now() >= clear_at:
                    index = raw[2].index(time)
                    if len(raw[2]) > 1:
                        await self.bot.rep_cd_db.exec_write_query("DELETE FROM repcooldown WHERE member_a_id = $1", (raw[0],))
                    else:
                        raw[1].remove(raw[1][index])
                        raw[2].remove(raw[2][index])
                        await self.bot.rep_cd_db.exec_write_query("UPDATE repcooldown SET member_b_ids = $1, times = $2 WHERE member_a_id = $3", (raw[1], raw[2], raw[0],))


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Reputation(bot))
