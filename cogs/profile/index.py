import typing
import discord
from discord.ext import commands
from cogs.profile.helper import convert_to_roles  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error

# move Profile storage to backend
# possibly link member id(s?) to a profile, and when an update_all_profiles is called, all profiles are update to be whatever the roles of the current member is


class Profile(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)

    @commands.group(aliases=["role_group"])
    async def profile(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send(
                embed=EmbedFactory(
                    self.command_info["embed"],
                    formatting_data={
                        "prefix": ctx.prefix,
                    },
                )
            )

    @profile.command(require_var_positional=True, aliases=["get"])
    async def create(self, ctx, profile_name, *role_sources):
        # convert and flatten role sources into a list of roles
        profile_roles = [
            role
            for roles in [await convert_to_roles(ctx, r_s) for r_s in role_sources]
            for role in roles
        ]
        # filter out discord or integration managed roles
        profile_roles = filter(
            lambda role: not (
                role.is_default()
                or role.is_bot_managed()
                or role.is_premium_subscriber()
                or role.is_integration()
            ),
            profile_roles,
        )
        # sort the roles by position
        profile_roles = sorted(
            profile_roles, key=lambda role: role.position, reverse=True
        )

        await ctx.send(
            embed=EmbedFactory(
                self.commands_info["profile"]["subcommands"]["create"]["embed"],
                formatting_data={
                    "profile_name": profile_name,
                    "roles": ", ".join([role.mention for role in profile_roles]),
                    "prefix": ctx.prefix,
                },
            )
        )


def setup(bot):
    bot.add_cog(Profile(bot))
