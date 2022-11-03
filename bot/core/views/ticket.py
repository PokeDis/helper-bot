import asyncio

import discord

from bot.core.helper import Conductor


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
    async def reopen_ticket(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.message.edit(view=None)
        for key in interaction.channel.overwrites:
            if isinstance(key, discord.Member):
                await interaction.channel.set_permissions(key, read_messages=True, send_messages=True)
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
    async def transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.defer()
        archive_channel = await Conductor.get_archive_channel(interaction)
        embed = discord.Embed(
            description=f"Preparing channel transcript and sending it to {archive_channel.mention}."
            f" This may take a few seconds...",
            color=discord.Color.blue(),
        )
        web_msg = await interaction.followup.send(
            embed=embed,
            wait=True,
        )
        await Conductor.export(interaction, web_msg, archive_channel)

    @discord.ui.button(
        emoji="🗑️",
        label="Delete",
        style=discord.ButtonStyle.red,
        custom_id="persistent_view:delete",
    )
    async def delete_ticket(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.message.edit(view=None)
        embed = discord.Embed(description="Deleting the ticket in 5 seconds...", color=discord.Color.red())
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
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        await interaction.message.edit(view=self)
        for key in interaction.channel.overwrites:
            if isinstance(key, discord.Member):
                await interaction.channel.set_permissions(key, read_messages=False, send_messages=False)
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
    async def create_ticket(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.defer()
        for text_channel in interaction.guild.text_channels:
            if interaction.user.name.lower() in text_channel.name:
                embed = discord.Embed(
                    description=f"<:no:1001136828738453514> You already have an open ticket."
                    f" Please head towards {text_channel.mention}.",
                    color=discord.Color.red(),
                )
                return await interaction.followup.send(
                    embed=embed,
                    ephemeral=True,
                )
        overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False)}
        channel = await interaction.guild.create_text_channel(
            f"{str(interaction.user)}",
            category=interaction.channel.category,
            overwrites=overwrites,
        )
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        a_embed = discord.Embed(
            description=f"<:tick:1001136782508826777> Created ticket. Please head towards {channel.mention}.",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=a_embed, ephemeral=True)
        await Conductor.set_perms(interaction, channel)
        create_time = discord.utils.format_dt(channel.created_at, style="F")
        view = InsideTicketView()
        embed = discord.Embed(title="Support Ticket", color=discord.Color.blue())
        embed.set_thumbnail(url=f"{interaction.user.display_avatar}")
        embed.add_field(name="Time Opened", value=f"{create_time}")
        embed.add_field(name="Opened For", value=str(interaction.user))
        embed.set_footer(text="Please be patient while a staff member gets to this ticket.")
        message = await channel.send(f"{interaction.user.mention}", embed=embed, view=view)
        await message.pin()
