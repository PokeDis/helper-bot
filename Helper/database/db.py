from __future__ import annotations

from datetime import datetime
from discord.ext import commands

from .postgre import DatabaseModel

__all__ = (
    "TagDB",
    "WarnDB",
)


class TagDB(DatabaseModel):
    async def setup(self, bot: commands.Bot) -> None:
        self.database_pool = bot.database_pool
        await self.exec_write_query(
            "CREATE TABLE IF NOT EXISTS tags(user_id BIGINT, name VARCHAR(50), content VARCHAR(4000))"
        )

    async def add_tag(self, user_id: int, tag: str, content: str) -> None:
        await self.exec_write_query(
            "INSERT INTO tags(user_id, name, content) VALUES($1, $2, $3)",
            (
                user_id,
                tag,
                content,
            ),
        )

    async def delete_tag(self, name: str) -> None:
        await self.exec_write_query("DELETE FROM tags WHERE name = $1", (name,))

    async def get_tag(self, tag: str) -> tuple:   
        data = await self.exec_fetchone("SELECT * FROM tags WHERE name = $1", (tag,))
        return data

    async def update_tag(self, name: str, new: str) -> None:
        await self.exec_write_query(
            "UPDATE tags SET content = $1 WHERE name = $2",
            (
                new,
                name,
            ),
        )
        

class WarnDB(DatabaseModel):
    async def setup(self, bot: commands.Bot) -> None:
        self.database_pool = bot.database_pool
        await self.exec_write_query(
            "CREATE TABLE IF NOT EXISTS warnlogs (guild_id BIGINT, member_id BIGINT, warns TEXT[], times DECIMAL[])"
        )

    async def warn_log(self, guild_id: int, member_id: int) -> list:
        data = await self.exec_fetchone(
            "SELECT * FROM warnlogs WHERE guild_id = $1 AND member_id = $2", (guild_id, member_id,)
            )
        return data or []

    async def remove_warn(self, guild_id: int, member_id: int, index: int) -> None:
        data = await self.warn_log(guild_id, member_id)
        if len(data[2]) >= 1:
            data[2].remove(data[2][index])
            data[3].remove(data[3][index])
            await self.exec_write_query(
                "UPDATE warnlogs SET warns = $1, times = $2 WHERE guild_id = $3 AND member_id = $4", (data[2], data[3], guild_id, member_id,)
            )
        else:
            await self.exec_write_query(
                "DELETE FROM warnlogs WHERE guild_id = $1 AND member_id = $2", (guild_id, member_id,)
            )

    async def warn_entry(self, guild_id: int, member_id: int, reason: str, time: datetime.timestamp) -> None:
        data = await self.warn_log(guild_id, member_id)
        if not data:
            await self.exec_write_query(
                "INSERT INTO warnlogs (guild_id, member_id, warns, times) VALUES ($1, $2, $3, $4)", (guild_id, member_id, [reason], [time],)
            )
            return
        warns = data[2]
        times = data[3]
        if not warns:
            warns = [reason]
            times = [time]
        else:
            warns.append(reason)
            times.append(time)
        await self.exec_write_query(
            "UPDATE warnlogs SET times = $1, warns = $2 WHERE guild_id = $3 AND member_id = $4", (times, warns, guild_id, member_id,)
        )
