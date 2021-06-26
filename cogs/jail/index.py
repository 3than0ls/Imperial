import asyncio

import discord
from checks.has_access import has_access  # pylint: disable=import-error
from cogs.settings.convert import to_client, to_store  # pylint: disable=import-error
from discord.ext import commands
from firecord import firecord  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error

# from cogs.jail.helper import (  # pylint: disable=import-error
# )


class Jail(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)

    async def jail_exists(self, ctx):
        jail_value_ids = to_client.jail(
            ctx, firecord.get_guild_data(str(ctx.guild.id))["jail"]
        )[0]

        if jail_value_ids["jail_channel"] != "N/A":
            jail_channel = discord.utils.find(
                lambda c: str(c.id) == jail_value_ids["jail_channel"],
                await ctx.guild.fetch_channels(),
            )
        else:
            jail_channel = None

        if jail_value_ids["jail_role"] != "N/A":
            jail_role = discord.utils.find(
                lambda r: str(r.id) == jail_value_ids["jail_role"],
                await ctx.guild.fetch_roles(),
            )
        else:
            jail_role = None

        return jail_channel, jail_role

    @has_access()
    @commands.command(aliases=["createjail", "create_jail", "jail_create"])
    async def jailcreate(self, ctx, channel: discord.TextChannel = None):
        jail_channel, jail_role = await self.jail_exists(ctx)
        print(jail_channel, jail_role)
        if jail_channel is not None and jail_role is not None:
            raise commands.BadArgument(self.command_info["errors"]["JailAlreadyExists"])

        if channel is not None:
            jail_channel = await channel.set_permissions(
                ctx.guild.default_role, read_messages=False
            )
        else:
            if jail_channel is None:
                jail_channel = await ctx.guild.create_text_channel(
                    name="jail",
                    overwrites={
                        ctx.guild.default_role: discord.PermissionOverwrite(
                            read_messages=False
                        )
                    },
                )
        print(jail_channel, jail_role)
        if jail_role is None:
            jail_role = await ctx.guild.create_role(name="Jailed", color=0x010101)
            modify_channels = [
                channel for channel in ctx.guild.channels if channel != jail_channel
            ]
            if len(modify_channels) > 1:
                asyncio.wait(
                    [
                        await channel.set_permissions(jail_role, read_messages=False)
                        for channel in modify_channels
                    ]
                )

        await jail_channel.set_permissions(
            jail_role, read_messages=True, send_messages=True
        )

        await ctx.send(embed=EmbedFactory(self.command_info["embed"]))


def setup(bot):
    bot.add_cog(Jail(bot))
