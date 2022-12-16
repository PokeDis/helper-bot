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
    async def make_base_embed(bot: "PokeHelper", message_id: int) -> tuple[discord.Embed, discord.Message] | None:
        data = await bot.db.giveaways.get_giveaway(message_id)
        if data is None:
            return
        relative_time = discord.utils.format_dt(data.end_time, style="R")
        full_time = discord.utils.format_dt(data.end_time, style="f")
        embed = discord.Embed(
            description=f"*React with 🎉 to enter!*\n\n"
            f"<:bullet:1014583675184230511> **Hosted by** ◆ <@{data.host_id}>\n"
            f"<:bullet:1014583675184230511> **Prize** ◆ *{data.prize}*\n"
            f"<:bullet:1014583675184230511> **Winners** ◆ `{data.winner_count}`\n"
            f"<:bullet:1014583675184230511> **Entries** ◆ `{len(data.participants)}`\n"
            f"<:bullet:1014583675184230511> **Ends at** ◆ {relative_time} 『{full_time}』",
            color=discord.Color.random(),
        )
        guild = bot.get_guild(data.guild_id) or await bot.fetch_guild(data.guild_id)
        embed.set_author(name=f"{guild.name}'s Giveaway", icon_url=guild.icon)
        embed.set_thumbnail(url=bot.user.display_avatar)
        embed.set_footer(text=f"Giveaway ID: {data.message_id}")
        embed.set_image(url="https://i.imgur.com/UYZatsQ.png")
        embed.timestamp = data.end_time
        channel = guild.get_channel(data.channel_id) or await guild.fetch_channel(data.channel_id)
        message = await channel.fetch_message(data.message_id)
        return embed, message

    @staticmethod
    async def make_after_embed(bot: "PokeHelper", message_id: int) -> discord.Embed | None:
        data = await bot.db.giveaways.get_giveaway(message_id)
        if data is None:
            return
        time = datetime.datetime.now()
        relative_time = discord.utils.format_dt(time, style="R")
        full_time = discord.utils.format_dt(time, style="f")
        embed = discord.Embed(
            description=f"*Giveaway ended!*\n\n"
            f"<:bullet:1014583675184230511> **Hosted by** ◆ <@{data.host_id}>\n"
            f"<:bullet:1014583675184230511> **Prize** ◆ *{data.prize}*\n"
            f"<:bullet:1014583675184230511> **Winners** ◆ `{data.winner_count}`\n"
            f"<:bullet:1014583675184230511> **Entries** ◆ `{len(data.participants)}`\n"
            f"<:bullet:1014583675184230511> **Ended** ◆ {relative_time} 『{full_time}』",
            color=discord.Color.random(),
        )
        embed.set_thumbnail(url=bot.user.display_avatar)
        embed.set_footer(text=f"Giveaway ID: {data.message_id}")
        embed.timestamp = time
        embed.set_image(url="https://i.imgur.com/UYZatsQ.png")
        guild = bot.get_guild(data.guild_id) or await bot.fetch_guild(data.guild_id)
        embed.set_author(name=f"{guild.name}'s Giveaway", icon_url=guild.icon)
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
            joined_embed = discord.Embed(
                title="<:tick:1001136782508826777> Joined Giveaway!", color=discord.Color.green()
            )
            await interaction.followup.send(embed=joined_embed, ephemeral=True)
        else:
            left_embed = discord.Embed(title="<:tick:1001136782508826777> Left Giveaway!", color=discord.Color.green())
            await interaction.followup.send(embed=left_embed, ephemeral=True)
        embed, message = await self.make_base_embed(self.bot, interaction.message.id)
        await message.edit(embed=embed)
