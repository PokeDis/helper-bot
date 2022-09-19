from __future__ import annotations

from .db import *

__all__: tuple[str, ...] = ("Database",)


class Database:

    def __init__(self):
        self.warn_db = WarnDB()
        self.tag_db = TagDB()
        self.rep_db = RepDB()
        self.rep_cd_db = RepCooldownDB()
        self.giveaway_db = GiveawayDB()
        self.reminder_db = ReminderDB()
        self.collection_db = CollectionDB()
