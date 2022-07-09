import asyncio
import os

import aiomysql
import dotenv
import hikari
import lightbulb

dotenv.load_dotenv()
from database.tags_db import TagsDatabase


class Bot(lightbulb.BotApp):
    def __init__(self) -> None:

        super().__init__(
            os.getenv("TOKEN"),
            prefix="!",
            intents=hikari.Intents.ALL,
            case_insensitive_prefix_commands=True,
            help_slash_command=True,
        )
        self.tags_db = TagsDatabase()
        self.event_manager.subscribe(hikari.StartingEvent, self.started)
        self.load_extensions_from("plugins")

    async def started(self, _: hikari.StartingEvent) -> None:
        self.database_pool: aiomysql.Pool = await aiomysql.create_pool(
            host=os.getenv("MYSQLHOST"),
            user=os.getenv("MYSQLUSER"),
            db=os.getenv("MYSQLDATABASE"),
            password=os.getenv("MYSQLPASSWORD"),
            port=int(os.getenv("MYSQLPORT") or "0000"),
            loop=asyncio.get_event_loop(),
            autocommit=False,
        )
        await self.tags_db.setup(self)
