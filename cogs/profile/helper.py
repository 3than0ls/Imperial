import discord
from discord.ext import commands
from discord.ext.commands import errors
from discord.ext.commands.converter import RoleConverter
from firecord import firecord  # pylint: disable=import-error


def role_filter(role):
    return not (
        role.is_default()
        or role.is_bot_managed()
        or role.is_premium_subscriber()
        or role.is_integration()
    )


### DISCORDPY STRING TO MEMBER/ROLE FUNCTIONS
async def convert_str_to_thing(ctx, str):
    """converts a string to either a discord Member or discord Role object"""
    try:
        return await commands.MemberConverter().convert(ctx, str)
    except errors.MemberNotFound:
        pass

    try:
        return await commands.RoleConverter().convert(ctx, str)
    except errors.RoleNotFound:
        pass

    raise errors.BadArgument(
        f'"{str}" is not a valid source of roles (could not be converted into a role or a list of roles from a member). Check if you spelled it correctly.'
    )


async def convert_to_roles(ctx, thing):
    """attempts to convert argument thing into a list of role(s). if thing is unable to be compiled into a list of roles, it throws an error"""
    roles = []
    if isinstance(thing, str):
        thing = await convert_str_to_thing(ctx, thing)

    if isinstance(thing, discord.Member):
        roles.extend(thing.roles)
    elif isinstance(thing, discord.Role):
        roles.append(thing)

    # filter out discord or integration managed roles
    roles = filter(
        role_filter,
        roles,
    )

    return roles


async def validate_convert_roles(ctx, profile):
    """validates (checks if exists) role ids in profile_roles, converts them into a role object, and return valid ones whilst deleting invalid ones"""
    valid = []
    invalid = []
    for role_id in profile["profile_roles"]:
        try:
            valid.append(await RoleConverter().convert(ctx, role_id))
        except commands.errors.RoleNotFound:
            invalid.append(role_id)

    if len(invalid) == len(profile["profile_roles"]):
        # if all roles in a profile are deleted, delete the profile and throw error
        firecord.profile_delete(ctx.guild.id, profile["name"])
        raise errors.BadArgument(
            f"The profile \"{profile['name']}\" no longer exists. The roles used by this profile have all been deleted, and so the profile was automatically deleted as well."
        )
    else:  # if only some roles are deleted, remove those from the profile on firebase
        firecord.profile_edit_roles(
            ctx.guild.id, profile["name"], [role.id for role in valid]
        )

    return list(set(valid))
