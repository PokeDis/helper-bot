import os

from motor import motor_asyncio

from .mongo import *


class Mongo(motor_asyncio.AsyncIOMotorClient):

    tags: TagDB
    warns: WarnDB
    rep: RepDB
    collections: CollectionDB
    giveaways: GiveawayDB
    reminders: ReminderDB
    roles: RolesDB
    guilds: GuildDB
    afk: AfkDB
    invites: InviteDB

    def __init__(self) -> None:
        super().__init__(os.getenv("MONGODB"))
        self.pokemondb = motor_asyncio.AsyncIOMotorClient(os.getenv("POKEMONDB"))
        self.user_data = self.pokemondb["users"]["data"]
        TagDB(self)
        WarnDB(self)
        RepDB(self)
        CollectionDB(self)
        GiveawayDB(self)
        ReminderDB(self)
        RolesDB(self)
        GuildDB(self)
        AfkDB(self)
        InviteDB(self)

    async def add_redeem(self, user_id: int) -> None:
        user = await self.user_data.find_one({"id": user_id})
        if not user:
            return
        user["bag"]["Key Items"].update({"Redeem": user["bag"]["Key Items"].get("Redeem", 0) + 1})
        await self.user_data.update_one({"id": user_id}, {"$set": {"bag": user["bag"]}})
