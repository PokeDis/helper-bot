import datetime

import discord
from discord.ext import commands

from .cache import ExpiringCache


class CooldownByContent(commands.CooldownMapping):
    def _bucket_key(self, message: discord.Message) -> tuple[int, str]:
        return message.channel.id, message.content


class SpamCheck:

    MENTION_COUNT = 5

    def __init__(self) -> None:
        self.by_content = CooldownByContent.from_cooldown(15, 17.0, commands.BucketType.member)
        self.by_user = commands.CooldownMapping.from_cooldown(10, 12.0, commands.BucketType.user)
        self.last_join: datetime.datetime | None = None
        self.new_user = commands.CooldownMapping.from_cooldown(30, 35.0, commands.BucketType.channel)
        self._by_mentions: commands.CooldownMapping | None = None
        self._by_mentions_rate: int | None = None
        self.fast_joiners: dict[int, bool] = ExpiringCache(seconds=1800.0)
        self.hit_and_run = commands.CooldownMapping.from_cooldown(10, 12, commands.BucketType.channel)

    def by_mentions(self) -> commands.CooldownMapping | None:
        mention_threshold = self.MENTION_COUNT * 2
        if self._by_mentions_rate != mention_threshold:
            self._by_mentions = commands.CooldownMapping.from_cooldown(
                mention_threshold, 12, commands.BucketType.member
            )
            self._by_mentions_rate = mention_threshold
        return self._by_mentions

    @staticmethod
    def is_new(member: discord.Member) -> bool:
        now = discord.utils.utcnow()
        seven_days_ago = now - datetime.timedelta(days=7)
        ninety_days_ago = now - datetime.timedelta(days=90)
        return (
            member.created_at > ninety_days_ago and member.joined_at is not None and member.joined_at > seven_days_ago
        )

    def is_spamming(self, message: discord.Message) -> bool:
        if message.guild is None:
            return False
        current = message.created_at.timestamp()

        if message.author.id in self.fast_joiners:
            bucket = self.hit_and_run.get_bucket(message)
            if bucket.update_rate_limit(current):
                return True

        if self.is_new(message.author):  # type: ignore
            new_bucket = self.new_user.get_bucket(message)
            if new_bucket.update_rate_limit(current):
                return True

        user_bucket = self.by_user.get_bucket(message)
        if user_bucket.update_rate_limit(current):
            return True

        content_bucket = self.by_content.get_bucket(message)
        if content_bucket.update_rate_limit(current):
            return True

        if self.is_mention_spam(message, current):
            return True

        return False

    def is_mention_spam(self, message: discord.Message, current: float) -> bool:
        mapping = self.by_mentions()
        if mapping is None:
            return False
        mention_bucket = mapping.get_bucket(message, current)
        mention_count = sum(not m.bot and m.id != message.author.id for m in message.mentions)
        return mention_bucket.update_rate_limit(current, tokens=mention_count) is not None

    def is_fast_join(self, member: discord.Member) -> bool:
        joined = member.joined_at or discord.utils.utcnow()
        if self.last_join is None:
            self.last_join = joined
            return False
        is_fast = (joined - self.last_join).total_seconds() <= 2.0
        self.last_join = joined
        if is_fast:
            self.fast_joiners[member.id] = True
        return is_fast
