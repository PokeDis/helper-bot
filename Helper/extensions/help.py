import discord
import humanfriendly
from discord.ext import commands

from ..main import HelperBot
from ..utils import Support


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
        return (
            f"```yaml\nAliases: {', '.join(command.aliases)}```"
            if command.aliases
            else "No aliases."
        )

    @staticmethod
    def __format_command_cooldown(command: commands.Command) -> str:
        return (
            f"Cooldown: {humanfriendly.format_timespan(command.cooldown.per)} per user."
            if command.cooldown
            else "No cooldown set."
        )

    @staticmethod
    def __format_command_enabled(command: commands.Command) -> str:
        return (
            f"Enabled: {command.enabled}" if command.enabled else "Command is disabled."
        )

    @staticmethod
    def __format_command_description(command: commands.Command) -> str:
        return command.description or "No description provided."

    def format_command(self, command: commands.Command) -> discord.Embed:
        signature = self.__format_command_signature(command)
        embed = discord.Embed(
            title=signature[0],
            description=signature[1] + self.__format_command_help(command),
            color=0x2F3136,
        )
        embed.add_field(
            name="Aliases", value=self.__format_command_aliases(command), inline=True
        )
        embed.add_field(
            name="Cooldown", value=self.__format_command_cooldown(command), inline=True
        )
        embed.add_field(
            name="Enabled", value=self.__format_command_enabled(command), inline=True
        )
        embed.set_footer(
            text=f"Requested by {self.ctx.author}",
            icon_url=self.ctx.author.display_avatar,
        )
        embed.set_thumbnail(url=self.ctx.bot.user.display_avatar)
        return embed

    def format_pages(
        self, pages: dict[str, list[commands.Command]], desc: list[str]
    ) -> list[discord.Embed]:
        embeds = []
        for num, (name, allcommand) in enumerate(pages.items()):
            embed = discord.Embed(title=name, description=desc[num], color=0x2F3136)
            for command in allcommand:
                signature = self.__format_command_signature(command)
                embed.add_field(
                    name=signature[0],
                    value=signature[1] + self.__format_command_help(command),
                    inline=False
                )
            embed.set_footer(
                text=f"Requested by {self.ctx.author} | Page {num + 1}/{len(pages)}",
                icon_url=self.ctx.author.display_avatar,
            )
            embed.set_thumbnail(url=self.ctx.bot.user.display_avatar)
            embeds.append(embed)
        return embeds


class MyHelp(commands.MinimalHelpCommand):
    async def send_bot_help(self, mapping):
        category = {}
        for k, v in self.context.bot.cogs.items():
            if len((x := v.get_commands())) > 0:
                category[k] = x
        categorydesc = [
            x if (x := i.description) else "No description provided."
            for i in self.context.bot.cogs.values()
            if len(i.get_commands()) > 0
        ]
        formatter = Formatter(self)
        await Support().paginate(
            formatter.format_pages(category, categorydesc), self.context
        )

    async def send_cog_help(self, cog):
        if len(subcommands := cog.get_commands()) == 0:
            return await self.send_empty_cog_help(cog)
        category = {cog.qualified_name: subcommands}
        categorydesc = (
            [cog.description] if cog.description else ["No description provided."]
        )
        formatter = Formatter(self)
        await Support().paginate(
            formatter.format_pages(category, categorydesc), self.context
        )

    async def send_group_help(self, group):
        if len(subcommands := group.all_commands) == 0:
            return await self.send_command_help(group)
        allcommands = list(subcommands.values())
        allcommands.insert(0, group)
        category = {group.qualified_name: allcommands}
        categorydesc = [group.help] if group.help else ["No description provided."]
        formatter = Formatter(self)
        await Support().paginate(
            formatter.format_pages(category, categorydesc), self.context
        )

    async def send_empty_cog_help(self, cog):
        embed = discord.Embed(
            color=0x2F3136,
            title=f"{cog.qualified_name.title()} Category",
        )
        embed.description = "*No such category found...*"
        embed.set_footer(
            text=f"Requested by {self.context.author}",
            icon_url=self.context.author.display_avatar,
        )
        await self.context.send(embed=embed)

    async def send_command_help(self, command):
        formatter = Formatter(self)
        embed = formatter.format_command(command)
        await self.context.send(embed=embed)


async def setup(bot: HelperBot) -> None:
    bot.help_command = MyHelp()
