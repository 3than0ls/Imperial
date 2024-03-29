import typing

import discord
from checks.has_access import has_access  # pylint: disable=import-error
from cogs.settings.convert import to_client, to_store  # pylint: disable=import-error
from discord.ext import commands
from firecord import firecord  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error


class Archive(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)

    async def create_archive_category(self, ctx):
        category = await ctx.guild.create_category(
            "Archived",
            position=999,
            overwrites={
                ctx.guild.default_role: discord.PermissionOverwrite(
                    view_channel=False, send_messages=False
                )
            },
        )
        firecord.set_guild_data(
            str(ctx.guild.id),
            {"archivecategory": to_store.archivecategory(ctx, category)},
        )
        return category

    @has_access()
    @commands.command(aliases=["hide"])
    async def archive(
        self,
        ctx,
        channel: typing.Optional[discord.TextChannel] = None,
        category=None,  # we don't use a converter because the converter is stupidly case sensitive, and also refers to category channels as just "channels"
    ):
        if channel is None:
            channel = ctx.channel

        if category is None:
            # get the default category ID (or None) from settings
            archivecategory = to_client.archivecategory(
                ctx, firecord.get_guild_data(str(ctx.guild.id))["archivecategory"]
            )
            if archivecategory is None:
                category = await self.create_archive_category(ctx)
            else:
                category = archivecategory[2]
                # category was deleted, just create a new one
                if category is None:
                    category = await self.create_archive_category(ctx)
        else:
            category_obj = discord.utils.find(
                lambda c: c.name.lower() == category.lower(),
                ctx.guild.categories,
            )
            if category_obj is not None:
                category = category_obj
            else:
                raise commands.BadArgument(
                    self.module_info["errors"]["InvalidCategory"].format(
                        category=category
                    )
                )

        await channel.edit(
            category=category,
            sync_permissions=True,
            topic="Archived"
            if not channel.topic or channel.topic.startswith("Archived: ")
            else f"Archived: {channel.topic}",
        )

        await ctx.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={"channel": channel.mention, "category": category.name},
            )
        )

    @has_access()
    @commands.command(aliases=["unhide", "reopen"])
    async def unarchive(
        self,
        ctx,
        channel: typing.Optional[discord.TextChannel] = None,
        category=None,
    ):

        if channel is None:
            channel = ctx.channel

        topic = channel.topic
        if channel.topic.startswith("Archived: "):
            topic = channel.topic[9:]
        elif channel.topic.startswith("Archived"):
            topic = ""

        if category is None:
            await channel.edit(
                topic=topic,
                overwrites={ctx.guild.default_role: discord.PermissionOverwrite()},
            )
        else:
            category_obj = discord.utils.find(
                lambda c: c.name.lower() == category.lower(),
                ctx.guild.categories,
            )
            if category_obj is not None:
                category = category_obj
                await channel.edit(
                    topic=topic,
                    overwrites={ctx.guild.default_role: discord.PermissionOverwrite()},
                    category=category,
                )
            else:
                raise commands.BadArgument(
                    self.module_info["errors"]["InvalidCategory"].format(
                        category=category
                    )
                )

        await ctx.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={
                    "channel": channel.mention,
                    "category_message": ""
                    if category is None
                    else f" in category {category.name}",
                },
            )
        )


def setup(bot):
    bot.add_cog(Archive(bot))
