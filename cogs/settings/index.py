import pathlib

import discord
from discord.ext import commands
from firecord import firecord, DEFAULT_CONFIG  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from utils.regexp import pascal_to_words, word_to_pascal  # pylint: disable=import-error
from cogs.settings.validate import validation_rules  # pylint: disable=import-error


class Settings(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)

    @ExtendedCog.listener(name="on_guild_join")
    async def on_guild_join(self, guild):
        firecord.init_guild(str(guild.id))

        # try to find a general/chat channel, and invoke help command there.
        if channel := discord.utils.find(
            lambda c: "general" in c.name.lower() or "chat" in c.name.lower(),
            guild.text_channels,
        ):
            ctx = await self.bot.get_context(
                (await channel.history(limit=1).flatten())[0]
            )
            help_command = self.bot.get_command("help")
            await ctx.invoke(help_command)

    @ExtendedCog.listener(name="on_ready")
    async def on_ready(self):
        # loop through every guild and if nickname was changed while bot could not detect on_nickname_change event, set it in backend
        pass

    @ExtendedCog.listener(name="on_member_update")
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            guild_id = str(after.guild.id)
            firecord.set_guild_data(guild_id, {"nickname": after.nick})

    def check_settings_exists(self, setting_name):
        setting_name = setting_name.lower()
        settings_list = self.module_info["settings"]
        if setting_name not in settings_list:
            raise commands.BadArgument(
                self.commands_info["settings"]["errors"]["BadArgument"].format(
                    setting_name=setting_name
                )
            )

        return setting_name, settings_list[setting_name]

    @commands.group(
        aliases=["setting", "config", "configuration", "env"],
        case_insensitive=True,
    )
    async def settings(self, ctx):
        if ctx.subcommand_passed is None:
            guild_data = firecord.get_guild_data(str(ctx.guild.id))
            await ctx.send(
                embed=EmbedFactory(
                    self.command_info["embed"],
                    formatting_data={
                        "guild": ctx.guild,
                        "guild_data": guild_data,
                        "prefix": ctx.prefix,
                    },
                )
            )

    @settings.command(require_var_positional=True, aliases=["get"])
    async def info(self, ctx, *, setting_name):
        setting_name, setting_info = self.check_settings_exists(setting_name)
        guild_data = firecord.get_guild_data(str(ctx.guild.id))
        await ctx.send(
            embed=EmbedFactory(
                {
                    **self.commands_info["settings"]["subcommands"]["info"]["embed"],
                    "fields": setting_info["fields"],
                },
                formatting_data={
                    "setting": setting_info,
                    "prefix": ctx.prefix,
                    "guild_data": guild_data,
                },
            )
        )

    @settings.command(require_var_positional=True)
    async def set(self, ctx, setting_name, *, value):
        setting_name = self.check_settings_exists(setting_name)

        # validate user input
        if not validation_rules[setting_name]:
            raise discord.InvalidArgument(
                self.commands_info["settings"]["subcommands"]["set"]["errors"][
                    "BadArgument"
                ].format(value=value, setting_name=setting_name, prefix=ctx.prefix)
            )

        firecord.set_guild_data(str(ctx.guild.id), {"prefix": value})
        await ctx.send(
            embed=EmbedFactory(
                self.commands_info["settings"]["subcommands"]["set"]["embed"],  # messy
                formatting_data={
                    "setting_name": setting_name,
                    "value": value,
                },
            )
        )

    @settings.command(require_var_positional=True)
    async def reset(self, ctx, *, setting_name):
        setting_name, _ = self.check_settings_exists(setting_name)

        firecord.set_guild_data(
            str(ctx.guild.id), {setting_name: DEFAULT_CONFIG[setting_name]}
        )
        await ctx.send(
            embed=EmbedFactory(
                self.commands_info["settings"]["subcommands"]["set"]["embed"],  # messy
                formatting_data={
                    "setting_name": setting_name,
                    "value": DEFAULT_CONFIG[setting_name],
                },
            )
        )


def setup(bot):
    bot.add_cog(Settings(bot))
