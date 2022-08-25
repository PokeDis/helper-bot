import asyncio
import datetime
import os

import asyncpg
import discord
from discord.ext import commands
from dotenv import load_dotenv

from Helper.extensions.ticket import (InsideTicketView, TicketCloseView,
                                      TicketCreateView)

from ..database import Database

load_dotenv()


class HelperBot(commands.Bot):

    database_pool: asyncpg.pool.Pool
    launch_time: datetime.datetime
    db: Database
    logs: discord.TextChannel
    LOGCHANNEL: int = 998285318987989063

    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or("?"),
            intents=discord.Intents.all(),
            case_insensitive=True,
        )

    async def setup_hook(self) -> None:
        self.add_view(TicketCreateView())
        self.add_view(InsideTicketView())
        self.add_view(TicketCloseView())
        self.db = Database()
        await self.db.setup()
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

    def run(self) -> None:
        super().run(os.getenv("TOKEN"))
