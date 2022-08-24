"""Base database model."""
from __future__ import annotations

import typing

import asyncpg

__all__: tuple[str, ...] = ("DatabaseModel",)


class DatabaseModel:  # model commands class for database
    """General methods for database."""

    database_pool: asyncpg.pool.Pool

    async def exec_write_query(
        self, query: str, data: typing.Optional[tuple] = None
    ) -> None:
        """
        Execute a write query.
        :param query:
        :type query: str
        :param data:
        :type data: typing.Optional[tuple]
        """
        if data:
            await self.database_pool.execute(query, *data)
            return

        await self.database_pool.execute(query)

    async def exec_fetchone(
        self, query: str, data: typing.Optional[tuple] = None
    ) -> typing.Optional[asyncpg.Record]:
        """
        Execute a fetchone query.
        :param query:
        :type query: str
        :param data:
        :type data: typing.Optional[tuple]
        :return:
        :rtype: typing.Optional[asyncpg.Record]
        """
        result: typing.Optional[asyncpg.Record] = await self.database_pool.fetchrow(
            query, *data
        )
        return result

    async def exec_fetchall(
        self, query: str, data: typing.Optional[tuple[typing.Any, ...]] = None
    ) -> list[asyncpg.Record]:
        """
        Execute a fetchall query.
        :param query:
        :type query: str
        :type data: typing.Optional[tuple]
        :return:
        :rtype: list[asyncpg.Record]
        """
        args: typing.Union[tuple, list] = data or []
        results: list[asyncpg.Record] = await self.database_pool.fetch(query, *args)
        return results
