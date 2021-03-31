import os
import pathlib

import discord
from discord.ext import commands
from utils.embed import EmbedFactory  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.info import get_module_info  # pylint: disable=import-error
from utils.regexp import pascal_to_words  # pylint: disable=import-error


class Help(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)

    @ExtendedCog.listener(name="on_message")
    async def on_message(self, message):
        if message.author.id == self.bot.user.id:
            return

        if (
            message.content == self.bot.user.mention
            or message.content == f"<@!{self.bot.user.id}>"
        ):
            ctx = await self.bot.get_context(message)
            return await ctx.invoke(self.help)

    @commands.command(aliases=["info"])
    async def help(self, ctx, keyword: str = None):
        if keyword is None:
            embed = EmbedFactory(
                self.command_info["embed"],
                formatting_data={
                    "me": ctx.me,
                    "guild": ctx.guild,
                    "prefix": ctx.prefix,
                    "invite_url": discord.utils.oauth_url(
                        os.environ["BOT_TOKEN"],
                        permissions=discord.Permissions(permissions=8),
                    ),
                },
            )
            return await ctx.send(embed=embed)

        try:
            return await ctx.invoke(self.module, module_name=keyword)
        except:
            pass

        try:
            return await ctx.invoke(self.command, command_name=keyword)
        except:
            pass

        # we have exhausted all possible options, keyword is not a command or module that exists, raise error
        raise commands.BadArgument(
            self.command_info["errors"]["BadArgument"].format(keyword=keyword)
        )

    @commands.command(aliases=["cogs"], require_var_positional=True)
    async def modules(self, ctx):
        await ctx.send(
            embed=EmbedFactory(
                {
                    **self.command_info["embed"],
                    "fields": [
                        {
                            "name": pascal_to_words(name),
                            "value": cog.module_info.get(
                                "description",
                                "No description provided for this module.",
                            ),
                            "inline": True,
                        }
                        for name, cog in self.bot.cogs.items()
                        if not cog.hidden
                    ],
                }
            )
        )

    @commands.command(
        aliases=["module_info", "cog", "cog_info"], require_var_positional=True
    )
    async def module(self, ctx, module_name: str):
        parsed_module_name = "".join(
            segment.capitalize() for segment in module_name.split("_")
        )
        cog = self.bot.get_cog(parsed_module_name) or self.bot.get_cog(module_name)

        if cog is None or cog.hidden:
            raise commands.BadArgument(
                self.command_info["errors"]["BadArgument"].format(
                    module_name=module_name
                )
            )

        await ctx.send(
            embed=EmbedFactory(
                {
                    **self.command_info["embed"],
                    "description": self.command_info["embed"].get("description", "")
                    + f"\n{cog.module_info.get('guide', '')}"
                    + (
                        "To get more information about a specific command, run `{prefix}command [command_name]`"
                        if cog.commands_info
                        else ""
                    ),
                    "fields": [
                        {
                            "name": f"`{ctx.prefix}{command.qualified_name}`",
                            "value": cog.commands_info[command.qualified_name][
                                "description"
                            ],
                            "inline": True,
                        }
                        for command in cog.get_commands()
                    ],
                },
                formatting_data={"module": cog.module_info, "prefix": ctx.prefix},
            )
        )

    @commands.command(
        aliases=["command_info", "cmd", "cmd_info"], require_var_positional=True
    )
    async def command(self, ctx, *, command_name: str):
        command = self.bot.get_command(command_name.lower()) or self.bot.get_command(
            command_name
        )

        if command is None:
            raise commands.BadArgument(
                self.command_info["errors"]["BadArgument"].format(
                    command_name=command_name
                )
            )

        command_info = command.cog.commands_info[command.qualified_name]

        await ctx.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={
                    "command": command,
                    "command_info": command_info,
                    "aliases": ", ".join(f"`{alias}`" for alias in command.aliases),
                    "params": "\n".join(
                        [
                            f'`{param.name}` - **{"Required" if param.default is param.empty else "Optional"}** - {command_info.get("params", {}).get(param.name, "No description was given.")}'
                            for param in command.clean_params.values()
                        ]
                    ),
                    "usage": (
                        "\n".join(
                            [
                                f"`{command.format(prefix=ctx.prefix)}` - {description}"
                                for command, description in command_info[
                                    "usage"
                                ].items()
                            ]
                        )
                    )
                    if "usage" in command_info
                    else "No usage examples provided.",
                    "guide": command_info.get(
                        "guide", "No guide or extra information is available."
                    ),
                },
            )
        )

    async def cog_command_error(self, ctx, error):
        error_command_string = f"{ctx.prefix}{ctx.invoked_with}"
        await ctx.send(
            embed=EmbedFactory(
                {"description": error.args[0]},
                error=True,
                error_command_string=error_command_string,
            )
        )


def setup(bot):
    bot.add_cog(Help(bot))
