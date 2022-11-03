import discord


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
            options=options,
            custom_id="persistent:role_menu"
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
    role_list: list[discord.Role]

    def __init__(
        self,
        *,
        timeout=180,
    ) -> None:
        super().__init__(timeout=timeout)

    @classmethod
    def from_roles(cls, role_list: list[discord.Role]) -> "RoleView":
        self = cls()
        self.role_list = role_list
        self.add_item(RoleMenu(role_list))
        return self
