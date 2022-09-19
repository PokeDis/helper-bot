import asyncio
import random
import typing
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks

from ..utils import DurationCoverter, Support


class GiveawayJoinView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @staticmethod
    async def make_base_embed(bot, message_id: int) -> discord.Embed:
        data = await bot.db.giveaway_db.get_giveaway(message_id)
        time = datetime.fromtimestamp(data["end_time"])
        relative_time = discord.utils.format_dt(time, style="R")
        full_time = discord.utils.format_dt(time, style="f")
        embed = discord.Embed(
            title=f"{data['prize']}",
            description=f"<:bullet:1014583675184230511> Ends: {relative_time} ({full_time})\n"
            f"<:bullet:1014583675184230511> Hosted by: <@{data['host']}>\n"
            f"<:bullet:1014583675184230511> Entries: {len(data['participants'])}\n"
            f"<:bullet:1014583675184230511> Winners: {data['winners']}\n",
            color=discord.Color.blue(),
        )
        embed.timestamp = datetime.fromtimestamp(data["end_time"])
        return embed

    @staticmethod
    async def make_after_embed(bot, message_id: int, winner_id: list) -> discord.Embed:
        data = await bot.db.giveaway_db.get_giveaway(message_id)
        time = datetime.now()
        relative_time = discord.utils.format_dt(time, style="R")
        full_time = discord.utils.format_dt(time, style="f")
        embed = discord.Embed(
            title=f"{data['prize']}",
            description=f"<:bullet:1014583675184230511> Ended: {relative_time} ({full_time})\n"
            f"<:bullet:1014583675184230511> Hosted by: <@{data['host']}>\n"
            f"<:bullet:1014583675184230511> Entries: {len(data['participants'])}\n"
            f"<:bullet:1014583675184230511> Winners: {', '.join(map(lambda x: f'<@!{x}>', winner_id))}\n",
            color=discord.Color.blue(),
        )
        embed.timestamp = time
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
            joined_embed = discord.Embed(
                description="Joined the giveaway!", color=discord.Color.blue()
            )
            await interaction.followup.send(embed=joined_embed, ephemeral=True)
        else:
            left_embed = discord.Embed(
                description="Left the giveaway!", color=discord.Color.blue()
            )
            await interaction.followup.send(embed=left_embed, ephemeral=True)
        embed = await self.make_base_embed(self.bot, interaction.message.id)
        await interaction.edit_original_response(embed=embed)


class Giveaway(
    commands.Cog,
    description="Hold giveaways quickly and easily!\n`<input>` are mandatory and `[input]` are optional.",
):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.group(name="giveaway", help="Shows all active giveaways")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def giveaway(self, ctx: commands.Context) -> typing.Optional[discord.Message]:
        if ctx.invoked_subcommand is None:
            data = await self.bot.db.giveaway_db.all_records()
            if not data:
                return await ctx.send("No active giveaways!")
            count = len([1 for _ in data if not data["ended"]])
            embeds = []
            for i in range(0, len(data), 5):
                embed = discord.Embed(
                    title=f"{ctx.guild.name}'s Active Giveaways",
                    description=f"**{count}** active giveaways",
                    color=discord.Color.blue(),
                )
                embed.set_thumbnail(url=ctx.guild.icon)
                for record in data[i : i + 5]:
                    if not record["ended"]:
                        end_at = discord.utils.format_dt(
                            datetime.fromtimestamp(record["end_time"]), style="R"
                        )
                        prize = (
                            record["prize"]
                            if len(record["prize"]) <= 20
                            else record["prize"][0:17] + "..."
                        )
                        message = self.bot.get_channel(record["channel"]).get_partial_message(record["message_id"])
                        embed.add_field(
                            name=f"Giveaway ID: {record['message_id']}",
                            value=f"<:bullet:1014583675184230511> Ends at: {end_at}\n"
                            f"<:bullet:1014583675184230511> Prize: {prize}\n"
                            f"<:bullet:1014583675184230511> Hosted by: <@{record['host']}>\n"
                            f"<:bullet:1014583675184230511> In: <#{record['channel']}>"
                            f"[Click here to visit!]({message.jump_url})",
                            inline=False,
                        )
                embeds.append(embed)
            return await Support().paginate(embeds, ctx)

    @giveaway.command(help="Start a giveaway")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def start(
        self,
        ctx: commands.Context,
        hoster: discord.Member,
        winners: int,
        duration: DurationCoverter,
        *,
        prize: str,
    ) -> None:
        duration: timedelta = duration  # type: ignore
        if duration.total_seconds() <= 1209600 and winners >= 1:
            view = GiveawayJoinView(self.bot)
            end_time = datetime.now() + timedelta(seconds=duration.total_seconds())
            relative_time = discord.utils.format_dt(end_time, style="R")
            full_time = discord.utils.format_dt(end_time, style="f")
            embed = discord.Embed(
                title=f"{prize}",
                description=f"<:bullet:1014583675184230511> Ends: {relative_time} ({full_time})\n"
                f"<:bullet:1014583675184230511> Hosted by: {hoster.mention}\n"
                "<:bullet:1014583675184230511> Entries: 0\n"
                f"<:bullet:1014583675184230511> Winners: {winners}\n",
                color=discord.Color.blue(),
            )
            embed.timestamp = end_time
            message = await ctx.send(embed=embed, view=view)
            view.stop()
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
            if data and not data["ended"]:
                if len(data["participants"]) >= data["winners"]:
                    await self.bot.db.giveaway_db.update_bool(message.id)
                    winner_list = random.sample(data["participants"], k=data["winners"])
                    await message.reply(
                        "Congratulations "
                        + ", ".join(map(lambda x: f"<@!{x}>", winner_list))
                        + f"! You won **{prize}**"
                    )
                    end_embed = await GiveawayJoinView.make_after_embed(
                        self.bot, message.id, winner_list
                    )
                    await message.edit(embed=end_embed, view=None)
                    return
                a_embed = discord.Embed(
                    description="<:no:1001136828738453514> I couldn't determine a winner for that giveaway...\n"
                    "**Reason:** Less number of people joined than winners to be declared.",
                    color=discord.Color.red(),
                )
                c_embed = await GiveawayJoinView.make_after_embed(
                    self.bot, message.id, [self.bot.user.id]
                )
                await message.reply(embed=a_embed)
                await message.edit(embed=c_embed, view=None)
                await self.bot.db.giveaway_db.end_giveaway(message.id)
            else:
                pass
        else:
            b_embed = discord.Embed(
                description="<:no:1001136828738453514> You cannot create a giveaway which lasts for more then 2 weeks or has less than 1 winner.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=b_embed)

    @giveaway.command(help="End a specified giveaway")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def end(self, ctx: commands.Context, message_id: int) -> None:
        data = await self.bot.db.giveaway_db.get_giveaway(message_id)
        if len(data) and not data["ended"]:
            if len(data["participants"]) >= data["winners"]:
                await self.bot.db.giveaway_db.update_bool(message_id)
                channel = self.bot.get_channel(data["channel"]) or await self.bot.fetch_channel(
                    data["channel"]
                )
                message = channel.get_partial_message(data["message_id"])
                winner_list = random.sample(data["participants"], k=data["winners"])
                await message.reply(
                    "Congratulations "
                    + ", ".join(map(lambda x: f"<@!{x}>", winner_list))
                    + f"! You won **{data['prize']}**"
                )
                end_embed = await GiveawayJoinView.make_after_embed(
                    self.bot, message_id, winner_list
                )
                await message.edit(embed=end_embed, view=None)
            else:
                channel = self.bot.get_channel(data["channel"]) or await self.bot.fetch_channel(
                    data["channel"]
                )
                message = channel.get_partial_message(data["message_id"])
                a_embed = discord.Embed(
                    description="<:no:1001136828738453514> I couldn't determine a winner for that giveaway...\n"
                    "**Reason:** Less number of people joined than winners to be declared.",
                    color=discord.Color.red(),
                )
                c_embed = await GiveawayJoinView.make_after_embed(
                    self.bot, message_id, [self.bot.user.id]
                )
                await message.reply(embed=a_embed)
                await message.edit(embed=c_embed, view=None)
                await self.bot.db.giveaway_db.end_giveaway(message_id)
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
    async def reroll(self, ctx: commands.Context, message_id: int) -> None:
        data = await self.bot.db.giveaway_db.get_giveaway(message_id)
        if len(data) and data["ended"]:
            await ctx.send(
                f"Congratulations <@!{random.choice(data['participants'])}>! You are the new winner of **{data['prize']}**"
            )
            return
        embed = discord.Embed(
            description="<:no:1001136828738453514> I couldn't determine a winner for that giveaway...\n"
            "**Reason:** Giveaway might already have been expired! Please re-check `message_id`.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @tasks.loop(seconds=10)
    async def update_giveaway(self):
        time = datetime.now()
        records = await self.bot.db.giveaway_db.by_time(time.timestamp())
        for record in records:
            channel = self.bot.get_channel(record['channel']) or await self.bot.fetch_channel(
                record['channel']
            )
            message = channel.get_partial_message(record['message_id'])
            embed = await GiveawayJoinView.make_base_embed(self.bot, record['message_id'])
            await message.edit(embed=embed)
            if len(record['participants']) >= record['winners']:
                await self.bot.db.giveaway_db.update_bool(record['message_id'])
                winner_list = random.sample(record['participants'], k=record['winners'])
                await message.reply(
                    "Congratulations "
                    + ", ".join(map(lambda x: f"<@!{x}>", winner_list))
                    + f"! You won **{record['prize']}**"
                )
                end_embed = await GiveawayJoinView.make_after_embed(
                    self.bot, record['message_id'], winner_list
                )
                await message.edit(embed=end_embed, view=None)
            else:
                a_embed = discord.Embed(
                    description="<:no:1001136828738453514> I couldn't determine a winner for that giveaway...\n"
                    "**Reason:** Less number of people joined than winners to be declared.",
                    color=discord.Color.red(),
                )
                c_embed = await GiveawayJoinView.make_after_embed(
                    self.bot, record['message_id'], [self.bot.user.id]
                )
                await message.reply(embed=a_embed)
                await message.edit(embed=c_embed, view=None)
                await self.bot.db.giveaway_db.end_giveaway(record['message_id'])

    @tasks.loop(minutes=30)
    async def delete_giveaway(self):
        time = datetime.now()
        data = await self.bot.db.giveaway_db.all_records()
        for record in data:
            delete_time = datetime.fromtimestamp(record['end_time']) + timedelta(hours=24)
            left = delete_time - time
            if left.total_seconds() <= 0:
                return await self.bot.db.giveaway_db.end_giveaway(record['message_id'])

    @update_giveaway.before_loop
    async def before_update_giveaway(self):
        await self.bot.wait_until_ready()
        print("🔃 Started Update Giveaway loop.")

    @delete_giveaway.before_loop
    async def before_delete_giveaway(self):
        await self.bot.wait_until_ready()
        print("🔃 Started Delete Giveaway loop.")

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")
        self.update_giveaway.start()
        self.delete_giveaway.start()


async def setup(bot) -> None:
    await bot.add_cog(Giveaway(bot))
