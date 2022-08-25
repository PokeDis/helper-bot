from __future__ import annotations

import datetime
import io

import discord
from discord.ext import commands

from ..main import HelperBot


class Logger(commands.Cog):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        embed = discord.Embed(
            title="Join",
            description=f"{member} has joined the server",
            colour=discord.Colour.green(),
        )
        embed.add_field(
            name="Name", value=f"{member} [{member.id}]\n{member.mention}", inline=True
        )
        embed.add_field(
            name="Joined",
            value=f"{discord.utils.format_dt(member.joined_at, style='D')}",
            inline=True,
        )
        embed.add_field(
            name="Account Created On",
            value=f"{discord.utils.format_dt(member.created_at, style='D')}",
            inline=True,
        )
        embed.add_field(
            name="Member Count", value=len(member.guild.members), inline=True
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.timestamp = discord.utils.utcnow()
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        embed = discord.Embed(
            title="Leave",
            description=f"{member} has left the server",
            colour=discord.Colour.red(),
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.timestamp = discord.utils.utcnow()
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(
        self, before: discord.Message, after: discord.Message
    ) -> None:
        embed = discord.Embed(
            title="Edit Message",
            description=f"{after.author} edited their message in {after.channel.mention}.\n[Go to message]({after.jump_url})",
            colour=discord.Colour.blue(),
        )
        embed.set_thumbnail(url=after.author.display_avatar)
        embed.timestamp = discord.utils.utcnow()
        if len(after.content) > 1024 or len(before.content) > 1024:
            buffer = io.BytesIO()
            message = f"Before:\n {before.content}\nAfter:\n {after.content}"
            buffer.write(bytes(message, "utf-8"))
            buffer.seek(0)
            file = discord.File(buffer, filename="message_edit.txt")
            await self.bot.logs.send(embed=embed, file=file)
            return
        embed.add_field(
            name="Before", value=before.content if before.content else "No content"
        )
        embed.add_field(
            name="After", value=after.content if after.content else "No content"
        )
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        embed = discord.Embed(
            title="Delete Message",
            description=f"{message.author} deleted their message in {message.channel.mention}",
            colour=discord.Colour.red(),
        )
        embed.set_thumbnail(url=message.author.display_avatar)
        embed.timestamp = discord.utils.utcnow()
        if len(message.content) > 1024:
            buffer = io.BytesIO()
            message = f"Message:\n{message.content}"
            buffer.write(bytes(message, "utf-8"))
            buffer.seek(0)
            file = discord.File(buffer, filename="message_delete.txt")
            await self.bot.logs.send(embed=embed, file=file)
            return
        embed.add_field(
            name="Message", value=message.content if message.content else "No content"
        )
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if before.channel == after.channel:
            return
        if before.channel is None:
            embed = discord.Embed(
                title="Join Voice",
                description=f"{member} has joined {after.channel.mention}",
                colour=discord.Colour.green(),
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.timestamp = discord.utils.utcnow()
            await self.bot.logs.send(embed=embed)
        elif after.channel is None:
            embed = discord.Embed(
                title="Leave Voice",
                description=f"{member} has left {before.channel.mention}",
                colour=discord.Colour.red(),
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.timestamp = discord.utils.utcnow()
            await self.bot.logs.send(embed=embed)
        elif before.mute != after.mute:
            embed = discord.Embed(
                title="Mute",
                description=f"{member} has {'unmuted' if after.mute else 'muted'} {after.channel.mention}",
                colour=discord.Colour.blue(),
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.timestamp = discord.utils.utcnow()
            await self.bot.logs.send(embed=embed)
        elif before.deaf != after.deaf:
            embed = discord.Embed(
                title="Deaf",
                description=f"{member} has {'undeafed' if after.deaf else 'deafed'} {after.channel.mention}",
                colour=discord.Colour.blue(),
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.timestamp = discord.utils.utcnow()
            await self.bot.logs.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Move Voice",
                description=f"{member} has moved from {before.channel.mention} to {after.channel.mention}",
                colour=discord.Colour.blue(),
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.timestamp = discord.utils.utcnow()
            await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User) -> None:
        embed = discord.Embed(title="Update User", colour=discord.Colour.blue())
        embed.set_thumbnail(url=after.display_avatar)
        embed.timestamp = discord.utils.utcnow()
        if before.display_name != after.display_name:
            embed.description = f"{after.mention} has updated their name."
            embed.add_field(name="Before", value=before.display_name)
            embed.add_field(name="After", value=after.display_name)
            embed.set_image(url=after.display_avatar)
            await self.bot.logs.send(embed=embed)
        elif before.avatar != after.avatar:
            embed.description = f"{after.mention} has updated their avatar."
            embed.add_field(name="Before", value=before.avatar.url)
            embed.add_field(name="After", value=after.avatar.url)
            embed2 = embed.copy()
            embed2.set_image(url=before.display_avatar)
            await self.bot.logs.send(embeds=[embed, embed2])
        elif before.discriminator != after.discriminator:
            embed.description = f"{after.mention} has updated their discriminator."
            embed.add_field(name="Before", value=f"{before.discriminator}")
            embed.add_field(name="After", value=f"{after.discriminator}")
            await self.bot.logs.send(embed=embed)
        else:
            return

    @commands.Cog.listener()
    async def on_member_update(
        self, before: discord.Member, after: discord.Member
    ) -> None:
        embed = discord.Embed(title="Update Member", colour=discord.Colour.blue())
        embed.set_thumbnail(url=after.display_avatar)
        embed.timestamp = discord.utils.utcnow()
        if before.nick != after.nick:
            embed.description = f"{after.mention} has updated their nickname."
            embed.add_field(name="Before", value=before.nick)
            embed.add_field(name="After", value=after.nick)
            await self.bot.logs.send(embed=embed)
        elif before.roles != after.roles:
            embed.description = f"{after.mention} has updated their roles."
            embed.add_field(
                name="Before", value=", ".join([role.mention for role in before.roles])
            )
            embed.add_field(
                name="After", value=", ".join([role.mention for role in after.roles])
            )
            await self.bot.logs.send(embed=embed)
        elif before.guild_avatar != after.guild_avatar:
            embed.description = f"{after.mention} has updated their guild avatar."
            embed.add_field(name="Before", value=before.guild_avatar.url)
            embed.add_field(name="After", value=after.guild_avatar.url)
            embed.set_image(url=after.guild_avatar.url)
            embed2 = embed.copy()
            embed2.set_image(url=before.display_avatar)
            await self.bot.logs.send(embeds=[embed, embed2])
        else:
            pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.Member) -> None:
        embed = discord.Embed(
            title="Ban",
            description=f"{user} has been banned from {guild.name}",
            colour=discord.Colour.red(),
        )
        embed.set_thumbnail(url=user.display_avatar)
        embed.timestamp = discord.utils.utcnow()
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.Member) -> None:
        embed = discord.Embed(
            title="Unban",
            description=f"{user} has been unbanned from {guild.name}",
            colour=discord.Colour.green(),
        )
        embed.set_thumbnail(url=user.display_avatar)
        embed.timestamp = discord.utils.utcnow()
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_update(
        self, before: discord.Guild, after: discord.Guild
    ) -> None:
        embed = discord.Embed(title="Update Guild", colour=discord.Colour.blue())
        embed.set_thumbnail(url=after.icon)
        embed.timestamp = discord.utils.utcnow()
        if before.description != after.description:
            embed.description = f"{after.name} has updated their description."
            embed.add_field(name="Before", value=before.description)
            embed.add_field(name="After", value=after.description)
            await self.bot.logs.send(embed=embed)
        elif before.name != after.name:
            embed.description = f"{after.name} has updated their name."
            embed.add_field(name="Before", value=before.name)
            embed.add_field(name="After", value=after.name)
            await self.bot.logs.send(embed=embed)
        elif before.icon != after.icon:
            embed.description = f"{after.name} has updated their icon."
            embed.add_field(name="Before", value=before.icon.url)
            embed.add_field(name="After", value=after.icon.url)
            await self.bot.logs.send(embed=embed)
        elif before.roles != after.roles:
            embed.description = f"Roles updated for {after.name}."
            embed.add_field(
                name="Before", value=", ".join([role.mention for role in before.roles])
            )
            embed.add_field(
                name="After", value=", ".join([role.mention for role in after.roles])
            )
            await self.bot.logs.send(embed=embed)
        else:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.TextChannel) -> None:
        embed = discord.Embed(
            title="Create Channel",
            description=f"{channel.mention} has been created.",
            colour=discord.Colour.blue(),
        )
        embed.set_thumbnail(url=channel.guild.icon)
        embed.timestamp = discord.utils.utcnow()
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.TextChannel) -> None:
        embed = discord.Embed(
            title="Delete Channel",
            description=f"{channel.mention} has been deleted.",
            colour=discord.Colour.red(),
        )
        embed.set_thumbnail(url=channel.guild.icon)
        embed.timestamp = discord.utils.utcnow()
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self, before: discord.TextChannel, after: discord.TextChannel
    ) -> None:
        embed = discord.Embed(title="Update Channel", colour=discord.Colour.blue())
        embed.set_thumbnail(url=after.guild.icon)
        embed.timestamp = discord.utils.utcnow()
        if before.name != after.name:
            embed.description = f"{after.mention} has updated their name."
            embed.add_field(name="Before", value=before.name)
            embed.add_field(name="After", value=after.name)
            await self.bot.logs.send(embed=embed)
        elif before.topic != after.topic:
            embed.description = f"{after.mention} has updated their topic."
            embed.add_field(name="Before", value=before.topic)
            embed.add_field(name="After", value=after.topic)
            await self.bot.logs.send(embed=embed)
        elif before.position != after.position:
            embed.description = f"{after.mention} has updated their position."
            embed.add_field(name="Before", value=before.position)
            embed.add_field(name="After", value=after.position)
            await self.bot.logs.send(embed=embed)
        elif before.category != after.category:
            embed.description = f"{after.mention} has updated their category."
            embed.add_field(name="Before", value=before.category.mention)
            embed.add_field(name="After", value=after.category.mention)
            await self.bot.logs.send(embed=embed)
        else:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(
        self, channel: discord.TextChannel, last_pin: datetime.datetime
    ) -> None:
        embed = discord.Embed(
            title="Update Channel",
            description=f"{channel.mention} has updated their pins.",
            colour=discord.Colour.blue(),
        )
        embed.set_thumbnail(url=channel.guild.icon)
        embed.timestamp = discord.utils.utcnow()
        embed.add_field(name="Last Pin", value=last_pin)
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(
        self,
        guild: discord.Guild,
        before: list[discord.Emoji],
        after: list[discord.Emoji],
    ) -> None:
        embed = discord.Embed(
            title="Update Emojis",
            description=f"{guild.name} has updated their emojis.",
            colour=discord.Colour.blue(),
        )
        embed.set_thumbnail(url=guild.icon)
        embed.timestamp = discord.utils.utcnow()
        embed.add_field(name="Before", value=", ".join([str(i) for i in before]))
        embed.add_field(name="After", value=", ".join([str(i) for i in after]))
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_stickers_update(
        self,
        guild: discord.Guild,
        before: list[discord.Sticker],
        after: list[discord.Sticker],
    ) -> None:
        embed = discord.Embed(
            title="Update Stickers",
            description=f"{guild.name} has updated their stickers.",
            colour=discord.Colour.blue(),
        )
        embed.set_thumbnail(url=guild.icon)
        embed.timestamp = discord.utils.utcnow()
        embed.add_field(
            name="Before", value=", ".join([sticker.name for sticker in before])
        )
        embed.add_field(
            name="After", value=", ".join([sticker.name for sticker in after])
        )
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_integrations_update(self, guild: discord.Guild) -> None:
        embed = discord.Embed(
            title="Update Integrations",
            description=f"{guild.name} has updated their integrations.",
            colour=discord.Colour.blue(),
        )
        embed.set_thumbnail(url=guild.icon)
        embed.timestamp = discord.utils.utcnow()
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_integration_create(self, integration: discord.Integration) -> None:
        embed = discord.Embed(
            title="Create Integration",
            description=f"{integration.name} has been created.",
            colour=discord.Colour.blue(),
        )
        embed.set_thumbnail(url=integration.guild.icon)
        embed.timestamp = discord.utils.utcnow()
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_integration_delete(self, integration: discord.Integration) -> None:
        embed = discord.Embed(
            title="Delete Integration",
            description=f"{integration.name} has been deleted.",
            colour=discord.Colour.red(),
        )
        embed.set_thumbnail(url=integration.guild.icon)
        embed.timestamp = discord.utils.utcnow()
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        embed = discord.Embed(
            title="Create Role",
            description=f"{role.mention} has been created.",
            colour=discord.Colour.blue(),
        )
        embed.set_thumbnail(url=role.guild.icon)
        embed.timestamp = discord.utils.utcnow()
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        embed = discord.Embed(
            title="Delete Role",
            description=f"{role.mention} has been deleted.",
            colour=discord.Colour.red(),
        )
        embed.set_thumbnail(url=role.guild.icon)
        embed.timestamp = discord.utils.utcnow()
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_update(
        self, before: discord.Role, after: discord.Role
    ) -> None:
        embed = discord.Embed(title="Update Role", colour=discord.Colour.blue())
        embed.set_thumbnail(url=after.guild.icon)
        embed.timestamp = discord.utils.utcnow()
        if before.name != after.name:
            embed.description = f"{after.mention} has updated their name."
            embed.add_field(name="Before", value=before.name)
            embed.add_field(name="After", value=after.name)
            await self.bot.logs.send(embed=embed)
        elif before.color != after.color:
            embed.description = f"{after.mention} has updated their color."
            embed.add_field(name="Before", value=before.color)
            embed.add_field(name="After", value=after.color)
            await self.bot.logs.send(embed=embed)
        elif before.hoist != after.hoist:
            embed.description = f"{after.mention} has updated their hoist."
            embed.add_field(name="Before", value=before.hoist)
            embed.add_field(name="After", value=after.hoist)
            await self.bot.logs.send(embed=embed)
        elif before.mentionable != after.mentionable:
            embed.description = f"{after.mention} has updated their mentionable."
            embed.add_field(name="Before", value=before.mentionable)
            embed.add_field(name="After", value=after.mentionable)
            await self.bot.logs.send(embed=embed)
        elif before.permissions != after.permissions:
            embed.description = f"{after.mention} has updated their permissions."
            embed.add_field(name="Before", value=before.permissions)
            embed.add_field(name="After", value=after.permissions)
            await self.bot.logs.send(embed=embed)
        else:
            pass

    @commands.Cog.listener()
    async def on_presence_update(
        self, before: discord.Member, after: discord.Member
    ) -> None:
        embed = discord.Embed(
            title="Update Presence",
            description=f"{after.mention} has updated their presence.",
            colour=discord.Colour.blue(),
        )
        embed.set_thumbnail(url=after.guild.icon)
        embed.timestamp = discord.utils.utcnow()
        if before.status != after.status:
            embed.add_field(name="Before", value=before.status.name)  # type: ignore
            embed.add_field(name="After", value=after.status.name)  # type: ignore
            await self.bot.logs.send(embed=embed)
        elif before.activity != after.activity:
            embed.add_field(name="Before", value=before.activity.name)
            embed.add_field(name="After", value=after.activity.name)
            await self.bot.logs.send(embed=embed)
        else:
            pass


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Logger(bot))
