import typing
from collections import defaultdict

import discord
from discord.ext import commands

from bot.core.helper import SpamCheck
from bot.database import Guild

if typing.TYPE_CHECKING:
    from bot.core import PokeHelper


class AutoMod(commands.Cog):
    """Automod and spam detection."""

    def __init__(self, bot: "PokeHelper") -> None:
        self.bot = bot
        self._spam_check: defaultdict[int, SpamCheck] = defaultdict(SpamCheck)

    async def check_raid(self, guild_id: int, member: discord.Member, message: discord.Message) -> None:
        checker = self._spam_check[guild_id]
        if not checker.is_spamming(message):
            return
        embed = discord.Embed(title=f"Auto-Ban {member}", color=discord.Color.red())
        embed.set_thumbnail(url=member.display_avatar)
        embed.timestamp = discord.utils.utcnow()
        try:
            embed.description = (
                f"**Automatic ban for spamming.\n[Raid Mode] Banned {member}"
                f" (ID: {member.id}) from server {member.guild} via strict mode.**"
            )
            await member.ban(reason="Auto-ban from spam (strict raid mode ban)")
        except discord.HTTPException:
            embed.description = f"**Failed to ban {member} for spamming.**"
            raise commands.CommandError(
                f"[Raid Mode] Failed to ban {member} (ID: {member.id}) from server {member.guild} via strict mode."
            )
        else:
            await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        author = message.author
        if author.id in (self.bot.user.id, self.bot.owner_id):
            return
        if message.guild is None:
            return
        if not isinstance(author, discord.Member):
            return
        if author.bot:
            return
        if author.guild_permissions.manage_messages:
            return
        guild_id = message.guild.id
        await self.check_raid(guild_id, author, message)
        if len(message.mentions) <= 3:
            return
        mention_count = sum(not m.bot and m.id != author.id for m in message.mentions)
        if mention_count < 5:
            return
        embed = discord.Embed(title=f"Auto-Ban {author}", color=discord.Color.red())
        embed.set_thumbnail(url=author.display_avatar)
        embed.timestamp = discord.utils.utcnow()
        try:
            embed.description = (
                f"**Automatic ban for spamming.\n[Mention Mode] Banned {author}"
                f" (ID: {author.id}) from server {author.guild} via strict mode.**"
            )
            await author.ban(reason=f"Spamming mentions ({mention_count} mentions)")
        except Exception as e:
            print(e)
            embed.description = f"**Failed to ban {author} for spamming mentions.**"
            raise commands.CommandError(f"Failed to autoban member {author} (ID: {author.id}) in guild ID {guild_id}")
        else:
            await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        guild_id = member.guild.id
        checker = self._spam_check[guild_id]
        if checker.is_fast_join(member):
            embed = discord.Embed(title=f"High-Speed Join {member}", color=discord.Color.red())
            embed.set_thumbnail(url=member.display_avatar)
            embed.timestamp = discord.utils.utcnow()
            embed.description = (
                f"**High-speed join from {member} (ID: {member.id}) in server {member.guild} via strict mode.**"
            )
            await self.bot.logs.send(embed=embed)

    @staticmethod
    async def start_lockdown(
        ctx: commands.Context,
        channels: list[discord.TextChannel | discord.VoiceChannel],
    ) -> tuple[list[discord.TextChannel | discord.VoiceChannel], list[discord.TextChannel | discord.VoiceChannel],]:
        success, failures = set(), set()
        await ctx.bot.logs.send(
            embed=discord.Embed(
                title="Lockdown", description=f"**Lockdown started by {ctx.author}**", color=discord.Color.red()
            )
        )
        reason = f"Lockdown request by {ctx.author} (ID: {ctx.author.id})"
        async with ctx.typing():
            for channel in channels:
                for role in ctx.guild.roles:
                    if not role.permissions.administrator and not role.is_bot_managed():
                        try:
                            await channel.set_permissions(
                                role,
                                send_messages=False,
                                reason=reason,
                                connect=False,
                                use_application_commands=False,
                                add_reactions=False,
                                create_private_threads=False,
                                create_public_threads=False,
                                send_messages_in_threads=False,
                            )
                        except discord.HTTPException:
                            failures.add(channel)
                        else:
                            success.add(channel)
        return list(success), list(failures)

    async def end_lockdown(
        self,
        ctx: commands.Context,
        channels: list[discord.TextChannel | discord.VoiceChannel],
    ) -> tuple[list[discord.TextChannel | discord.VoiceChannel], list[discord.TextChannel | discord.VoiceChannel],]:
        success, failures = set(), set()
        await ctx.bot.logs.send(
            embed=discord.Embed(
                title="Lockdown", description=f"**Lockdown ended by {ctx.author}**", color=discord.Color.green()
            )
        )
        reason = f"Lockdown-Lift request by {ctx.author} (ID: {ctx.author.id})"
        async with ctx.typing():
            settings = await self.bot.db.guilds.get_channels(ctx.guild.id)
            for old_channel, setting in settings.items():
                if int(old_channel) in [channel.id for channel in channels]:
                    for role_id, role_setting in setting.items():
                        try:
                            channel = ctx.guild.get_channel(int(old_channel))
                            role = ctx.guild.get_role(int(role_id))
                            await channel.set_permissions(
                                role,
                                **role_setting,
                                reason=reason,
                            )
                        except discord.HTTPException:
                            failures.add(channel)
                        else:
                            success.add(channel)
        return list(success), list(failures)

    @commands.command(help="Locks down the server.")
    @commands.has_permissions(administrator=True)
    async def lockdown(
        self,
        ctx: commands.Context,
        *,
        channels: commands.Greedy[discord.TextChannel | discord.VoiceChannel] = None,
    ) -> None:
        if channels is None:
            channels = ctx.guild.channels
        await self.add_guild_data(ctx.guild.id)
        success, failures = await self.start_lockdown(ctx, channels)
        if failures:
            await ctx.send(
                embed=discord.Embed(
                    title="Lockdown",
                    description=f"<:no:1001136828738453514> **Failed to lockdown"
                    f" {len(failures)} channels.**\n"
                    f"<:tick:1001136782508826777> **{len(success)}"
                    f" channels were locked down.**",
                    color=discord.Color.red(),
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(
                    title=f"<:tick:1001136782508826777> Successfully locked down" f" {len(success)} channels.",
                    color=discord.Color.green(),
                )
            )

    @commands.command(help="Lifts the lockdown on the server or specified channels.")
    @commands.has_permissions(administrator=True)
    async def lockdownlift(
        self,
        ctx: commands.Context,
        *,
        channels: commands.Greedy[discord.TextChannel | discord.VoiceChannel] = None,
    ) -> None:
        if channels is None:
            channels = ctx.guild.channels
        success, failures = await self.end_lockdown(ctx, channels)
        if failures:
            await ctx.send(
                embed=discord.Embed(
                    title="Lockdown-Lift",
                    description=f"<:no:1001136828738453514> **Failed to lift lockdown"
                    f" {len(failures)} channels.**\n"
                    f"<:tick:1001136782508826777> **{len(success)}"
                    f" channels were unlocked.**",
                    color=discord.Color.red(),
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(
                    title=f"<:tick:1001136782508826777> Successfully unlocked" f" {len(success)} channels.",
                    color=discord.Color.green(),
                )
            )

    @staticmethod
    def add_channel_data(guild: discord.Guild) -> dict[str, dict[str, dict[str, bool | None]]]:
        channels = {}
        for channel in guild.channels:
            channels[f"{channel.id}"] = {}
            for k, v in channel.overwrites.items():
                if isinstance(k, discord.Role):
                    channels[f"{channel.id}"][f"{k.id}"] = dict(v)
            if not channels[f"{channel.id}"]:
                for role in guild.roles:
                    if not role.permissions.administrator and not role.is_bot_managed():
                        channels[f"{channel.id}"][f"{role.id}"] = dict(
                            send_messages=None,
                            connect=None,
                            use_application_commands=None,
                            add_reactions=None,
                            create_private_threads=None,
                            create_public_threads=None,
                            send_messages_in_threads=None,
                        )
        return channels

    async def add_guild_data(self, guild_id: int = 998133764960039033) -> None:
        guild = await self.bot.db.guilds.get_guild(guild_id)
        data = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)
        channels = self.add_channel_data(data)
        if guild is None:
            await self.bot.db.guilds.add_guild(Guild(guild_id, channels))
            print(f"✅ Added guild {data} to the database!")
        else:
            await self.bot.db.guilds.update_channel(guild_id, channels)
            print(f"✅ Updated guild {data} in the database!")

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")


async def setup(bot: "PokeHelper") -> None:
    await bot.add_cog(AutoMod(bot))
