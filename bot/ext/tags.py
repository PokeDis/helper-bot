import difflib
import typing

import discord
from discord.ext import commands

from bot.core.views.paginators import ClassicPaginator
from bot.database import Tag

if typing.TYPE_CHECKING:
    from bot.core import PokeHelper


class Tags(commands.Cog):
    """Commands to create tags for quick notes."""

    INVALIDTAG: discord.Embed = discord.Embed(
        description=f"<:no:1001136828738453514> Tag does not exist.",
        color=discord.Color.red(),
    )

    def __init__(self, bot: "PokeHelper") -> None:
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
    async def paginate(matches: list, ctx: commands.Context, name: str | None = None) -> None | discord.Message:
        name = name or "All"
        sr_num = [f"**{i}〉** {j}" for i, j in enumerate(matches, start=1)]
        chunks = list(discord.utils.as_chunks(sr_num, 10))
        embeds = []
        for j in chunks:
            embed = discord.Embed(description="\n".join(j), color=discord.Color.blue())
            embed.set_author(
                name=f"Tags matching {name}",
                icon_url=f"{ctx.author.display_avatar}",
            )
            embeds.append(embed)
        return await ClassicPaginator(ctx, embeds).start()

    @commands.group(
        help="Tag to display",
        invoke_without_command=True,
    )
    @commands.guild_only()
    async def tag(self, ctx: commands.Context, *, name: str) -> None:
        tag_data = await self.bot.db.tags.get_tag(name)
        if tag_data is None:
            tags = await self.bot.db.tags.get_all_tags
            matches = difflib.get_close_matches(name, [tag.title for tag in tags])
            if matches:
                sr_num = "\n".join([f"**{i}〉** {j}" for i, j in enumerate(matches, start=1)])
                description = f"<:no:1001136828738453514> No such tag found.\nDid you mean...\n{sr_num}"
                embed = discord.Embed(
                    description=description,
                    color=discord.Color.red(),
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(
                    embed=discord.Embed(
                        description=f"<:no:1001136828738453514> No such tag found.",
                        color=discord.Color.red(),
                    )
                )
        else:
            user = self.bot.get_user(tag_data.user_id) or await self.bot.fetch_user(tag_data.user_id)
            embed = discord.Embed(description=tag_data.content, color=discord.Color.random())
            embed.set_author(name=tag_data.title, icon_url=user.display_avatar)
            embed.set_thumbnail(url=self.bot.user.display_avatar)
            await ctx.send(embed=embed)

    @tag.command(help="Searches for a tag")
    @commands.guild_only()
    async def search(self, ctx: commands.Context, name: str) -> None:
        tags = await self.bot.db.tags.get_all_tags
        matches = [i.title for i in tags if i.title.lower() == name.lower()]
        if matches:
            await self.paginate(matches, ctx, name)
            return
        await ctx.send(
            embed=discord.Embed(
                description=f"<:no:1001136828738453514> No tags matching {name} found.",
                color=discord.Color.red(),
            )
        )

    @tag.command(help="Lists all tags")
    @commands.guild_only()
    async def all(self, ctx: commands.Context) -> None:
        tags = await self.bot.db.tags.get_all_tags
        if tags:
            await self.paginate([i.title for i in tags], ctx)
            return
        await ctx.send(
            embed=discord.Embed(
                description=f"<:no:1001136828738453514> No tags published yet.",
                color=discord.Color.red(),
            )
        )

    @tag.command(
        help="Lists all tags that belong to you or someone else",
        name="list",
    )
    @commands.guild_only()
    async def _list(self, ctx: commands.Context, member: discord.Member | None):
        pronoun = "They" if member else "You"
        member = member or ctx.author
        tags = await self.bot.db.tags.get_user_tags(member.id)
        if tags:
            await self.paginate([i.title for i in tags], ctx, f"{member.display_name}'s tags")
        else:
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:no:1001136828738453514> {pronoun} haven't published any tags.",
                    color=discord.Color.red(),
                )
            )

    @tag.command(help="Add a new tag")
    @commands.guild_only()
    async def add(self, ctx: commands.Context, name: str, *, content: str) -> discord.Message | None:
        tag = await self.bot.db.tags.get_tag(name)
        if tag is not None:
            embed1 = discord.Embed(
                description=f"<:no:1001136828738453514> This tag already exists.",
                color=discord.Color.red(),
            )
            return await ctx.send(embed=embed1)

        await self.bot.db.tags.add_tag(Tag(ctx.author.id, name, content))
        embed2 = discord.Embed(
            description=f"<:tick:1001136782508826777> New tag `{name}` successfully created.",
            color=discord.Color.green(),
        )
        embed2.timestamp = discord.utils.utcnow()
        return await ctx.send(embed=embed2)

    @tag.command(help="Delete an existing tag")
    @commands.guild_only()
    async def delete(self, ctx: commands.Context, *, name: str) -> discord.Message | None:
        tag_data = await self.bot.db.tags.get_tag(name)
        if tag_data is None:
            return await ctx.send(embed=self.INVALIDTAG)
        if not await self.can_edit_tag(ctx, tag_data.user_id):
            return None
        await self.bot.db.tags.delete_tag(name)
        embed2 = discord.Embed(
            description=f"<:tick:1001136782508826777> Tag `{name}` successfully deleted.",
            color=discord.Color.green(),
        )
        embed2.timestamp = discord.utils.utcnow()
        return await ctx.send(embed=embed2)

    @tag.command(help="Edit/update an existing tag")
    @commands.guild_only()
    async def update(self, ctx: commands.Context, name: str, *, content: str) -> discord.Message | None:
        tag_data = await self.bot.db.tags.get_tag(name)
        if tag_data is None:
            return await ctx.send(embed=self.INVALIDTAG)
        if not await self.can_edit_tag(ctx, tag_data.user_id):
            return None
        await self.bot.db.tags.update_tag(name, content)
        embed2 = discord.Embed(
            description=f"<:tick:1001136782508826777> Tag `{name}` successfully updated.",
            color=discord.Color.green(),
        )
        embed2.timestamp = discord.utils.utcnow()
        return await ctx.send(embed=embed2)

    async def cog_load(self) -> None:
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")


async def setup(bot: "PokeHelper") -> None:
    await bot.add_cog(Tags(bot))
