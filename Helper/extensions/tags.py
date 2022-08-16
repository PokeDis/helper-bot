import discord
from discord.ext import commands

from ..main import HelperBot


async def can_edit_tag(ctx: commands.Context, tag_owner: int) -> bool:
    if (ctx.author.id == tag_owner) or (ctx.author.guild_permissions.manage_guild):
        return True

    else:
        await ctx.reply("This tag is not owned by you.")
        return False


class Tag(commands.Cog, description="Tag related commands."):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot


    @commands.command(
        brief="Tag to display",
        help="Tag to display."
        )
    async def tag(self, ctx: commands.Context, name: str) -> None:
        if not (tag_data := await self.bot.tag_db.get_tag(name)):
            return await ctx.reply("No such tag found.")
        await ctx.reply(tag_data[2])


    @commands.command(
        brief="Add a new tag",
        help="Create a new tag.",
        aliases=["ta", "tagcreate", "tc"]
        )
    async def tagadd(self, ctx: commands.Context, name: str, content: str) -> None:
        if await self.bot.tag_db.get_tag(name):
            return await ctx.reply("This tag already exists.")
        await self.bot.tag_db.add_tag(ctx.author.id, name, content)
        embed=discord.Embed(
            title="<a:_:1000859478217994410>  Created Tag",
            description=f"> New tag `{name}` successfully created.",
            color=0x2F3136)
        embed.timestamp = discord.utils.utcnow()
        await ctx.reply(embed=embed)


    @commands.command(
        brief="Delete an existing tag",
        help="Delete an existing tag.",
        aliases=["td", "tagdelete"]
        )
    async def tagdel(self, ctx: commands.Context, tag: str) -> None:
        if not (tag_data := await self.bot.tag_db.get_tag(tag)):
            return await ctx.reply(f"Tag named {tag} does not exist.")
        if not await can_edit_tag(ctx, tag_data[0]):
            return
        await self.bot.tag_db.delete_tag(tag)
        embed=discord.Embed(
            title="<a:_:1000859478217994410>  Deleted Tag",
            description=f"> Tag `{tag}` successfully deleted.",
            color=0x2F3136)
        embed.timestamp = discord.utils.utcnow()
        await ctx.reply(embed=embed)


    @commands.command(
        brief="Edit an existing tag",
        help="Edit an existing tag.",
        aliases=["tu", "tagedit", "te"]
        )
    async def tagupdate(self, ctx: commands.Context, name: str, content: str) -> None:
        if not (tag_data := await self.bot.tag_db.get_tag(name)):
            return await ctx.reply(f"Tag named {name} does not exist.")
        if not await can_edit_tag(ctx, tag_data[0]):
            return
        await self.bot.tag_db.update_tag(name, content)
        embed=discord.Embed(
            title="<a:_:1000859478217994410>  Updated Tag",
            description=f"> Tag `{name}` successfully updated.",
            color=0x2F3136)
        embed.timestamp = discord.utils.utcnow()
        await ctx.reply(embed=embed)


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Tag(bot))
