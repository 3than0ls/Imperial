import pathlib

import discord
from discord.ext import commands
from firecord import firecord  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from utils.info import get_module_info  # pylint: disable=import-error
from utils.regexp import pascal_to_words  # pylint: disable=import-error


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

    @ExtendedCog.listener(name="on_message")
    async def on_message(self, message):
        print(firecord.prefix_map)
        ctx = await self.bot.get_context(message)
        if message.content == "change":
            firecord.set_guild_data(str(ctx.guild.id), {"prefix": "<"})
            await ctx.send("changed!")

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
