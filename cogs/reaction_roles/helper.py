import random


def random_circle_emoji(emojis=["🟠", "🟣", "⚫", "🟤", "🔵", "🟡", "🟢", "⚪", "🔴"]):
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
    if (
        guild.id in live_listeners.keys()
        and channel.id in live_listeners[guild.id].keys()
        and message.id in live_listeners[guild.id][channel.id]
    ):
        return live_listeners[guild.id][channel.id][message.id]
    return None
