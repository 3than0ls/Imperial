from discord.ext import commands
from discord.ext.commands.converter import MemberConverter, UserConverter
from cogs.profile.helper import (  # pylint: disable=import-error
    convert_to_roles,
    validate_convert_roles,
)
from firecord import firecord  # pylint: disable=import-error
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from utils.confirm import confirm  # pylint: disable=import-error
from utils.proper import proper  # pylint: disable=import-error
from utils.pagination import pagination  # pylint: disable=import-error
from checks.has_access import has_access  # pylint: disable=import-error


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
    @profile.command(require_var_positional=True, aliases=["new"])
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
            str(ctx.author.id),
            str(profile_name),
            [str(role.id) for role in set(profile_roles)],
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

    @has_access()
    @commands.command()
    async def profiles(self, ctx):
        await ctx.invoke(self.bot.get_command("profile _list"))

    @has_access()
    @profile.command(require_var_positional=True, aliases=["replace"])
    async def assign(self, ctx, profile_name, *members):
        # handle/process/filter members
        member_objs = []
        for member in members:
            try:
                member_obj = await MemberConverter().convert(ctx, member)
            except commands.errors.MemberNotFound:
                raise commands.BadArgument(
                    self.commands_info["profile"]["subcommands"]["assign"]["errors"][
                        "MemberError"
                    ].format(member=member)
                )
            member_objs.append(member_obj)

        # handle/process/filter profile and profile roles
        profile = firecord.profile_get(str(ctx.guild.id), profile_name)
        if profile is None:
            raise commands.BadArgument(
                self.commands_info["profile"]["subcommands"]["assign"]["errors"][
                    "ProfileError"
                ].format(profile_name=profile_name, prefix=ctx.prefix)
            )
        profile = profile.to_dict()

        role_objs = await validate_convert_roles(ctx, profile)

        # for each member mentioned edit their roles
        for member_obj in member_objs:
            await member_obj.edit(roles=role_objs)

        await ctx.send(
            embed=EmbedFactory(
                self.commands_info["profile"]["subcommands"]["assign"]["embed"],
                formatting_data={
                    "profile_name": profile["name"],
                    "members": proper(
                        [member_obj.mention for member_obj in member_objs]
                    ),
                },
            )
        )

    @has_access()
    @profile.command(require_var_positional=True, aliases=["give"])
    async def add(self, ctx, profile_name, *members):
        """adds the profile roles to a member as opposed to replacing the members roles like how assign does"""
        # handle/process/filter members
        member_objs = []
        for member in members:
            try:
                member_obj = await MemberConverter().convert(ctx, member)
            except commands.errors.MemberNotFound:
                raise commands.BadArgument(
                    self.commands_info["profile"]["subcommands"]["assign"]["errors"][
                        "MemberError"
                    ].format(member=member)
                )
            member_objs.append(member_obj)

        # handle/process/filter profile and profile roles
        profile = firecord.profile_get(str(ctx.guild.id), profile_name)
        if profile is None:
            raise commands.BadArgument(
                self.commands_info["profile"]["subcommands"]["add"]["errors"][
                    "ProfileError"
                ].format(profile_name=profile_name, prefix=ctx.prefix)
            )
        profile = profile.to_dict()

        role_objs = await validate_convert_roles(ctx, profile)

        # for each member mentioned edit their roles
        for member_obj in member_objs:
            await member_obj.edit(
                roles=[
                    *role_objs,
                    *[role for role in member_obj.roles],
                ]
            )

        await ctx.send(
            embed=EmbedFactory(
                self.commands_info["profile"]["subcommands"]["add"]["embed"],
                formatting_data={
                    "profile_name": profile["name"],
                    "members": proper(
                        [member_obj.mention for member_obj in member_objs]
                    ),
                },
            )
        )

    @has_access()
    @profile.command(require_var_positional=True, aliases=["subtract"])
    async def remove(self, ctx, profile_name, *members):
        """removes all roles from the given profile from the members given"""
        # handle/process/filter members
        member_objs = []
        for member in members:
            try:
                member_obj = await MemberConverter().convert(ctx, member)
            except commands.errors.MemberNotFound:
                raise commands.BadArgument(
                    self.commands_info["profile"]["subcommands"]["assign"]["errors"][
                        "MemberError"
                    ].format(member=member)
                )
            member_objs.append(member_obj)

        profile = firecord.profile_get(str(ctx.guild.id), profile_name)
        if profile is None:
            raise commands.BadArgument(
                self.commands_info["profile"]["subcommands"]["add"]["errors"][
                    "ProfileError"
                ].format(profile_name=profile_name, prefix=ctx.prefix)
            )
        profile = profile.to_dict()
        # for each member mentioned edit their roles
        for member_obj in member_objs:
            await member_obj.edit(
                roles=[
                    role
                    for role in member_obj.roles
                    if str(role.id) not in profile["profile_roles"]
                ]
            )

        await ctx.send(
            embed=EmbedFactory(
                self.commands_info["profile"]["subcommands"]["remove"]["embed"],
                formatting_data={
                    "profile_name": profile["name"],
                    "members": proper(
                        [member_obj.mention for member_obj in member_objs]
                    ),
                },
            )
        )

    @has_access()
    @profile.command(require_var_positional=True, aliases=["roles"])
    async def info(self, ctx, profile_name):
        profile = firecord.profile_get(str(ctx.guild.id), profile_name)

        if profile is None:
            raise commands.BadArgument(
                self.commands_info["profile"]["subcommands"]["assign"]["errors"][
                    "ProfileError"
                ].format(profile_name=profile_name, prefix=ctx.prefix)
            )

        profile = profile.to_dict()

        await ctx.send(
            embed=EmbedFactory(
                self.commands_info["profile"]["subcommands"]["info"]["embed"],
                formatting_data={
                    "profile_name": profile["name"],
                    "created": profile["created"].strftime("%m-%d-%y"),
                    "creator": (
                        await UserConverter().convert(ctx, str(profile["creator"]))
                    ).mention,
                    "profile_roles": proper(
                        [
                            role.mention
                            for role in sorted(
                                [*await validate_convert_roles(ctx, profile)],
                                key=lambda role: role.position,
                                reverse=True,
                            )
                        ]
                    ),
                    "prefix": ctx.prefix,
                },
            )
        )

    @has_access()
    @profile.command(require_var_positional=True, aliases=["erase"])
    async def delete(self, ctx, profile_name):
        profile = firecord.profile_get(str(ctx.guild.id), profile_name)

        if profile is None:
            raise commands.BadArgument(
                self.commands_info["profile"]["subcommands"]["delete"]["errors"][
                    "ProfileError"
                ].format(profile_name=profile_name, prefix=ctx.prefix)
            )
        profile = profile.to_dict()

        if await confirm(
            ctx, f"Are you sure you want to delete the profile **{profile_name}**?"
        ):
            firecord.profile_delete(str(ctx.guild.id), profile["name"])
            await ctx.send(
                embed=EmbedFactory(
                    self.commands_info["profile"]["subcommands"]["delete"]["embed"],
                    formatting_data={
                        "profile_name": profile["name"],
                        "prefix": ctx.prefix,
                    },
                )
            )


def setup(bot):
    bot.add_cog(Profile(bot))
