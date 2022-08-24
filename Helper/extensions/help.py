from itertools import starmap

import discord
from discord.ext import commands, menus

from ..main import HelperBot
from ..utils import Support


class HelpPageSource(menus.ListPageSource):
    def __init__(self, data, helpcommand, mode, cog_check: bool = False):
        super().__init__(data, per_page=25)
        self.helpcommand = helpcommand
        self.mode = mode
        self.cog_check = cog_check
        self.holder = []

    def format_command_help(self, no, command):
        prefix = self.helpcommand.context.prefix
        name = command.qualified_name
        signature = str(command.signature).lower().replace("=none", "")
        docs = command.short_doc or "Command is not documented."
        if signature:
            return f"> ‣ **{prefix}{name}** `{signature}` - {docs}"
        else:
            return f"> ‣ **{prefix}{name}** - {docs}"

    async def format_page(self, menu, entries, num, curr_page):
        iterator = starmap(self.format_command_help, enumerate(entries, start=1))
        page_content = "\n".join(iterator)
        new_line_and_pgno = "\n" + f"Page {curr_page} of {num}"
        desc = ""
        if self.cog_check:
            cog = {k.lower(): k for k, v in menu.context.bot.cogs.items()}
            cog = cog[self.mode.lower()]
            cog_ = menu.context.bot.get_cog(cog)
            desc = data if (data := cog_.description) else "No description found..."

        embed = discord.Embed(
            title=f"{self.mode.title()} Command"
            if not self.cog_check
            else f"{cog} Commands",
            description=f"{desc}\n\n{page_content}",
            color=0x2F3136,
        )
        author = menu.context.author
        embed.set_footer(
            text=f"Requested by {author} {new_line_and_pgno}",
            icon_url=author.display_avatar,
        )
        self.holder.append(embed)
        return embed


class MyHelp(commands.MinimalHelpCommand):
    async def send_bot_help(self, mapping):
        filtered = lambda i: self.filter_commands(i, sort=False)
        category_wise = {
            k: x
            for k, v in self.context.bot.cogs.items()
            if (x := await filtered(v.get_commands()))
        }
        formatting = lambda x, y, num, z: HelpPageSource(
            x, self, y, cog_check=True
        ).format_page(self, x, num, z)
        category_formatter = [
            await formatting(v, k, len(category_wise), i)
            for i, (k, v) in enumerate(category_wise.items(), start=1)
        ]
        await Support().paginate(category_formatter, self.context)

    async def send_cog_help(self, cog):
        if len(subcommands := cog.get_commands()) == 0:
            return await self.send_empty_cog_help(cog)
        filtered = await self.filter_commands(subcommands, sort=True)
        formatter = await HelpPageSource(
            filtered, self, f"{cog.qualified_name}", cog_check=True
        ).format_page(self, filtered, 1, 1)
        await Support().paginate([formatter], self.context)

    async def send_group_help(self, group):
        # if len(subcommands := group.commands) == 0:
        #     return await self.send_command_help(group)
        # filtered = await self.filter_commands(subcommands, sort=True)
        # filtered.insert(0, group)
        # formatter = await HelpPageSource(filtered, self, f"{group.qualified_name}").format_page(self, filtered, 1, 1)
        # await Support().paginate([formatter], self.context)
        if len(subcommands := group.commands) == 0:
            return await self.send_command_help(group)
        filtered = await self.filter_commands(subcommands, sort=True)
        filtered.insert(0, group)
        chunks = list(discord.utils.as_chunks(filtered, 6))
        embeds = []
        for chunk in chunks:
            embeds.append(
                await HelpPageSource(
                    chunk, self, f"{group.qualified_name}"
                ).format_page(self, chunk, len(chunks), len(embeds) + 1)
            )
        await Support().paginate(embeds, self.context)

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
        embed = discord.Embed(
            color=0x2F3136,
            title=f"{command.qualified_name.title()} Command",
        )
        if command.description:
            embed.description = f"{command.description}\n\n{command.help}"
        else:
            embed.description = command.help or "No help found..."
        embed.add_field(
            name="Usage",
            value=f"```{self.get_command_signature(command).lower().replace('=none', '')}```",
        )
        if command.aliases:
            embed.add_field(name="Aliases", value=f"```{', '.join(command.aliases)}```")
        embed.set_footer(
            text=f"Requested by {self.context.author}",
            icon_url=self.context.author.display_avatar,
        )
        await self.context.send(embed=embed)


async def setup(bot: HelperBot) -> None:
    bot.help_command = MyHelp()
