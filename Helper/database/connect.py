from __future__ import annotations

import asyncio
import os

import asyncpg

from .db import *

__all__: tuple[str, ...] = ("Database",)


class Database:

    database_pool: asyncpg.pool.Pool

    def __init__(self):
        self.warn_db = WarnDB()
        self.tag_db = TagDB()
        self.rep_db = RepDB()
        self.rep_cd_db = RepCooldownDB()

    async def setup(self) -> None:
        self.database_pool = await asyncpg.create_pool(
            host=os.getenv("PGHOST"),
            user=os.getenv("PGUSER"),
            database=os.getenv("PGDATABASE"),
            password=os.getenv("PGPASSWORD"),
            port=os.getenv("PGPORT"),
            ssl="require",
            loop=asyncio.get_event_loop(),
        )
        await self.tag_db.setup(self)
        await self.warn_db.setup(self)
        await self.rep_db.setup(self)
        await self.rep_cd_db.setup(self)
