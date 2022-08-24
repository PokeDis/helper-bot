import asyncio
import os

import asyncpg
import discord
from discord.ext import commands
from dotenv import load_dotenv

from Helper.extensions.ticket import TicketCreateView, InsideTicketView, TicketCloseView

from ..database import RepDB, TagDB, WarnDB, RepCooldownDB

load_dotenv()


class HelperBot(commands.Bot):
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
        self.warn_db = WarnDB()
        self.tag_db = TagDB()
        self.rep_db = RepDB()
        self.rep_cd_db = RepCooldownDB()
        await self.tag_db.setup(self)
        await self.warn_db.setup(self)
        await self.rep_db.setup(self)
        await self.rep_cd_db.setup(self)
        self.launch_time = discord.utils.utcnow()
        [
            await self.load_extension(f"Helper.extensions.{file[:-3]}")
            for file in os.listdir("Helper/extensions")
            if file.endswith(".py") and not file.startswith("_")
        ]

    def run(self) -> None:
        super().run(os.getenv("TOKEN"))
