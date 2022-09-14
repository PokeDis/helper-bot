from __future__ import annotations

import datetime
import time
from collections import defaultdict
from typing import Any, MutableMapping, Optional

import discord
from discord.ext import commands

from ..main import HelperBot


class ExpiringCache(dict):
    def __init__(self, seconds: float):
        self.__ttl: float = seconds
        super().__init__()

    def __verify_cache_integrity(self):
        # Have to do this in two steps...
        current_time = time.monotonic()
        to_remove = [
            k for (k, (v, t)) in self.items() if current_time > (t + self.__ttl)
        ]
        for k in to_remove:
            del self[k]

    def __contains__(self, key: str):
        self.__verify_cache_integrity()
        return super().__contains__(key)

    def __getitem__(self, key: str):
        self.__verify_cache_integrity()
        return super().__getitem__(key)

    def __setitem__(self, key: str, value: Any):
        super().__setitem__(key, (value, time.monotonic()))


class CooldownByContent(commands.CooldownMapping):
    def _bucket_key(self, message: discord.Message) -> tuple[int, str]:
        return message.channel.id, message.content


class SpamCheck:

    MENTION_COUNT = 5

    def __init__(self) -> None:
        self.by_content = CooldownByContent.from_cooldown(
            15, 17.0, commands.BucketType.member
        )
        self.by_user = commands.CooldownMapping.from_cooldown(
            10, 12.0, commands.BucketType.user
        )
        self.last_join: Optional[datetime.datetime] = None
        self.new_user = commands.CooldownMapping.from_cooldown(
            30, 35.0, commands.BucketType.channel
        )
        self._by_mentions: Optional[commands.CooldownMapping] = None
        self._by_mentions_rate: Optional[int] = None
        self.fast_joiners: MutableMapping[int, bool] = ExpiringCache(seconds=1800.0)

        # user_id flag mapping (for about 30 minutes)
        self.hit_and_run = commands.CooldownMapping.from_cooldown(
            10, 12, commands.BucketType.channel
        )

    def by_mentions(self) -> Optional[commands.CooldownMapping]:
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
            member.created_at > ninety_days_ago
            and member.joined_at is not None
            and member.joined_at > seven_days_ago
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
        mention_count = sum(
            not m.bot and m.id != message.author.id for m in message.mentions
        )
        return (
            mention_bucket.update_rate_limit(current, tokens=mention_count) is not None
        )

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


class Mod(commands.Cog):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot
        self._spam_check: defaultdict[int, SpamCheck] = defaultdict(SpamCheck)

    async def check_raid(
        self, guild_id: int, member: discord.Member, message: discord.Message
    ) -> None:
        checker = self._spam_check[guild_id]
        if not checker.is_spamming(message):
            return
        embed = discord.Embed(title=f"Auto-Ban {member}", color=discord.Color.red())
        embed.set_thumbnail(url=member.display_avatar)
        embed.timestamp = discord.utils.utcnow()
        try:
            embed.description = f"**Automatic ban for spamming.\n[Raid Mode] Banned {member} (ID: {member.id}) from server {member.guild} via strict mode.**"
            await member.ban(reason="Auto-ban from spam (strict raid mode ban)")
        except discord.HTTPException:
            embed.description = f"**Failed to ban {member} for spamming.**"
            raise commands.CommandError(
                f"[Raid Mode] Failed to ban {member} (ID: {member.id}) from server {member.guild} via strict mode."
            )
        else:
            await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        author = message.author
        if author.id in (self.bot.user.id, self.bot.owner_id):
            return

        if message.guild is None:
            return
        if not isinstance(author, discord.Member):
            return
        if author.bot:
            return
        # we're going to ignore members with manage messages
        if author.guild_permissions.manage_messages:
            return
        guild_id = message.guild.id

        # check for raid mode stuff
        await self.check_raid(guild_id, author, message)

        # auto-ban tracking for mention spams begin here
        if len(message.mentions) <= 3:
            return

        # check if it meets the thresholds required
        mention_count = sum(not m.bot and m.id != author.id for m in message.mentions)
        if mention_count < 5:
            return
        embed = discord.Embed(title=f"Auto-Ban {author}", color=discord.Color.red())
        embed.set_thumbnail(url=author.display_avatar)
        embed.timestamp = discord.utils.utcnow()

        try:
            embed.description = f"**Automatic ban for spamming.\n[Mention Mode] Banned {author} (ID: {author.id}) from server {author.guild} via strict mode.**"
            await author.ban(reason=f"Spamming mentions ({mention_count} mentions)")
        except Exception as e:
            print(e)
            embed.description = f"**Failed to ban {author} for spamming mentions.**"
            raise commands.CommandError(
                f"Failed to autoban member {author} (ID: {author.id}) in guild ID {guild_id}"
            )
        else:
            await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id

        checker = self._spam_check[guild_id]
        fastjoin = False

        if checker.is_fast_join(member):
            fastjoin = True

        if fastjoin:
            embed = discord.Embed(
                title=f"High-Speed Join {member}", color=discord.Color.red()
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.timestamp = discord.utils.utcnow()
            embed.description = f"**High-speed join from {member} (ID: {member.id}) in server {member.guild} via strict mode.**"
            await self.bot.logs.send(embed=embed)

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Mod(bot))
