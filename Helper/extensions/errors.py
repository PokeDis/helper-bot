import random
import traceback
from io import BytesIO

import discord
import humanfriendly
from discord.ext import commands


class ErrorHandler(commands.Cog, description="Handles errors for the bot."):
    def __init__(self, bot):
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
        if hasattr(ctx, "error_handled"):
            return

        if isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, commands.MissingRequiredArgument):
            desc = f"{ctx.prefix}{ctx.command.name} {ctx.command.signature}"
            inside = self.underline(
                desc, desc.index(f"{error.param.name}"), len(f"{error.param.name}")
            )

            desc = f"\n```ini\n{inside}\n```"
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description=f"Seems like you didn't provide a required argument : `{error.param.name}`{desc}",
                    color=0x2F3136,
                )
            )

        elif isinstance(error, commands.RoleNotFound):
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description=f"Unable to find a role named `{error.argument}`.",
                    color=0x2F3136,
                )
            )

        elif isinstance(error, commands.CommandOnCooldown):
            msg = f"This command is on a cooldown! try again in {humanfriendly.format_timespan(error.retry_after)}."
            cooldown_embed = discord.Embed(
                title=random.choice(
                    [
                        "<a:_:1000851617182142535>  Slow down!",
                        "<a:_:1000851617182142535>  You're going a little too fast bud...",
                        "<a:_:1000851617182142535>  Hold your horses!",
                        "<a:_:1000851617182142535>  Woah now, slow it down...",
                        "<a:_:1000851617182142535>  Take a breather...",
                        "<a:_:1000851617182142535>  NEGATORY.",
                    ]
                ),
                description=error.reason if hasattr(error, "reason") else msg,
                color=0x2F3136,
            )
            await ctx.send(embed=cooldown_embed)

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description=f"I see you naughty one, but unfortunately this command requires you to have `{self.perms_parser(error.missing_permissions)}` permissions.",
                    color=0x2F3136,
                ),
            )

        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description=f"I am missing `{self.perms_parser(error.missing_permissions)}` permissions required to run the command.",
                    color=0x2F3136,
                )
            )

        elif isinstance(error, commands.MemberNotFound):
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description=f"Unable to find any member named `{error.argument}` in `{ctx.guild.name}`",
                    color=0x2F3136,
                )
            )

        elif isinstance(error, commands.UserNotFound):
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description=f"Unable to find a user named `{error.argument}`",
                    color=0x2F3136,
                )
            )

        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description=f"No channel named `{error.argument}` found",
                    color=0x2F3136,
                )
            )

        elif isinstance(error, commands.MissingRole):
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description=f"I see you naughty one, but unfortunately this command requires you to have `{error.missing_role}` role.",
                    color=0x2F3136,
                )
            )

        elif isinstance(error, commands.MissingAnyRole):
            roles = ""
            for roleID in error.missing_roles:
                roles += f"<@&{roleID}> "
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description=f"I see you naughty one, but unfortunately this command requires you to have **ANY ONE** of [ {roles}] roles.",
                    color=0x2F3136,
                )
            )

        elif isinstance(error, commands.NotOwner):
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description=f"`{ctx.command.name}` is an owner only command, only bot owner can use it.",
                    color=0x2F3136,
                )
            )

        elif isinstance(error, commands.TooManyArguments):
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description=f"Too many arguments provided.\nUsage : **{ctx.prefix}{ctx.command.name} {self.signature_parser(ctx.command)}**",
                    color=0x2F3136,
                )
            )

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description="This command is disabled",
                    color=0x2F3136,
                )
            )

        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description=f"`{ctx.command.name}` can be used only in DMs",
                    color=0x2F3136,
                )
            )

        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description=f"`{ctx.command.name}` command cannot be used in DMs",
                    color=0x2F3136,
                )
            )

        else:
            await ctx.send(
                embed=discord.Embed(
                    title="<a:_:1000851617182142535>  Error!",
                    description=f"> An unexpected error occurred! Reporting this to my developer...",
                    color=0x2F3136,
                )
            )
            error_type = type(error)
            error_trace = error.__traceback__
            error_lines = traceback.format_exception(error_type, error, error_trace)
            strange_error = "".join(error_lines)
            buffer = BytesIO(strange_error.encode("utf8"))
            channel = self.bot.get_user(730271192778539078)
            await channel.send(file=discord.File(fp=buffer, filename="error.txt"))
            raise error


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
