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
            description="Select roles to add or remove to menu. You can select up to 25 roles.",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Select roles to add or remove to menu. You can select up to 25 roles.")
        for role_id in container:
            role = ctx.guild.get_role(role_id)
            if role is not None:
                embed.add_field(name=role.name, value=role.mention, inline=False)
        view = RoleMenu(ctx, self.bot, container, embed, added=roles if roles is not None else None)
        await ctx.send(embed=embed, view=view)

    @commands.command(help="Delete self roles menu.")
    @commands.has_permissions(manage_roles=True)
    async def delroles(self, ctx: commands.Context, menu_id: int) -> None | discord.Message:
        menu = await self.bot.db.roles.get_menu(menu_id)
        if menu is None:
            return await ctx.send("Menu not found.")
        await self.bot.db.roles.delete_menu(menu_id)
        channel = self.bot.get_channel(menu.channel_id) or await self.bot.fetch_channel(menu.channel_id)
        message = await channel.fetch_message(menu.message_id)
        await message.delete()
        await ctx.send("Menu deleted.")

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")


async def setup(bot: "PokeHelper") -> None:
    await bot.add_cog(SelfRoles(bot))
