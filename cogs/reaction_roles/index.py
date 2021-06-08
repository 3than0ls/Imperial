from datetime import datetime
import discord
from discord.ext import commands
from discord.ext.commands.converter import (
    RoleConverter,
)
from discord.ext.commands.errors import BadArgument, MemberNotFound, RoleNotFound
from firecord import firecord  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from checks.has_access import has_access  # pylint: disable=import-error
from cogs.reaction_roles.helper import (  # pylint: disable=import-error
    in_live_listeners,
    random_circle_emoji,
)


class ReactionRoles(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.live_listeners = firecord.rr_map
        self.on_cooldown = {}

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

    @commands.Cog.listener()  # this will probably cause problems
    async def on_raw_reaction_add(self, payload):
        message = await self.bot.get_channel(payload.channel_id).fetch_message(
            payload.message_id
        )

        if (
            message.author.id != self.bot.user.id
            or payload.user_id == self.bot.user.id
            or message.guild is None
        ):
            return

        now_time = datetime.now()
        if (
            payload.member.id in self.on_cooldown
            and (self.on_cooldown[payload.member.id] - now_time).total_seconds() > 5
        ):
            print("cooling down")
            return  # apply a cooldown
        else:
            self.on_cooldown[payload.member.id] = datetime.now()

        ctx = await self.bot.get_context(message)
        emoji = payload.emoji
        member = payload.member

        live_listener = in_live_listeners(message, self.live_listeners)
        if live_listener is not None and (
            rr_info := live_listener.get(
                emoji.name
            )  # value is string, either specifying an emoji or a profile name
        ):
            try:
                if rr_info["type"] == "role":
                    assigned_role = await RoleConverter().convert(
                        ctx, str(rr_info["id"])
                    )
                    dm = member.dm_channel
                    if dm is None:
                        dm = await member.create_dm()
                    await dm.send(
                        embed=EmbedFactory(
                            {
                                "title": "Reaction Role Profile Assigned",
                                "description": f'Successfully assigned role "{assigned_role.name}".',
                                "color": "success",
                            },
                        )
                    )

                elif rr_info["type"] == "profile":
                    assigned_profile = firecord.profile_get(ctx.guild.id, rr_info["id"])
                    if (
                        assigned_profile is None
                    ):  # profile doesnt exist, just raise keyerror to be handled later
                        raise KeyError()

                    dm = member.dm_channel
                    if dm is None:
                        dm = await member.create_dm()
                    await dm.send(
                        embed=EmbedFactory(
                            {
                                "title": "Reaction Role Profile Assigned",
                                "description": f"Successfully assigned profile \"{assigned_profile['name']}\".",
                                "color": "success",
                            }
                        )
                    )
            except (RoleNotFound, KeyError):
                dm = member.dm_channel
                if dm is None:
                    dm = await member.create_dm()
                await dm.send(
                    embed=EmbedFactory(
                        {
                            "description": f"The requested role or profile was unable to be assigned, likely because it no longer exists. Ask a server administrator for more information.",
                        },
                        error=True,
                    )
                )

            # elif live_listener["type"] == "profile, roles, profiles"

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        ctx = await self.bot.get_context(message)
        if ctx.guild is None:
            return

        live_listener = in_live_listeners(message, self.live_listeners)
        # somehow find a way to remove it

    def initialize_rr(self, ctx, channel, message, rr_info):
        firecord.rr_create(ctx.guild.id, channel.id, message.id, rr_info)
        if ctx.guild.id not in self.live_listeners:
            self.live_listeners[ctx.guild.id] = {}
        self.live_listeners[ctx.guild.id][f"{channel.id}-{message.id}"] = rr_info

    @has_access()
    @commands.command(require_var_positional=True, aliases=["reactionrole", "rr"])
    async def reaction_role(
        self,
        ctx,
        role: discord.Role,
        channel: discord.TextChannel = None,
        emoji: discord.PartialEmoji = None,
    ):
        # check and validate all the parameters
        if channel is None:
            channel = ctx.channel
        if emoji is None:
            emoji = random_circle_emoji()

        message = await channel.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={"emoji": emoji, "role_mention": role.mention},
            )
        )

        self.initialize_rr(
            ctx,
            channel,
            message,
            {
                emoji
                if isinstance(emoji, str)
                else emoji.name: {
                    "type": "role",
                    "id": role.id,
                }
            },
        )
        await message.add_reaction(emoji)


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
