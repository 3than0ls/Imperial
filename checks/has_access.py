from cogs.settings.convert import to_client  # pylint: disable=import-error
from discord.ext import commands
from firecord import firecord  # pylint: disable=import-error
import os


def has_access():
    async def predicate(ctx, owner_id=None):
        security = to_client.security(
            ctx, firecord.get_guild_data(str(ctx.guild.id))["security"]
        )

        if owner_id is None:
            owner_id = (await ctx.bot.application_info()).owner.id

        # if the author is bot owner, allow access
        if ctx.author.id == owner_id or ctx.author.id == os.environ["OWNER_UID"]:
            return True

        if security == "none":
            return True
        elif security == "manage_server":
            return ctx.author.guild_permissions.manage_guild
        elif security == "admin":
            return ctx.author.guild_permissions.administrator
        elif security == "owner":
            return ctx.guild.owner.id == ctx.guild.author.id

    return commands.check(predicate)
