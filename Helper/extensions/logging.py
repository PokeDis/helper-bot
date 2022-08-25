import discord
from discord.ext import commands
from ..main import HelperBot


class Logger(commands.Cog):
    
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        await self.bot.logs.send(f"{member.mention} joined the server.")
        
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        await self.bot.logs.send(f"{member.mention} left the server.")
        
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.content == after.content:
            return
        await self.bot.logs.send(
            f"{before.author.mention} edited their message in {before.channel.mention} from `{before.content}` to `{after.content}`."
        )
        
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        await self.bot.logs.send(
            f"{message.author.mention} deleted their message in {message.channel.mention} from `{message.content}`."
        )
        
    @commands.Cog.listener()
    async def on_message_delete_bulk(self, messages: list[discord.Message]) -> None:
        await self.bot.logs.send(
            f"{len(messages)} messages were deleted in {messages[0].channel.mention}."
        )
        
    @commands.Cog.listener()
    async def on_message_reaction_add(self, reaction: discord.Reaction, user: discord.User) -> None:
        await self.bot.logs.send(
            f"{user.mention} added {reaction.emoji} to {reaction.message.channel.mention} in {reaction.message.author.mention}."
        )
        
    @commands.Cog.listener()
    async def on_message_reaction_remove(self, reaction: discord.Reaction, user: discord.User) -> None:
        await self.bot.logs.send(
            f"{user.mention} removed {reaction.emoji} from {reaction.message.channel.mention} in {reaction.message.author.mention}."
        )
        

async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Logger(bot))
        