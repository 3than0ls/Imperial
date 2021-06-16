import os
from pathlib import Path


def cogs_list():
    """returns a list of cog paths (in the form of cog.{cog_name}.index) to be used in load_extension"""
    cogs_dir = os.path.dirname(__file__)
    return [
        f"cogs.{Path(root).stem}.index"
        for root, _, files in os.walk(cogs_dir)
        for file in files
        if file.endswith("index.py")
    ]
