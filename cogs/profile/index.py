import discord
from discord.ext import commands
from cogs.profile.helper import convert_to_roles  # pylint: disable=import-error
from firecord import firecord  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from utils.confirm import confirm  # pylint: disable=import-error

# move Profile storage to backend
# possibly link member id(s?) to a profile, and when an update_all_profiles is called, all profiles are update to be whatever the roles of the current member is


class Profile(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.profile_role_limit = 16

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

        if len(profile_roles) > self.profile_role_limit:
            raise commands.BadArgument(
                self.commands_info["profile"]["subcommands"]["create"]["errors"][
                    "TooManyRoles"
                ].format(
                    profile_role_limit=self.profile_role_limit,
                    profile_role_number=len(profile_roles),
                )
            )

        if firecord.profile_exists(str(ctx.guild.id), profile_name) and await confirm(
            ctx,
            f'The profile "{profile_name}" already exists. Creating a profile with this name will override and replace the old one. Are you sure you want to proceed?',
        ):
            pass
        else:
            return

        # sort the roles by position
        profile_roles = sorted(
            profile_roles, key=lambda role: role.position, reverse=True
        )

        firecord.profile_create(
            str(ctx.guild.id),
            ctx.author.id,
            profile_name,
            [role.id for role in profile_roles],
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

    @commands.command()
    async def testconfirm(self, ctx):
        print("a")
        await confirm(ctx, "prompt")
        print("b")


def setup(bot):
    bot.add_cog(Profile(bot))
