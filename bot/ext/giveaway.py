import asyncio
import datetime
import random
import typing

import discord
from discord.ext import commands, tasks

from bot.core.helper import DurationConvertor
from bot.core.views import GiveawayJoinView
from bot.core.views.paginators import ClassicPaginator
from bot.database.models import Giveaway as GiveawayModel

if typing.TYPE_CHECKING:
    from bot.core import PokeHelper


class Giveaway(commands.Cog):

    """Host giveaways and events for your server!"""

    def __init__(self, bot: "PokeHelper") -> None:
        self.bot = bot

    async def end_giveaway(self, message: discord.Message, data: GiveawayModel) -> None | discord.Message:
        if data is None:
            return
        if not data.ended:
            await self.bot.db.giveaways.update_bool(message.id)
            if len(data.participants) >= data.winner_count:
                data.winners = random.sample(data.participants, k=data.winner_count)
                await message.reply(
                    "Congratulations "
                    + ", ".join(map(lambda x: f"<@!{x}>", data.winners))
                    + f"! You won **{data.prize}**"
                )
                await self.bot.db.giveaways.update_winners(message.id, list(data.winners))
                end_embed = await GiveawayJoinView.make_after_embed(self.bot, message.id)
                return await message.edit(embed=end_embed, view=None)
            a_embed = discord.Embed(
                description="<:no:1001136828738453514> I couldn't determine a winner for that giveaway...\n"
                "**Reason:** Less number of people joined than winners to be declared.",
                color=discord.Color.red(),
            )
            c_embed = await GiveawayJoinView.make_after_embed(self.bot, message.id)
            await message.reply(embed=a_embed)
            await message.edit(embed=c_embed, view=None)
            await self.bot.db.giveaway_db.end_giveaway(message.id)
        else:
            pass

    @staticmethod
    def format_giveaway_embed(embed: discord.Embed, data: GiveawayModel) -> None:
        end_at = discord.utils.format_dt(data.end_time, style="R")
        embed.add_field(
            name=f"Giveaway ID: {data.message_id}",
            value=f"<:bullet:1014583675184230511> Ends at: {end_at}\n"
            f"<:bullet:1014583675184230511> Prize: {data.prize}\n"
            f"<:bullet:1014583675184230511> Hosted by: <@{data.host_id}>\n"
            f"<:bullet:1014583675184230511> In: <#{data.message_id}>"
            f"[Click here to visit!]"
            f"(https://discord.com/channels/{data.guild_id}/{data.channel_id}/{data.message_id})\n"
            f"<:bullet:1014583675184230511> Entries: {len(data.participants)}\n"
            f"<:bullet:1014583675184230511> Winners: {data.winner_count}\n",
            inline=False,
        )
        embed.timestamp = data.end_time
        return None

    @commands.group(name="giveaway", help="Shows all active giveaways")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def giveaway(self, ctx: commands.Context) -> discord.Message | None:
        if ctx.invoked_subcommand is None:
            data = await self.bot.db.giveaways.get_giveaways(ctx.guild.id)
            if not data:
                return await ctx.send("No giveaways are currently active!")
            embeds = []
            for giveaway in data:
                embed = discord.Embed(
                    title=f"{ctx.guild.name}'s Active Giveaways",
                    description=f"React with 🎉 to enter!\n\n",
                    color=discord.Color.blue(),
                )
                embed.set_footer(text=f"{len(data)} active giveaways")
                self.format_giveaway_embed(embed, giveaway)
                embed.set_thumbnail(url=ctx.guild.icon)
                embeds.append(embed)
            return await ClassicPaginator(ctx, embeds).start()

    @giveaway.command(help="Start a giveaway")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def start(
        self,
        ctx: commands.Context,
        hoster: discord.Member,
        winners: int,
        duration: DurationConvertor,
        *,
        prize: str,
    ) -> None | discord.Message:
        if duration.total_seconds() <= 1209600 and winners >= 1:
            view = GiveawayJoinView(self.bot)
            embed = discord.Embed(
                title="Giveaway",
                description=f"React with 🎉 to enter!\n\n"
                f"Hosted by: {hoster.mention}\n"
                f"Prize: {prize}\n"
                f"Ends at: {discord.utils.format_dt(datetime.datetime.now() + duration, style='R')}",
                color=discord.Color.blue(),
            )
            embed.set_footer(text="Giveaway", icon_url=hoster.avatar)
            embed.timestamp = datetime.datetime.now() + duration
            embed.set_thumbnail(url=ctx.guild.icon)
            message = await ctx.send(embed=embed, view=view)
            await self.bot.db.giveaways.giveaway_start(
                GiveawayModel(
                    message_id=message.id,
                    channel_id=message.channel.id,
                    guild_id=message.guild.id,
                    winner_count=winners,
                    prize=prize,
                    host_id=hoster.id,
                    end_time=datetime.datetime.now() + duration,
                )
            )
            await asyncio.sleep(duration.total_seconds())
            data = await self.bot.db.giveaways.get_giveaway(message.id)
            return await self.end_giveaway(message, data)
        else:
            b_embed = discord.Embed(
                description="<:no:1001136828738453514> You cannot create a giveaway which lasts"
                " for more than 2 weeks or has less than 1 winner.",
                color=discord.Color.red(),
            )
            return await ctx.send(embed=b_embed)

    @giveaway.command(help="End a specified giveaway")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def end(self, ctx: commands.Context, message_id: int) -> discord.Message | None:
        data = await self.bot.db.giveaways.get_giveaway(message_id)
        if data is None:
            return await ctx.reply("That giveaway doesn't exist!")
        if not data.ended:
            channel = self.bot.get_channel(data.channel_id) or await self.bot.fetch_channel(data.channel_id)
            message = await channel.fetch_message(data.message_id)
            return await self.end_giveaway(message, data)
        else:
            b_embed = discord.Embed(
                description="<:no:1001136828738453514> I couldn't determine a winner for that giveaway...\n"
                "**Reason:** Giveaway might already have been expired! Please re-check `message_id`.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=b_embed)

    @giveaway.command(help="Re-rolls a specified giveaway's winner")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def reroll(self, ctx: commands.Context, message_id: int) -> None | discord.Message:
        data = await self.bot.db.giveaways.get_giveaway(message_id)
        if data is None:
            return await ctx.reply("That giveaway doesn't exist!")
        if data.ended:
            return await ctx.send(
                f"Congratulations <@!{random.choice(list(data.participants - data.winners))}>!"
                f" You are the new winner of **{data.prize}**"
            )
        embed = discord.Embed(
            description="<:no:1001136828738453514> I couldn't determine a winner for that giveaway...\n"
            "**Reason:** Giveaway might already have been expired! Please re-check `message_id`.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @tasks.loop(seconds=10)
    async def update_giveaway(self) -> None:
        records = await self.bot.db.giveaways.get_all_giveaway
        for record in records:
            channel = self.bot.get_channel(record.channel_id) or await self.bot.fetch_channel(record.channel_id)
            message = await channel.fetch_message(record.message_id)
            await self.end_giveaway(message, record)

    @tasks.loop(minutes=30)
    async def delete_giveaway(self) -> None:
        records = await self.bot.db.giveaways.giveaway_by_end
        for record in records:
            await self.bot.db.giveaways.end_giveaway(record.message_id)

    @update_giveaway.before_loop
    async def before_update_giveaway(self) -> None:
        await self.bot.wait_until_ready()
        print("🔃 Started Update Giveaway loop.")

    @delete_giveaway.before_loop
    async def before_delete_giveaway(self) -> None:
        await self.bot.wait_until_ready()
        print("🔃 Started Delete Giveaway loop.")

    async def cog_load(self) -> None:
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")
        self.update_giveaway.start()
        self.delete_giveaway.start()


async def setup(bot: "PokeHelper") -> None:
    await bot.add_cog(Giveaway(bot))
