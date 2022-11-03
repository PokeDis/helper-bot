import typing

import discord
import humanfriendly
from discord.ext import commands

from bot.core.views.paginators import ClassicPaginator, SelectPaginator

if typing.TYPE_CHECKING:
    from bot.core import PokeHelper


class Formatter:
    def __init__(self, helpcommand: commands.MinimalHelpCommand) -> None:
        self.ctx = helpcommand.context
        self.helpcommand = helpcommand

    def __format_command_signature(self, command: commands.Command) -> tuple[str, str]:
        params = self.__format_param(command)
        return f"{command.qualified_name}\n", f"```yaml\n{params}```"

    def __format_param(self, param: commands.Command) -> str:
        signature = self.helpcommand.get_command_signature(param)
        return signature

    @staticmethod
    def __format_command_help(command: commands.Command) -> str:
        return command.help or "No help provided."

    @staticmethod
    def __format_command_aliases(command: commands.Command) -> str:
        return f"```yaml\nAliases: {', '.join(command.aliases)}```" if command.aliases else "No aliases."

    @staticmethod
    def __format_command_cooldown(command: commands.Command) -> str:
        return (
            f"Cooldown: {humanfriendly.format_timespan(command.cooldown.per, max_units=2)} per user."
            if command.cooldown
            else "No cooldown set."
        )

    @staticmethod
    def __format_command_enabled(command: commands.Command) -> str:
        return f"Enabled: {command.enabled}" if command.enabled else "Command is disabled."

    @staticmethod
    def __format_command_description(command: commands.Command) -> str:
        return command.description or "No description provided."

    def format_command(self, command: commands.Command) -> discord.Embed:
        signature = self.__format_command_signature(command)
        embed = discord.Embed(
            title=signature[0],
            description=signature[1] + self.__format_command_help(command),
            color=discord.Color.blue(),
        )
        embed.add_field(name="Aliases", value=self.__format_command_aliases(command), inline=True)
        embed.add_field(name="Cooldown", value=self.__format_command_cooldown(command), inline=True)
        embed.add_field(name="Enabled", value=self.__format_command_enabled(command), inline=True)
        embed.set_footer(
            text=f"Requested by {self.ctx.author}",
            icon_url=self.ctx.author.display_avatar,
        )
        embed.set_thumbnail(url=self.ctx.bot.user.display_avatar)
        return embed

    async def format_pages(
        self,
        pages: dict[str, list[commands.Command]],
        desc: list[str],
        home: bool = False,
    ) -> dict[str, list[discord.Embed]]:
        embeds = {"Home": [await self.home_page]} if home else {}
        for num, (name, allcommand) in enumerate(pages.items()):
            for i in range(0, len(allcommand), 8):
                embed = discord.Embed(
                    title=f"{name} Commands",
                    description=desc[num],
                    color=discord.Color.blue(),
                )
                for command in allcommand[i : i + 8]:
                    signature = self.__format_command_signature(command)
                    embed.add_field(
                        name=signature[0],
                        value=signature[1] + self.__format_command_help(command),
                        inline=False,
                    )
                embed.set_thumbnail(url=self.ctx.bot.user.display_avatar)
                embeds.setdefault(name, []).append(embed)
        return embeds

    @property
    async def home_page(self) -> discord.Embed:
        embed = discord.Embed(
            title="Home",
            description="*Welcome to the home page of the bot.*\n\n",
            color=discord.Color.random(),
        )
        for k, v in sorted(self.ctx.bot.cogs.items(), key=lambda c: c[0][0]):
            if len(v.get_commands()) == 0:
                continue
            embed.add_field(name=f"{k}", value=f"*{v.description or 'No description provided.'}*", inline=False)
        embed.set_thumbnail(url=self.ctx.bot.user.display_avatar)
        return embed


class MyHelp(commands.MinimalHelpCommand):
    async def send_bot_help(self, mapping: typing.Mapping[commands.Cog | None, list[commands.Command]]):
        category = {}
        categorydesc = []
        mapping = {
            k: v
            for k, v in sorted(
                mapping.items(),
                key=lambda c: c[0].qualified_name[0] if c[0] else "\u200bMisc",
            )
        }
        for cog, allcommand in mapping.items():
            filtered = await self.filter_commands(allcommand, sort=True, key=lambda c: c.qualified_name[0])
            if cog is None or len(filtered) == 0:
                continue
            for command in filtered:
                category.setdefault(cog.qualified_name, []).append(command)
                if isinstance(command, commands.Group):
                    category.setdefault(cog.qualified_name, []).extend(command.commands)
            categorydesc.append(cog.description or "No description provided.")
        formatter = await Formatter(self).format_pages(category, categorydesc, home=True)
        await SelectPaginator(self.context, formatter).start()

    async def send_cog_help(self, cog: commands.Cog):
        filtered = await self.filter_commands(cog.get_commands(), sort=True, key=lambda c: c.qualified_name)
        if len(filtered) == 0:
            return await self.send_empty_cog_help(cog)
        desc = cog.description or "No description provided."
        formatter = await Formatter(self).format_pages({cog.qualified_name: filtered}, [desc])
        await ClassicPaginator(self.context, formatter[cog.qualified_name]).start()

    async def send_group_help(self, group):
        filtered = await self.filter_commands(group.commands, sort=True, key=lambda c: c.qualified_name)
        if len(filtered) == 0:
            return await self.no_such_command(group.qualified_name)
        desc = group.cog.description or "No description provided."
        formatter = await Formatter(self).format_pages({group.qualified_name: filtered}, [desc])
        await ClassicPaginator(self.context, formatter[group.qualified_name]).start()

    async def send_empty_cog_help(self, cog):
        embed = discord.Embed(
            color=discord.Color.blue(),
            title=f"{cog.qualified_name.title()} Category",
        )
        embed.set_thumbnail(url=self.context.bot.user.display_avatar)
        embed.description = "*No such category found...*"
        embed.set_footer(
            text=f"Requested by {self.context.author}",
            icon_url=self.context.author.display_avatar,
        )
        await self.context.send(embed=embed)

    async def no_such_command(self, command):
        embed = discord.Embed(
            color=discord.Color.blue(),
            title=f"{command.title()} Command",
        )
        embed.set_thumbnail(url=self.context.bot.user.display_avatar)
        embed.description = "*No such command found...*"
        embed.set_footer(
            text=f"Requested by {self.context.author}",
            icon_url=self.context.author.display_avatar,
        )
        await self.context.send(embed=embed)

    async def send_command_help(self, command):
        filtered = await self.filter_commands([command], sort=True, key=lambda c: c.qualified_name)
        if len(filtered) == 0:
            return await self.no_such_command(command.qualified_name)
        formatter = Formatter(self).format_command(command)
        await self.context.send(embed=formatter)


async def setup(bot: "PokeHelper") -> None:
    bot.help_command = MyHelp(verify_checks=False)
