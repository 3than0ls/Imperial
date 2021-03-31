import random

from discord import Embed


class EmbedFactory(Embed):
    """a embed factory that formats the embed data"""

    def __new__(
        cls, data, formatting_data=None, error=False, error_command_string=None
    ):
        if hasattr(data, "color") and data["color"] == "random":
            data["color"] = random.randint(0, 16777215)

        if error:
            if not hasattr(data, "color"):
                data["color"] = 16715054
            if not hasattr(data, "title"):
                data["title"] = (
                    "An Error has occured."
                    if error_command_string is None
                    else f"An Error occured attempting to run `{error_command_string}`"
                )

        if formatting_data:
            formatted_data = EmbedFactory.format_text(data, **formatting_data)
            return Embed.from_dict(formatted_data)
        else:
            return Embed.from_dict(data)

    @staticmethod
    def format_text(data, **kwargs):
        formatted_data = {}
        for key, value in data.items():
            if isinstance(
                value, dict
            ):  # for nested dictionaries, recursively call format_text
                formatted_data[key] = EmbedFactory.format_text(value, **kwargs)
            elif isinstance(
                value, list
            ):  # for embed fields list, iterate through and format
                formatted_embed_fields = []
                for embed_field in value:
                    formatted_embed_field = {}
                    formatted_embed_field["name"] = embed_field["name"].format(**kwargs)
                    formatted_embed_field["value"] = embed_field["value"].format(
                        **kwargs
                    )
                    formatted_embed_fields.append(
                        {**embed_field, **formatted_embed_field}
                    )
                formatted_data[key] = formatted_embed_fields
            elif isinstance(value, str):  # for strings, just format
                formatted_data[key] = value.format(**kwargs)
            else:  # don't modify anything else (ints, bools, etc.)
                formatted_data[key] = value
        return formatted_data
