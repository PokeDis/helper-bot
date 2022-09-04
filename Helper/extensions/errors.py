import random
import traceback

import discord
from discord.ext import commands

from ..main import HelperBot


class ErrorHandler(commands.Cog, description="Handles errors for the bot."):
    def __init__(self, bot: HelperBot):
        self.bot = bot

    @staticmethod
    def underline(text, at, for_):
        underline = (" " * at) + ("^" * for_)
        return text + "\n" + underline

    @staticmethod
    def signature_parser(cmd) -> str:
        command_signature = ""
        for arg in cmd.signature.split(" ")[: len(cmd.params) - 2]:
            if "=" in arg:
                parsed_arg = "{" + arg.split("=")[0].strip("[]<>]") + "}"
            else:
                parsed_arg = "[" + arg.strip("[]<>") + "]"
                if parsed_arg == "[]":
                    parsed_arg = ""
            command_signature += parsed_arg + " "
        return command_signature

    @staticmethod
    def perms_parser(perms: list) -> str:
        return f"`{'` , `'.join(perms).title().replace('guild','server').replace('_',' ')}`"

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error: Exception):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            desc = f"{ctx.prefix}{ctx.command.name} {ctx.command.signature}"
            print(error.param.name)
            inside = self.underline(
                desc, desc.index(f"{error.param.name}"), len(f"{error.param.name}")
            )
            desc = f"\n```ini\n{inside}\n```"
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:no:1001136828738453514> Seems like you didn't provide a required argument : `{error.param.name}`{desc}",
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:no:1001136828738453514> Unable to find a role named `{error.argument}`",
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.CommandOnCooldown):
            cooldown_embed = discord.Embed(
                title=random.choice(
                    [
                        "<:no:1001136828738453514> Slow down!",
                        "<:no:1001136828738453514> You're going a little too fast bud...",
                        "<:no:1001136828738453514> Hold your horses!",
                        "<:no:1001136828738453514> Noooooo!",
                        "<:no:1001136828738453514> Woah now, slow it down...",
                        "<:no:1001136828738453514> Take a breather...",
                        "<:no:1001136828738453514> NEGATORY.",
                    ]
                ),
                description=f"This command is on a cooldown! try again in `{round(error.retry_after, 2)}` seconds.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=cooldown_embed)
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:no:1001136828738453514> You are missing `{self.perms_parser(error.missing_permissions)}` permissions required to run the command",
                    color=discord.Color.red(),
                ),
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:no:1001136828738453514> I am missing `{self.perms_parser(error.missing_permissions)}` permissions required to run the command",
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(
                    title="<:no:1001136828738453514> Invalid Argument",
                    description=error.args[0],
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:no:1001136828738453514> Unable to find any member named `{error.argument}` in `{ctx.guild.name}`",
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.UserNotFound):
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:no:1001136828738453514> Unable to find a user named `{error.argument}`",
                    color=discord.Color.red(),
                )
            )

        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:no:1001136828738453514> No channel named `{error.argument}` found",
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.MissingRole):
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:no:1001136828738453514> You need `{error.missing_role}` role in order to use this command",
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.NotOwner):
            await ctx.send(
                embed=discord.Embed(
                    title="<:no:1001136828738453514> No No",
                    description=f"`{ctx.command.name}` is an owner only command , only bot owner(s) can use it",
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.TooManyArguments):
            await ctx.send(
                embed=discord.Embed(
                    title=f"<:no:1001136828738453514> Too many arguments provided",
                    description=f"**Usage :** ```\nini{ctx.prefix} {ctx.command.name} {self.signature_parser(ctx.command)}\n```",
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(
                embed=discord.Embed(
                    description="<:no:1001136828738453514> This command is disabled",
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:no:1001136828738453514> `{ctx.command.name}` can be used only in DMs",
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:no:1001136828738453514> `{ctx.command.name}` command cannot be used in DMs",
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.CheckFailure):
            pass
        else:
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:no:1001136828738453514> **An unexpected error occurred! Reporting this to my developer...**",
                    color=discord.Color.red(),
                )
            )
            channel = self.bot.get_channel(
                1012229238415433768
            ) or await self.bot.get_channel(1012229238415433768)
            await channel.send(
                f"```yaml\n{''.join(traceback.format_exception(error, error, error.__traceback__))}\n```"
            )
            print(error)
            raise error


async def setup(bot: HelperBot):
    await bot.add_cog(ErrorHandler(bot))
