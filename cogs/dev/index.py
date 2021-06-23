import logging
import os
import pathlib
import sys
import traceback

import discord
from discord.ext import commands
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error


class Dev(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)

    @ExtendedCog.listener(name="on_message")
    async def on_message(self, message):
        if message.author.id == self.bot.user.id and not message.author.bot:
            return

        if str(message.author.id) == os.environ["OWNER_UID"]:
            if message.content == "--quit" or message.content == "-Q":
                logMsg = (
                    f"----- SHUTDOWN COMMAND ISSUED BY USER {message.author.id}  -----"
                )
                print(logMsg)
                logging.info(logMsg)
                await self.bot.close()
                quit()

            elif message.content == "--restart" or message.content == "-R":
                logMsg = (
                    f"----- RESTART COMMAND ISSUED BY USER {message.author.id} -----"
                )
                print(logMsg)
                logging.info(logMsg)
                await self.bot.close()
                os.execl(sys.executable, *([sys.executable] + sys.argv))


def setup(bot):
    if os.environ["DEV"]:
        bot.add_cog(Dev(bot))
