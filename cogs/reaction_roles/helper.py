from firecord import firecord  # pylint: disable=import-error
import random
import discord
from discord.ext.commands.converter import EmojiConverter, RoleConverter
from discord.ext.commands.errors import BadArgument, EmojiNotFound, RoleNotFound
from emoji import UNICODE_EMOJI


def random_circle_emoji(emojis=["🟠", "🟣", "🟤", "🔵", "🟡", "🟢", "⚪", "🔴"]):
    return random.choice(emojis)


def invalid_role(role):
    return (
        role.is_default()
        or role.is_bot_managed()
        or role.is_premium_subscriber()
        or role.is_integration()
    )


def in_live_listeners(message, live_listeners):
    channel = message.channel
    guild = channel.guild
    if str(guild.id) in live_listeners.keys() and (
        live_listener := live_listeners[str(guild.id)].get(
            f"{channel.id}-{message.id}", None
        )
    ):
        return live_listener
    return None


async def validate_params(ctx, command_info, emoji, thing, description):
    if len(description) >= 100:
        raise BadArgument(command_info["errors"]["InvalidDescription"].format())
    emoji_flag = False
    # here we need to check if we can convert the emoji and use it, or alternatively if it's a string if it's a unicode emoji, and if none of those pass
    # set emoji_flag to True which raises an error later
    if isinstance(emoji, discord.Emoji):
        if not emoji.is_usable():
            emoji_flag = True
    elif isinstance(emoji, discord.PartialEmoji):
        emoji_flag = True
    elif isinstance(emoji, str):
        if emoji not in UNICODE_EMOJI["en"]:
            emoji_flag = True

    if emoji_flag:
        raise BadArgument(command_info["errors"]["InvalidEmoji"].format(emoji=emoji))

    try:
        role = await RoleConverter().convert(ctx, str(thing))
        if invalid_role(role):
            raise BadArgument(
                command_info["errors"]["InvalidRole"].format(role_mention=role.mention)
            )
    except RoleNotFound:
        if not firecord.profile_exists(str(ctx.guild.id), thing):
            raise BadArgument(command_info["errors"]["InvalidArg"].format(arg=thing))
