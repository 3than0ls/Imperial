import discord
from checks.has_access import has_access  # pylint: disable=import-error
from cogs.settings.convert import (  # pylint: disable=import-error
    ToStoreError,
    to_client,
    to_store,
)
from discord.ext import commands
from firecord import DEFAULT_CONFIG, firecord  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error


class Settings(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.exclude_setting = ["jail"]

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
            guild_data = {
                setting: to_client.convert(ctx, setting, value)
                for setting, value in firecord.get_guild_data(str(ctx.guild.id)).items()
            }
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
        guild_data = {
            setting: to_client.convert(ctx, setting, value)
            for setting, value in firecord.get_guild_data(str(ctx.guild.id)).items()
        }
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

    @has_access()
    @settings.command(require_var_positional=True)
    async def set(self, ctx, setting_name, *, value):
        setting_name, _ = self.check_settings_exists(setting_name)
        if setting_name in self.exclude_setting:
            raise commands.BadArgument(
                self.commands_info["settings"]["errors"]["Immutable"].format(
                    setting_name=setting_name, prefix=ctx.prefix
                )
            )
        try:
            value = to_store.convert(ctx, setting_name, value)
        except ToStoreError:
            raise commands.BadArgument(
                self.commands_info["settings"]["subcommands"]["set"]["errors"][
                    "InvalidArgument"
                ].format(
                    value=to_client.convert(ctx, setting_name, value),
                    setting_name=setting_name,
                    prefix=ctx.prefix,
                )
            )

        if setting_name == "automath":
            self.bot.cache[str(ctx.guild.id)]["automath"] = value

        firecord.set_guild_data(str(ctx.guild.id), {setting_name: value})

        value = to_client.convert(ctx, setting_name, value)
        await ctx.send(
            embed=EmbedFactory(
                self.commands_info["settings"]["subcommands"]["set"]["embed"],
                formatting_data={
                    "setting_name": setting_name,
                    "value": value if isinstance(value, str) else value[1],
                },
            )
        )

    @has_access()
    @settings.command(require_var_positional=True)
    async def reset(self, ctx, *, setting_name):
        setting_name, _ = self.check_settings_exists(setting_name)

        firecord.set_guild_data(
            str(ctx.guild.id), {setting_name: DEFAULT_CONFIG[setting_name]}
        )
        await ctx.send(
            embed=EmbedFactory(
                self.commands_info["settings"]["subcommands"]["reset"][
                    "embed"
                ],  # messy
                formatting_data={
                    "setting_name": setting_name,
                    "value": DEFAULT_CONFIG[setting_name],
                },
            )
        )


def setup(bot):
    bot.add_cog(Settings(bot))
