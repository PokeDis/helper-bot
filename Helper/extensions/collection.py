import difflib
from typing import Optional

import discord
from discord.ext import commands

from ..main import HelperBot
from ..utils import valid_mons, Support


class Collection(
    commands.Cog,
    description="Allows members to keep track of their collectibles.\n`<input>` are mandatory and `[input]` are optional.",
):
    def __init__(self, bot: HelperBot) -> None:
        self.bot = bot

    @commands.group(help="Shows all pokemon collected by a member")
    @commands.guild_only()
    async def collect(self, ctx: commands.Context, member: Optional[discord.Member]) -> Optional[discord.Message]:
        if ctx.invoked_subcommand is None:
            pronoun = "They" if member else "You"
            member = member or ctx.author
            data = await self.bot.db.collection_db.show(member.id)
            if data and data[1]:
                sr_num = [f"{i}. {j.replace('-', ' ').title()}" for i, j in enumerate(data[1], start=1)]
                chunks = list(discord.utils.as_chunks(sr_num, 10))
                embeds = []
                for i, j in enumerate(chunks):
                    embed = discord.Embed(description="\n".join(j), color=discord.Color.blue())
                    embed.set_author(
                        name=f"{ctx.author.name}'s collectibles",
                        icon_url=f"{ctx.author.display_avatar}",
                    )
                    embed.set_footer(text=f"Page {i + 1} of {len(chunks)}")
                    embeds.append(embed)
                await Support().paginate(embeds, ctx)
                return

            embed = discord.Embed(
                description=f"<:no:1001136828738453514> {pronoun} do not have any collectibles set.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @collect.command(help="Add a pokemon to your collectibles")
    @commands.guild_only()
    async def add(
        self, ctx: commands.Context, *, pokemon: str
    ) -> Optional[discord.Message]:
        if (neme_proc := pokemon.strip().lower().replace(" ", "-")) not in valid_mons:
            possible = [
                str(i).replace("-", " ").title()
                for i in difflib.get_close_matches(neme_proc, valid_mons, cutoff=0.5)
            ]
            sr_num = [f"{i}. {j}" for i, j in enumerate(possible, start=1)]
            description = (
                "<:no:1001136828738453514> No such pokemon found.\nDid you mean...\n"
                + "\n".join(sr_num)
            )
            notfound_embed = discord.Embed(
                description=description,
                color=discord.Color.red(),
            )
            return await ctx.send(embed=notfound_embed)

        s = await self.bot.db.collection_db.show(ctx.author.id)
        if s and neme_proc in s[1]:
            embed1 = discord.Embed(
                description=f"<:no:1001136828738453514> This pokemon is already in your collectibles.",
                color=discord.Color.red(),
            )
            return await ctx.send(embed=embed1)

        await self.bot.db.collection_db.add(ctx.author.id, neme_proc)
        embed2 = discord.Embed(
            description=f"<:tick:1001136782508826777> Successfully Added `{neme_proc}` to your collectibles.",
            color=discord.Color.green(),
        )
        embed2.timestamp = discord.utils.utcnow()
        return await ctx.send(embed=embed2)

    @collect.command(help="Remove a pokemon from your collectibles")
    @commands.guild_only()
    async def remove(
        self, ctx: commands.Context, *, pokemon: str
    ) -> Optional[discord.Message]:
        if (neme_proc := pokemon.strip().lower().replace(" ", "-")) not in valid_mons:
            possible = [
                str(i).replace("-", " ").title()
                for i in difflib.get_close_matches(neme_proc, valid_mons, cutoff=0.5)
            ]
            sr_num = [f"{i}. {j}" for i, j in enumerate(possible, start=1)]
            description = (
                "<:no:1001136828738453514> No such pokemon found.\nDid you mean...\n"
                + "\n".join(sr_num)
            )
            notfound_embed = discord.Embed(
                description=description,
                color=discord.Color.red(),
            )
            return await ctx.send(embed=notfound_embed)

        data = await self.bot.db.collection_db.show(ctx.author.id)
        if neme_proc not in data[1]:
            embed1 = discord.Embed(
                description=f"<:no:1001136828738453514> {neme_proc} is not in your collectibles.",
                color=discord.Color.red(),
            )
            return await ctx.send(embed=embed1)

        await self.bot.db.collection_db.remove(ctx.author.id, neme_proc)
        embed2 = discord.Embed(
            description=f"<:tick:1001136782508826777> Successfully removed `{neme_proc}` from your collectibles.",
            color=discord.Color.green(),
        )
        embed2.timestamp = discord.utils.utcnow()
        return await ctx.send(embed=embed2)

    @collect.command(help="Remove all pokemon from your collectibles")
    @commands.guild_only()
    async def clear(
        self, ctx: commands.Context
    ) -> Optional[discord.Message]:
        await self.bot.db.collection_db.delete_record(ctx.author.id)
        embed = discord.Embed(
            description=f"<:tick:1001136782508826777> Successfully cleared your collectibles.",
            color=discord.Color.green(),
            timestamp = discord.utils.utcnow(),
        )
        await ctx.send(embed=embed)

    @collect.command(help="Shows all members who collect a pokemon")
    @commands.guild_only()
    async def search(
        self, ctx: commands.Context, *, pokemon: str
    ) -> Optional[discord.Message]:
        if (neme_proc := pokemon.strip().lower().replace(" ", "-")) not in valid_mons:
            possible = [
                str(i).replace("-", " ").title()
                for i in difflib.get_close_matches(neme_proc, valid_mons, cutoff=0.5)
            ]
            sr_num = [f"{i}. {j}" for i, j in enumerate(possible, start=1)]
            description = (
                "<:no:1001136828738453514> No such pokemon found.\nDid you mean...\n"
                + "\n".join(sr_num)
            )
            notfound_embed = discord.Embed(
                description=description,
                color=discord.Color.red(),
            )
            return await ctx.send(embed=notfound_embed)

        if (s := await self.bot.db.collection_db.get_by_pokemon(neme_proc)):
            sr_no = [f"{i}. <@{j}>" for i, j in enumerate(s, start=1)]
            chunks = list(discord.utils.as_chunks(sr_no, 10))
            embeds = []
            for i, j in enumerate(chunks):
                embed = discord.Embed(
                    title=f"{neme_proc} Collectors",
                    description="\n".join(j),
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"Page {i + 1} of {len(chunks)}")
                embeds.append(embed)
            await Support().paginate(embeds, ctx)
            return

        sad_embed = discord.Embed(
            description=f"<:no:1001136828738453514> There's no `{neme_proc}` collector yet.",
            color=discord.Color.red()
        )
        await ctx.send(embed=sad_embed)

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")


async def setup(bot: HelperBot) -> None:
    await bot.add_cog(Collection(bot))
