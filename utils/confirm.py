from utils.embed import EmbedFactory  # pylint: disable=import-error
import asyncio


async def confirm(ctx, prompt, timeout=30, color=None):
    confirmation_message = await ctx.send(
        embed=EmbedFactory(
            {
                "title": "Confirm Decision",
                "description": f"{prompt}\n\nRespond with :white_check_mark: to confirm, or with :x: to deny.",
                "color": "confirm",
            }
        ),
    )

    # add reaction to confirmation message
    await confirmation_message.add_reaction("✅")
    await confirmation_message.add_reaction("❌")

    try:
        reaction, _ = await ctx.bot.wait_for(
            "reaction_add",
            timeout=timeout,
            check=lambda r, u: u == ctx.message.author
            and (str(r.emoji) == "✅" or str(r.emoji) == "❌"),
        )
    except asyncio.TimeoutError:
        await confirmation_message.edit(
            embed=EmbedFactory(
                {
                    "title": "Confirmation Timed Out",
                    "description": f"{prompt}\n\nUser did not respond after {timeout} seconds, so the confirmation was timed out.",
                    "color": "confirm",
                }
            ),
        )
        return False

    if reaction.emoji == "✅":
        await confirmation_message.edit(
            embed=EmbedFactory(
                {
                    "title": "Confirmed Decision",
                    "description": f"{prompt}\n\n**✅ Decision Confirmed.**",
                    "color": "success",
                }
            ),
        )
        return True
    elif reaction.emoji == "❌":
        await confirmation_message.edit(
            embed=EmbedFactory(
                {
                    "title": "Denied Decision",
                    "description": f"{prompt}\n\n**❌ Decision Denied.**",
                    "color": "error",
                }
            ),
        )
    return False