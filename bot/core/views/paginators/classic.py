import discord
from discord.ext import commands

from ..emojis import Paginator


class ClassicPaginator(discord.ui.View):
    __slots__: tuple[str, ...] = ("ctx", "page", "items", "message")
    message: discord.Message
    page: int

    def __init__(
        self,
        ctx: commands.Context | discord.Interaction,
        items: list[discord.Embed],
        *,
        timeout: int = 60,
    ) -> None:
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.page = 0
        self.items = items

    async def set_message_to_index(self, inter: discord.Interaction, index: int) -> None:
        await inter.response.defer()
        self.page = index
        embed = self.items[self.page]
        embed.set_footer(
            text=f"Page {self.page + 1}/{len(self.items)}",
            icon_url=self.ctx.author.display_avatar,
        )
        await inter.edit_original_response(embed=embed, view=self.disable_items())

    def disable_items(self) -> "ClassicPaginator":
        for child in self.children:
            if self.page == 0 and child.custom_id in ["first", "back"]:  # type: ignore
                child.disabled = True
            elif self.page == len(self.items) - 1 and child.custom_id in ["last", "next"]:  # type: ignore
                child.disabled = True
            else:
                child.disabled = False
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
                embed=discord.Embed(title="You are not allowed to use this view.", color=discord.Color.red()),
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
        if len(self.items) == 1:
            return await self.ctx.send(embed=self.items[0])
        embed = self.items[self.page]
        embed.set_footer(
            text=f"Page {self.page + 1}/{len(self.items)}",
            icon_url=self.ctx.author.display_avatar,
        )
        self.message = await self.ctx.send(embed=embed, view=self.disable_items())
        return None
