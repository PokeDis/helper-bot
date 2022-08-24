import asyncio
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
    launch_time: discord.utils.utcnow
    db: Database

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
        self.database_pool = await asyncpg.create_pool(
            host=os.getenv("PGHOST"),
            user=os.getenv("PGUSER"),
            database=os.getenv("PGDATABASE"),
            password=os.getenv("PGPASSWORD"),
            port=int(os.getenv("PGPORT")),
            ssl="require",
            loop=asyncio.get_event_loop(),
        )
        self.add_view(TicketCreateView())
        self.add_view(InsideTicketView())
        self.add_view(TicketCloseView())
        self.db = Database()
        await self.db.setup()
        self.launch_time = discord.utils.utcnow()
        [
            await self.load_extension(f"Helper.extensions.{file[:-3]}")
            for file in os.listdir("Helper/extensions")
            if file.endswith(".py") and not file.startswith("_")
        ]

    async def on_ready(self) -> None:
        print(f"{self.user} is ready!")

    def run(self) -> None:
        super().run(os.getenv("TOKEN"))
