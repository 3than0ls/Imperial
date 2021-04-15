from discord.ext import commands
from firecord import DEFAULT_CONFIG, firecord  # pylint: disable=import-error


def has_access():
    async def predicate(ctx):
        guild_settings = firecord.get_guild_data(str(ctx.guild.id))

        # if the author is bot owner, allow access
        if ctx.author.id == (await ctx.bot.application_info()).owner.id:
            return True

        if guild_settings["security"] == "none":
            return True
        elif guild_settings["security"] == "manage_server":
            return ctx.author.guild_permissions.manage_guild
        elif guild_settings["security"] == "admin":
            return ctx.author.guild_permissions.administrator
        else:
            # final else clause: if security is owner
            return ctx.guild.owner.id == ctx.guild.author.id

    return commands.check(predicate)
