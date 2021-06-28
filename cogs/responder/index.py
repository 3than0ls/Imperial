from discord.ext.commands.converter import UserConverter
from discord.ext.commands.errors import BadArgument
from firecord import firecord  # pylint: disable=import-error
from discord.ext import commands
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from utils.confirm import confirm  # pylint: disable=import-error


class Responder(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.responder_map = firecord.responder_map
        self.cache = self.bot.cache["responder"]

    def _create_responder(self, ctx, responder_info):
        self.cache[str(ctx.guild.id)][responder_info["trigger"]] = responder_info
        firecord.responder_create(
            str(ctx.guild.id),
            str(ctx.author.id),
            responder_info,
        )

    @ExtendedCog.listener(name="on_message")
    async def on_message(self, message):
        if message.author.id == self.bot.user.id and not message.author.bot:
            return

        # check if the message isn't a bot command, if it is, just return and dont do anything
        msg = message.content
        start = msg.split(" ")[0]
        if start.startswith(">") and self.bot.get_command(start[1:]) is not None:
            return

        guild_id = str(message.guild.id)
        if msg in self.responder_map[guild_id]:
            return await message.channel.send(
                self.responder_map[guild_id][msg]["responder"]
            )

        wildcards = [
            responder
            for responder in self.responder_map[guild_id].values()
            if responder.get("wildcard", False) == True
        ]
        for responder in wildcards:
            if responder["trigger"] in msg:
                return await message.channel.send(responder["responder"])

    @commands.group(
        aliases=["responders", "autoresponder", "autoresponders"],
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
            f"Creating a responder. Please verify that these are the correct values.\n\n**Trigger Phrase: **{len(trigger)} character(s), {len(trigger.split())} character(s).\n{trigger}\n\n**Response:** {len(responder)} characters(s) {len(responder.split())} word(s)\n{responder}\n\n**Wildcard:** {wildcard}",
        ):
            self._create_responder(
                ctx, {"trigger": trigger, "responder": responder, "wildcard": wildcard}
            )

            await ctx.send(
                embed=EmbedFactory(
                    self.module_info["commands"]["responder"]["subcommands"]["create"][
                        "embed"
                    ],
                    formatting_data={
                        "prefix": ctx.prefix,
                        "trigger": trigger,
                    },
                )
            )

    @responder.command(aliases=["remove"])
    async def delete(self, ctx, *trigger):
        trigger = " ".join(trigger)
        command_info = self.module_info["commands"]["responder"]["subcommands"][
            "delete"
        ]
        guild_id = str(ctx.guild.id)
        if firecord.responder_get(guild_id, trigger) is None:
            raise BadArgument(
                command_info["errors"]["ResponderNotExist"].format(trigger=trigger)
            )

        del self.responder_map[guild_id][trigger]
        firecord.responder_delete(guild_id, trigger)

        await ctx.send(
            embed=EmbedFactory(
                command_info["trigger"],
                formatting_data={
                    "trigger": trigger,
                },
            )
        )

    @responder.command(aliases=["information"])
    async def info(self, ctx, *trigger):
        trigger = " ".join(trigger)
        command_info = self.module_info["commands"]["responder"]["subcommands"]["info"]
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


def setup(bot):
    bot.add_cog(Responder(bot))
