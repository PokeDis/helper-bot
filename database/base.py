from __future__ import annotations

import typing as t

import aiomysql  # type: ignore

__all__: t.Tuple[str, ...] = ("DatabaseModel",)


class DatabaseModel:
    database_pool: aiomysql.Pool

    async def exec_write_query(
        self, query: str, data: t.Tuple[t.Any, ...] | None = None
    ) -> None:
        async with self.database_pool.acquire() as conn:  # conn: aiomysql.Connection
            async with conn.cursor() as cursor:  # cursor: aiomysql.Cursor
                await cursor.execute(query, data)
            await conn.commit()

    async def exec_fetchone(
        self, query: str, data: t.Tuple[t.Any, ...] | None = None
    ) -> tuple[t.Any, ...]:

        async with self.database_pool.acquire() as conn:  # conn: aiomysql.Connection
            async with conn.cursor() as cursor:  # cursor: aiomysql.Cursor
                await cursor.execute(query, data)
            return await cursor.fetchone()

    async def exec_fetchmany(
        self, num: int, query: str, data: t.Tuple[t.Any, ...] | None = None
    ) -> list[tuple[t.Any, ...]]:

        async with self.database_pool.acquire() as conn:  # conn: aiomysql.Connection
            async with conn.cursor() as cursor:  # cursor: aiomysql.Cursor
                await cursor.execute(query, data)
            return await cursor.fetchmany(num)

    async def exec_fetchall(
        self, query: str, data: t.Tuple[t.Any, ...] | None = None
    ) -> list[tuple[t.Any, ...]]:

        async with self.database_pool.acquire() as conn:  # conn: aiomysql.Connection
            async with conn.cursor() as cursor:  # cursor: aiomysql.Cursor
                await cursor.execute(query, data)
            return await cursor.fetchall()
