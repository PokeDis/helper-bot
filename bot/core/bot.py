import datetime
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from bot.core.helper import EMOJIS, POKEMONS
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
            command_prefix=commands.when_mentioned_or("?"),
            intents=discord.Intents.all(),
            case_insensitive=True,
            owner_ids={656838010532265994, 580034015759826944, 730271192778539078},
        )

    def emoji(
        self,
        name: str,
        *,
        animated: bool = False,
        shiny: bool = False,
        string: bool = False,
    ) -> discord.Emoji | str:
        if isinstance(name, int):
            return self.get_emoji(name)
        name = name.replace("-", "").replace(" ", "").lower()
        name = (f"a:{name}" + "_sh" if shiny else f"a:{name}") if animated else f":{name}"
        read = EMOJIS.get(name, 998459023613493289)
        read_n = "<:unknown:998459023613493289>" if read == 998459023613493289 else f"<{name}:{read}>"
        return self.get_emoji(EMOJIS.get(name, 998459023613493289)) if not string else read_n

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
        await self.load_extension("jishaku")
        self.logs = self.get_channel(998285318987989063) or await self.fetch_channel(998285318987989063)
        self.add_views(
            GiveawayJoinView(self), TicketCreateView(), TicketCloseView(), InsideTicketView(), RoleView(self)
        )

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}")

    async def start(self, token: str | None = None, *, reconnect: bool = True) -> None:
        await super().start(token or os.getenv("TOKEN"), reconnect=reconnect)
