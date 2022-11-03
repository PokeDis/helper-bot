import io

import chat_exporter
import discord
from discord.ext import commands


class Conductor:
    @staticmethod
    async def export(
        interaction: commands.Context | discord.Interaction,
        message: discord.Message,
        channel: discord.TextChannel,
    ) -> None:
        transcript = await chat_exporter.export(interaction.channel, tz_info="UTC")
        transcript_file = discord.File(io.BytesIO(transcript.encode()), filename=f"{interaction.channel.name}.html")
        await channel.send(f"{interaction.channel.name}", file=transcript_file)
        embed = discord.Embed(description="<:tick:1001136782508826777> Done!", color=discord.Color.green())
        await message.edit(embed=embed)

    @staticmethod
    async def get_category(ctx: commands.Context | discord.Interaction) -> discord.CategoryChannel:
        ticket_category = discord.utils.get(ctx.guild.categories, name="TICKETS")
        if ticket_category is None:
            overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)}
            ticket_category = await ctx.guild.create_category(
                "TICKETS",
                overwrites=overwrites,
            )
        return ticket_category

    @staticmethod
    async def set_perms(
        inter: commands.Context | discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        community_helpers = inter.guild.get_role(998284527908683806)
        if community_helpers:
            await channel.set_permissions(community_helpers, read_messages=True, send_messages=True)

    @staticmethod
    async def get_archive_channel(ctx: commands.Context | discord.Interaction) -> discord.TextChannel:
        archive_channel = discord.utils.get(ctx.guild.text_channels, name="archived-tickets")
        if archive_channel is None:
            overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)}
            archive_channel = await ctx.guild.create_text_channel(
                "archived-tickets",
                category=ctx.channel.category,
                overwrites=overwrites,
            )
        return archive_channel
