import json
import typing

import discord
from discord.ext import commands

from utils.logger import log  # pylint: disable=import-error


# the purpose of this file is to convert values inputted from settings set [setting] [new_value] into something that can be stored into the backend
# example: >settings set example_setting @Role1 would likely store the role ID for @Role1. lets say the ID for @Role1 is 12345. 12345 is stored at the backend
# it also converts values from backend/firestore to client/bot usable values.
# example: when fetching the setting example_setting specified above, it sends back 12345. This is then converted into @Role1
# this will also be used to validate settings

with open(r"firecord\default_config.json") as f:
    DEFAULT_CONFIG = json.load(f)
    SETTINGS_LIST = list(DEFAULT_CONFIG.keys())


def init_converters(self):
    """
    create default converters that don't do anything but return.
    These will be rewritten in almost every case, but it's good to have something to default to so it doesnt just throw errors
    """

    def wrapper(setting):
        def returner(value):
            log.info(
                f"A default converter (and maybe also validator) was called. \tSetting: {setting}\tValue: {input}"
            )
            return value

        return returner

    for setting in SETTINGS_LIST:
        if not hasattr(self, setting):
            setattr(self, setting, wrapper(setting))


class InvalidSetting(Exception):
    """this setting does not exist!"""

    def __init__(self, setting):
        super().__init__(f'The setting "{setting}" does not exist!.')
        self.setting = setting


class ToStoreError(Exception):
    """base exception for ToStoreError and ToClientError"""

    def __init__(self, setting, value):
        super().__init__(
            f'Failed to validate or convert value "{value}" for setting "{setting}".'
        )
        self.setting = setting
        self.value = value


class ToStore:
    """used to verify and convert values. if verification or conversion fails, throw a ToStoreError. values returned are the values that will be stored in firestore"""

    def __init__(self):
        init_converters(self)
        # get a list of all converters
        self._converters = {
            converter: getattr(self, converter)
            for converter in dir(self)
            if callable(getattr(self, converter)) and not converter.startswith("__")
        }

    def convert(self, ctx, setting, value):
        if setting in self._converters.keys():
            return self._converters[setting](ctx, value)
        else:
            raise InvalidSetting(setting)

    def prefix(self, ctx: commands.Context, value: str):
        """for convenience, limit prefix size to greater than 0 and less than or equal to 5. no further conversions"""
        converted = value
        if len(converted) > 0 and len(converted) <= 5:
            return value
        else:
            raise ToStoreError("prefix", value)

    def security(self, ctx: commands.Context, value: str):
        """must be either none, server_manager, admin, or owner. no further conversions."""
        converted = value.lower()
        if converted in ["none", "server_manager", "admin", "owner"]:
            return converted
        else:
            raise ToStoreError("security", value)

    def automath(self, ctx: commands.Context, value: str):
        """take a value similar to yes, y, true, no, n, false. convert it into boolean True or False"""
        converted = value.lower()
        if converted in ["yes", "y", "true", "enable", "enabled"]:
            converted = True
            return converted
        elif converted in ["no", "n", "false", "disable", "disabled"]:
            converted = False
            return converted
        else:
            raise ToStoreError("automath", value)

    def archivecategory(self, ctx: commands.Context, value: str):
        """name or ID of a category. convert to id of category"""
        converted = None
        if isinstance(value, str):
            converted = discord.utils.find(
                lambda cat: cat.name == value or str(cat.id) == value,
                ctx.guild.categories,
            )
            # if converted is still none, attempt again but using lowercase matching
            if converted is None:
                converted = discord.utils.find(
                    lambda cat: cat.name.lower() == value.lower(),
                    ctx.guild.categories,
                )
        elif isinstance(value, discord.CategoryChannel):
            converted = value

        if converted is not None:
            return str(converted.id)
        else:
            raise ToStoreError("archivecategory", value)

    # def jail(self, ctx: commands.Context, value: dict):
    #     """dict of a jail_channel id and jail_role id. convert to dict of jail_channel discord Channel and jail_role Role"""
    #     pass
    #     else:
    #         raise ToStoreError("archivecategory", value)


class ToClient:
    """used to convert/process already validated values for the bot to use or display. returned values will vary, depending on what the setting is used for"""

    def __init__(self):
        init_converters(self)
        # get a list of all converters
        self._converters = {
            converter: getattr(self, converter)
            for converter in dir(self)
            if callable(getattr(self, converter)) and not converter.startswith("__")
        }

    def convert(self, ctx, setting, value):
        if setting in self._converters.keys():
            return self._converters[setting](ctx, value)
        else:
            raise InvalidSetting(setting)

    def prefix(self, ctx: commands.Context, value: str) -> str:
        """no further conversions"""
        return value

    def security(self, ctx: commands.Context, value: str) -> str:
        """no need to capitalize. no further conversions. returns only the value"""
        return value

    def automath(self, ctx: commands.Context, value: bool) -> typing.Tuple[bool, str]:
        """convert to string \"Yes\" or \"No\". returns a tuple with the first value being True or False and the second value being either \"Yes\" or \"No\""""
        return (value, "Yes" if value else "No")

    def archivecategory(
        self, ctx: commands.Context, value: int
    ) -> typing.Union[None, typing.Tuple[int, str, discord.CategoryChannel]]:
        """convert ID to a discord Category. if value is N/A (not set), return None. otherwise, returns a tuple, first being raw int ID from firestore, second being the name of the category, and third being the discord Category object"""
        category = discord.utils.find(
            lambda cat: str(cat.id) == value, ctx.guild.categories
        )

        if value == "N/A" or category is None:
            return (value, "N/A", None)

        return (value, category.name, category)

    def jail(
        self, ctx: commands.Context, value: dict
    ) -> typing.Union[None, typing.Tuple[int, discord.TextChannel]]:
        """convert text channel ID into text channel object. returns a tuple of (id from firestore, discord TextChannel object)"""
        converted = {}
        display = {}
        jail_channel = (
            discord.utils.find(
                lambda c: str(c.id) == value["jail_channel"], ctx.guild.text_channels
            )
            or "N/A"
        )
        jail_role = (
            discord.utils.find(
                lambda r: str(r.id) == value["jail_role"],
                ctx.guild.roles,
            )
            or "N/A"
        )

        converted["jail_channel"] = jail_channel
        converted["jail_role"] = jail_role
        display["jail_channel"] = (
            jail_channel if jail_channel == "N/A" else jail_channel.mention
        )
        display["jail_role"] = jail_role if jail_role == "N/A" else jail_role.mention

        # print(value, converted, display)
        return (value, converted, display)


to_store = ToStore()
to_client = ToClient()