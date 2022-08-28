import asyncio
import random
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks

from ..utils import DurationCoverter


class GiveawayJoinView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @staticmethod
    async def make_base_embed(bot, message_id: int) -> discord.Embed:
        data = await bot.db.giveaway_db.get_giveaway(message_id)
        time = datetime.fromtimestamp(data[4])
        relative_time = discord.utils.format_dt(time, style="R")
        full_time = discord.utils.format_dt(time, style="f")
        user = bot.get_user(data[5]) or await bot.fetch_user(data[5])
        embed = discord.Embed(
            title=f"{data[3]}",
            description=f"""
                        Ends: {relative_time} ({full_time})
                        Hosted by: {user.mention}
                        Entries: {len(data[1])}
                        Winners: {data[2]}
                        """,
        )
        embed.timestamp = datetime.fromtimestamp(data[4])
        return embed

    @discord.ui.button(
        emoji="🎉",
        style=discord.ButtonStyle.red,
        custom_id="persistent_view:join",
    )
    async def join_giveaway(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ):
        await interaction.response.defer()
        check = await self.bot.db.giveaway_db.giveaway_click(
            interaction.message.id, interaction.user.id
        )
        if check:
            await interaction.followup.send("Joined the giveaway!", ephemeral=True)
        else:
            await interaction.followup.send("Left the giveaway.", ephemeral=True)
        embed = await self.make_base_embed(self.bot, interaction.message.id)
        await interaction.edit_original_response(embed=embed)


class Giveaway(commands.Cog, description="Giveaway commands."):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def gstart(
        self,
        ctx: commands.Context,
        hoster: discord.Member,
        winners: int,
        duration: DurationCoverter,
        *,
        prize: str,
    ) -> None:
        duration: timedelta = duration  # type: ignore
        if duration.total_seconds() < 1209600:
            view = GiveawayJoinView(self.bot)
            end_time = datetime.now() + timedelta(seconds=duration.total_seconds())
            relative_time = discord.utils.format_dt(end_time, style="R")
            full_time = discord.utils.format_dt(end_time, style="f")
            embed = discord.Embed(
                title=f"{prize}",
                description=f"""
                Ends: {relative_time} ({full_time})
                Hosted by: {hoster.mention}
                Entries: 0
                Winners: {winners}
                """,
            )
            embed.timestamp = end_time
            message = await ctx.send(embed=embed, view=view)
            await self.bot.db.giveaway_db.giveaway_start(
                message.id,
                winners,
                prize,
                end_time.timestamp(),
                hoster.id,
                ctx.channel.id,
            )
            await asyncio.sleep(duration.total_seconds())
            data = await self.bot.db.giveaway_db.get_giveaway(message.id)
            if not data[7]:
                if len(data[1]) >= data[2]:
                    winner_list = random.sample(data[1], k=data[2])
                    await ctx.send(", ".join(map(str, winner_list)))
                    await self.bot.db.giveaway_db.update_bool(message.id)
                    return
                await ctx.send(""":boom: I couldn't determine a winner for that giveaway...
                **Reason:** Less number of people joined than winners to be declared.
                """)
                await self.bot.db.giveaway_db.end_giveaway(message.id)
            else:
                pass
        else:
            await ctx.send(
                "You cannot create a giveaway which lasts for more then 2 weeks."
            )

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def gend(
        self,
        ctx: commands.Context,
        message_id: int
    ) -> None:
        data = await self.bot.db.giveaway_db.get_giveaway(message_id)
        if len(data) and not data[7]:
            if len(data[1]) >= data[2]:
                winner_list = random.sample(data[1], k=data[2])
                await ctx.send(", ".join(map(str, winner_list)))
                await self.bot.db.giveaway_db.update_bool(message_id)
                return
            await ctx.send(""":boom: I couldn't determine a winner for that giveaway...
            **Reason:** Less number of people joined than winners to be declared.
            """)
            await self.bot.db.giveaway_db.end_giveaway(message_id)
        else:
            await ctx.send(""":boom: I couldn't determine a winner for that giveaway...
            **Reason:** Giveaway might already have been ended! Please re-check `message_id`.
            """)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def greroll(
        self,
        ctx: commands.Context,
        message_id: int
    ) -> None:
        data = await self.bot.db.giveaway_db.get_giveaway(message_id)
        if len(data) and data[7]:
            await ctx.send(f"{random.choice(data[1])}")
            return
        await ctx.send(""":boom: I couldn't determine a winner for that giveaway...
        **Reason:** Giveaway might already have been expired! Please re-check `message_id`.
        """)

    @tasks.loop(seconds=20)
    async def update_giveaway(self):
        time = datetime.now()
        records = await self.bot.db.giveaway_db.by_time(time.timestamp())
        for record in records:
            channel = self.bot.get_channel(record[6]) or await self.bot.fetch_channel(
                record[6]
            )
            message = await channel.fetch_message(record[0])
            embed = await GiveawayJoinView.make_base_embed(self.bot, record[0])
            await message.edit(embed=embed)
            if len(record[1]) >= record[2]:
                winner_list = random.sample(record[1], k=record[2])
                await channel.send(", ".join(map(str, winner_list)))
                await self.bot.db.giveaway_db.update_bool(record[0])
            else:
                await channel.send(""":boom: I couldn't determine a winner for that giveaway...
                **Reason:** Less number of people joined than winners to be declared.
                """)
                await self.bot.db.giveaway_db.end_giveaway(message.id)

    @tasks.loop(minutes=30)
    async def delete_giveaway(self):
        time = datetime.now()
        data = await self.bot.db.giveaway_db.all_records()
        for record in data:
            delete_time = datetime.fromtimestamp(record[4]) + timedelta(hours=24)
            left = delete_time - time
            if left.total_seconds() <= 0:
                return await self.bot.db.giveaway_db.end_giveaway(record[0])

    @commands.Cog.listener()
    async def on_ready(self):
        self.update_giveaway.start()
        self.delete_giveaway.start()


async def setup(bot) -> None:
    await bot.add_cog(Giveaway(bot))
