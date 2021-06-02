from discord.ext import commands
from cogs.profile.helper import convert_to_roles  # pylint: disable=import-error
from firecord import firecord  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from utils.confirm import confirm  # pylint: disable=import-error
from utils.pagination import pagination  # pylint: disable=import-error
from checks.has_access import has_access  # pylint: disable=import-error

# move Profile storage to backend
# possibly link member id(s?) to a profile, and when an update_all_profiles is called, all profiles are update to be whatever the roles of the current member is


class Profile(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.profile_role_limit = 16

    @has_access()
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

    @has_access()
    @profile.command(require_var_positional=True, aliases=["add", "new"])
    async def create(self, ctx, profile_name, *role_sources):
        if len(profile_name) > 32 or "/" in profile_name:
            raise commands.BadArgument(
                self.commands_info["profile"]["subcommands"]["create"]["errors"][
                    "IllegalName"
                ]
            )

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

        if firecord.profile_exists(str(ctx.guild.id), profile_name):
            if not await confirm(
                ctx,
                f'The profile "{profile_name}" already exists. Creating a profile with this name will override and replace the old one. Are you sure you want to proceed?',
            ):
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

    @has_access()
    @profile.command(require_var_positional=True, aliases=["list", "all"])
    async def _list(self, ctx, order="alphabetical"):
        # perhaps a with typing()...
        profile_list = firecord.profile_list(str(ctx.guild.id))

        if order == "created" or order == "date":
            profile_list = sorted(profile_list, key=lambda profile: profile["created"])
        elif order == "creator":
            profile_list = sorted(profile_list, key=lambda profile: profile["creator"])
        elif (
            order == "length"
            or order == "roles"
            or order == "number"
            or order == "size"
        ):
            profile_list = sorted(
                profile_list, key=lambda profile: len(profile["profile_roles"])
            )
        else:  # default to alphabetical
            profile_list = sorted(profile_list, key=lambda profile: profile["name"])

        await pagination(
            ctx,
            EmbedFactory(
                {
                    **self.commands_info["profile"]["subcommands"]["_list"]["embed"],
                    "fields": [
                        {
                            "name": profile["name"],
                            "value": f'Contains **{len(profile["profile_roles"])}** roles.',
                            "inline": True,
                        }
                        for profile in profile_list
                    ],
                },
                {
                    "server_name": ctx.guild.name,
                    "profiles_num": str(len(profile_list)),
                    "prefix": ctx.prefix,
                },
            ),
        )

    @commands.command()
    async def profiles(self, ctx):
        await ctx.invoke(self.bot.get_command("profile _list"))


def setup(bot):
    bot.add_cog(Profile(bot))
