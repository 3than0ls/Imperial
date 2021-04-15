import datetime
import logging
import os
import sys
import time

import discord
from discord.ext import commands

from cogs import cogs_list
from firecord import DEFAULT_CONFIG, firecord


class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.__prefix)

        # disable help command
        self.help_command = None

    def __prefix(self, bot, message):
        return firecord.prefix_map.get(
            str(message.guild.id), DEFAULT_CONFIG.get("prefix", ">")
        )

    def start_bot(self):
        for cog_path in cogs_list():
            self.load_extension(cog_path)
        self.run(os.environ["BOT_TOKEN"])

    async def on_ready(self):
        print(
            f"{self.user} is connected and ready active on time: {datetime.datetime.now()}"
        )

    async def on_message(self, message):
        # maybe move below to a decorator check
        if message.author.id == self.user.id:
            return

        ctx = await self.get_context(message)
        if ctx.guild is None:
            return await ctx.send("Cannot work in DMs")

        await self.process_commands(message)
