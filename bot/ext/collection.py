import difflib
import typing

import discord
from discord.ext import commands

from bot.core.views.paginators import ClassicPaginator

if typing.TYPE_CHECKING:
    from bot.core import PokeHelper
    from bot.database.models import Collection as CollectionModel


class Collection(commands.Cog):

    """Allows members to keep track of their collectibles."""

    def __init__(self, bot: "PokeHelper") -> None:
        self.bot = bot

    @staticmethod
    def format_name(name: str) -> str:
        return name.strip().lower().replace(" ", "-")

    async def check_mon(self, ctx: commands.Context, mon: str) -> bool:
        if (name := self.format_name(mon)) not in self.bot.pokemons:
            possible = difflib.get_close_matches(name, self.bot.pokemons, n=1)
            if not possible:
                embed = discord.Embed(
                    description=f"<:no:1001136828738453514> {name} is not a valid Pokémon.",
                    color=discord.Color.red(),
                )
                await ctx.send(embed=embed)
                return False
            else:
                desc = ", ".join((f"**{str(i).replace('-', ' ').title()}**" for i in possible))
                embed = discord.Embed(
                    description=f"<:no:1001136828738453514> {name} is not a valid Pokémon. Did you mean {desc}?",
                    color=discord.Color.red(),
                )
                await ctx.send(embed=embed)
                return False
        return True

    @staticmethod
    async def paginate(
        member: discord.Member, ctx: commands.Context, data: "CollectionModel"
    ) -> None | discord.Message:
        sr_num = [f"{i}. {j}" for i, j in enumerate(data.collection, start=1)]
        chunks = list(discord.utils.as_chunks(sr_num, 10))
        embeds = []
        for i, j in enumerate(chunks):
            embed = discord.Embed(description="\n".join(j), color=discord.Color.blue())
            embed.set_author(
                name=f"{member.display_name}'s collection",
                icon_url=f"{member.display_avatar}",
            )
            embeds.append(embed)
        return await ClassicPaginator(ctx, embeds).start()

    @commands.group(help="Shows all pokemon collected by a member")
    @commands.guild_only()
    async def collect(self, ctx: commands.Context, member: discord.Member | None = None) -> None:
        if ctx.invoked_subcommand is None:
            pronoun = "They" if member else "You"
            member = member or ctx.author
            data = await self.bot.db.collections.get_collection(member.id)
            if data is None:
                embed = discord.Embed(
                    description=f"<:no:1001136828738453514> {pronoun} do not have any collectibles set.",
                    color=discord.Color.red(),
                )
                await ctx.send(embed=embed)
                return
            await self.paginate(member, ctx, data)

    @collect.command(help="Add a pokemon to your collectibles")
    @commands.guild_only()
    async def add(self, ctx: commands.Context, *, pokemon: str) -> None | discord.Message:
        if not await self.check_mon(ctx, pokemon):
            return
        await self.bot.db.collections.add_item(ctx.author.id, self.format_name(pokemon))
        embed2 = discord.Embed(
            description=f"<:tick:1001136782508826777> Successfully Added `{self.format_name(pokemon)}` to your collectibles.",
            color=discord.Color.green(),
        )
        embed2.timestamp = discord.utils.utcnow()
        return await ctx.send(embed=embed2)

    @collect.command(help="Remove a pokemon from your collectibles")
    @commands.guild_only()
    async def remove(self, ctx: commands.Context, *, pokemon: str) -> discord.Message | None:
        if not await self.check_mon(ctx, pokemon):
            return
        await self.bot.db.collections.remove_item(ctx.author.id, self.format_name(pokemon))
        embed2 = discord.Embed(
            description=f"<:tick:1001136782508826777> Successfully removed"
            f" `{self.format_name(pokemon)}` from your collectibles.",
            color=discord.Color.green(),
        )
        embed2.timestamp = discord.utils.utcnow()
        return await ctx.send(embed=embed2)

    @collect.command(help="Remove all pokemon from your collectibles")
    @commands.guild_only()
    async def clear(self, ctx: commands.Context) -> discord.Message:
        await self.bot.db.collections.delete_collection(ctx.author.id)
        embed = discord.Embed(
            description=f"<:tick:1001136782508826777> Successfully cleared your collectibles.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        return await ctx.send(embed=embed)

    @collect.command(help="Shows all members who collect a pokemon")
    @commands.guild_only()
    async def search(self, ctx: commands.Context, *, pokemon: str) -> discord.Message | None:
        if not await self.check_mon(ctx, pokemon):
            return
        records = await self.bot.db.collections.get_item_collection(self.format_name(pokemon))
        if not records:
            embed = discord.Embed(
                description=f"<:no:1001136828738453514> No one has collected `{self.format_name(pokemon)}`",
                color=discord.Color.red(),
            )
            return await ctx.send(embed=embed)
        embeds = []
        sr_no = [f"{i}. <@{j.user_id}>" for i, j in enumerate(records, start=1)]
        chunks = list(discord.utils.as_chunks(sr_no, 10))
        for i, j in enumerate(chunks):
            embed = discord.Embed(
                title=f"{self.format_name(pokemon)} Collectors",
                description="\n".join(j),
                color=discord.Color.blue(),
            )
            embeds.append(embed)
        return await ClassicPaginator(ctx, embeds).start()

    async def cog_load(self) -> None:
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")


async def setup(bot: "PokeHelper") -> None:
    await bot.add_cog(Collection(bot))
