import logging
import pathlib
import sys
import traceback

import discord
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from discord.ext import commands


class ErrorHandler(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot, hidden=True)

    @ExtendedCog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        Parameters
        ------------
        ctx: commands.Context
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.
        """

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, "on_error"):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound,)

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, "original", error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(
                    f"{ctx.command} can not be used in Private Messages."
                )
            except discord.HTTPException:
                pass

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            logging.error(error)
            print(
                "Ignoring exception in command {}:".format(ctx.command), file=sys.stderr
            )
            embed = EmbedFactory(
                {
                    "title": ":x: An unmanaged error has occured",
                    "description": f"**Ignoring exception in command `{ctx.command}`**\n```py\n{''.join(traceback.format_exception(type(error), error, error.__traceback__))}```",
                },
                error=True,
            )
            await ctx.send(embed=embed)
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )


def setup(bot):
    bot.add_cog(ErrorHandler(bot))