import typing

import discord
from discord.ext import commands

from bot.core.views import RoleMenu

if typing.TYPE_CHECKING:
    from bot.core import PokeHelper


class SelfRoles(commands.Cog):

    """Sets up self roles for the server."""

    def __init__(self, bot: "PokeHelper") -> None:
        self.bot = bot

    @commands.command(help="Sets up self roles for the server.")
    @commands.has_permissions(manage_roles=True)
    async def selfroles(self, ctx: commands.Context, message_id: int | None = None) -> None:
        roles = await self.bot.db.roles.get_menu(message_id or 0)
        container = roles.role_ids if roles is not None else set()
        embed = discord.Embed(
            title="Self Roles",
            description="<:bullet:1014583675184230511> *Select roles to add or remove to menu."
            " You can select up to 25 roles.*",
            color=discord.Color.blurple(),
        )
        for role_id in container:
            role = ctx.guild.get_role(role_id)
            if role is not None:
                embed.add_field(name=role.name, value=role.mention, inline=False)
        view = RoleMenu(ctx, self.bot, container, embed, added=roles if roles is not None else None)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(help="Delete self roles menu.")
    @commands.has_permissions(manage_roles=True)
    async def delroles(self, ctx: commands.Context, menu_id: int) -> None | discord.Message:
        menu = await self.bot.db.roles.get_menu(menu_id)
        if menu is None:
            return await ctx.send(
                embed=discord.Embed(title="<:no:1001136828738453514> Menu does not exist.", color=discord.Color.red())
            )
        await self.bot.db.roles.delete_menu(menu_id)
        channel = self.bot.get_channel(menu.channel_id) or await self.bot.fetch_channel(menu.channel_id)
        message = await channel.fetch_message(menu.message_id)
        await message.delete()
        await ctx.send(
            embed=discord.Embed(
                title="<:tick:1001136782508826777> Menu deleted.",
                color=discord.Color.green(),
            )
        )

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")


async def setup(bot: "PokeHelper") -> None:
    await bot.add_cog(SelfRoles(bot))
