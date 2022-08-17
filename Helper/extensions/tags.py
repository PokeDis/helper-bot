import discord
from discord.ext import commands

from ..main import HelperBot


async def can_edit_tag(ctx: commands.Context, tag_owner: int) -> bool:
    if (ctx.author.id == tag_owner) or (ctx.author.guild_permissions.manage_guild):
        return True

    else:
        embed = discord.Embed(
            title="<a:_:1000851617182142535>  Nu Uh!",
            description = f"> This tag is not owned by you.",
            colour=0x2F3136
        )
        await ctx.send(embed=embed)
        return False


class Tag(commands.Cog, description="Tag related commands.\n`<input>` are mandatory and `[input]` are optional."):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot


    @commands.hybrid_command(
        brief="Tag to display",
        help="Tag to display."
        )
    @commands.guild_only()
    async def tag(self, ctx: commands.Context, name: str) -> None:
        if not (tag_data := await self.bot.tag_db.get_tag(name)):
            return await ctx.send("No such tag found.")
            
        await ctx.send(tag_data[2])


    @commands.hybrid_command(
        brief="Add a new tag",
        help="Create a new tag.",
        aliases=["ta", "tagcreate", "tc"]
        )
    @commands.guild_only()
    async def tagadd(self, ctx: commands.Context, name: str, content: str) -> None:
        if await self.bot.tag_db.get_tag(name):
            embed1 = discord.Embed(
                title="<a:_:1000851617182142535>  Tag submission failed!",
                description = f"> This tag already exists.",
                colour=0x2F3136
            )
            return await ctx.send(embed=embed1)

        await self.bot.tag_db.add_tag(ctx.author.id, name, content)
        embed2=discord.Embed(
            title="<a:_:1000859478217994410>  Created Tag",
            description=f"> New tag `{name}` successfully created.",
            color=0x2F3136)
        embed2.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed2)


    @commands.hybrid_command(
        brief="Delete an existing tag",
        help="Delete an existing tag.",
        aliases=["td", "tagdelete"]
        )
    @commands.guild_only()
    async def tagdel(self, ctx: commands.Context, tag: str) -> None:
        if not (tag_data := await self.bot.tag_db.get_tag(tag)):
            embed1 = discord.Embed(
                title="<a:_:1000851617182142535>  Oops! Something wasn't right",
                description = f"> Tag named {tag} does not exist.",
                colour=0x2F3136
            )
            return await ctx.send(embed=embed1)

        if not await can_edit_tag(ctx, tag_data[0]):
            return

        await self.bot.tag_db.delete_tag(tag)
        embed2=discord.Embed(
            title="<a:_:1000859478217994410>  Deleted Tag",
            description=f"> Tag `{tag}` successfully deleted.",
            color=0x2F3136)
        embed2.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed2)


    @commands.hybrid_command(
        brief="Edit an existing tag",
        help="Edit an existing tag.",
        aliases=["tu", "tagedit", "te"]
        )
    @commands.guild_only()
    async def tagupdate(self, ctx: commands.Context, name: str, content: str) -> None:
        if not (tag_data := await self.bot.tag_db.get_tag(name)):
            embed1 = discord.Embed(
                title="<a:_:1000851617182142535>  Oops! Something wasn't right",
                description = f"> Tag named {name} does not exist.",
                colour=0x2F3136
            )
            return await ctx.send(embed=embed1)

        if not await can_edit_tag(ctx, tag_data[0]):
            return

        await self.bot.tag_db.update_tag(name, content)
        embed2=discord.Embed(
            title="<a:_:1000859478217994410>  Updated Tag",
            description=f"> Tag `{name}` successfully updated.",
            color=0x2F3136)
        embed2.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed2)


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Tag(bot))
