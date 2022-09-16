import difflib
from typing import Optional

import discord
from discord.ext import commands

from ..main import HelperBot
from ..utils import Support


class Tag(
    commands.Cog,
    description="View, create, edit or delete a tag.\n`<input>` are mandatory and `[input]` are optional.",
):

    INVALIDTAG: discord.Embed = discord.Embed(
        description=f"<:no:1001136828738453514> Tag does not exist.",
        color=discord.Color.red(),
    )

    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot

    @staticmethod
    async def can_edit_tag(ctx: commands.Context, tag_owner: int) -> bool:
        if (ctx.author.id == tag_owner) or ctx.author.guild_permissions.manage_guild:
            return True

        else:
            embed = discord.Embed(
                description=f"<:no:1001136828738453514> This tag is not owned by you.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return False

    @staticmethod
    async def paginate(
        matches: list, ctx: commands.Context, name: Optional[str] = None
    ) -> None:
        name = name or "All tags"
        sr_num = [f"{i}. {j}" for i, j in enumerate(matches, start=1)]
        chunks = list(discord.utils.as_chunks(sr_num, 10))
        embeds = []
        for i, j in enumerate(chunks):
            embed = discord.Embed(description="\n".join(j), color=discord.Color.blue())
            embed.set_author(
                name=f"Tags matching {name}",
                icon_url=f"{ctx.author.display_avatar}",
            )
            embed.set_footer(text=f"Page {i + 1} of {len(chunks)}")
            embeds.append(embed)
        await Support().paginate(embeds, ctx)

    @commands.group(
        help="Tag to display",
        invoke_without_command=True,
    )
    @commands.guild_only()
    async def tag(self, ctx: commands.Context, *, name: str) -> None:
        if not (tag_data := await self.bot.db.tag_db.get_tag(name)):
            s = await self.bot.db.tag_db.get_all()
            matches = difflib.get_close_matches(name, s)
            no_matches = discord.Embed(
                description=f"<:no:1001136828738453514> No such tag found.",
                color=discord.Color.red(),
            )
            if matches:
                sr_num = [f"{i}. {j}" for i, j in enumerate(matches, start=1)]
                description = (
                    "<:no:1001136828738453514> No such tag found.\nDid you mean...\n"
                    + "\n".join(sr_num)
                )
                embed = discord.Embed(
                    description=description,
                    color=discord.Color.red(),
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=no_matches)
        else:
            await ctx.send(tag_data[2])

    @tag.command(help="Searches for a tag")
    @commands.guild_only()
    async def search(self, ctx: commands.Context, name: str) -> None:
        s = await self.bot.db.tag_db.get_all()
        matches = [i for i in s if name.lower() in i.lower()]
        no_matches = discord.Embed(
            description=f"<:no:1001136828738453514> No tags matching {name} found.",
            color=discord.Color.red(),
        )
        if matches:
            await self.paginate(matches, ctx, name)
        else:
            await ctx.send(embed=no_matches)

    @tag.command(help="Lists all tags")
    @commands.guild_only()
    async def all(self, ctx: commands.Context) -> None:
        s = await self.bot.db.tag_db.get_all()
        await self.paginate(s, ctx)

    @tag.command(
        help="Lists all tags that belong to you or someone else",
        name="list",
    )
    @commands.guild_only()
    async def _list(self, ctx: commands.Context, member: Optional[discord.Member]):
        pronoun = "They" if member else "You"
        member = member or ctx.author
        s = await self.bot.db.tag_db.get_from_user(member.id)
        no_tags = discord.Embed(
            description=f"<:no:1001136828738453514> {pronoun} haven't published any tags.",
            color=discord.Color.red(),
        )
        if s:
            await self.paginate(s, ctx, f"{member.display_name}'s tags")
        else:
            await ctx.send(embed=no_tags)

    @tag.command(help="Add a new tag")
    @commands.guild_only()
    async def add(
        self, ctx: commands.Context, name: str, *, content: str
    ) -> Optional[discord.Message]:
        s = await self.bot.db.tag_db.get_tag(name)
        if s:
            embed1 = discord.Embed(
                description=f"<:no:1001136828738453514> This tag already exists.",
                color=discord.Color.red(),
            )
            return await ctx.send(embed=embed1)

        await self.bot.db.tag_db.add_tag(ctx.author.id, name, content)
        embed2 = discord.Embed(
            description=f"<:tick:1001136782508826777> New tag `{name}` successfully created.",
            color=discord.Color.green(),
        )
        embed2.timestamp = discord.utils.utcnow()
        return await ctx.send(embed=embed2)

    @tag.command(help="Delete an existing tag")
    @commands.guild_only()
    async def delete(
        self, ctx: commands.Context, *, tag: str
    ) -> Optional[discord.Message]:
        if not (tag_data := await self.bot.db.tag_db.get_tag(tag)):
            return await ctx.send(embed=self.INVALIDTAG)

        if not await self.can_edit_tag(ctx, tag_data[0]):
            return None

        await self.bot.db.tag_db.delete_tag(tag)
        embed2 = discord.Embed(
            description=f"<:tick:1001136782508826777> Tag `{tag}` successfully deleted.",
            color=discord.Color.green(),
        )
        embed2.timestamp = discord.utils.utcnow()
        return await ctx.send(embed=embed2)

    @tag.command(help="Edit/update an existing tag")
    @commands.guild_only()
    async def update(
        self, ctx: commands.Context, name: str, *, content: str
    ) -> Optional[discord.Message]:
        if not (tag_data := await self.bot.db.tag_db.get_tag(name)):
            return await ctx.send(embed=self.INVALIDTAG)

        if not await self.can_edit_tag(ctx, tag_data[0]):
            return None

        await self.bot.db.tag_db.update_tag(name, content)
        embed2 = discord.Embed(
            description=f"<:tick:1001136782508826777> Tag `{name}` successfully updated.",
            color=discord.Color.green(),
        )
        embed2.timestamp = discord.utils.utcnow()
        return await ctx.send(embed=embed2)

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Tag(bot))
