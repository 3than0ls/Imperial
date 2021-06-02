# from utils.embed import EmbedFactory  # pylint: disable=import-error
import asyncio
import discord.ext
import discord


async def pagination(
    ctx, embed, timeout=40, max_fields=25, author_only=True, flatten=False
):
    """sends a pagination type message for users to view. timeout is reset every time a reaction is inputted, and max_fields must be below 25. be sure to not exeed the 6k total character limit of embeds"""

    embed = embed.to_dict()

    field_chunks = [
        embed["fields"][i : i + max_fields]
        for i in range(0, len(embed["fields"]), max_fields)
    ]

    pages = [
        discord.Embed.from_dict(
            {
                **embed,
                "fields": field_chunk,
                "footer": {"text": f"Page {i+1} of {len(field_chunks)}"},
            }
        )
        for i, field_chunk in enumerate(field_chunks)
    ]

    if flatten:
        for page in pages:
            return await ctx.send(embed=page)

    index = 0
    message = await ctx.send(embed=pages[index])

    if len(pages) == 1:
        return

    # add reaction to confirmation message
    await message.add_reaction("◀️")
    await message.add_reaction("▶️")

    def check(reaction, user):
        if author_only:
            return user == ctx.message.author and (
                str(reaction.emoji) == "◀️" or str(reaction.emoji) == "▶️"
            )
        else:
            return str(reaction.emoji) == "◀️" or str(reaction.emoji) == "▶️"

    while True:
        try:
            reaction, _ = await ctx.bot.wait_for(
                "reaction_add",
                timeout=timeout,
                check=check,
            )
            # modify and constratin the index
            if reaction.emoji == "◀️":
                index -= 1
            if reaction.emoji == "▶️":
                index += 1

            if index >= len(pages):
                index = 0
            elif index < 0:
                index = len(pages) - 1

            await message.edit(embed=pages[index])

        except asyncio.TimeoutError:
            return
