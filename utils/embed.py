import random

from discord import Embed


class EmbedFactory(Embed):
    """a embed factory that formats the embed data"""

    def __new__(
        cls, data, formatting_data=None, error=False, error_command_string=None
    ):
        if "color" in data:
            if data["color"] == "random":
                data["color"] = random.randint(0, 16777215)
            elif data["color"] == "success":
                data["color"] = 7208711
            elif data["color"] == "error":
                data["color"] = 16715054
            elif data["color"] == "confirm":
                data["color"] = 15329284
            elif data["color"] == "cooldown":
                data["color"] = 15571792

        if error:
            if "color" not in data:
                data["color"] = 16715054
            if "title" not in data:
                data["title"] = (
                    "An Error has occured."
                    if error_command_string is None
                    else f"An error occured attempting to run `{error_command_string}`"
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
                    formatted_embed_fields.append(
                        {
                            "name": embed_field["name"].format(**kwargs),
                            "value": embed_field["value"].format(**kwargs),
                            "inline": embed_field.get("inline", False),
                        }
                    )
                formatted_data[key] = formatted_embed_fields
            elif isinstance(value, str):  # for strings, just format
                formatted_data[key] = value.format(**kwargs)
            else:  # don't modify anything else (ints, bools, etc.)
                formatted_data[key] = value
        return formatted_data
