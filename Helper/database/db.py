from __future__ import annotations

from datetime import datetime

from discord.ext import commands

from .postgre import DatabaseModel

__all__ = (
    "TagDB",
    "WarnDB",
    "RepDB",
    "RepCooldownDB"
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
            "SELECT * FROM warnlogs WHERE guild_id = $1 AND member_id = $2",
            (
                guild_id,
                member_id,
            ),
        )
        return data or []

    async def remove_warn(self, guild_id: int, member_id: int, index: int) -> None:
        data = await self.warn_log(guild_id, member_id)
        if len(data[2]) >= 1:
            data[2].remove(data[2][index])
            data[3].remove(data[3][index])
            await self.exec_write_query(
                "UPDATE warnlogs SET warns = $1, times = $2 WHERE guild_id = $3 AND member_id = $4",
                (
                    data[2],
                    data[3],
                    guild_id,
                    member_id,
                ),
            )
        else:
            await self.exec_write_query(
                "DELETE FROM warnlogs WHERE guild_id = $1 AND member_id = $2",
                (
                    guild_id,
                    member_id,
                ),
            )

    async def warn_entry(
        self, guild_id: int, member_id: int, reason: str, time: datetime.timestamp
    ) -> None:
        data = await self.warn_log(guild_id, member_id)
        if not data:
            await self.exec_write_query(
                "INSERT INTO warnlogs (guild_id, member_id, warns, times) VALUES ($1, $2, $3, $4)",
                (
                    guild_id,
                    member_id,
                    [reason],
                    [time],
                ),
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
            "UPDATE warnlogs SET times = $1, warns = $2 WHERE guild_id = $3 AND member_id = $4",
            (
                times,
                warns,
                guild_id,
                member_id,
            ),
        )


class RepDB(DatabaseModel):
    async def setup(self, bot: commands.Bot) -> None:
        self.database_pool = bot.database_pool
        await self.exec_write_query(
            "CREATE TABLE IF NOT EXISTS reputation(user_id BIGINT PRIMARY KEY, rep INT)"
        )

    async def add_user(self, user_id: int, rep: int) -> None:
        await self.exec_write_query(
            "INSERT INTO reputation(user_id, rep) VALUES($1, $2)",
            (
                user_id,
                rep,
            ),
        )

    async def clear_rep(self, user_id: int) -> None:
        await self.exec_write_query(
            "DELETE FROM reputation WHERE user_id = $1", (user_id,)
        )

    async def get_rep(self, user_id: int) -> tuple:
        data = await self.exec_fetchone(
            "SELECT * FROM reputation WHERE user_id = $1", (user_id,)
        )
        return data or []

    async def update_rep(self, user_id: int, new_rep: int) -> None:
        await self.exec_write_query(
            "UPDATE reputation SET rep = $1 WHERE user_id = $2",
            (
                new_rep,
                user_id,
            ),
        )


class RepCooldownDB(DatabaseModel):
    async def setup(self, bot: commands.Bot) -> None:
        self.database_pool = bot.database_pool
        await self.exec_write_query(
            "CREATE TABLE IF NOT EXISTS repcooldown (member_a_id BIGINT, member_b_ids BIGINT[], times DECIMAL[])"
        )

    async def cd_log(self, member_id: int) -> list:
        data = await self.exec_fetchone(
            "SELECT * FROM repcooldown WHERE member_a_id = $1", (member_id,)
        )
        return data or []

    async def cd_entry(
        self, member_id: int, member_b_id: int, time: datetime.timestamp
    ) -> None:
        data = await self.cd_log(member_id)
        if not data:
            await self.exec_write_query(
                "INSERT INTO repcooldown (member_a_id, member_b_ids, times) VALUES ($1, $2, $3)",
                (
                    member_id,
                    [member_b_id],
                    [time],
                ),
            )
            return
        member_b_ids = data[1]
        times = data[2]
        if not member_b_ids:
            member_b_ids = [member_b_id]
            times = [time]
        else:
            member_b_ids.append(member_b_id)
            times.append(time)
        await self.exec_write_query(
            "UPDATE repcooldown SET times = $1, member_b_ids = $2 WHERE member_a_id = $3",
            (
                times,
                member_b_ids,
                member_id,
            ),
        )
