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

    def __init__(self) -> None:
        super().__init__(os.getenv("MONGODB"))
        TagDB(self)
        WarnDB(self)
        RepDB(self)
        CollectionDB(self)
        GiveawayDB(self)
        ReminderDB(self)
        RolesDB(self)
