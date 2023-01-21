import typing

import discord
from discord.ext import commands

from bot.database.models import InviterData

if typing.TYPE_CHECKING:
    from bot.core.bot import PokeHelper


class InviteTracker(commands.Cog):
    def __init__(self, bot: PokeHelper) -> None:
        self.bot = bot
        self.invite_map: dict[str, int] = {}
        super().__init__()

    async def get_current_invites_map(self) -> None:

        guild = self.bot.get_guild(id := 998133764960039033) or await self.bot.fetch_guild(id)
        return {invite.code: invite.uses for invite in await guild.invites()}

    async def cog_load(self) -> None:
        self.invite_map = await self.get_current_invites_map()

    @commands.Cog.listener("on_invite_create")
    async def add_invite_code(self, invite: discord.Invite) -> None:
        data = InviterData(invite_code=invite.code, user_id=invite.inviter.id)
        # push data in the invite collection .....

    @commands.Cog.listener("on_member_join")
    async def add_invite(self, member: discord.Member) -> None:
        older_data = self.invite_map.copy()
        self.invite_map = (new_data := await self.get_current_invites_map())
        new_invite = [code for code, uses in new_data if new_data[code] != older_data[code]]
        if not new_invite:
            return
        code = new_invite[0]
        data: InviterData = object()
        # get the data from your collection using the `code` key
        data.uses += 1
        data.invited_users.append(member.id)
        # push the new data instance back into the collection with updated info
        await self.bot.dispatch(f"on_{data.uses - data.left}_invites", data.user_id)

    @commands.Cog.listener("on_member_remove")
    async def remove_invite(self, member: discord.Member) -> None:
        # find the data collection which holds member.id in invited_users
        data: InviterData = object()
        if data:
            data.invited_users.remove(member.id)
            data.left -= 1
            # push the updated data instances back into collection

    @commands.command("invites", description="Check invite info for a user.")
    async def invites(self, ctx: commands.Context, user: discord.Member = commands.Author) -> None:
        invite_data_list: list[InviterData] = []
        # fetch all InviteDatas collection which have their creator id as user.id
        if invite_data_list == []:
            await ctx.reply("User has not created any valid invite yet")
        total_invites = sum([inv.uses for inv in invite_data_list])
        left_users = sum([inv.left for inv in invite_data_list])
        embed = discord.Embed(
            color=discord.Color.random(),
            description=f"Total invites: {total_invites}\nValid invites: {total_invites-left_users}\nLeft users: {left_users}",
            title=f"{user}'s invite info",
        )
        await ctx.reply(embed=embed)

    @commands.command("inviter", description="Check who invited the user in the server.")
    async def inviter(self, ctx: commands.Context, user: discord.Member = commands.Author) -> None:
        # find the data collection which holds user.id in invited_users, None if not found
        data: InviterData | None = object()
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
