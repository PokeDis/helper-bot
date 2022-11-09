import datetime
import typing

import discord

if typing.TYPE_CHECKING:
    from bot.core import PokeHelper


class GiveawayJoinView(discord.ui.View):
    def __init__(self, bot: "PokeHelper"):
        super().__init__(timeout=None)
        self.bot = bot

    @staticmethod
    async def make_base_embed(bot: "PokeHelper", message_id: int) -> discord.Embed | None:
        data = await bot.db.giveaways.get_giveaway(message_id)
        if data is None:
            return
        relative_time = discord.utils.format_dt(data.end_time, style="R")
        full_time = discord.utils.format_dt(data.end_time, style="f")
        embed = discord.Embed(
            title="Giveaway!",
            description=f"React with 🎉 to enter!\n\n"
            f"Hosted by: <@{data.host_id}>\n"
            f"Prize: {data.prize}\n"
            f"Winners: {data.winner_count}\n"
            f"Entries: {len(data.participants)}\n"
            f"Ends at: {relative_time} ({full_time})\n",
            color=discord.Color.blue(),
        )
        embed.set_footer(text="PokéLore Giveaway")
        embed.timestamp = data.end_time
        return embed

    @staticmethod
    async def make_after_embed(bot: "PokeHelper", message_id: int) -> discord.Embed | None:
        data = await bot.db.giveaways.get_giveaway(message_id)
        if data is None:
            return
        time = datetime.datetime.now()
        relative_time = discord.utils.format_dt(time, style="R")
        full_time = discord.utils.format_dt(time, style="f")
        embed = discord.Embed(
            title="Giveaway!",
            description=f"This giveaway has been ended.\n\n"
            f"Ended: {relative_time} ({full_time})\n"
            f"Hosted by: <@{data.host_id}>\n"
            f"Prize: {data.prize}\n"
            f"Winners: {', '.join(map(lambda x: f'<@!{x}>', data.winners))}\n"
            f"Entries: {len(data.participants)}\n",
            color=discord.Color.blue(),
        )
        embed.set_footer(text="PokéLore Giveaway")
        embed.timestamp = time
        return embed

    @discord.ui.button(
        emoji="🎉",
        style=discord.ButtonStyle.red,
        custom_id="persistent_view:join",
    )
    async def join_giveaway(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.defer()
        check = await self.bot.db.giveaways.giveaway_click(interaction.message.id, interaction.user.id)
        if check:
            joined_embed = discord.Embed(description="Joined the giveaway!", color=discord.Color.blue())
            await interaction.followup.send(embed=joined_embed, ephemeral=True)
        else:
            left_embed = discord.Embed(description="Left the giveaway!", color=discord.Color.blue())
            await interaction.followup.send(embed=left_embed, ephemeral=True)
        embed = await self.make_base_embed(self.bot, interaction.message.id)
        embed.set_thumbnail(url=interaction.message.author.guild.icon.url)
        await interaction.edit_original_response(embed=embed)
