import typing

import discord
from discord.ext import commands

from bot.core.views import RoleView
from bot.database.models import Menu

if typing.TYPE_CHECKING:
    from bot.core import PokeHelper


class RoleMenu(discord.ui.View):
    def __init__(
        self,
        ctx: commands.Context,
        bot: "PokeHelper",
        container: set[int],
        embed: discord.Embed,
        *,
        added: Menu | None = None,
        timeout: float = 180.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.bot = bot
        self.container = container
        self.embed = embed
        self.added = added

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.ctx.author.id

    def prepare_embed(self) -> discord.Embed:
        self.embed.clear_fields()
        for role in self.get_roles():
            self.embed.add_field(name=role.name, value=role.mention, inline=False)
        return self.embed

    def base_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="Self Roles",
            description="Select roles to add or remove to yourself.",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Select roles to add or remove to yourself.")
        for role in self.get_roles():
            embed.add_field(name=role.name, value=role.mention, inline=False)
        return embed

    def get_roles(self) -> list[discord.Role]:
        return [self.ctx.guild.get_role(role_id) for role_id in self.container]

    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder="Pick roles from guild to add or remove", max_values=25)
    async def role_menu(self, interaction: discord.Interaction, option: discord.ui.RoleSelect) -> None:
        await interaction.response.defer()
        for role in option.values:
            if role.is_assignable():
                if role.id not in self.container:
                    self.container.add(role.id)
                else:
                    self.container.remove(role.id)
        await interaction.edit_original_response(embed=self.prepare_embed(), view=self)

    @discord.ui.button(label="Save", style=discord.ButtonStyle.green, emoji="✅")
    async def save(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        await interaction.response.defer()
        if self.added is not None:
            channel = self.bot.get_channel(self.added.channel_id) or await self.bot.fetch_channel(
                self.added.channel_id
            )
            message = await channel.fetch_message(self.added.message_id)
            await message.edit(embed=self.base_embed(), view=RoleView(role_list=self.get_roles()))
            await self.bot.db.roles.update_roles(self.added.message_id, self.container)
        else:
            embed = self.base_embed()
            message = await self.ctx.send(embed=embed, view=RoleView(role_list=self.get_roles()))
            menu = Menu(
                message_id=message.id,
                guild_id=self.ctx.guild.id,
                role_ids=self.container,
                channel_id=message.channel.id,
            )
            await self.bot.db.roles.add_menu(menu)
        await interaction.delete_original_response()
        await interaction.followup.send(
            embed=discord.Embed(description="Saved roles!", color=discord.Color.green()), ephemeral=True
        )
