import asyncio

import discord
from discord.ext.commands.converter import MemberConverter
from discord.ext.commands.errors import MemberNotFound
from checks.has_access import has_access  # pylint: disable=import-error
from cogs.settings.convert import to_client, to_store  # pylint: disable=import-error
from discord.ext import commands
from firecord import firecord  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from utils.confirm import confirm  # pylint: disable=import-error


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
            if jail_channel is None:
                firecord.set_guild_data(
                    str(ctx.guild.id),
                    {"jail.jail_channel": None},
                )
        else:
            jail_channel = None

        if jail_value_ids["jail_role"] != "N/A":
            jail_role = discord.utils.find(
                lambda r: str(r.id) == jail_value_ids["jail_role"],
                await ctx.guild.fetch_roles(),
            )
            if jail_role is None:
                firecord.set_guild_data(
                    str(ctx.guild.id),
                    {"jail.jail_role": None},
                )
        else:
            jail_role = None

        return jail_channel, jail_role

    @has_access()
    @commands.command(aliases=["createjail", "jailcreate", "jail_create"])
    async def create_jail(self, ctx, channel: discord.TextChannel = None):
        jail_channel, jail_role = await self.jail_exists(ctx)

        if jail_channel is not None and jail_role is not None:
            raise commands.BadArgument(
                self.command_info["errors"]["JailAlreadyExists"].format(
                    jail_channel=jail_channel.mention,
                    jail_role=jail_role.mention,
                    prefix=ctx.prefix,
                )
            )

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

        if jail_role is None:
            jail_role = await ctx.guild.create_role(name="Jailed", color=0x010101)
            modify_channels = [
                channel for channel in ctx.guild.channels if channel != jail_channel
            ]
            if len(modify_channels) > 1:
                await asyncio.wait(
                    [
                        channel.set_permissions(jail_role, read_messages=False)
                        for channel in modify_channels
                    ]
                )

        await jail_channel.set_permissions(
            jail_role, read_messages=True, send_messages=True
        )

        firecord.set_guild_data(
            str(ctx.guild.id),
            to_store.jail(ctx, {"jail_channel": jail_channel, "jail_role": jail_role}),
        )

        await ctx.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={
                    "prefix": ctx.prefix,
                    "jail_channel": jail_channel.mention,
                    "jail_role": jail_role.mention,
                },
            )
        )

    @has_access()
    @commands.command(aliases=["deletejail", "jaildelete", "jail_delete"])
    async def delete_jail(self, ctx):
        jail_channel, jail_role = await self.jail_exists(ctx)
        if jail_channel is None and jail_role is None:
            raise commands.BadArgument(
                self.module_info["errors"]["JailNotExists"].format(
                    prefix=ctx.prefix,
                )
            )

        proceed = await confirm(
            ctx,
            "Are you sure you want to delete the jail system? This will delete the jail channel and the jail role from the server",
        )
        if proceed:
            await asyncio.sleep(1)
            if isinstance(jail_channel, discord.TextChannel):
                await jail_channel.delete()
            if isinstance(jail_role, discord.Role):
                await jail_role.delete()

            firecord.set_guild_data(
                str(ctx.guild.id),
                {"jail.jail_channel": None, "jail.jail_role": None},
            )

        # it would send it in the channel thats being deleted- not very helpful
        # await ctx.send(
        #     embed=EmbedFactory(
        #         self.command_info["embed"],
        #         formatting_data={
        #             "prefix": ctx.prefix,
        #         },
        #     )
        # )

    @has_access()
    @commands.command(aliases=["imprison"])
    async def jail(self, ctx, *members):
        jail_channel, jail_role = await self.jail_exists(ctx)

        if jail_channel is None and jail_role is None:
            raise commands.BadArgument(
                self.module_info["errors"]["JailNotExists"].format(prefix=ctx.prefix)
            )
        if jail_channel is None or jail_role is None:
            raise commands.BadArgument(
                self.module_info["errors"]["JailBroken"].format(prefix=ctx.prefix)
            )

        if len(members) == 0:
            raise commands.BadArgument(self.module_info["errors"]["MissingMembers"])

        member_objs = []
        for member in members:
            try:
                member_objs.append(await MemberConverter().convert(ctx, member))
            except MemberNotFound:
                raise commands.BadArgument(
                    self.module_info["errors"]["InvalidMember"].format(value=member)
                )

        members = member_objs

        await asyncio.wait([member.edit(roles=[jail_role]) for member in members])

        await ctx.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={
                    "members": ", ".join([member.mention for member in members]),
                    "jail_role": jail_role.mention,
                    "jail_channel": jail_channel.mention,
                },
            )
        )

    @has_access()
    @commands.command(aliases=["free"])
    async def unjail(self, ctx, *members):
        jail_channel, jail_role = await self.jail_exists(ctx)
        if jail_channel is None and jail_role is None:
            raise commands.BadArgument(
                self.module_info["errors"]["JailNotExists"].format(prefix=ctx.prefix)
            )
        if jail_channel is None or jail_role is None:
            raise commands.BadArgument(
                self.command_info["errors"]["JailBroken"].format(prefix=ctx.prefix)
            )

        if len(members) == 0:
            raise commands.BadArgument(self.module_info["errors"]["MissingMembers"])

        member_objs = []
        for member in members:
            try:
                member_objs.append(await MemberConverter().convert(ctx, member))
            except MemberNotFound:
                raise commands.BadArgument(
                    self.module_info["errors"]["InvalidMember"].format(value=member)
                )

        members = member_objs

        await asyncio.wait(
            [
                member.edit(roles=[role for role in member.roles if role != jail_role])
                for member in members
            ]
        )

        await ctx.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={
                    "members": ", ".join([member.mention for member in members]),
                    "jail_role": jail_role.mention,
                    "jail_channel": jail_channel.mention,
                },
            )
        )


def setup(bot):
    bot.add_cog(Jail(bot))
