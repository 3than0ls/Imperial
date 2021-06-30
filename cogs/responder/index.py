from datetime import datetime

from checks.has_access import has_access  # pylint: disable=import-error
from discord.ext import commands
from discord.ext.commands.converter import UserConverter
from discord.ext.commands.errors import BadArgument
from firecord import firecord  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.confirm import confirm  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from utils.pagination import pagination  # pylint: disable=import-error


class Responder(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot.cache["responder"] = firecord.responder_map
        self.cache = self.bot.cache["responder"]
        self.cd_cache = self.bot.cache["responder_cd"]

    def _create_responder(self, ctx, responder_info):
        self.cache[str(ctx.guild.id)][responder_info["trigger"]] = responder_info
        firecord.responder_create(
            str(ctx.guild.id),
            str(ctx.author.id),
            responder_info,
        )

    @ExtendedCog.listener(name="on_message")
    async def on_message(self, message):
        if (
            message.author.id == self.bot.user.id
            or message.author.bot
            or message.guild is None
        ):
            return

        # apply a cooldown check
        now_time = datetime.now()
        guild_id = str(message.guild.id)
        if (
            self.cd_cache[guild_id]
            and (now_time - self.cd_cache[guild_id]).total_seconds() < 2
        ):
            return
        else:
            self.cd_cache[guild_id] = now_time

        # check if the message isn't a bot command, if it is, just return and dont do anything
        msg = message.content
        start = msg.split(" ")[0]
        if start.startswith(">") and self.bot.get_command(start[1:]) is not None:
            return

        guild_id = str(message.guild.id)
        if msg in self.cache[guild_id]:
            return await message.channel.send(self.cache[guild_id][msg]["responder"])

        wildcards = [
            responder
            for responder in self.cache[guild_id].values()
            if responder.get("wildcard", False) == True
        ]
        for responder in wildcards:
            if responder["trigger"] in msg:
                return await message.channel.send(responder["responder"])

    @commands.group(
        aliases=["autoresponder"],
        case_insensitive=True,
    )
    async def responder(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send(
                embed=EmbedFactory(
                    self.command_info["embed"],
                    formatting_data={
                        "prefix": ctx.prefix,
                    },
                )
            )

    @has_access()
    @responder.command(aliases=["add", "new"])
    async def create(self, ctx, trigger, responder, *, wildcard="No"):
        """restrict trigger to be less than 50 characters, and response to less than 1800 characters."""
        if len(trigger) > 50:
            raise BadArgument(
                self.command_info["errors"]["InvalidTrigger"].format(
                    length=len(trigger)
                )
            )
        if len(responder) > 1800:
            raise BadArgument(
                self.command_info["errors"]["InvalidResponder"].format(
                    length=len(responder)
                )
            )
        if wildcard.lower() in ["yes", "ye", "y", "true", "agree", "sure", "ok"]:
            wildcard = True
        else:
            wildcard = False

        if await confirm(
            ctx,
            f"Creating a responder. Please verify that these are the correct values.\n\n**Trigger Phrase: **{len(trigger)} character(s), {len(trigger.split())} character(s).\n{trigger}\n\n**Response:** {len(responder)} characters(s), {len(responder.split())} word(s)\n{responder}\n\n**Wildcard:** {wildcard}",
        ):
            self._create_responder(
                ctx, {"trigger": trigger, "responder": responder, "wildcard": wildcard}
            )

            await ctx.send(
                embed=EmbedFactory(
                    self.commands_info["responder"]["subcommands"]["create"]["embed"],
                    formatting_data={
                        "prefix": ctx.prefix,
                        "trigger": trigger,
                    },
                )
            )

    @has_access()
    @responder.command(aliases=["remove"])
    async def delete(self, ctx, *trigger):
        trigger = " ".join(trigger)
        command_info = self.commands_info["responder"]["subcommands"]["delete"]
        guild_id = str(ctx.guild.id)
        if firecord.responder_get(guild_id, trigger) is None:
            raise BadArgument(
                command_info["errors"]["ResponderNotExist"].format(trigger=trigger)
            )

        del self.cache[guild_id][trigger]
        firecord.responder_delete(guild_id, trigger)

        await ctx.send(
            embed=EmbedFactory(
                command_info["embed"],
                formatting_data={
                    "trigger": trigger,
                },
            )
        )

    @responder.command(aliases=["information"])
    async def info(self, ctx, *trigger):
        trigger = " ".join(trigger)
        command_info = self.commands_info["responder"]["subcommands"]["info"]
        guild_id = str(ctx.guild.id)

        responder = firecord.responder_get(guild_id, trigger)
        if responder is None:
            raise BadArgument(
                command_info["errors"]["ResponderNotExist"].format(trigger=trigger)
            )

        responder = responder.to_dict()

        await ctx.send(
            embed=EmbedFactory(
                command_info["embed"],
                formatting_data={
                    "responder": responder["responder"],
                    "trigger": responder["trigger"],
                    "created": responder["created"].strftime("%m-%d-%y"),
                    "creator": (
                        await UserConverter().convert(ctx, str(responder["creator"]))
                    ).mention,
                },
            )
        )

    @responder.command(aliases=["list"])
    async def _list(self, ctx, order="alphabetical"):
        await ctx.invoke(self.bot.get_command("responders"), order=order)

    @commands.command(aliases=["autoresponders"])
    async def responders(self, ctx, order="alphabetical"):
        responders = firecord.responder_list(str(ctx.guild.id))

        if order == "created" or order == "date":
            responder_list = sorted(
                responders, key=lambda responder: responder["created"]
            )
        elif order == "creator":
            responder_list = sorted(
                responders, key=lambda responder: responder["creator"]
            )
        else:  # default to alphabetical
            responder_list = sorted(
                responders, key=lambda responder: responder["trigger"]
            )

        await pagination(
            ctx,
            EmbedFactory(
                {
                    **self.command_info["embed"],
                    "fields": [
                        {
                            "name": responder["trigger"],
                            "value": f'`>responder info {responder["trigger"]}`',
                            "inline": True,
                        }
                        for responder in responder_list
                    ],
                },
                {
                    "server_name": ctx.guild.name,
                    "responder_num": str(len(responder_list)),
                    "prefix": ctx.prefix,
                },
            ),
        )


def setup(bot):
    bot.add_cog(Responder(bot))
