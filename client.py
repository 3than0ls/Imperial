import datetime

from utils.logger import log
import os

import discord
from discord.ext import commands

from cogs import cogs_list
from firecord import DEFAULT_CONFIG, firecord
from utils.cache import cache


class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.__prefix, intents=discord.Intents.all())
        self.cache = cache
        # disable help command
        self.help_command = None

    def __prefix(self, bot, message):
        try:
            return firecord.prefix_map.get(
                str(message.guild.id), DEFAULT_CONFIG.get("prefix", ">")
            )
        except AttributeError:
            return ">"

    def start_bot(self):
        for cog_path in cogs_list():
            self.load_extension(cog_path)
        self.run(os.environ["BOT_TOKEN"])

    async def on_ready(self):
        logMsg = f"{self.user} is connected and ready active on time: {datetime.datetime.now()}"
        print(logMsg)
        log.info(logMsg)

    async def on_message(self, message):
        # maybe move below to a decorator check
        if message.author.id == self.user.id and not message.author.bot:
            return

        ctx = await self.get_context(message)
        if ctx.guild is None:
            return

        await self.process_commands(message)
