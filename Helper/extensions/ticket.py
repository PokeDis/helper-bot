import io
import chat_exporter
import discord
import asyncio

from discord.ext import commands


class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction):
        if "manage_guild" in [key for key, value in (dict(interaction.user.guild_permissions)).items() if value == True]:
            return interaction.user

    @discord.ui.button(emoji="🔓", label='Re-open', style=discord.ButtonStyle.green, custom_id='persistent_view:reopen')
    async def reopen_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.defer()
        for key in interaction.channel.overwrites:
            if isinstance(key, discord.Member):
                await interaction.channel.set_permissions(key, read_messages=True, send_messages=True)
        view = InsideTicketView()
        embed = discord.Embed(
            title="Ticket Re-opened",
            description=f"""
            The ticket has been re-opened by {interaction.user.mention}.\n
            Click `🔒` to close the ticket.
            """,
            color=0x2F3136
        )
        await interaction.edit_original_message(embed=embed, view=view)

    @discord.ui.button(emoji="📄", label='Transcript', style=discord.ButtonStyle.gray, custom_id='persistent_view:transcript')
    async def transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.defer()
        archive_channel = discord.utils.get(interaction.guild.text_channels, name = "archived-tickets")
        if archive_channel is None:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False)
            }
            archive_channel = await interaction.guild.create_text_channel(
                "archived-tickets",
                category=interaction.channel.category,
                overwrites=overwrites
            )
        await interaction.followup.send(f"Preparing channel transcript and sending it to {archive_channel.mention}. This may take a few seconds", ephemeral=False)
        transcript = await chat_exporter.export(interaction.channel, tz_info='UTC')
        transcript_file = discord.File(io.BytesIO(transcript.encode()), filename=f"{interaction.channel.name}.html")
        await archive_channel.send(file=transcript_file)

    @discord.ui.button(emoji="🗑️", label='Delete', style=discord.ButtonStyle.red, custom_id='persistent_view:delete')
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.edit(view=None)
        await interaction.response.send_message("Deleting the ticket in 5 seconds.", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()


class InsideTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction):
        if "manage_guild" in [key for key, value in (dict(interaction.user.guild_permissions)).items() if value == True]:
            return interaction.user

    @discord.ui.button(emoji="🔒", label='Close', style=discord.ButtonStyle.red, custom_id='persistent_view:close')
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        await interaction.message.edit(view=self)
        for key in interaction.channel.overwrites:
            if isinstance(key, discord.Member):
                await interaction.channel.set_permissions(key, read_messages=False, send_messages=False)
        view = TicketCloseView()
        embed = discord.Embed(
            title="Ticket Closed",
            description=f"""
            The ticket has been closed by {interaction.user.mention}.\n
            Click `🔓` to reopen the ticket.
            Click `📄` to save the transcript.
            Click `🗑️` to delete the ticket.
            """,
            color=0x2F3136
        )
        await interaction.response.send_message(embed=embed, view=view)

        
class TicketCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Create Ticket', style=discord.ButtonStyle.green, custom_id='persistent_view:create')
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }
        channel = await interaction.guild.create_text_channel(
            f'{str(interaction.user)}',
            category=interaction.channel.category,
            overwrites=overwrites
        )
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await interaction.followup.send(f"Created ticket. Please head towards {channel.mention}.", ephemeral=True)
        community_helpers = interaction.guild.get_role(998284527908683806)
        if community_helpers:
            await channel.set_permissions(community_helpers, read_messages=True, send_messages=True)
        create_time = discord.utils.format_dt(channel.created_at, style="F")
        view = InsideTicketView()
        embed = discord.Embed(
            title="Support Ticket",
            color=0x2F3136
        )
        embed.set_thumbnail(url=f"{interaction.user.display_avatar}")
        embed.add_field(name="Time Opened", value=f"{create_time}")
        embed.add_field(name="Opened For", value=str(interaction.user))
        embed.set_footer(text="Please be patient while a staff member gets to this ticket.")
        message = await channel.send(embed=embed, view=view)
        await message.pin()


class Ticket(commands.Cog, description="Tag related commands."):
    def __init__(self, bot) -> None:
        self.bot = bot


    @commands.command(
        brief="Setup Ticket System",
        help="Setup Ticket System."
    )
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def tsetup(self, ctx: commands.Context):
        view = TicketCreateView()
        embed = discord.Embed(
            title="Support Ticket",
            description="""
            <:_:1000864068506230855> Opening tickets without reason will result in penalties.
            <:_:1000864068506230855> Mention the reason you opened the ticket for right away or it might get closed.
            <:_:1000864068506230855> Specify the reason descriptively.
            <:_:1000864068506230855> Do not ping any staff or developers. Wait patiently as all tickets will be attended.
            """,
            color=0x2F3136,
        )
        await ctx.send(embed=embed, view=view)

    # @commands.command(
    #     brief="Add a member to the ticket",
    #     help="Add a member to the ticket"
    # )


async def setup(bot) -> None:
    await bot.add_cog(Ticket(bot))
