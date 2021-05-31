import os
import pathlib

import discord
from discord.ext import commands
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from cogs.define.helper import (  # pylint: disable=import-error
    dictionary_define,
    urban_define,
)


class Define(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)

    @commands.command(
        aliases=[
            "dictionary",
            "thesaurus",
        ]
    )
    async def define(self, ctx, *keyword: str):
        keyword = " ".join(keyword)

        async with ctx.channel.typing():
            definition = dictionary_define(keyword)

        if definition is None:
            raise commands.BadArgument(
                self.command_info["errors"]["BadArgument"].format(keyword=keyword)
            )
        else:
            nl = "\n"
            formatted_definition = [
                f"**{part}:**\n {nl.join([f'**{i+1}**. {part_def}' for i, part_def in enumerate(part_definitions) if i < 3])}"
                for part, part_definitions in definition["definition"].items()
            ]
            await ctx.send(
                embed=EmbedFactory(
                    self.command_info["embed"],
                    formatting_data={
                        "keyword": keyword,
                        "prefix": ctx.prefix,
                        "definition": "\n\n".join(formatted_definition),
                        "synonyms": ", ".join(definition["synonyms"]),
                        "antonyms": ", ".join(definition["antonyms"]),
                    },
                )
            )

    @commands.command(aliases=["urban_dictionary", "urban_define"])
    async def urban(self, ctx, *keyword: str):
        keyword = " ".join(keyword)

        async with ctx.channel.typing():
            definition = urban_define(keyword)

        if definition is None:
            raise commands.BadArgument(
                self.command_info["errors"]["BadArgument"].format(keyword=keyword)
            )
        else:
            await ctx.send(
                embed=EmbedFactory(
                    self.command_info["embed"],
                    formatting_data={
                        "keyword": keyword,
                        "prefix": ctx.prefix,
                        "definition": definition["definition"],
                        "example": definition["example"],
                    },
                )
            )


def setup(bot):
    bot.add_cog(Define(bot))
