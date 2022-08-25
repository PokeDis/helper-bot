import io

import discord
from discord.ext import commands
from ..main import HelperBot


class Logger(commands.Cog):
    
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        embed = discord.Embed(title="Join", description=f"{member} has joined the server", colour=discord.Colour.green())
        embed.add_field(name="Name", value=f"{member} [{member.id}]\n{member.mention}", inline=True)
        embed.add_field(name="Joined", value=member.joined_at, inline=True)
        embed.add_field(name="Account Age", value=member.created_at, inline=True)
        embed.add_field(name="Member Count", value=len(member.guild.members), inline=True)
        embed.set_thumbnail(url=member.display_avatar)
        embed.timestamp = discord.utils.utcnow()
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        embed = discord.Embed(title="Leave", description=f"{member} has left the server", colour=discord.Colour.red())
        embed.set_thumbnail(url=member.display_avatar)
        embed.timestamp = discord.utils.utcnow()
        await self.bot.logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        embed = discord.Embed(title="Edit Message", description=f"{after.author} edited their message in {after.channel.mention}.\n[Go to message]({after.jump_url})", colour=discord.Colour.blue())
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
        embed.add_field(name="Before", value=before.content if before.content else "No content")
        embed.add_field(name="After", value=after.content if after.content else "No content")
        await self.bot.logs.send(embed=embed)
        
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        embed = discord.Embed(title="Delete Message", description=f"{message.author} deleted their message in {message.channel.mention}", colour=discord.Colour.red())
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
        embed.add_field(name="Message", value=message.content if message.content else "No content")
        await self.bot.logs.send(embed=embed)


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Logger(bot))
        