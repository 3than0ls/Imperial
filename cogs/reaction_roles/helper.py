import random
from discord.ext.commands.converter import RoleConverter
from discord.ext.commands.errors import BadArgument, MemberNotFound


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
    if guild.id in live_listeners.keys() and (
        live_listener := live_listeners[guild.id].get(
            f"{channel.id}-{message.id}", None
        )
    ):
        return live_listener
    return None


async def validate_params(ctx, command_info, emoji, role):

    if not emoji.is_usable():
        raise BadArgument(command_info["errors"]["InvalidEmoji"].format(emoji=emoji))

    try:
        role = RoleConverter().convert(ctx, role)
    except MemberNotFound:
        raise BadArgument(command_info["errors"]["RoleError"].format(role=role))

    if invalid_role(role):
        raise BadArgument(
            command_info["errors"]["InvalidRole"].format(role_mention=role.mention)
        )