import asyncio
import io
import re
import typing

import chat_exporter
import discord
from discord.ext import commands


class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction):
        if isinstance(interaction.user, discord.Member):
            if interaction.user.guild_permissions.manage_guild:
                return interaction.user

    @discord.ui.button(
        emoji="🔓",
        label="Re-open",
        style=discord.ButtonStyle.green,
        custom_id="persistent_view:reopen",
    )
    async def reopen_ticket(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ):
        await interaction.message.edit(view=None)
        for key in interaction.channel.overwrites:
            if isinstance(key, discord.Member):
                await interaction.channel.set_permissions(
                    key, read_messages=True, send_messages=True
                )
        view = InsideTicketView()
        embed = discord.Embed(
            description=f"<:tick:1001136782508826777> The ticket has been re-opened by {interaction.user.mention}.\n\n"
            "Click `🔒` to close the ticket.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, view=view)
        self.stop()

    @discord.ui.button(
        emoji="📄",
        label="Transcript",
        style=discord.ButtonStyle.gray,
        custom_id="persistent_view:transcript",
    )
    async def transcript(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        button.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.defer()
        archive_channel = await Ticket.get_archive_channel(interaction)
        embed = discord.Embed(
            description=f"Preparing channel transcript and sending it to {archive_channel.mention}. This may take a few seconds...",
            color=discord.Color.blue(),
        )
        web_msg = await interaction.followup.send(
            embed=embed,
            wait=True,
        )
        await Ticket.export(interaction, web_msg, archive_channel)

    @discord.ui.button(
        emoji="🗑️",
        label="Delete",
        style=discord.ButtonStyle.red,
        custom_id="persistent_view:delete",
    )
    async def delete_ticket(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ):
        await interaction.message.edit(view=None)
        embed = discord.Embed(
            description="Deleting the ticket in 5 seconds...", color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()
        self.stop()


class InsideTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction):
        if isinstance(interaction.user, discord.Member):
            if interaction.user.guild_permissions.manage_guild:
                return interaction.user

    @discord.ui.button(
        emoji="🔒",
        label="Close",
        style=discord.ButtonStyle.red,
        custom_id="persistent_view:close",
    )
    async def close_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        button.disabled = True
        await interaction.message.edit(view=self)
        for key in interaction.channel.overwrites:
            if isinstance(key, discord.Member):
                await interaction.channel.set_permissions(
                    key, read_messages=False, send_messages=False
                )
        view = TicketCloseView()
        embed = discord.Embed(
            description=f"<:tick:1001136782508826777> The ticket has been closed by {interaction.user.mention}.\n\n"
            "Click `🔓` to reopen the ticket.\n"
            "Click `📄` to save the transcript.\n"
            "Click `🗑️` to delete the ticket.",
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed, view=view)
        self.stop()


class TicketCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Create Ticket",
        style=discord.ButtonStyle.green,
        custom_id="persistent_view:create",
    )
    async def create_ticket(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ):
        await interaction.response.defer()
        for text_channel in interaction.guild.text_channels:
            if interaction.user.name.lower() in text_channel.name:
                embed = discord.Embed(
                    description=f"<:no:1001136828738453514> You already have an open ticket. Please head towards {text_channel.mention}.",
                    color=discord.Color.red(),
                )
                return await interaction.followup.send(
                    embed=embed,
                    ephemeral=True,
                )
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                read_messages=False
            )
        }
        channel = await interaction.guild.create_text_channel(
            f"{str(interaction.user)}",
            category=interaction.channel.category,
            overwrites=overwrites,
        )
        await channel.set_permissions(
            interaction.user, read_messages=True, send_messages=True
        )
        a_embed = discord.Embed(
            description=f"<:tick:1001136782508826777> Created ticket. Please head towards {channel.mention}.",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=a_embed, ephemeral=True)
        await Ticket.set_perms(interaction, channel)
        create_time = discord.utils.format_dt(channel.created_at, style="F")
        view = InsideTicketView()
        embed = discord.Embed(title="Support Ticket", color=discord.Color.blue())
        embed.set_thumbnail(url=f"{interaction.user.display_avatar}")
        embed.add_field(name="Time Opened", value=f"{create_time}")
        embed.add_field(name="Opened For", value=str(interaction.user))
        embed.set_footer(
            text="Please be patient while a staff member gets to this ticket."
        )
        message = await channel.send(
            f"{interaction.user.mention}", embed=embed, view=view
        )
        await message.pin()


class Ticket(
    commands.Cog,
    description="Reaction ticket system to provide support & help!\n`<input>` are mandatory and `[input]` are optional.",
):
    def __init__(self, bot) -> None:
        self.bot = bot

    @staticmethod
    async def set_perms(
        inter: typing.Union[commands.Context, discord.Interaction],
        channel: discord.TextChannel,
    ) -> None:
        community_helpers = inter.guild.get_role(998284527908683806)
        if community_helpers:
            await channel.set_permissions(
                community_helpers, read_messages=True, send_messages=True
            )

    @staticmethod
    async def get_archive_channel(
        ctx: typing.Union[commands.Context, discord.Interaction]
    ) -> discord.TextChannel:
        archive_channel = discord.utils.get(
            ctx.guild.text_channels, name="archived-tickets"
        )
        if archive_channel is None:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
            }
            archive_channel = await ctx.guild.create_text_channel(
                "archived-tickets",
                category=ctx.channel.category,
                overwrites=overwrites,
            )
        return archive_channel

    @staticmethod
    async def get_category(
        ctx: typing.Union[commands.Context, discord.Interaction]
    ) -> discord.CategoryChannel:
        ticket_category = discord.utils.get(ctx.guild.categories, name="TICKETS")
        if ticket_category is None:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
            }
            ticket_category = await ctx.guild.create_category(
                "TICKETS",
                overwrites=overwrites,
            )
        return ticket_category

    @staticmethod
    async def export(
        interaction: typing.Union[commands.Context, discord.Interaction],
        message: discord.Message,
        channel: discord.TextChannel,
    ) -> None:
        transcript = await chat_exporter.export(interaction.channel, tz_info="UTC")
        transcript_file = discord.File(
            io.BytesIO(transcript.encode()), filename=f"{interaction.channel.name}.html"
        )
        await channel.send(f"{interaction.channel.name}", file=transcript_file)
        embed = discord.Embed(
            description="<:tick:1001136782508826777> Done!", color=discord.Color.green()
        )
        await message.edit(embed=embed)

    @commands.group(
        name="ticket",
        help="Creates a ticket for mentioned member",
        invoke_without_command=True,
    )
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def _ticket(
        self, ctx: commands.Context, member: discord.Member
    ) -> typing.Optional[discord.Message]:
        for text_channel in ctx.guild.text_channels:
            if member.name.lower() in text_channel.name:
                embed1 = discord.Embed(
                    description=f"<:no:1001136828738453514> They already have an open ticket. Please head towards {text_channel.mention}.",
                    color=discord.Color.red(),
                )
                return await ctx.send(embed=embed1)
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }
        channel = await ctx.guild.create_text_channel(
            f"{str(member)}",
            category=await self.get_category(ctx),
            overwrites=overwrites,
        )
        await channel.set_permissions(member, read_messages=True, send_messages=True)
        embed2 = discord.Embed(
            description=f"<:tick:1001136782508826777> Created ticket. Please head towards {channel.mention}.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed2)
        await self.set_perms(ctx, channel)
        create_time = discord.utils.format_dt(channel.created_at, style="F")
        view = InsideTicketView()
        embed = discord.Embed(title="Support Ticket", color=discord.Color.blue())
        embed.set_thumbnail(url=f"{member.display_avatar}")
        embed.add_field(name="Time Opened", value=f"{create_time}")
        embed.add_field(name="Opened For", value=str(member))
        embed.set_footer(
            text="Please be patient while a staff member gets to this ticket."
        )
        message = await channel.send(f"{member.mention}", embed=embed, view=view)
        await message.pin()

    @_ticket.command(help="Setup ticket system")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def setup(self, ctx: commands.Context):
        ticket_category = await self.get_category(ctx)
        create_channel = discord.utils.get(
            ctx.guild.text_channels, name="create-ticket"
        )
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
            "<:bullet:1014583675184230511> Mention the reason you opened the ticket for right away or it might get closed.\n"
            "<:bullet:1014583675184230511> Specify the reason descriptively.\n"
            "<:bullet:1014583675184230511> Do not ping any staff or developers. Wait patiently as all tickets will be attended.",
            color=discord.Color.blue(),
        )
        await create_channel.send(embed=embed, view=view)
        await ctx.message.add_reaction("<:tick:1001136782508826777>")

    @_ticket.command(help="Add a member to the ticket")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def add(self, ctx: commands.Context, member: discord.Member):
        discrim = int(re.sub(r"\D+", "", ctx.channel.name) or 0)
        if discrim > 999:
            await ctx.channel.set_permissions(
                member, read_messages=True, send_messages=True
            )
            a_embed = discord.Embed(
                description=f"<:tick:1001136782508826777> Added {member.mention} to {ctx.channel.mention}",
                color=discord.Color.green(),
            )
            await ctx.send(member.mention, embed=a_embed)
            return
        embed = discord.Embed(
            description=f"<:no:1001136828738453514> This channel is not a ticket.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @_ticket.command(help="Remove a member from the ticket")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def remove(self, ctx: commands.Context, member: discord.Member):
        discrim = int(re.sub(r"\D+", "", ctx.channel.name) or 0)
        if discrim > 999:
            await ctx.channel.set_permissions(member, overwrite=None)
            a_embed = discord.Embed(
                description=f"<:tick:1001136782508826777> Removed {member.mention} from {ctx.channel.mention}",
                color=discord.Color.green(),
            )
            await ctx.send(embed=a_embed)
            return
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
    async def transcript(self, ctx: commands.Context):
        discrim = int(re.sub(r"\D+", "", ctx.channel.name) or 0)
        if discrim > 999:
            archive_channel = await self.get_archive_channel(ctx)
            a_embed = discord.Embed(
                description=f"Preparing channel transcript and sending it to {archive_channel.mention}. This may take a few seconds...",
                color=discord.Color.blue(),
            )
            message = await ctx.send(embed=a_embed)
            await self.export(ctx, message, archive_channel)
            return
        embed = discord.Embed(
            description=f"<:no:1001136828738453514> This channel is not a ticket.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    async def cog_load(self):
        print(f"✅ Cog {self.qualified_name} was successfully loaded!")


async def setup(bot) -> None:
    await bot.add_cog(Ticket(bot))
