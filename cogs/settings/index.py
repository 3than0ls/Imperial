import pathlib

import discord
from discord.ext import commands
from firecord import firecord  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from utils.regexp import pascal_to_words, word_to_pascal  # pylint: disable=import-error


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

    @commands.group(
        aliases=["setting", "config", "configuration", "env"],
        case_insensitive=True,
    )
    async def settings(self, ctx):
        if ctx.subcommand_passed is None:
            guild_id = str(ctx.guild.id)
            guild_data = firecord.get_guild_data(guild_id)
            await ctx.send(
                embed=EmbedFactory(
                    self.command_info["embed"],
                    formatting_data={"guild": ctx.guild, "prefix": ctx.prefix},
                )
            )

    @settings.command(require_var_positional=True)
    async def info(self, ctx, *, setting_name):
        setting_name = setting_name.lower()
        settings_list = self.module_info["settings"]
        if setting_name not in settings_list:
            raise commands.BadArgument(
                self.commands_info["settings"]["errors"]["BadArgument"].format(
                    setting_name=setting_name
                )
            )

        await ctx.send(
            embed=EmbedFactory(
                settings_list[setting_name],
                formatting_data={
                    "setting_name": pascal_to_words(setting_name).title(),
                    "prefix": ctx.prefix,
                },
            )
        )

    @settings.command(require_var_positional=True)
    async def set(self, ctx, setting_name, *, value):
        setting_name = setting_name.lower()
        settings_list = self.module_info["settings"]
        if setting_name not in settings_list:
            raise commands.BadArgument(
                self.commands_info["settings"]["errors"]["BadArgument"].format(
                    setting_name=setting_name
                )
            )

        if not (len(value) > 0 and len(value) <= 5):
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

    # async def cog_command_error(self, ctx, error):
    #     error_command_string = f"{ctx.prefix}{ctx.invoked_with}"
    #     print(error)
    #     print(error.args)
    #     await ctx.send(
    #         embed=EmbedFactory(
    #             {"description": error.args[0]},
    #             error=True,
    #             error_command_string=error_command_string,
    #         )
    #     )


def setup(bot):
    bot.add_cog(Settings(bot))
