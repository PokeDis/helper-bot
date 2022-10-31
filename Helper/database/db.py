from __future__ import annotations

import os
import typing
from datetime import datetime

from motor import motor_asyncio

__all__: tuple[str, ...] = (
    "TagDB",
    "WarnDB",
    "RepDB",
    "RepCooldownDB",
    "GiveawayDB",
    "ReminderDB",
    "CollectionDB",
    "RolesDB"
)


class MongoDb:

    def __init__(self) -> None:
        self.client = motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URL"))


class TagDB(MongoDb):

    def __init__(self) -> None:
        super().__init__()
        self.collection = self.client["users"]["tags"]

    async def add_tag(self, user_id: int, tag: str, content: str) -> None:
        await self.collection.insert_one({"user_id": user_id, "tag": tag, "content": content})

    async def delete_tag(self, name: str) -> None:
        await self.collection.delete_one({"tag": name})

    async def get_tag(self, tag: str) -> dict[str, typing.Any]:
        data = await self.collection.find_one({"tag": tag})
        return data

    async def update_tag(self, name: str, new: str) -> None:
        await self.collection.update_one({"tag": name}, {"$set": {"content": new}})

    async def get_all(self) -> list[dict[str, typing.Any]]:
        data = await self.collection.find().to_list(None)
        return [record["tag"] for record in data]

    async def get_from_user(self, user: int) -> list[dict[str, typing.Any]]:
        data = await self.collection.find({"user_id": user}).to_list(None)
        return [record["tag"] for record in data]


class WarnDB(MongoDb):

    def __init__(self) -> None:
        super().__init__()
        self.collection = self.client["users"]["warns"]

    async def warn_log(
        self, guild_id: int, member_id: int
    ) -> dict[str, typing.Any]:
        data = await self.collection.find_one({"guild_id": guild_id, "member_id": member_id})
        return data

    async def remove_warn(self, guild_id: int, member_id: int, index: int) -> None:
        data = await self.warn_log(guild_id, member_id)
        if len(data["warns"]) > 1:
            data["warns"].pop([index])
            data["times"].pop([index])
            await self.collection.update_one({"guild_id": guild_id, "member_id": member_id}, {"$set": {"warns": data["warns"], "times": data["times"]}})
        else:
            await self.collection.delete_one({"guild_id": guild_id, "member_id": member_id})

    async def warn_entry(
        self, guild_id: int, member_id: int, reason: str, time: float
    ) -> None:
        data = await self.warn_log(guild_id, member_id)
        if not data:
            await self.collection.insert_one({"guild_id": guild_id, "member_id": member_id, "warns": [reason], "times": [time]})
            return
        warns = data["warns"] + [reason] if data["warns"] else [reason]
        times = data["times"] + [time] if data["times"] else [time]
        await self.collection.update_one({"guild_id": guild_id, "member_id": member_id}, {"$set": {"warns": warns, "times": times}})

    async def get_all(self) -> list[dict[str, typing.Any]]:
        data = await self.collection.find().to_list(None)
        return data

    async def update_warn(self, data: list) -> None:
        args = (*data,)
        await self.collection.update_one({"guild_id": args[0], "member_id": args[1]}, {"$set": {"warns": args[2], "times": args[3]}})


class RepDB(MongoDb):

    def __init__(self) -> None:
        super().__init__()
        self.collection = self.client["users"]["reputation"]

    async def add_user(self, user_id: int, rep: int) -> None:
        await self.collection.insert_one({"user_id": user_id, "rep": rep})

    async def clear_rep(self, user_id: int) -> None:
        await self.collection.delete_one({"user_id": user_id})

    async def get_rep(self, user_id: int) -> dict[str, typing.Any]:
        data = await self.collection.find_one({"user_id": user_id})
        return data

    async def update_rep(self, user_id: int, new_rep: int) -> None:
        await self.collection.update_one({"user_id": user_id}, {"$set": {"rep": new_rep}})

    async def get_leaderboard(self, user: int) -> tuple[list[dict[str, typing.Any]], str]:
        data = await self.collection.find().sort("rep", -1).to_list(None)
        rank = "Unranked"
        for i, record in enumerate(data):
            if record["user_id"] == user:
                rank = f"{i + 1}"
                break
        return data, rank


class RepCooldownDB(MongoDb):

    def __init__(self) -> None:
        super().__init__()
        self.collection = self.client["users"]["repcooldown"]

    async def cd_log(self, member_id: int) -> dict[str, typing.Any]:
        data = await self.collection.find_one({"member_a_id": member_id})
        return data

    async def remove_cd(self, member_id: int) -> None:
        await self.collection.delete_one({"member_a_id": member_id})

    async def update_cd(self, member_b_id: int, time: float, member_a_id: int) -> None:
        await self.collection.update_one({"member_a_id": member_a_id}, {"$push": {"member_b_ids": member_b_id, "times": time}})

    async def get_all(self) -> list[dict[str, typing.Any]]:
        data = await self.collection.find().to_list(None)
        return data

    async def cd_entry(self, member_id: int, member_b_id: int, time: float) -> None:
        if not (data := await self.cd_log(member_id)):
            await self.collection.insert_one({"member_a_id": member_id, "member_b_ids": [member_b_id], "times": [time]})
            return
        member_b_ids = data["member_b_ids"] + [member_b_id] if data["member_b_ids"] else [member_b_id]
        times = data["times"] + [time] if data["times"] else [time]
        await self.collection.update_one({"member_a_id": member_id}, {"$set": {"member_b_ids": member_b_ids, "times": times}})


class GiveawayDB(MongoDb):

    def __init__(self) -> None:
        super().__init__()
        self.collection = self.client["servers"]["giveaways"]

    async def giveaway_start(
        self,
        message_id: int,
        winners: int,
        prize: str,
        end_date: float,
        host: int,
        channel: int,
    ) -> None:
        await self.collection.insert_one(
            {
                "message_id": message_id,
                "participants": [],
                "winners": winners,
                "prize": prize,
                "end_time": end_date,
                "host": host,
                "channel": channel,
                "ended": False,
            }
        )

    async def get_giveaway(self, message_id: int) -> dict[str, typing.Any]:
        data = await self.collection.find_one({"message_id": message_id})
        return data

    async def giveaway_click(self, message_id: int, user_id: int) -> bool:
        data = await self.get_giveaway(message_id)
        check, _ = (False, data["participants"].remove(user_id)) if user_id in data["participants"] else (True, data["participants"].append(user_id))
        await self.collection.update_one({"message_id": message_id}, {"$set": {"participants": data["participants"]}})
        return check

    async def all_records(self) -> list[dict[str, typing.Any]]:
        data = await self.collection.find().to_list(None)
        return data

    async def end_giveaway(self, message_id: int) -> None:
        await self.collection.delete_one({"message_id": message_id})

    async def by_time(self, time: float) -> list[dict[str, typing.Any]]:
        time = datetime.fromtimestamp(time)
        data = await self.all_records()
        timeout = []
        for record in data:
            in_time = datetime.fromtimestamp(record["end_time"])
            if (in_time - time).total_seconds() <= 0 and not record["ended"]:
                timeout.append(record)
        return timeout

    async def update_bool(self, message_id: int) -> None:
        await self.collection.update_one({"message_id": message_id}, {"$set": {"ended": True}})


class ReminderDB(MongoDb):

    def __init__(self) -> None:
        super().__init__()
        self.collection = self.client["users"]["reminders"]

    async def add_reminder(self, data: list) -> None:
        await self.collection.insert_one({"message_id": data[0], "time": data[1], "channel_id": data[2], "author": data[3], "message": data[4]})

    async def get_all(self) -> list[dict[str, typing.Any]]:
        data = await self.collection.find().to_list(None)
        return data

    async def get_one(self, message_id: int) -> list[dict[str, typing.Any]]:
        data = await self.collection.find_one({"message_id": message_id})
        return data

    async def get_by_time(self, time: float) -> list[dict[str, typing.Any]]:
        time = datetime.fromtimestamp(time)
        data = await self.get_all()
        timeout = []
        for i in data:
            in_time = datetime.fromtimestamp(i["time"])
            if (in_time - time).total_seconds() < 0:
                timeout.append(i)
        return timeout

    async def get_by_user(self, user_id: int) -> list[dict[str, typing.Any]]:
        data = await self.collection.find({"author": user_id}).to_list(None)
        return data

    async def remove_reminder(self, _id: int) -> None:
        await self.collection.delete_one({"message_id": _id})


class CollectionDB(MongoDb):

    def __init__(self) -> None:
        super().__init__()
        self.collection = self.client["servers"]["collections"]

    async def show(self, member_id: int) -> dict[str, typing.Any]:
        data = await self.collection.find_one({"member_id": member_id})
        return data

    async def remove(self, member_id: int, pokemon: str) -> None:
        data = await self.show(member_id)
        if len(data["pokemon"]) > 1:
            data["pokemon"].remove(pokemon)
            await self.collection.update_one({"member_id": member_id}, {"$set": {"pokemon": data["pokemon"]}})
        else:
            await self.collection.delete_one({"member_id": member_id})

    async def add(self, member_id: int, pokemon: str) -> None:
        data = await self.show(member_id)
        if not data:
            await self.collection.insert_one({"member_id": member_id, "pokemon": [pokemon]})
            return
        mons = data["pokemon"] + [pokemon] if data["pokemon"] else [pokemon]
        await self.collection.update_one({"member_id": member_id}, {"$set": {"pokemon": mons}})

    async def delete_record(self, member_id: int) -> None:
        await self.collection.delete_one({"member_id": member_id})

    async def get_by_pokemon(self, pokemon: str) -> list[dict[str, typing.Any]]:
        data = await self.collection.find({"pokemon": pokemon}).to_list(None)
        collector_ids = [i["member_id"] for i in data if pokemon in i["pokemon"]]
        return collector_ids


class RolesDB(MongoDb):

    def __init__(self) -> None:
        super().__init__()
        self.collection = self.client["servers"]["selfroles"]

    async def register_roles(
        self,
        menu_message: str,
        guild_id: int,
        channel_id: int,
        message_id: int,
    ) -> None:
        await self.collection.insert_one(
            {
                "menu_message": menu_message,
                "guild_id": guild_id,
                "channel_id": channel_id,
                "message_id": message_id,
                "role_ids": [],
            }
        )

    async def get_menu(self, message_id: int) -> None:
        data = await self.collection.find_one({"message_id": message_id})
        return data if data else None

    async def add_roles(self, message_id: int, role_ids: list[int]) -> None:
        data = await self.get_menu(message_id)
        data["role_ids"].extend(role_ids)
        await self.collection.update_one({"message_id": message_id}, {"$set": {"role_ids": list(dict.fromkeys(data["role_ids"]))}})

    async def remove_roles(self, message_id: int, role_ids: list[int]) -> None:
        data = await self.get_menu(message_id)
        updated_list = [i for i in data["role_ids"] if i not in role_ids]
        await self.collection.update_one({"message_id": message_id}, {"$set": {"role_ids": updated_list}})

    async def delete_menu(self, message_id: int) -> None:
        await self.collection.delete_one({"message_id": message_id})
