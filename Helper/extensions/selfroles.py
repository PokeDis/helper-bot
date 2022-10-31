import discord
from discord.ext import commands

from ..main import HelperBot


class RoleMenu(discord.ui.Select):
    def __init__(
        self,
        role_list: list[discord.Role]
    ) -> None:
        self.roles = role_list
        options = [
            discord.SelectOption(
                label=f"{role.name.title()}",
                value=f"{role.id}",
                emoji=role.unicode_emoji if role.unicode_emoji else "<:dustbin:989150297333043220>"
            )
            for role in self.roles
        ]
        super().__init__(
            placeholder="Select role",
            options=options
        )
    async def callback(
        self,
        interaction: discord.Interaction
    ) -> None:
        await interaction.response.defer()
        role = interaction.guild.get_role(int(self.values[0]))
        await interaction.user.add_roles(role)
        await interaction.followup.send(
            content=f"Gave you {role.name.title()} role!",
            ephemeral=True
        )


class RoleView(discord.ui.View):
    def __init__(
        self,
        role_list: list[discord.Role],
        *,
        timeout = 180,
    ) -> None:
        super().__init__(timeout=timeout)
        self.add_item(RoleMenu(role_list))


class SelfRoles(
    commands.Cog,
    description="Sets up self roles for the server.\n`<input>` are mandatory and `[input]` are optional.",
):
    def __init__(self, bot: HelperBot) -> None:
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
        info = await self.bot.db.roles_db.get_menu(message_id)
        if info:
            return await ctx.send(info)
        return await ctx.send("Role menu not found. Please re-check the message-id.")

    @_menu.command(help="Creates a role menu")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def create(
        self, ctx: commands.Context, *, message: str
    ) -> None:
        warning = await ctx.send("**DO NOT DELETE THIS MESSAGE.\nPLEASE COPY THIS MESSAGE'S ID AND ADD ROLES AFTER THIS**")
        await self.bot.db.roles_db.register_roles(message, ctx.guild.id, ctx.channel.id, warning.id)
        return None

    @_menu.command(help="Adds a role to role menu")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def add(
        self, ctx: commands.Context, message_id: int, role_ids: commands.Greedy[int]
    ) -> discord.Message:
        if await self.bot.db.roles_db.get_menu(message_id):
            await self.bot.db.roles_db.add_roles(message_id, role_ids)
            return await ctx.send("Added roles. Please run the update command to update the menu.")
        return await ctx.send("Role menu not found. Please re-check the message-id.")

    @_menu.command(help="Removes a role from role menu")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def remove(
        self, ctx: commands.Context, message_id: int, role_ids: commands.Greedy[int]
    ) -> discord.Message:
        if await self.bot.db.roles_db.get_menu(message_id):
            await self.bot.db.roles_db.remove_roles(message_id, role_ids)
            return await ctx.send("Removed roles. Please run the update command to update the menu.")
        return await ctx.send("Role menu not found. Please re-check the message-id.")

    @_menu.command(help="Deletes a role menu")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def delete(
        self, ctx: commands.Context, message_id: int
    ) -> discord.Message:
        if (data := await self.bot.db.roles_db.get_menu(message_id)):
            channel = self.bot.get_channel(data["channel_id"]) or await self.bot.fetch_channel(data["channel_id"])
            message = channel.get_partial_message(message_id)
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass
            await self.bot.db.roles_db.delete_menu(message_id)
            return await ctx.send("Role Menu deleted successfully.")
        return await ctx.send("Role menu not found. Please re-check the message-id.")

    @_menu.command(help="Update a role menu")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def update(
        self, ctx: commands.Context, message_id: int
    ) -> None:
        if (data := await self.bot.db.roles_db.get_menu(message_id)):
            guild = self.bot.get_guild(data["guild_id"])
            try:
                channel = guild.get_channel(data["channel_id"]) or await self.bot.fetch_channel(data["channel_id"])
            except (discord.errors.NotFound, discord.HTTPException):
                await self.bot.db.roles_db.delete_menu(message_id)
                return None
            message = channel.get_partial_message(message_id)
            roles = [guild.get_role(x) for x in data["role_ids"]]
            embed = discord.Embed(color=discord.Color.blue())
            embed.set_footer(text=f'{data["menu_message"]}')
            try:
                await message.edit(content="", embed=embed, view=RoleView(roles))
                return None
            except discord.errors.NotFound:
                await self.bot.db.roles_db.delete_menu(message_id)
        await ctx.send("Role menu not found. Please re-check the message-id.")
        return None

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(SelfRoles(bot))
