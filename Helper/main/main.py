import datetime
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from Helper.extensions.giveaway import GiveawayJoinView
from Helper.extensions.ticket import (InsideTicketView, TicketCloseView,
                                      TicketCreateView)

from ..database import Database


class HelperBot(commands.Bot):

    load_dotenv()
    launch_time: datetime.datetime
    db: Database
    logs: discord.TextChannel
    LOGCHANNEL: int = 998285318987989063
    TOKEN: str = os.getenv("TOKEN")

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.reactions = True
        super().__init__(
            command_prefix=commands.when_mentioned_or("?"),
            intents=intents,
            case_insensitive=True,
        )

    async def setup_hook(self) -> None:
        self.add_view(TicketCreateView())
        self.add_view(InsideTicketView())
        self.add_view(TicketCloseView())
        self.add_view(GiveawayJoinView(self))
        self.db = Database()
        self.launch_time = discord.utils.utcnow()
        self.logs = self.get_channel(self.LOGCHANNEL) or await self.fetch_channel(
            self.LOGCHANNEL
        )
        [
            await self.load_extension(f"Helper.extensions.{file[:-3]}")
            for file in os.listdir("Helper/extensions")
            if file.endswith(".py") and not file.startswith("_")
        ]

    async def on_ready(self) -> None:
        print(f"{self.user} is ready!")

    def begin(self) -> None:
        self.run(self.TOKEN)
