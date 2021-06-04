import discord
from discord.ext import commands
from discord.ext.commands.converter import MemberConverter, RoleConverter
from discord.ext.commands.errors import BadArgument, MemberNotFound
from firecord import firecord  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from checks.has_access import has_access  # pylint: disable=import-error
from cogs.reaction_roles.helper import (  # pylint: disable=import-error
    in_live_listeners,
    random_circle_emoji,
    invalid_role,
)


class ReactionRoles(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.live_listeners = {
            # guild_id: { channel_id: { message_id: [] } }
        }

    def create_live_listener(self, message):
        guild_id = message.guild.id
        channel_id = message.channel.id
        message_id = message.channel.id

    @commands.Cog.listener()  # this will probably cause problems
    async def on_reaction_add(self, reaction, user):
        ctx = await self.bot.get_context(reaction.message)
        if ctx.guild is None:
            return

        live_listener = in_live_listeners(reaction.message, self.live_listeners)
        if reaction.emoji == live_listener["emoji"]:
            if live_listener["type"] == "role":
                user.add_role(
                    await MemberConverter().convert(ctx, live_listener["role"])
                )
            # elif live_listener["type"] == "profile, roles, profiles"

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        ctx = await self.bot.get_context(message)
        if ctx.guild is None:
            return

        live_listener = in_live_listeners(message, self.live_listeners)
        # somehow find a way to remove it

    @has_access()
    @commands.command(require_var_positional=True, aliases=["new"])
    async def reaction_role(
        self,
        ctx,
        role,
        channel: discord.TextChannel = None,
        emoji: discord.Emoji = None,
    ):
        # check and validate all the parameters
        if channel is None:
            channel = ctx.channel
        if emoji is None:
            emoji = random_circle_emoji()

        if emoji.is_usable():
            raise BadArgument(
                self.command_info["errors"]["InvalidEmoji"].format(emoji=emoji)
            )

        try:
            role = RoleConverter().convert(ctx, role)
        except MemberNotFound:
            raise BadArgument(
                self.command_info["errors"]["RoleError"].format(role=role)
            )

        if invalid_role(role):
            raise BadArgument(
                self.command_info["errors"]["InvalidRole"].format(
                    role_mention=role.mention
                )
            )

        message = await channel.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={"emoji": emoji, "role_mention": role.mention},
            )
        )

        message.add_reaction(emoji)

        # add it to the thing


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
