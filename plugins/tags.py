import hikari
import lightbulb

from core.bot import Bot


class Plugin(lightbulb.Plugin):
    def __init__(self) -> None:
        super().__init__("Tags", "Tag related commands.")
        self.bot: Bot


plugin = Plugin()


async def can_edit_tag(context: lightbulb.Context, tag_owner: int) -> bool:
    member_perms = lightbulb.utils.permissions_for(context.member)
    if (
        not (member_perms & hikari.Permissions.MANAGE_GUILD)
        and context.author.id != tag_owner
    ):
        await context.respond("This tag is now owned by you.", reply=True)
        return False

    else:
        return True


@plugin.command
@lightbulb.option(
    "tag", "Tag to display", modifier=lightbulb.OptionModifier.CONSUME_REST
)
@lightbulb.command("tag", "Check, edit and delete tags", pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def _tag(context: lightbulb.Context, tag: str) -> None:
    if not (g_id := context.guild_id):
        return
    if not (tag_data := await plugin.bot.tags_db.get_tag(g_id, tag)):
        await context.respond("No such tag found.", reply=True)
        return

    await context.respond(tag_data[3], reply=True)


@_tag.child
@lightbulb.option(
    "content", "Content of the tag", modifier=lightbulb.OptionModifier.CONSUME_REST
)
@lightbulb.option("name", "Name of the tag")
@lightbulb.command(
    "add", "Create a new tag", aliases=["create", "make"], pass_options=True
)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def add_tag(context: lightbulb.Context, name: str, content: str) -> None:
    if not (g_id := context.guild_id):
        return
    if await plugin.bot.tags_db.get_tag(context.guild_id, name):
        await context.respond("This tag already exists.", reply=True)
        return

    await plugin.bot.tags_db.add_tag(g_id, context.author.id, name, content)
    await context.respond(
        embed=hikari.Embed(
            title="Created Tag",
            description=f"New tag `{name}` created with content: \n\n{content}",
        )
    )


@_tag.child
@lightbulb.option(
    "tag", "The tag to delete.", modifier=lightbulb.OptionModifier.CONSUME_REST
)
@lightbulb.command("delete", "Delete tags.", pass_options=True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def delete_tag(context: lightbulb.Context, tag: str) -> None:
    if not (g_id := context.guild_id):
        return
    if not (tag_data := await plugin.bot.tags_db.get_tag(context.guild_id, tag)):
        await context.respond(f"Tag named {tag} does not exist.", reply=True)
        return

    if not await can_edit_tag(context, tag_data[1]):
        return
    await plugin.bot.tags_db.delete_tag(g_id, tag)
    await context.respond(f"Deleted the {tag} tag.")


@_tag.child
@lightbulb.option(
    "content", "New content of the tag", modifier=lightbulb.OptionModifier.CONSUME_REST
)
@lightbulb.option("name", "Name of tag to update")
@lightbulb.command("update", "Update a tag", pass_options=True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def update_tag(context: lightbulb.Context, name: str, content: str) -> None:
    if not (g_id := context.guild_id):
        return
    if not (tag_data := await plugin.bot.tags_db.get_tag(context.guild_id, name)):
        await context.respond(f"Tag named {name} does not exist.", reply=True)
        return

    if not await can_edit_tag(context, tag_data[1]):
        return
    await plugin.bot.tags_db.update_tag(g_id, name, content)
    await context.respond(
        embed=hikari.Embed(
            title="Updated Tag",
            description=f"Updated tag {name} with new content: \n\n{content}",
        )
    )


def load(bot: Bot) -> None:
    bot.add_plugin(plugin)
