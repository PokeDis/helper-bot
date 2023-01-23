import typing

import discord
from discord.ext import commands

from bot.database.models import InviterData

if typing.TYPE_CHECKING:
    from bot.core.bot import PokeHelper


class InviteTracker(commands.Cog):
    """Track your invite progress"""

    INVITE_STREAK_GAP: int = 5

    def __init__(self, bot: "PokeHelper") -> None:
        self.bot = bot
        self.invite_map: dict[str, int] = {}

    async def get_current_invites_map(self) -> dict[str, int]:
        guild = self.bot.get_guild(id_ := 998133764960039033) or await self.bot.fetch_guild(id_)
        return {invite.code: invite.uses for invite in await guild.invites()}

    async def cog_load(self) -> None:
        self.invite_map = await self.get_current_invites_map()

    @commands.Cog.listener("on_invite_create")
    async def add_invite_code(self, invite: discord.Invite) -> None:
        data = InviterData(invite_code=invite.code, user_id=invite.inviter.id)
        await self.bot.db.invites.add_invite(data)

    @commands.Cog.listener("on_member_join")
    async def add_invite(self, member: discord.Member) -> None:
        older_data = self.invite_map.copy()
        self.invite_map = (new_data := await self.get_current_invites_map())
        new_invite = [code for code, uses in new_data.items() if new_data[code] != older_data.get(code)]
        if not new_invite:
            return
        data: InviterData | None = None
        inviter = await self.bot.db.invites.get_by_invite(member.id)
        if inviter:
            _rejoin = True
        else:
            code = new_invite[0]
            data: InviterData = await self.bot.db.invites.get_invite(code)
            data.uses += 1
            data.invited_users.append(member.id)
            await self.bot.db.invites.update_invite(code, data)
            _rejoin = False
            invite_data_list = await self.bot.db.invites.get_all_invites(data.user_id)
            total_invites = sum([inv.uses for inv in invite_data_list])
            left_users = sum([inv.left for inv in invite_data_list])
            if (invites := total_invites - left_users) % self.INVITE_STREAK_GAP == 0:
                self.bot.dispatch("invite_streak", invites // self.INVITE_STREAK_GAP, data.user_id)
        invitee = inviter or data
        await self.bot.get_partial_messageable(1012229238415433768).send(
            embed=discord.Embed(
                description=f"`{member}` ({member.id}) was invited by <@{invitee.user_id}> ({invitee.user_id}) (rejoin: {_rejoin})"
            )
        )

    @commands.Cog.listener()
    async def on_invite_streak(self, _streak: int, user_id: int) -> None:
        await self.bot.db.add_redeem(user_id)

    @commands.Cog.listener("on_member_remove")
    async def remove_invite(self, member: discord.Member) -> None:
        data: InviterData = await self.bot.db.invites.get_by_invite(member.id)
        if data:
            data.left += 1
            await self.bot.db.invites.update_invite(data.invite_code, data)

    @commands.command("invites", help="Check invite info for a user.")
    async def invites(self, ctx: commands.Context, user: discord.Member = commands.Author) -> None:
        invite_data_list: list[InviterData] = await self.bot.db.invites.get_all_invites(user.id)
        if not invite_data_list:
            await ctx.reply("User has not created any valid invite yet")
            return
        total_invites = sum([inv.uses for inv in invite_data_list])
        left_users = sum([inv.left for inv in invite_data_list])
        embed = discord.Embed(
            color=discord.Color.random(),
            description=f"Total invites: {total_invites}\nValid invites: {total_invites-left_users}\nLeft users: {left_users}",
            title=f"{user}'s invite info",
        )
        await ctx.reply(embed=embed)

    @commands.command("inviter", help="Check who invited the user in the server.")
    async def inviter(self, ctx: commands.Context, user: discord.Member = commands.Author) -> None:
        data: InviterData | None = await self.bot.db.invites.get_by_invite(user.id)
        if data:
            await ctx.reply(
                embed=discord.Embed(
                    color=discord.Color.random(), description=f"{user} was invited by <@{data.user_id}>"
                )
            )
        else:
            await ctx.reply(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description=f"We were unable to figure out how {user} joined the server.",
                )
            )


async def setup(bot: "PokeHelper") -> None:
    await bot.add_cog(InviteTracker(bot))
