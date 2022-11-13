import dataclasses
import datetime

from discord.ext import commands

__all__: tuple[str, ...] = (
    "Tag",
    "WarnLog",
    "Cooldown",
    "UserRep",
    "Collection",
    "Giveaway",
    "Reminder",
    "Menu",
)


@dataclasses.dataclass
class Warn:
    reason: str
    time: datetime.datetime

    def get_payload(self) -> tuple[str, datetime.datetime]:
        return self.reason, self.time


@dataclasses.dataclass
class Cooldown:
    user_id: int
    time: datetime.datetime

    def get_payload(self) -> tuple[int, datetime.datetime]:
        return self.user_id, self.time


@dataclasses.dataclass
class Tag:
    user_id: int
    title: str
    content: str

    def get_payload(self) -> dict[str, str | int]:
        return {"user_id": self.user_id, "title": self.title, "content": self.content}


@dataclasses.dataclass
class WarnLog:
    guild_id: int
    user_id: int
    logs: list[tuple[str, datetime.datetime]]

    def __post_init__(self) -> None:
        self.logs: list[Warn] = [Warn(*log) for log in self.logs]

    def add_record(self, reason: str) -> None:
        self.logs.append(Warn(reason, datetime.datetime.utcnow()))

    def get_payload(self) -> dict[str, str | int | list[Warn]]:
        return {
            "guild_id": self.guild_id,
            "user_id": self.user_id,
            "logs": [log.get_payload() for log in self.logs],
        }


@dataclasses.dataclass
class UserRep:
    user_id: int
    reps: int
    cooldown: list[tuple[int, datetime.datetime]]

    def __post_init__(self) -> None:
        self.cooldown: list[Cooldown] = [Cooldown(*cooldown) for cooldown in self.cooldown]

    def get_payload(self) -> dict[str, str | int | list[Cooldown]]:
        return {
            "user_id": self.user_id,
            "reps": self.reps,
            "cooldown": [(cooldown.user_id, cooldown.time) for cooldown in self.cooldown],
        }

    def add_cooldown(self, user_id: int) -> None:
        for cd in self.cooldown:
            if user_id == cd.user_id:
                self.cooldown[self.cooldown.index(cd)] = Cooldown(user_id, datetime.datetime.utcnow())
                return
        self.cooldown.append(Cooldown(user_id, datetime.datetime.utcnow()))
        return


@dataclasses.dataclass
class Collection:
    user_id: int
    collection: set[str]

    def __post_init__(self) -> None:
        self.collection: set[str] = set(self.collection)

    def get_payload(self) -> dict[str, int | set[str]]:
        return {
            "user_id": self.user_id,
            "collection": list(self.collection),
        }

    def add_item(self, item: str) -> None:
        if item in self.collection:
            raise commands.BadArgument("You already have this item in your collection.")
        self.collection.add(item)

    def remove_item(self, item: str) -> None:
        if item not in self.collection:
            raise commands.BadArgument("You don't have this item in your collection.")
        self.collection.remove(item)


@dataclasses.dataclass
class Giveaway:
    message_id: int
    channel_id: int
    guild_id: int
    winner_count: int
    prize: str
    host_id: int
    end_time: datetime.datetime = dataclasses.field(default_factory=datetime.datetime.now)
    participants: set[int] = dataclasses.field(default_factory=set)
    winners: set[int] = dataclasses.field(default_factory=set)
    ended: bool = False

    def __post_init__(self) -> None:
        self.participants: set[int] = set(self.participants)
        self.winners: set[int] = set(self.winners)

    def get_payload(self) -> dict[str, int | datetime.datetime | str | list[int]]:
        return {
            "message_id": self.message_id,
            "channel_id": self.channel_id,
            "guild_id": self.guild_id,
            "winner_count": self.winner_count,
            "prize": self.prize,
            "host_id": self.host_id,
            "end_time": self.end_time,
            "participants": list(self.participants),
            "winners": list(self.winners),
            "ended": self.ended,
        }

    def add_participant(self, user_id: int) -> None:
        self.participants.add(user_id)

    def remove_participant(self, user_id: int) -> None:
        self.participants.remove(user_id)


@dataclasses.dataclass
class Reminder:
    message_id: int
    end_time: datetime.datetime
    guild_id: int
    channel_id: int
    user_id: int

    def get_payload(self) -> dict[str, int | datetime.datetime]:
        return {
            "message_id": self.message_id,
            "end_time": self.end_time,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "user_id": self.user_id,
        }


@dataclasses.dataclass
class Menu:
    message_id: int
    channel_id: int
    guild_id: int
    role_ids: set[int] = dataclasses.field(default_factory=set)

    def __post_init__(self) -> None:
        self.role_ids: set[int] = set(self.role_ids)

    def get_payload(self) -> dict[str, int | list[int]]:
        return {
            "message_id": self.message_id,
            "channel_id": self.channel_id,
            "guild_id": self.guild_id,
            "role_ids": list(self.role_ids),
        }
