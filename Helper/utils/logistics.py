from datetime import timedelta

import discord
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu

from custom_durations import Duration


class Support:
    @staticmethod
    async def paginate(pages: list, context: commands.Context):
        if len(pages) == 1:
            await context.send(embed=pages[0])
            return
        menu = ViewMenu(context, menu_type=ViewMenu.TypeEmbed)
        menu.add_pages(pages)
        back = ViewButton(
            style=discord.ButtonStyle.gray,
            emoji="<:ArrowLeft:989134685068202024>",
            custom_id=ViewButton.ID_PREVIOUS_PAGE,
        )
        turn = ViewButton(
            style=discord.ButtonStyle.gray,
            emoji="<:rightArrow:989136803284004874>",
            custom_id=ViewButton.ID_NEXT_PAGE,
        )
        stop = ViewButton(
            style=discord.ButtonStyle.gray,
            emoji="<:dustbin:989150297333043220>",
            custom_id=ViewButton.ID_END_SESSION,
        )
        ff = ViewButton(
            style=discord.ButtonStyle.gray,
            emoji="<:DoubleArrowRight:989134892384256011>",
            custom_id=ViewButton.ID_GO_TO_LAST_PAGE,
        )
        fb = ViewButton(
            style=discord.ButtonStyle.gray,
            emoji="<:DoubleArrowLeft:989134953142956152>",
            custom_id=ViewButton.ID_GO_TO_FIRST_PAGE,
        )
        menu.add_button(fb)
        menu.add_button(back)
        menu.add_button(stop)
        menu.add_button(turn)
        menu.add_button(ff)
        menu.show_page_director = False
        return await menu.start()


class DurationCoverter(commands.Converter):
    async def convert(self, ctx: commands.Context, args: str) -> timedelta:
        args = args.strip()
        time = Duration(args)
        return timedelta(seconds=time.to_seconds())
