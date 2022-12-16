import datetime
import typing

from .models import Collection, Giveaway, Menu, Reminder, Tag, UserRep, WarnLog

if typing.TYPE_CHECKING:
    from .database import Mongo


__all__: tuple[str, ...] = (
    "TagDB",
    "WarnDB",
    "RepDB",
    "CollectionDB",
    "GiveawayDB",
    "ReminderDB",
    "RolesDB",
)


class TagDB:

    __slots__: tuple[str, ...] = (
        "client",
        "collection",
    )

    def __init__(self, client: "Mongo") -> None:
        self.client = client
        self.collection = client["data"]["tags"]
        self.client.tags = self

    async def add_tag(self, data: Tag) -> None:
        await self.collection.insert_one(data.get_payload())

    async def delete_tag(self, name: str) -> None:
        await self.collection.delete_one({"title": name})

    async def get_tag(self, tag: str) -> Tag | None:
        data = await self.collection.find_one({"title": tag}, {"_id": 0})
        return Tag(**data) if data else None

    async def update_tag(self, name: str, content: str) -> None:
        await self.collection.update_one({"title": name}, {"$set": {"content": content}})

    async def get_user_tags(self, user_id: int) -> list[Tag]:
        tags = await self.collection.find({"user_id": user_id}, {"_id": 0}).to_list(None)
        return [Tag(**tag) for tag in tags]

    @property
    async def get_all_tags(self) -> list[Tag]:
        tags = await self.collection.find({}, {"_id": 0}).to_list(None)
        return [Tag(**tag) for tag in tags]


class WarnDB:

    __slots__: tuple[str, ...] = (
        "client",
        "collection",
    )

    def __init__(self, client: "Mongo") -> None:
        self.client = client
        self.collection = client["data"]["warns"]
        self.client.warns = self

    async def add_warn(self, data: WarnLog) -> None:
        await self.collection.insert_one(data.get_payload())

    async def delete_warn(self, guild_id: int, user_id: int) -> None:
        await self.collection.delete_one({"guild_id": guild_id, "user_id": user_id})

    async def get_warn(self, guild_id: int, user_id: int) -> WarnLog | None:
        data = await self.collection.find_one({"guild_id": guild_id, "user_id": user_id}, {"_id": 0})
        return WarnLog(**data) if data else None

    async def remove_warn(self, guild_id: int, user_id: int, index: int) -> None:
        data = await self.get_warn(guild_id, user_id)
        if len(data.logs) == 1:
            return await self.delete_warn(guild_id, user_id)
        data.logs.pop(index)
        await self.collection.update_one(
            {"guild_id": guild_id, "user_id": user_id}, {"$set": {"logs": [log.get_payload() for log in data.logs]}}
        )

    async def update_warn(self, guild_id: int, user_id: int, reason: str) -> WarnLog:
        time = datetime.datetime.utcnow()
        data = await self.get_warn(guild_id, user_id)
        if data is None:
            await self.add_warn(WarnLog(guild_id, user_id, [(reason, time)]))
            return WarnLog(guild_id, user_id, [(reason, time)])
        data.add_record(reason)
        await self.collection.update_one(
            {"guild_id": guild_id, "user_id": user_id}, {"$set": {"logs": [log.get_payload() for log in data.logs]}}
        )
        return data

    async def get_guild_warns(self, guild_id: int) -> list[WarnLog]:
        logs = await self.collection.find({"guild_id": guild_id}, {"_id": 0}).to_list(None)
        return [WarnLog(**log) for log in logs]

    @property
    async def get_all_warns(self) -> list[WarnLog]:
        logs = await self.collection.find({}, {"_id": 0}).to_list(None)
        return [WarnLog(**log) for log in logs]


class RepDB:
    def __init__(self, client: "Mongo") -> None:
        self.client = client
        self.collection = client["data"]["rep"]
        self.client.rep = self

    async def add_rep(self, data: UserRep) -> None:
        await self.collection.insert_one(data.get_payload())

    async def delete_rep(self, user_id: int) -> None:
        await self.collection.delete_one({"user_id": user_id})

    async def get_rep(self, user_id: int) -> UserRep | None:
        data = await self.collection.find_one({"user_id": user_id}, {"_id": 0})
        return UserRep(**data) if data else None

    async def update_rep(self, user_id: int, rep_giver: int) -> UserRep:
        user = await self.get_rep(user_id)
        if user is None:
            data = UserRep(user_id, 1, [(rep_giver, datetime.datetime.utcnow())])
            await self.add_rep(data)
            return data
        user.add_cooldown(rep_giver)
        user.reps += 1
        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"reps": user.reps, "cooldown": [cooldown.get_payload() for cooldown in user.cooldown]}},
        )
        return user

    async def remove_cooldown(self, user_id: int, rep_giver: int) -> None:
        user = await self.get_rep(user_id)
        if user is None:
            return
        await self.collection.update_one(
            {"user_id": user_id}, {"$set": {"cooldown": [x for x in user.cooldown if x.user_id != rep_giver]}}
        )

    async def remove_rep(self, user_id: int, rep_removed: int) -> int:
        user = await self.get_rep(user_id)
        if user is None:
            return 0
        user.reps = max(0, user.reps - rep_removed)
        await self.collection.update_one({"user_id": user_id}, {"$set": {"reps": user.reps}})
        return user.reps

    async def clear_rep(self, user_id: int) -> None:
        user = await self.get_rep(user_id)
        if user is None:
            return
        await self.collection.update_one({"user_id": user_id}, {"$set": {"reps": 0}})

    @property
    async def leaderboard(self) -> list[UserRep]:
        data = await self.collection.find({}, {"_id": 0}).sort("reps", -1).to_list(None)
        return [UserRep(**rep) for rep in data]

    @property
    async def get_all_rep(self) -> list[UserRep]:
        data = await self.collection.find({}, {"_id": 0}).to_list(None)
        return [UserRep(**rep) for rep in data]

    @property
    async def get_all_cooldown(self) -> list[UserRep]:
        data = await self.collection.find({}, {"_id": 0}).to_list(None)
        return [UserRep(**rep) for rep in data if rep["cooldown"]]


class CollectionDB:
    def __init__(self, client: "Mongo") -> None:
        self.client = client
        self.collection = client["data"]["collection"]
        self.client.collections = self

    async def add_collection(self, data: Collection) -> None:
        await self.collection.insert_one(data.get_payload())

    async def delete_collection(self, user_id: int) -> None:
        await self.collection.delete_one({"user_id": user_id})

    async def get_collection(self, user_id: int) -> Collection | None:
        data = await self.collection.find_one({"user_id": user_id}, {"_id": 0})
        return Collection(**data) if data else None

    async def add_item(self, user_id: int, item: str) -> Collection:
        collection = await self.get_collection(user_id)
        if collection is None:
            data = Collection(user_id, {item})
            await self.add_collection(data)
            return data
        collection.add_item(item)
        await self.collection.update_one({"user_id": user_id}, {"$set": {"collection": list(collection.collection)}})
        return collection

    async def remove_item(self, user_id: int, item: str) -> Collection | None:
        collection = await self.get_collection(user_id)
        if collection is None:
            return None
        collection.remove_item(item)
        await self.collection.update_one({"user_id": user_id}, {"$set": {"collection": list(collection.collection)}})
        return collection

    async def get_item_collection(self, item: str) -> list[Collection]:
        data = await self.collection.find({"collection": item}, {"_id": 0}).to_list(None)
        return [Collection(**collection) for collection in data]

    @property
    async def get_all_collection(self) -> list[Collection]:
        data = await self.collection.find({}, {"_id": 0}).to_list(None)
        return [Collection(**collection) for collection in data]


class GiveawayDB:
    def __init__(self, client: "Mongo") -> None:
        self.client = client
        self.collection = client["data"]["giveaway"]
        self.client.giveaways = self

    async def giveaway_start(self, data: Giveaway) -> None:
        await self.collection.insert_one(data.get_payload())

    async def get_giveaway(self, message_id: int) -> Giveaway | None:
        data = await self.collection.find_one({"message_id": message_id}, {"_id": 0})
        return Giveaway(**data) if data else None

    async def get_giveaways(self, guild_id: int) -> list[Giveaway]:
        data = await self.collection.find({"guild_id": guild_id, "ended": False}, {"_id": 0}).to_list(None)
        return [Giveaway(**giveaway) for giveaway in data]

    async def giveaway_click(self, message_id: int, user_id: int) -> bool:
        giveaway = await self.get_giveaway(message_id)
        if giveaway is None:
            return False
        if user_id in giveaway.participants:
            giveaway.remove_participant(user_id)
            await self.collection.update_one(
                {"message_id": message_id}, {"$set": {"participants": list(giveaway.participants)}}
            )
            return False
        giveaway.add_participant(user_id)
        await self.collection.update_one(
            {"message_id": message_id}, {"$set": {"participants": list(giveaway.participants)}}
        )
        return True

    async def end_giveaway(self, message_id: int) -> None:
        await self.collection.delete_one({"message_id": message_id})

    async def update_bool(self, message_id: int) -> None:
        await self.collection.update_one({"message_id": message_id}, {"$set": {"ended": True}})

    async def update_winners(self, message_id: int, winners: list[int]) -> None:
        await self.collection.update_one({"message_id": message_id}, {"$set": {"winners": list(winners)}})

    @property
    async def giveaway_by_time(self) -> list[Giveaway]:
        time = datetime.datetime.now()
        data = await self.collection.find({"end_time": {"$lte": time}, "ended": False}, {"_id": 0}).to_list(None)
        return [Giveaway(**giveaway) for giveaway in data]

    @property
    async def giveaway_by_end(self) -> list[Giveaway]:
        data = await self.collection.find(
            {"end_time": {"$gte": datetime.datetime.utcnow() + datetime.timedelta(days=1)}, "ended": True}, {"_id": 0}
        ).to_list(None)
        return [Giveaway(**giveaway) for giveaway in data]


class ReminderDB:
    def __init__(self, client: "Mongo") -> None:
        self.client = client
        self.collection = client["data"]["reminder"]
        self.client.reminders = self

    async def add_reminder(self, data: Reminder) -> None:
        await self.collection.insert_one(data.get_payload())

    async def get_reminder(self, message_id: int) -> Reminder | None:
        data = await self.collection.find_one({"message_id": message_id}, {"_id": 0})
        return Reminder(**data) if data else None

    async def get_all_reminder(self, user_id: int) -> list[Reminder]:
        data = await self.collection.find({}, {"user_id": user_id}, {"_id": 0}).to_list(None)
        return [Reminder(**reminder) for reminder in data]

    async def delete_reminder(self, message_id: int) -> None:
        await self.collection.delete_one({"message_id": message_id})

    @property
    async def get_reminder_by_time(self) -> list[Reminder]:
        time = datetime.datetime.now()
        data = await self.collection.find({"end_time": {"$lte": time}}, {"_id": 0}).to_list(None)
        return [Reminder(**reminder) for reminder in data]


class RolesDB:
    def __init__(self, client: "Mongo") -> None:
        self.client = client
        self.collection = client["data"]["roles"]
        self.client.roles = self

    async def add_menu(self, data: Menu) -> None:
        await self.collection.insert_one(data.get_payload())

    async def get_menu(self, message_id: int) -> Menu | None:
        data = await self.collection.find_one({"message_id": message_id}, {"_id": 0})
        return Menu(**data) if data else None

    async def update_roles(self, message_id: int, roles: set[int]) -> None:
        await self.collection.update_one({"message_id": message_id}, {"$set": {"role_ids": list(roles)}})

    async def delete_menu(self, message_id: int) -> None:
        await self.collection.delete_one({"message_id": message_id})
