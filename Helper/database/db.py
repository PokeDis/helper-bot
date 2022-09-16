from __future__ import annotations

import typing
from datetime import datetime
from typing import TYPE_CHECKING

import asyncpg

from .postgre import DatabaseModel

if TYPE_CHECKING:
    from .connect import Database

__all__: tuple[str, ...] = (
    "TagDB",
    "WarnDB",
    "RepDB",
    "RepCooldownDB",
    "GiveawayDB",
    "ReminderDB",
    "CollectionDB",
)


class TagDB(DatabaseModel):
    async def setup(self, con: Database) -> None:
        self.database_pool = con.database_pool
        await self.exec_write_query(
            "CREATE TABLE IF NOT EXISTS tags(user_id BIGINT, name VARCHAR(50), content VARCHAR(2000))"
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

    async def get_tag(self, tag: str) -> asyncpg.Record | None:
        data = await self.exec_fetchone("SELECT * FROM tags WHERE name = $1", (tag,))
        return data or []

    async def update_tag(self, name: str, new: str) -> None:
        await self.exec_write_query(
            "UPDATE tags SET content = $1 WHERE name = $2",
            (
                new,
                name,
            ),
        )

    async def get_all(self) -> list[asyncpg.Record]:
        data = await self.exec_fetchall("SELECT name FROM tags")
        return [record[0] for record in data]

    async def get_from_user(self, user: int) -> list[asyncpg.Record]:
        data = await self.exec_fetchall(
            "SELECT name FROM tags WHERE user_id = $1", (user,)
        )
        return [record[0] for record in data]


class WarnDB(DatabaseModel):
    async def setup(self, con: Database) -> None:
        self.database_pool = con.database_pool
        await self.exec_write_query(
            "CREATE TABLE IF NOT EXISTS warnlogs (guild_id BIGINT, member_id BIGINT, warns VARCHAR(250)[], times DECIMAL[])"
        )

    async def warn_log(
        self, guild_id: int, member_id: int
    ) -> typing.Optional[asyncpg.Record]:
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
        if len(data[2]) > 1:
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
        self, guild_id: int, member_id: int, reason: str, time: float
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

    async def get_all(self) -> list[asyncpg.Record]:
        data = await self.exec_fetchall("SELECT * FROM warnlogs")
        return data

    async def update_warn(self, data: list) -> None:
        args = (*data,)
        await self.exec_write_query(
            "UPDATE warnlogs SET warns = $3, times = $4 WHERE member_id = $2 AND guild_id = $1",
            (args,),
        )


class RepDB(DatabaseModel):
    async def setup(self, con: Database) -> None:
        self.database_pool = con.database_pool
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

    async def get_rep(self, user_id: int) -> asyncpg.Record | None:
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

    async def get_leaderboard(self, user: int) -> tuple[list[asyncpg.Record], str]:
        data = await self.exec_fetchall("SELECT * FROM reputation ORDER BY rep DESC")
        rank = "Unranked"
        for i, record in enumerate(data):
            if record[0] == user:
                rank = f"{i + 1}"
                break
        return data, rank


class RepCooldownDB(DatabaseModel):
    async def setup(self, con: Database) -> None:
        self.database_pool = con.database_pool
        await self.exec_write_query(
            "CREATE TABLE IF NOT EXISTS repcooldown (member_a_id BIGINT, member_b_ids BIGINT[], times DECIMAL[])"
        )

    async def cd_log(self, member_id: int) -> asyncpg.Record | None:
        data = await self.exec_fetchone(
            "SELECT * FROM repcooldown WHERE member_a_id = $1", (member_id,)
        )
        return data or []

    async def remove_cd(self, member_id: int) -> None:
        await self.exec_write_query(
            "DELETE FROM repcooldown WHERE member_a_id = $1", (member_id,)
        )

    async def update_cd(self, member_b_id: int, time: float, member_a_id: int) -> None:
        await self.exec_write_query(
            "UPDATE repcooldown SET member_b_ids = $2, times = $3 WHERE member_a_id = $1",
            (
                member_b_id,
                time,
                member_a_id,
            ),
        )

    async def get_all(self) -> list[asyncpg.Record]:
        data = await self.exec_fetchall("SELECT * FROM repcooldown")
        return data or []

    async def cd_entry(self, member_id: int, member_b_id: int, time: float) -> None:
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


class GiveawayDB(DatabaseModel):
    async def setup(self, con: Database) -> None:
        self.database_pool = con.database_pool
        await self.exec_write_query(
            "CREATE TABLE IF NOT EXISTS giveaway (message_id BIGINT, participants BIGINT[], winners INT, prize VARCHAR(250), end_date FLOAT, host BIGINT, channel BIGINT, end_check BOOLEAN DEFAULT FALSE)"
        )

    async def giveaway_start(
        self,
        message_id: int,
        winners: int,
        prize: str,
        end_date: float,
        host: int,
        channel: int,
    ) -> None:
        await self.exec_write_query(
            "INSERT INTO giveaway(message_id, participants, winners, prize, end_date, host, channel) VALUES($1, $2, $3, $4, $5, $6, $7)",
            (
                message_id,
                [],
                winners,
                prize,
                end_date,
                host,
                channel,
            ),
        )

    async def get_giveaway(self, message_id: int) -> list[asyncpg.Record]:
        data = await self.exec_fetchone(
            "SELECT * FROM giveaway WHERE message_id = $1", (message_id,)
        )
        if data:
            return [*data]
        return []

    async def giveaway_click(self, message_id: int, user_id: int) -> bool:
        data = await self.get_giveaway(message_id)
        check = False
        if user_id in data[1]:
            data[1].remove(user_id)
        else:
            data[1].append(user_id)
            check = not check
        await self.exec_write_query(
            "UPDATE giveaway SET participants = $1 WHERE message_id = $2",
            (
                data[1],
                message_id,
            ),
        )
        return check

    async def all_records(self) -> list[asyncpg.Record]:
        data = await self.exec_fetchall("SELECT * FROM giveaway")
        return data

    async def end_giveaway(self, message_id: int) -> None:
        await self.exec_write_query(
            "DELETE FROM giveaway WHERE message_id = $1",
            (message_id,),
        )

    async def by_time(self, time: float) -> list[asyncpg.Record]:
        time = datetime.fromtimestamp(time)
        data = await self.all_records()
        timeout = []
        for record in data:
            in_time = datetime.fromtimestamp(record[4])
            left = in_time - time
            if left.total_seconds() <= 0 and not record[7]:
                timeout.append(record)
        return timeout

    async def update_bool(self, message_id: int) -> None:
        await self.exec_write_query(
            "UPDATE giveaway SET end_check = TRUE WHERE message_id = $1",
            (message_id,),
        )


class ReminderDB(DatabaseModel):
    async def setup(self, con: Database) -> None:
        self.database_pool = con.database_pool
        await self.exec_write_query(
            "CREATE TABLE IF NOT EXISTS reminder (message_id BIGINT, time FLOAT, channel_id BIGINT, author BIGINT, message VARCHAR(1000))"
        )

    async def add_reminder(self, data: list) -> None:
        await self.exec_write_query(
            "INSERT INTO reminder (message_id, time, channel_id, author, message) VALUES ($1, $2, $3, $4, $5)",
            (*data,),
        )

    async def get_all(self) -> list[asyncpg.Record]:
        data = await self.exec_fetchall("SELECT * FROM reminder")
        return data

    async def get_one(self, message_id: int) -> list[asyncpg.Record]:
        data = await self.exec_fetchone(
            "SELECT * FROM reminder WHERE message_id = $1", (message_id,)
        )
        if data:
            return [*data]
        return []

    async def get_by_time(self, time: float) -> list[asyncpg.Record]:
        time = datetime.fromtimestamp(time)
        data = await self.get_all()
        timeout = []
        for i in data:
            in_time = datetime.fromtimestamp(i[1])
            left = in_time - time
            if left.total_seconds() < 0:
                timeout.append(i)
        return timeout

    async def get_by_user(self, user_id: int) -> list[asyncpg.Record]:
        data = await self.exec_fetchall(
            "SELECT * FROM reminder WHERE author = $1", (user_id,)
        )
        return data or []

    async def remove_reminder(self, _id: int) -> None:
        await self.exec_write_query(
            "DELETE FROM reminder WHERE message_id = $1", (_id,)
        )


class CollectionDB(DatabaseModel):
    async def setup(self, con: Database) -> None:
        self.database_pool = con.database_pool
        await self.exec_write_query(
            "CREATE TABLE IF NOT EXISTS collection (member_id BIGINT, pokemon VARCHAR(50)[])"
        )

    async def show(self, member_id: int) -> typing.Optional[asyncpg.Record]:
        data = await self.exec_fetchone(
            "SELECT * FROM collection WHERE member_id = $1",
            (member_id,),
        )
        return data or []

    async def remove(self, member_id: int, pokemon: str) -> None:
        data = await self.show(member_id)
        if len(data[1]) > 1:
            data[1].remove(pokemon)
            await self.exec_write_query(
                "UPDATE collection SET pokemon = $1 WHERE member_id = $2",
                (
                    data[1],
                    member_id,
                ),
            )
        else:
            await self.exec_write_query(
                "DELETE FROM collection WHERE member_id = $1",
                (member_id,),
            )

    async def add(self, member_id: int, pokemon: str) -> None:
        data = await self.show(member_id)
        if not data:
            await self.exec_write_query(
                "INSERT INTO collection (member_id, pokemon) VALUES ($1, $2)",
                (
                    member_id,
                    [pokemon],
                ),
            )
            return
        mons = data[1]
        if not mons:
            mons = [pokemon]
        else:
            mons.append(pokemon)
        await self.exec_write_query(
            "UPDATE collection SET pokemon = $1 WHERE member_id = $2",
            (
                mons,
                member_id,
            ),
        )

    async def delete_record(self, member_id: int) -> None:
        await self.exec_write_query(
            "DELETE FROM collection WHERE message_id = $1", (member_id,)
        )

    async def get_by_pokemon(self, pokemon: str) -> list[asyncpg.Record]:
        data = await self.exec_fetchall("SELECT * FROM collection")
        collector_ids = []
        for record in data:
            if pokemon in record[1]:
                collector_ids.append(record[0])
        return collector_ids
