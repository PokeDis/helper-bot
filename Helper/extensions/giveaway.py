import asyncio
import random
import discord

from discord.ext import commands
from datetime import datetime, timedelta

from ..utils import DurationCoverter


class GiveawayJoinView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        emoji="🎉",
        style=discord.ButtonStyle.red,
        custom_id="persistent_view:join",
    )
    async def join_giveaway(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        data = await self.bot.db.giveaway_db.get_giveaway(interaction.message.id)
        print(data)
        if interaction.user.id in data[1]:
            view = GiveawayLeaveView(self.bot, interaction.message.id)
            await interaction.followup.send("leave bancho", view=view, ephemeral=True)
        else:
            await self.bot.db.giveaway_db.giveaway_entry_add(interaction.message.id, interaction.user.id)
            await interaction.followup.send("joined bancho", ephemeral=True)


class GiveawayLeaveView(discord.ui.View):
    def __init__(self, bot, message_id: int):
        super().__init__(timeout=30)
        self.bot = bot
        self.message_id = message_id
        self.response = None

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.response.edit(view=self)

    @discord.ui.button(
        label="Leave Giveaway",
        style=discord.ButtonStyle.red,
        custom_id="persistent_view:join",
    )
    async def leave_giveaway(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.bot.db.giveaway_db.giveaway_entry_remove(self.message_id, interaction.user.id)
        await interaction.response.send_message("left bancho")


class Giveaway(commands.Cog, description="Giveaway commands."):
    def __init__(self, bot) -> None:
        self.bot = bot


    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def gstart(
        self,
        ctx: commands.Context,
        winners: int,
        duration: DurationCoverter,
        *,
        prize: str
    ) -> None:
        duration: timedelta = duration  # type: ignore
        view = GiveawayJoinView(self.bot)
        end_time = datetime.now() + timedelta(seconds=duration.total_seconds())
        message = await ctx.send("giveaway bancho", view=view)
        await self.bot.db.giveaway_db.giveaway_start(message.id, winners, prize, end_time)
        await asyncio.sleep(duration.total_seconds())
        data = await self.bot.db.giveaway_db.get_giveaway(message.id)
        if len(data[1]) >= data[2]:
            winner_list = random.sample(data[1], k=data[2])
            await ctx.send(winner_list)
            await self.bot.db.giveaway_db.end_giveaway(message.id)
            return
        await ctx.send("no. of ppl joined < no. of winners to be declared.")
        await self.bot.db.giveaway_db.end_giveaway(message.id)


async def setup(bot) -> None:
    await bot.add_cog(Giveaway(bot))
