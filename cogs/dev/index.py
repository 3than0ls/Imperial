import logging
import os
import pathlib
import sys
import traceback

import discord
from discord.ext import commands
from utils.embed import EmbedFactory  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error


class Dev(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)

    @ExtendedCog.listener(name="on_message")
    async def on_message(self, message):
        if message.author.id == self.bot.user.id:
            return

        if str(message.author.id) == os.environ["OWNER_UID"]:
            if message.content == "--quit" or message.content == "-Q":
                print("shutting down")
                await self.bot.close()
                quit()

            elif message.content == "--restart" or message.content == "-R":
                print("restarting")
                logging.error("--- RESTARTING ---")
                await self.bot.close()
                os.execl(sys.executable, *([sys.executable] + sys.argv))


def setup(bot):
    if os.environ["DEV"]:
        bot.add_cog(Dev(bot))
