import asyncio
import random
import discord
import re

from datetime import datetime, timedelta
from discord.ext import commands

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
        try:
            await interaction.response.defer()
            data = await self.bot.db.giveaway_db.get_giveaway(interaction.message.id)
            if interaction.user.id in data[1]:
                view = GiveawayLeaveView(self.bot, interaction.message.id)
                await interaction.followup.send("leave bancho", view=view, ephemeral=True)
            else:
                end_time = data[4]
                relative_time = discord.utils.format_dt(end_time, style="R")
                full_time = discord.utils.format_dt(end_time, style="f")
                for embed in interaction.message.embeds:
                    description = embed.to_dict()["description"]
                    host = self.bot.get_user(
                        int(re.findall('<@!?([0-9]+)>', description)[0])
                    )
                updated_embed = discord.Embed(
                    title=f"{data[3]}",
                    description=f"""
                    Ends: {relative_time} ({full_time})
                    Hosted by: {host.mention}
                    Entries: {len(data[1]) + 1}
                    Winners: {data[2]}
                    """,
                )
                updated_embed.timestamp = end_time
                await self.bot.db.giveaway_db.giveaway_entry_add(
                    interaction.message.id, interaction.user.id
                )
                await interaction.edit_original_message(embed=updated_embed)
                await interaction.followup.send("joined bancho", ephemeral=True)
        except Exception as e:
            print(e)


class GiveawayLeaveView(discord.ui.View):
    def __init__(self, bot, message_id: int):
        super().__init__(timeout=30)
        self.bot = bot
        self.message_id = message_id

    @discord.ui.button(
        label="Leave Giveaway",
        style=discord.ButtonStyle.red,
        custom_id="persistent_view:join",
    )
    async def leave_giveaway(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.bot.db.giveaway_db.giveaway_entry_remove(
            self.message_id, interaction.user.id
        )
        await interaction.edit_original_message("left bancho", ephemeral=True)


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
                Hosted by: {ctx.author.mention}
                Entries: 0
                Winners: {winners}
                """,
            )
            embed.timestamp = end_time
            message = await ctx.send(embed=embed, view=view)
            await self.bot.db.giveaway_db.giveaway_start(
                message.id, winners, prize, end_time
            )
            await asyncio.sleep(duration.total_seconds())
            data = await self.bot.db.giveaway_db.get_giveaway(message.id)
            if len(data[1]) >= data[2]:
                winner_list = random.sample(data[1], k=data[2])
                await ctx.send(winner_list)
                await self.bot.db.giveaway_db.end_giveaway(message.id)
                return
            await ctx.send("no. of ppl joined < no. of winners to be declared.")
            # await self.bot.db.giveaway_db.end_giveaway(message.id)
        else:
            await ctx.send(
                "You cannot create a giveaway which lasts for more then 2 weeks."
            )


async def setup(bot) -> None:
    await bot.add_cog(Giveaway(bot))
