from discord.ext import commands
from firecord import firecord, DEFAULT_CONFIG  # pylint: disable=import-error


def has_access():
    async def predicate(ctx):
        guild_settings = firecord.get_guild_data(str(ctx.guild.id))
        if guild_settings["security"] == "none":
            return True
        elif guild_settings["security"] == "manage_server":
            pass
        elif guild_settings["security"] == "admin"
            pass
        else: 
            # final else clause: if security is owner
            return ctx.guild.owner.id == ctx.guild.author.id



    return commands.check(predicate)