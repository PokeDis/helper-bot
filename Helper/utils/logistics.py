import discord

from discord.ext import commands
from datetime import timedelta

from reactionmenu import ViewButton, ViewMenu
from custom_durations import Duration


class Support():
    @staticmethod
    async def paginate(pages: list, context: commands.Context):
        menu = ViewMenu(context, menu_type=ViewMenu.TypeEmbed)
        menu.add_pages(pages)
        back = ViewButton(
            style=discord.ButtonStyle.gray,
            emoji="<:_:998564013212434462>",
            custom_id=ViewButton.ID_PREVIOUS_PAGE,
        )
        next = ViewButton(
            style=discord.ButtonStyle.gray,
            emoji="<:_:998563574689583144>",
            custom_id=ViewButton.ID_NEXT_PAGE,
        )
        stop = ViewButton(
            style=discord.ButtonStyle.gray,
            emoji="<:_:998563829493534750>",
            custom_id=ViewButton.ID_END_SESSION,
        )
        ff = ViewButton(
            style=discord.ButtonStyle.gray,
            emoji="<:_:998563714338914344>",
            custom_id=ViewButton.ID_GO_TO_LAST_PAGE,
        )
        fb = ViewButton(
            style=discord.ButtonStyle.gray,
            emoji="<:_:998563905993461851>",
            custom_id=ViewButton.ID_GO_TO_FIRST_PAGE,
        )
        menu.add_button(fb)
        menu.add_button(back)
        menu.add_button(stop)
        menu.add_button(next)
        menu.add_button(ff)
        menu.show_page_director = False
        return await menu.start()

class DurationCoverter(commands.Converter):
    async def convert(self, ctx: commands.Context, args: str) -> timedelta:
        args = args.strip()
        time = Duration(args)
        return timedelta(seconds=time.to_seconds())
