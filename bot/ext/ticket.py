import re
import typing

import discord
from discord.ext import commands

from bot.core.helper import Conductor
from bot.core.views import InsideTicketView, TicketCreateView

if typing.TYPE_CHECKING:
    from bot.core import PokeHelper


class Ticket(commands.Cog):

    """Reaction ticket system to provide support & help!"""

    def __init__(self, bot: "PokeHelper") -> None:
        self.bot = bot

    @commands.group(
        name="ticket",
        help="Creates a ticket for mentioned member",
        invoke_without_command=True,
    )
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def _ticket(self, ctx: commands.Context, member: discord.Member) -> discord.Message | None:
        for text_channel in ctx.guild.text_channels:
            if member.name.lower() in text_channel.name:
                embed1 = discord.Embed(
                    description=f"<:no:1001136828738453514> They already have an open ticket."
                    f" Please head towards {text_channel.mention}.",
                    color=discord.Color.red(),
                )
                return await ctx.send(embed=embed1)
        overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)}
        channel = await ctx.guild.create_text_channel(
            f"{str(member)}",
            category=await Conductor.get_category(ctx),
            overwrites=overwrites,
        )
        await channel.set_permissions(member, read_messages=True, send_messages=True)
        embed2 = discord.Embed(
            description=f"<:tick:1001136782508826777> Created ticket. Please head towards {channel.mention}.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed2)
        await Conductor.set_perms(ctx, channel)
        create_time = discord.utils.format_dt(channel.created_at, style="F")
        view = InsideTicketView()
        embed = discord.Embed(title="Support Ticket", color=discord.Color.blue())
        embed.set_thumbnail(url=f"{member.display_avatar}")
        embed.add_field(name="Time Opened", value=f"{create_time}")
        embed.add_field(name="Opened For", value=str(member))
        embed.set_footer(text="Please be patient while a staff member gets to this ticket.")
        message = await channel.send(f"{member.mention}", embed=embed, view=view)
        await message.pin()

    @_ticket.command(help="Setup ticket system")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def setup(self, ctx: commands.Context) -> discord.Message | None:
        ticket_category = await Conductor.get_category(ctx)
        create_channel = discord.utils.get(ctx.guild.text_channels, name="create-ticket")
        if create_channel:
            embed = discord.Embed(
                description="<:no:1001136828738453514> You already seem to have an active setup.\n"
                f"If you wish to create a new setup, please delete {create_channel.mention}",
                color=discord.Color.red(),
            )
            return await ctx.send(embed=embed)
        create_channel = await ticket_category.create_text_channel("create-ticket")
        view = TicketCreateView()
        embed = discord.Embed(
            title="Support Ticket",
            description="<:bullet:1014583675184230511> Opening tickets without reason will result in penalties.\n"
            "<:bullet:1014583675184230511> Mention the reason you opened the ticket for right away.\n"
            "<:bullet:1014583675184230511> Specify the reason descriptively.\n"
            "<:bullet:1014583675184230511> Do not ping any staff or developers."
            " Wait patiently as all tickets will be attended.",
            color=discord.Color.blue(),
        )
        await create_channel.send(embed=embed, view=view)
        await ctx.message.add_reaction("<:tick:1001136782508826777>")

    @_ticket.command(help="Add a member to the ticket")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def add(self, ctx: commands.Context, member: discord.Member) -> discord.Message | None:
        discrim = int(re.sub(r"\D+", "", ctx.channel.name) or 0)
        if discrim > 999:
            await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
            a_embed = discord.Embed(
                description=f"<:tick:1001136782508826777> Added {member.mention} to {ctx.channel.mention}",
                color=discord.Color.green(),
            )
            return await ctx.send(member.mention, embed=a_embed)
        embed = discord.Embed(
            description=f"<:no:1001136828738453514> This channel is not a ticket.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @_ticket.command(help="Remove a member from the ticket")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def remove(self, ctx: commands.Context, member: discord.Member) -> discord.Message | None:
        discrim = int(re.sub(r"\D+", "", ctx.channel.name) or 0)
        if discrim > 999:
            await ctx.channel.set_permissions(member, overwrite=None)
            a_embed = discord.Embed(
                description=f"<:tick:1001136782508826777> Removed {member.mention} from {ctx.channel.mention}",
                color=discord.Color.green(),
            )
            return await ctx.send(embed=a_embed)
        embed = discord.Embed(
            description=f"<:no:1001136828738453514> This channel is not a ticket.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @_ticket.command(
        help="Generate transcript of the ticket",
    )
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def transcript(self, ctx: commands.Context) -> discord.Message | None:
        discrim = int(re.sub(r"\D+", "", ctx.channel.name) or 0)
        if discrim > 999:
            archive_channel = await Conductor.get_archive_channel(ctx)
            a_embed = discord.Embed(
                description=f"Preparing channel transcript and sending it to {archive_channel.mention}."
                f" This may take a few seconds...",
                color=discord.Color.blue(),
            )
            message = await ctx.send(embed=a_embed)
            return await Conductor.export(ctx, message, archive_channel)
        embed = discord.Embed(
            description=f"<:no:1001136828738453514> This channel is not a ticket.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    async def cog_load(self) -> None:
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")


async def setup(bot: "PokeHelper") -> None:
    await bot.add_cog(Ticket(bot))
