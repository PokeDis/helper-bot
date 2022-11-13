import datetime
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from bot.core.helper import POKEMONS
from bot.core.views import GiveawayJoinView, InsideTicketView, RoleView, TicketCloseView, TicketCreateView
from bot.database import Mongo

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(logging.StreamHandler())


class PokeHelper(commands.Bot):

    __slots__: tuple[str, ...] = (
        "uptime",
        "db",
        "logs",
    )
    db: Mongo
    uptime: datetime.datetime
    logs: discord.TextChannel
    pokemons: list[str] = POKEMONS

    def __init__(self) -> None:
        load_dotenv()
        super().__init__(
            command_prefix=commands.when_mentioned_or("?"), intents=discord.Intents.all(), case_insensitive=True
        )

    def add_views(self, *views: discord.ui.View) -> None:
        for view in views:
            self.add_view(view)

    async def setup_hook(self) -> None:
        self.uptime = discord.utils.utcnow()
        self.db = Mongo()
        [
            await self.load_extension(f"bot.ext.{file[:-3]}")
            for file in os.listdir("bot/ext")
            if file.endswith(".py") and not file.startswith("_")
        ]
        self.logs = self.get_channel(998285318987989063) or await self.fetch_channel(998285318987989063)
        self.add_views(GiveawayJoinView(self), TicketCreateView(), TicketCloseView(), InsideTicketView(), RoleView())

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}")

    async def start(self, token: str | None = None, *, reconnect: bool = True) -> None:
        await super().start(token or os.getenv("TOKEN"), reconnect=reconnect)
