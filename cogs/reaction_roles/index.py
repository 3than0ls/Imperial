from datetime import datetime
import typing

import discord
from discord.errors import Forbidden
from discord.ext import commands
from discord.ext.commands.converter import (
    EmojiConverter,
    MemberConverter,
    PartialEmojiConverter,
    RoleConverter,
)
from discord.ext.commands.errors import (
    BadArgument,
    CommandOnCooldown,
    EmojiNotFound,
    NoPrivateMessage,
    RoleNotFound,
)
from firecord import firecord  # pylint: disable=import-error
from utils.dm import dm  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from checks.has_access import has_access  # pylint: disable=import-error
from cogs.reaction_roles.helper import (  # pylint: disable=import-error
    in_live_listeners,
    random_circle_emoji,
    validate_params,
)
import asyncio


class ReactionRoles(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.live_listeners = firecord.rr_map
        self.cache = self.bot.cache

    async def on_ready(self):
        # validate all listeners in live listeners when on ready
        async def pred(guild_id, rr_id):
            try:
                guild = self.bot.get_guild(guild_id)
                channel_id, message_id = rr_id.split("-")
                channel = guild.get_channel(channel_id)
                if channel is None:
                    raise BadArgument()
                else:
                    await channel.fetch_message(message_id)
            except (Forbidden, BadArgument):
                del self.live_listeners[guild_id][rr_id]
                firecord.rr_delete(guild_id, channel_id, message_id)

        for guild_id, rr in self.live_listeners.items():
            asyncio.gather([await pred(guild_id, rr_id) for rr_id in rr.keys()])

    def create_live_listener(self, message: discord.Message, rr_info):
        """
        creates a live listener on the bot (and on the database if it does not exist. reaction role info needs to be stored on database if the bot restarts
        rr_info is an object that contains 2 keys, 'type' (role or profile) and 'data' which is a dictionary mapping emoji to role/profile
        example of an rr_info:
        {
            'type': 'role',
            'data': {
                '🟠': 1234567890 <- role ID
            }
        }
        """
        guild_id = message.guild.id
        channel_id = message.channel.id
        message_id = message.channel.id

        self.live_listeners[guild_id][f"{channel_id}-{message_id}"] = rr_info
        firecord.rr_create(guild_id, channel_id, message_id, rr_info)

    def apply_cooldown(
        self, message, member
    ):  # check if the user is on reaction role cooldown
        now_time = datetime.now()
        if (
            member.id in self.cache[message.guild.id]["rr"][message.id]
            and (
                now_time - self.cache[message.guild.id]["rr"][message.id][member.id]
            ).total_seconds()
            < 5
        ):
            # user has reacted to this within the last 5 seconds, just ignore and
            raise BadArgument(
                "literally the most scuffed and dumbly hacky way because i'm too lazy to create a custom error"
            )
        else:
            self.cache[message.guild.id]["rr"][message.id][member.id] = now_time

    async def receive_payload(self, payload):
        if not hasattr(payload, "guild_id"):
            raise NoPrivateMessage()
        message = await self.bot.get_channel(payload.channel_id).fetch_message(
            payload.message_id
        )

        # if the reaction is just the bot reacting to itself, or if the message isnt from the bot, or if it is DM, skip
        if message.author.id != self.bot.user.id or payload.user_id == self.bot.user.id:
            raise NoPrivateMessage()

        if payload.member is None:
            ctx = await self.bot.get_context(message)
            member = await MemberConverter().convert(ctx, str(payload.user_id))
            return message, payload.emoji, member, ctx
        else:
            return message, payload.emoji, payload.member

    async def get_live_listener(self, ctx, message, emoji):
        live_listener = in_live_listeners(message, self.live_listeners)
        if live_listener is not None and (
            rr_info := live_listener.get(
                str(emoji)
            )  # value is string, either specifying an emoji or a profile name
        ):
            try:
                if rr_info["type"] == "role":
                    assigned_role = await RoleConverter().convert(
                        ctx, str(rr_info["id"])
                    )
                    return rr_info["type"], assigned_role
                elif rr_info["type"] == "profile":
                    assigned_profile = firecord.profile_get(ctx.guild.id, rr_info["id"])
                    if assigned_profile is None:
                        # profile doesnt exist, just raise keyerror to be handled later
                        raise KeyError()
                    return rr_info["type"], assigned_profile.to_dict()

            except (RoleNotFound, KeyError):
                return None, None

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            message, emoji, member = await self.receive_payload(payload)
            self.apply_cooldown(message, payload.member)
        except (NoPrivateMessage, BadArgument):
            return
        ctx = await self.bot.get_context(message)

        _type, _object = await self.get_live_listener(ctx, message, emoji)

        if _type == None:
            return dm(
                member,
                embed=EmbedFactory(
                    {
                        "description": f"The requested role or profile was unable to be assigned, likely because it no longer exists. Ask a server administrator for more information.",
                    },
                    error=True,
                ),
            )
        elif _type == "role":
            await member.add_roles(_object)
        elif _type == "profile":
            roles = member.roles
            member_role_ids = [role.id for role in roles]
            for role_id in _object["profile_roles"]:
                try:
                    if role_id not in member_role_ids:
                        roles.append(await RoleConverter().convert(ctx, str(role_id)))
                except RoleNotFound:
                    pass

            await member.edit(roles=roles)

        await dm(
            member,
            embed=EmbedFactory(
                {
                    "title": f"Reaction {_type.capitalize()} Assigned",
                    "description": f"**Successfully assigned {_type} \"{_object['name'] if _type == 'profile' else _object.name}\"**\nDepending on your roles prior to this, nothing may have changed.",
                    "color": "success",
                }
            ),
        )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        try:
            message, emoji, member, ctx = await self.receive_payload(payload)
            self.apply_cooldown(message, member)
        except (NoPrivateMessage, CommandOnCooldown):
            return

        _type, _object = await self.get_live_listener(ctx, message, emoji)

        if _type == None:
            return dm(
                member,
                embed=EmbedFactory(
                    {
                        "description": f"The requested role or profile was unable to be removed, likely because it no longer exists. Ask a server administrator for more information.",
                    },
                    error=True,
                ),
            )
        elif _type == "role":
            await member.remove_roles(_object)
        elif _type == "profile":
            roles = [
                role for role in member.roles if role.id not in _object["profile_roles"]
            ]
            await member.edit(roles=roles)

        await dm(
            member,
            embed=EmbedFactory(
                {
                    "title": f"Reaction {_type.capitalize()} Removed",
                    "description": f"**Successfully removed {_type} \"{_object['name'] if _type == 'profile' else _object.name}\".**\nDepending on your roles prior to this, nothing may have changed.",
                    "color": "success",
                }
            ),
        )

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        if not hasattr(payload, "guild_id"):
            return

        if (
            payload.guild_id in self.live_listeners
            and f"{payload.channel_id}-{payload.message_id}"
            in self.live_listeners[payload.guild_id]
        ):
            del self.live_listeners[payload.guild_id][
                f"{payload.channel_id}-{payload.message_id}"
            ]
            firecord.rr_delete(payload.guild_id, payload.channel_id, payload.message_id)

    def initialize_rr(self, ctx, channel, message, rr_info):
        firecord.rr_create(ctx.guild.id, channel.id, message.id, rr_info)
        if ctx.guild.id not in self.live_listeners:
            self.live_listeners[ctx.guild.id] = {}
        self.live_listeners[ctx.guild.id][f"{channel.id}-{message.id}"] = rr_info

    @has_access()
    @commands.command(
        require_var_positional=True,
        aliases=["reactionrole", "rr", "reactionprofile", "rp"],
    )
    async def reaction_role(
        self,
        ctx,
        role_or_profile: typing.Union[discord.Role, str],
        channel: typing.Optional[discord.TextChannel] = None,
        emoji: typing.Optional[
            typing.Union[discord.Emoji, discord.PartialEmoji, str]
        ] = None,
    ):
        # check and validate all the parameters
        if channel is None:
            channel = ctx.channel
        if emoji is None:
            emoji = random_circle_emoji()

        await validate_params(ctx, self.command_info, emoji, role_or_profile)

        is_role = isinstance(role_or_profile, discord.Role)
        _type = "role" if is_role else "profile"

        message = await channel.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={
                    "emoji": emoji,
                    "name": role_or_profile.mention if is_role else role_or_profile,
                    "_type": _type,
                },
            )
        )
        await message.add_reaction(emoji)

        self.initialize_rr(
            ctx,
            channel,
            message,
            {
                str(emoji): {
                    "type": _type,
                    "id": role_or_profile.id if is_role else role_or_profile,
                }
            },
        )

    @has_access()
    @commands.command(require_var_positional=True, aliases=["reactionmenu", "rm"])
    async def reaction_menu(
        self,
        ctx,
        *args,
        channel: discord.TextChannel = None,
    ):
        inputs = [input for input in args if input]
        individual_args = "".join(inputs).split(",")

        econvert = EmojiConverter().convert
        peconvert = PartialEmojiConverter().convert
        rconvert = RoleConverter().convert

        if channel is None:
            channel = ctx.channel

        rr_info = {}
        temp = {}
        for arg in individual_args:
            emoji, rr_info_assigned = arg.split("/")

            try:
                emoji = await econvert(ctx, emoji)
            except EmojiNotFound:
                try:
                    emoji = await peconvert(ctx, emoji)
                except:
                    pass

            await validate_params(ctx, self.command_info, emoji, rr_info_assigned)

            data = {}

            if firecord.profile_exists(ctx.guild.id, rr_info_assigned):
                data["type"] = "profile"
                data["id"] = rr_info_assigned
            else:
                role = await rconvert(ctx, str(rr_info_assigned))
                temp[emoji] = role
                data["type"] = "role"
                data["id"] = role.id
            rr_info[str(emoji)] = data

        description = (
            "**React with the emoji to get the correlated role or profile.**\n\n"
        )
        description += "\n\n".join(
            f"{emoji} - {('Role: **' + temp[emoji].mention) if info['type'] == 'role' else ('Profile: **' + str(info['id']))}**"
            for emoji, info in rr_info.items()
        )
        message = await channel.send(
            embed=EmbedFactory(
                {**self.command_info["embed"], "description": description},
                formatting_data={"emoji": emoji, "role_mention": role.mention},
            )
        )
        for emoji in rr_info.keys():
            await message.add_reaction(emoji)

        self.initialize_rr(
            ctx,
            channel,
            message,
            rr_info,
        )


def setup(bot):
    bot.add_cog(ReactionRoles(bot))