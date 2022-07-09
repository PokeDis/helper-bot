from __future__ import annotations

import typing as t

import aiomysql  # type: ignore

from .base import DatabaseModel


class TagsDatabase(DatabaseModel):
    database_pool: aiomysql.Pool

    async def setup(self, bot) -> None:

        self.database_pool = bot.database_pool

        await self.exec_write_query(
            """
            CREATE TABLE IF NOT EXISTS tags
            (
                guild_id BIGINT,
                user_id BIGINT,
                name VARCHAR(50),
                content VARCHAR(4000),
                uses BIGINT
            )
            """
        )

    async def add_tag(
        self, guild_id: int, user_id: int, tag: str, content: str
    ) -> None:

        await self.exec_write_query(
            """
            INSERT INTO tags
            VALUES ( %s, %s, %s, %s, 0 )
            """,
            (
                guild_id,
                user_id,
                tag,
                content,
            ),
        )

    async def delete_tag(self, guild_id: int, name: str) -> None:

        await self.exec_write_query(
            """
            DELETE FROM tags
            WHERE guild_id = %s and name = %s
            """,
            (guild_id, name),
        )

    async def get_tag(self, guild_id: int, tag: str) -> tuple:
        data = await self.exec_fetchone(
            """
            SELECT * FROM tags
            WHERE guild_id = %s and name = %s
            """,
            (guild_id, tag),
        )
        return data

    async def update_tag(self, guild_id: int, name: str, new: str) -> None:
        await self.exec_write_query(
            """
            UPDATE tags
            SET content = %s
            WHERE guild_id = %s and name = %s
            """,
            (new, guild_id, name),
        )
