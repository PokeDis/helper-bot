import typing

import discord
from discord.ext import commands

from ..emojis import Paginator


class PageSelect(discord.ui.Select):
    __slots__: tuple[str, ...] = ("category", "selector")

    def __init__(
        self,
        options: list[discord.SelectOption],
        *,
        placeholder: str,
        view: "SelectPaginator",
    ) -> None:
        super().__init__(placeholder=placeholder, options=options, custom_id="page_select")
        self.category = placeholder
        self.selector = view

    async def callback(self, interaction: discord.Interaction) -> None:
        category = interaction.data["values"][0]
        self.category = category
        return await self.selector.set_message_to_index(interaction, 0)


class SelectPaginator(discord.ui.View):
    __slots__: tuple[str, ...] = ("ctx", "page", "items", "message", "select")
    message: discord.Message
    page: int

    def __init__(
        self,
        ctx: commands.Context | discord.Interaction,
        items: typing.Mapping[str, list[discord.Embed]],
        *,
        timeout: int = 60,
    ) -> None:
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.page = 0
        self.items = items
        self.select = PageSelect(
            options=[discord.SelectOption(label=category, value=category) for category in self.items.keys()],
            placeholder="Home",
            view=self,
        )
        self.add_item(self.select)

    async def set_message_to_index(self, inter: discord.Interaction, index: int) -> None:
        await inter.response.defer()
        self.page = index
        embed = self.items[self.select.category][self.page]
        embed.set_footer(
            text=f"Page {self.page + 1}/{len(self.items[self.select.category])}",
            icon_url=self.ctx.author.avatar.url,
        )
        await inter.edit_original_response(embed=embed, view=self.disable_items())

    def set_items(self) -> None:
        dummy = self.children.copy()
        self.clear_items()
        self.add_item(self.select)
        for item in dummy[:-1]:
            self.add_item(item)

    def disable_items(self) -> "SelectPaginator":
        for child in self.children:
            if self.page == 0 and child.custom_id in ["first", "back"]:  # type: ignore
                child.disabled = True
            elif self.page == len(self.items[self.select.category]) - 1 and child.custom_id in [  # type: ignore
                "last",
                "next",
            ]:
                child.disabled = True
            else:
                child.disabled = False
            if len(self.items[self.select.category]) == 1 and child.custom_id in [  # type: ignore
                "first",
                "back",
                "last",
                "next",
            ]:
                child.disabled = True
        return self

    async def on_timeout(self) -> None:
        try:
            for button in self.children:
                button.disabled = True
            await self.message.edit(view=self)
        except discord.errors.NotFound:
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                embed=self.ctx.bot.embeds.no_embed("You are not allowed to use this view."),
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(emoji=Paginator.FIRST, style=Paginator.STYLE, custom_id="first")
    async def fb_button(self, interaction: discord.Interaction, _button: discord.Button) -> None:
        return await self.set_message_to_index(interaction, 0)

    @discord.ui.button(emoji=Paginator.BACK, style=Paginator.STYLE, custom_id="back")
    async def back_button(self, interaction: discord.Interaction, _button: discord.Button) -> None:
        return await self.set_message_to_index(interaction, self.page - 1)

    @discord.ui.button(emoji=Paginator.STOP, style=Paginator.STYLE, custom_id="stop")
    async def stop_button(self, interaction: discord.Interaction, _button: discord.Button) -> None:
        await interaction.response.defer()
        await interaction.delete_original_response()
        return self.stop()

    @discord.ui.button(emoji=Paginator.NEXT, style=Paginator.STYLE, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, _button: discord.Button) -> None:
        return await self.set_message_to_index(interaction, self.page + 1)

    @discord.ui.button(emoji=Paginator.LAST, style=Paginator.STYLE, custom_id="last")
    async def ff_button(self, interaction: discord.Interaction, _button: discord.Button) -> None:
        return await self.set_message_to_index(interaction, len(self.items) - 1)

    async def start(self) -> None | discord.Message:
        self.set_items()
        embed = self.items[self.select.category][self.page]
        embed.set_footer(
            text=f"Page {self.page + 1}/{len(self.items[self.select.category])}",
            icon_url=self.ctx.author.avatar.url,
        )
        self.message = await self.ctx.send(embed=embed, view=self.disable_items())
        return None
