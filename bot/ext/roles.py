import discord
from discord.ext import commands

import typing

from bot.database.models import Menu
from bot.core.views import RoleView

if typing.TYPE_CHECKING:
    from bot.core import PokeHelper


class SelfRoles(commands.Cog):

    """Sets up self roles for the server."""

    def __init__(self, bot: "PokeHelper") -> None:
        self.bot = bot

    @commands.group(
        name="menu",
        help="Views a role menu",
        invoke_without_command=True,
    )
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def _menu(
        self, ctx: commands.Context, message_id: int
    ) -> discord.Message:
        info = await self.bot.db.roles.get_menu(message_id)
        if info is not None:
            guild = self.bot.get_guild(info.guild_id) or await self.bot.fetch_guild(info.guild_id)
            roles = [f"{role.mention}" for role in guild.roles if role.id in info.role_ids]
            embed = discord.Embed(
                title="Role Menu",
                description=f"Roles: [{', '.join(roles)}]\n"
                            f"[Jump to message]"
                            f"(https://discord.com/channels/{info.guild_id}/{info.channel_id}/{info.message_id})",
                color=discord.Color.blue(),
            )
            return await ctx.send(embed=embed)
        return await ctx.send("Role menu not found. Please re-check the message-id.")

    @_menu.command(help="Creates a role menu")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def create(
        self, ctx: commands.Context, *, message: str
    ) -> None:
        warning = await ctx.send("**DO NOT DELETE THIS MESSAGE.\nPLEASE COPY THIS MESSAGE'S ID AND ADD ROLES AFTER THIS**")
        return await self.bot.db.roles.add_menu(Menu(warning.id, ctx.guild.id, ctx.channel.id, message))

    @_menu.command(help="Adds a role to role menu")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def add(
        self, ctx: commands.Context, message_id: int, role_ids: commands.Greedy[discord.Role]
    ) -> discord.Message:
        menu = await self.bot.db.roles.get_menu(message_id)
        if menu is not None:
            role_ids = [role.id for role in role_ids]
            await self.bot.db.roles.add_roles(menu.message_id, role_ids)
            return await ctx.send("Added roles. Please run the update command to update the menu.")
        return await ctx.send("Role menu not found. Please re-check the message-id.")

    @_menu.command(help="Removes a role from role menu")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def remove(
        self, ctx: commands.Context, message_id: int, role_ids: commands.Greedy[discord.Role]
    ) -> discord.Message:
        menu = await self.bot.db.roles.get_menu(message_id)
        if menu is not None:
            role_ids = [role.id for role in role_ids]
            await self.bot.db.roles.remove_roles(menu.message_id, role_ids)
            return await ctx.send("Removed roles. Please run the update command to update the menu.")
        return await ctx.send("Role menu not found. Please re-check the message-id.")

    @_menu.command(help="Deletes a role menu")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def delete(
        self, ctx: commands.Context, message_id: int
    ) -> discord.Message:
        menu = await self.bot.db.roles.get_menu(message_id)
        if menu is not None:
            await self.bot.db.roles.delete_menu(menu.message_id)
            channel = self.bot.get_channel(menu.channel_id) or await self.bot.fetch_channel(menu.channel_id)
            message = await channel.fetch_message(menu.message_id)
            try:
                await message.delete()
            except discord.NotFound:
                pass
            return await ctx.send("Deleted role menu.")
        return await ctx.send("Role menu not found. Please re-check the message-id.")

    @_menu.command(help="Update a role menu")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def update(
        self, ctx: commands.Context, message_id: int
    ) -> discord.Message | None:
        menu = await self.bot.db.roles.get_menu(message_id)
        if menu is not None:
            guild = self.bot.get_guild(menu.guild_id) or await self.bot.fetch_guild(menu.guild_id)
            channel = self.bot.get_channel(menu.channel_id) or await self.bot.fetch_channel(menu.channel_id)
            try:
                message = await channel.fetch_message(menu.message_id)
                roles = [role for role in guild.roles if role.id in menu.role_ids]
                embed = discord.Embed(
                    title="Role Menu",
                    description=f"React to this message to get a role.\n",
                    color=discord.Color.blue(),
                )
                for role in roles:
                    embed.add_field(name=f"{role.name}", value=f"{role.mention}", inline=False)
                embed.set_footer(text=f"Message ID: {menu.message_id} | Message: {menu.message}")
                return await message.edit(content="", embed=embed, view=RoleView.from_roles(roles))
            except discord.NotFound:
                return await ctx.send("Message not found. Please re-check the message-id.")

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")


async def setup(bot: "PokeHelper") -> None:
    await bot.add_cog(SelfRoles(bot))
