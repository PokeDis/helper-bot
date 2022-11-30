import typing

import discord

if typing.TYPE_CHECKING:
    from bot.core import PokeHelper


class RoleMenu(discord.ui.Select):
    def __init__(self, bot: "PokeHelper", role_list: list[discord.Role]) -> None:
        self.roles = role_list
        options = [
            discord.SelectOption(
                label=f"{role.name.title()}",
                value=f"{role.id}",
                emoji=role.unicode_emoji if role.unicode_emoji else bot.emoji(role.name),
            )
            for role in self.roles
        ]
        super().__init__(placeholder="Select role", options=options, custom_id="persistent:role_menu")

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        role = interaction.guild.get_role(int(self.values[0]))
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.followup.send(f"Removed {role.mention} from you.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.followup.send(content=f"Gave you {role.mention} role!", ephemeral=True)


class RoleView(discord.ui.View):
    role_list: list[discord.Role]

    def __init__(
        self,
        bot: "PokeHelper",
        *,
        timeout: float | None = None,
        role_list: list[discord.Role] | None = None,
    ) -> None:
        super().__init__(timeout=timeout)
        self.role_list = role_list or []
        self.add_item(RoleMenu(bot, self.role_list))
