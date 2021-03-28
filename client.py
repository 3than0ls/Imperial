import datetime
import logging
import os
import sys
import time

from discord.ext import commands

from cogs import cogs_list


class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.__prefix)

        # disable help command
        self.help_command = None

    def __prefix(self, bot, message):
        return os.environ["PREFIX"]

    def start_bot(self):
        for cog_path in cogs_list():
            self.load_extension(cog_path)
        self.run(os.environ["BOT_TOKEN"])

    async def on_ready(self):
        print(
            f"{self.user} is connected and ready active on time: {datetime.datetime.now()}"
        )

    async def test_on_message(self, message):
        ctx = await self.get_context(message)

        if message.content == f"<@!{self.user.id}>":
            await ctx.send("pogchamp")

        if ctx.guild is None:
            return await ctx.send("Cannot work in DMs")

    async def on_message(self, message):
        # maybe move below to a decorator check
        if message.author.id == self.user.id:
            return

        await self.test_on_message(message)

        await self.process_commands(message)