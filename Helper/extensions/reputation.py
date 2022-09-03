from datetime import datetime, timedelta
from typing import Optional

import discord
import humanfriendly
from discord.ext import commands, tasks

from ..main import HelperBot


class Reputation(
    commands.Cog,
    description="Reputation may be used to determine trust factor.\n`<input>` are mandatory and `[input]` are optional.",
):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot

    @staticmethod
    async def can_manage_rep(ctx: commands.Context, member_id: int) -> bool:
        if (ctx.author.id != member_id) or ctx.author.guild_permissions.manage_guild:
            return True

        else:
            embed = discord.Embed(
                description=f"<:no:1001136828738453514> You cant 'manage' rep.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return False

    @commands.group(help="Check your/others rep")
    @commands.guild_only()
    async def rep(
        self, ctx: commands.Context, member: Optional[discord.Member]
    ) -> Optional[discord.Message]:
        if ctx.invoked_subcommand is None:
            member = member or ctx.author
            embed = discord.Embed(color=discord.Color.blue())
            embed.set_author(name=f"{member.name}", icon_url=member.display_avatar)

            if not (rep_data := await self.bot.db.rep_db.get_rep(member.id)):
                embed.add_field(name="Reputation", value="0")
                return await ctx.send(embed=embed)

            embed.add_field(name="Reputation", value=f"{rep_data[1]}")
            return await ctx.send(embed=embed)
        return None

    @rep.command(help="Give +1 rep to a member")
    @commands.cooldown(1, 120, commands.BucketType.user)
    @commands.guild_only()
    async def give(
        self, ctx: commands.Context, member: discord.Member
    ) -> Optional[discord.Message]:
        embed = discord.Embed(
            description=f"<:tick:1001136782508826777> Gave +1 rep to {member.mention}.",
            color=discord.Color.green(),
        )

        data = await self.bot.db.rep_cd_db.cd_log(ctx.author.id)
        if len(data) and member.id in data[1]:
            index = data[1].index(member.id)
            time = data[2][index]
            diff = datetime.now() - datetime.fromtimestamp(float(time))
            cooldown = 7200 - round(diff.total_seconds())
            error = commands.CommandOnCooldown(
                retry_after=cooldown,
                cooldown=discord.app_commands.Cooldown(rate=cooldown, per=1),
                type=commands.BucketType.user,
            )
            error.reason = f"You can rep {member.mention} again after {humanfriendly.format_timespan(error.retry_after)}."
            raise error

        if not await self.can_manage_rep(ctx, member.id):
            return None

        data = await self.bot.db.rep_db.get_rep(member.id)
        if not data:
            await self.bot.db.rep_db.add_user(member.id, 1)
            await self.bot.db.rep_cd_db.cd_entry(
                ctx.author.id, member.id, ctx.message.created_at.timestamp()
            )
            return await ctx.send(embed=embed)

        s = await self.bot.db.rep_db.get_rep(member.id)
        new_rep = s[1] + 1
        await self.bot.db.rep_db.update_rep(member.id, new_rep)
        await self.bot.db.rep_cd_db.cd_entry(
            ctx.author.id, member.id, ctx.message.created_at.timestamp()
        )
        return await ctx.send(embed=embed)

    @rep.command(
        help="Remove certain amount of rep from a member"
    )
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def take(
        self, ctx: commands.Context, member: discord.Member, amount: int
    ) -> Optional[discord.Message]:
        embed1 = discord.Embed(
            description=f"<:tick:1001136782508826777> Removed {amount} rep from {member.mention}.",
            color=discord.Color.green(),
        )
        embed2 = discord.Embed(
            description=f"<:no:1001136828738453514> {member.mention}'s rep is already 0.",
            color=discord.Color.red(),
        )
        embed3 = discord.Embed(
            description=f"<:no:1001136828738453514> Cannot remove rep more than what they have.",
            color=discord.Color.red(),
        )
        data = await self.bot.db.rep_db.get_rep(member.id)
        if not data:
            return await ctx.send(embed=embed2)
        s = await self.bot.db.rep_db.get_rep(member.id)
        if s[1] == 0:
            return await ctx.send(embed=embed2)
        if s[1] - amount < 0:
            return await ctx.send(embed=embed3)
        new_rep = s[1] - amount
        await self.bot.db.rep_db.update_rep(member.id, new_rep)
        return await ctx.send(embed=embed1)

    @rep.command(help="Reset a members rep to 0")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def clear(
        self, ctx: commands.Context, member: discord.Member
    ) -> Optional[discord.Message]:
        embed = discord.Embed(
            description=f"<:tick:1001136782508826777> {member.mention}'s rep reset to 0.",
            color=discord.Color.green(),
        )
        data = await self.bot.db.rep_db.get_rep(member.id)
        if not data:
            return await ctx.send(embed=embed)
        await self.bot.db.rep_db.clear_rep(member.id)
        return await ctx.send(embed=embed)

    @tasks.loop(minutes=10)
    async def clean_rep_cd(self) -> None:
        data = await self.bot.db.rep_cd_db.get_all()
        for raw in data:
            if not raw[2]:
                await self.bot.db.rep_cd_db.remove_cd(raw[0])
                continue
            for time in raw[2]:
                diff = datetime.now() - datetime.fromtimestamp(float(time))
                clear_after = 6600 - round(diff.total_seconds())
                clear_at = datetime.now() + timedelta(seconds=clear_after)
                if datetime.now() >= clear_at:
                    index = raw[2].index(time)
                    if len(raw[2]) > 1:
                        await self.bot.db.rep_cd_db.remove_cd(raw[0])
                    else:
                        raw[1].remove(raw[1][index])
                        raw[2].remove(raw[2][index])
                        await self.bot.db.rep_cd_db.update_cd(*raw)

    @clean_rep_cd.before_loop
    async def before_clean_rep_cd(self):
        await self.bot.wait_until_ready()
        print("🔃 Started Clean Reputation Cooldown loop.")

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")
        self.clean_rep_cd.start()


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Reputation(bot))
