import discord
import difflib

from discord.ext import commands
from typing import Optional

from ..main import HelperBot
from ..utils.logistics import Support


async def can_edit_tag(ctx: commands.Context, tag_owner: int) -> bool:
    if (ctx.author.id == tag_owner) or (ctx.author.guild_permissions.manage_guild):
        return True

    else:
        embed = discord.Embed(
            title="<a:_:1000851617182142535>  Nu Uh!",
            description=f"> This tag is not owned by you.",
            colour=0x2F3136,
        )
        await ctx.send(embed=embed)
        return False


class Tag(
    commands.Cog,
    description="Tag related commands.\n`<input>` are mandatory and `[input]` are optional.",
):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot

    @commands.hybrid_group(
        brief="Tag to display",
        help="Tag to display."
    )
    @commands.guild_only()
    async def tag(self, ctx: commands.Context, *, name: str) -> None:
        if not (tag_data := await self.bot.tag_db.get_tag(name)):
            s = await self.bot.tag_db.get_all()
            matches = difflib.get_close_matches(name, s)
            no_matches = discord.Embed(
                title=":mag:  Nu Uh!",
                description=f"> No such tag found.",
                colour=0x2F3136,
            )
            if len(matches):
                sr_num = []
                count = 1
                for elem in matches:
                    new_elem = f"{count}. {elem}"
                    sr_num.append(new_elem)
                    count += 1
                newline = "\n"
                description = "Did you mean...\n"
                for tag in sr_num:
                    description += f"> {tag}{newline}"
                    embed = discord.Embed(
                        title=":mag:  No such tag found",
                        description=description, 
                        color=0x2F3136
                    )
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=no_matches)
        else:
            await ctx.send(tag_data[2])

    @tag.command(
        brief="Searches for a tag",
        help="Searches for a tag."
    )
    @commands.guild_only()
    async def search(self, ctx: commands.Context, name: str) -> None:
        s = await self.bot.tag_db.get_all()
        matches = []
        for tag_name in s:
            if name in tag_name:
                matches.append(name)
        no_matches = discord.Embed(
            title=":mag:  Nu Uh!",
            description=f"> No tags matching {name} found.",
            colour=0x2F3136,
        )
        if len(matches):
            sr_num = []
            count = 1
            for elem in matches:
                new_elem = f"{count}. {elem}"
                sr_num.append(new_elem)
                count += 1
            chunks = list(discord.utils.as_chunks(sr_num, 2))
            embeds = []
            newline = "\n"
            for chunk in chunks:
                index = chunks.index(chunk)
                description = ""
                counter = 1
                for tag in chunk:
                    description += f"{tag}{newline}"
                    embed = discord.Embed(
                        description=description, 
                        color=0x2F3136
                    )
                    counter += 1
                    embed.set_author(name=f"Tags matching {name}", icon_url=f"{ctx.author.display_avatar}")
                    embed.set_footer(text=f"Page {index+1} of {len(chunks)}")
                embeds.append(embed)
            if len(embeds) > 1:
                await Support().paginate(embeds, ctx)
            else:
                for page in embeds:
                    await ctx.send(embed=page)
        else:
            await ctx.send(embed=no_matches)

    @tag.command(
        brief="Lists all tags",
        help="Lists all tags."
    )
    @commands.guild_only()
    async def all(self, ctx: commands.Context) -> None:
        s = await self.bot.tag_db.get_all()
        sr_num = []
        count = 1
        for elem in s:
            new_elem = f"{count}. {elem}"
            sr_num.append(new_elem)
            count += 1
        chunks = list(discord.utils.as_chunks(sr_num, 2))
        embeds = []
        newline = "\n"
        for chunk in chunks:
            index = chunks.index(chunk)
            description = ""
            counter = 1
            for tag in chunk:
                description += f"{tag}{newline}"
                embed = discord.Embed(
                    description=description, 
                    color=0x2F3136
                )
                counter += 1
                embed.set_footer(text=f"Page {index+1} of {len(chunks)}")
            embeds.append(embed)
        await Support().paginate(embeds, ctx)

    @tag.command(
        brief="Lists all tags that belong to you or someone else",
        help="Lists all tags that belong to you or someone else.",
        name="list"
    )
    @commands.guild_only()
    async def _list(self, ctx: commands.Context, member: Optional[discord.Member]):
        pronoun = "They" if member else "You"
        member = member or ctx.author
        s = await self.bot.tag_db.get_from_user(member.id)
        no_tags = discord.Embed(
            title=":mag:  Nu Uh!",
            description=f"> {pronoun} haven't published any tags.",
            colour=0x2F3136,
        )
        if len(s):
            sr_num = []
            count = 1
            for elem in s:
                new_elem = f"{count}. {elem}"
                sr_num.append(new_elem)
                count += 1
            chunks = list(discord.utils.as_chunks(sr_num, 2))
            embeds = []
            newline = "\n"
            for chunk in chunks:
                index = chunks.index(chunk)
                description = ""
                counter = 1
                for tag in chunk:
                    description += f"{tag}{newline}"
                    embed = discord.Embed(
                        description=description, 
                        color=0x2F3136
                    )
                    counter += 1
                    embed.set_author(name=f"{str(member.name)}'s tags", icon_url=f"{member.display_avatar}")
                    embed.set_footer(text=f"Page {index+1} of {len(chunks)}")
                embeds.append(embed)
            if len(embeds) > 1:
                await Support().paginate(embeds, ctx)
            else:
                for page in embeds:
                    await ctx.send(embed=page)
        else:
            await ctx.send(embed=no_tags)

    @tag.command(
        brief="Add a new tag",
        help="Add a new tag."
    )
    @commands.guild_only()
    async def add(self, ctx: commands.Context, name: str, *, content: str) -> None:
        s = await self.bot.tag_db.get_tag(name)
        if s:
            embed1 = discord.Embed(
                title="<a:_:1000851617182142535>  Tag submission failed!",
                description=f"> This tag already exists.",
                colour=0x2F3136,
            )
            return await ctx.send(embed=embed1)

        await self.bot.tag_db.add_tag(ctx.author.id, name, content)
        embed2 = discord.Embed(
            title="<a:_:1000859478217994410>  Created Tag",
            description=f"> New tag `{name}` successfully created.",
            color=0x2F3136,
        )
        embed2.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed2)

    @tag.command(
        brief="Delete an existing tag",
        help="Delete an existing tag."
    )
    @commands.guild_only()
    async def delete(self, ctx: commands.Context, *, tag: str) -> None:
        if not (tag_data := await self.bot.tag_db.get_tag(tag)):
            embed1 = discord.Embed(
                title="<a:_:1000851617182142535>  Oops! Something wasn't right",
                description=f"> Tag named {tag} does not exist.",
                colour=0x2F3136,
            )
            return await ctx.send(embed=embed1)

        if not await can_edit_tag(ctx, tag_data[0]):
            return

        await self.bot.tag_db.delete_tag(tag)
        embed2 = discord.Embed(
            title="<a:_:1000859478217994410>  Deleted Tag",
            description=f"> Tag `{tag}` successfully deleted.",
            color=0x2F3136,
        )
        embed2.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed2)

    @tag.command(
        brief="Edit an existing tag",
        help="Edit an existing tag."
    )
    @commands.guild_only()
    async def update(self, ctx: commands.Context, name: str, *, content: str) -> None:
        if not (tag_data := await self.bot.tag_db.get_tag(name)):
            embed1 = discord.Embed(
                title="<a:_:1000851617182142535>  Oops! Something wasn't right",
                description=f"> Tag named {name} does not exist.",
                colour=0x2F3136,
            )
            return await ctx.send(embed=embed1)

        if not await can_edit_tag(ctx, tag_data[0]):
            return

        await self.bot.tag_db.update_tag(name, content)
        embed2 = discord.Embed(
            title="<a:_:1000859478217994410>  Updated Tag",
            description=f"> Tag `{name}` successfully updated.",
            color=0x2F3136,
        )
        embed2.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed2)


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Tag(bot))
