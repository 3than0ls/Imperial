import discord
from discord.ext import commands
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error

# from cogs.jail.helper import (  # pylint: disable=import-error
# )


class Jail(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)


def setup(bot):
    bot.add_cog(Jail(bot))
