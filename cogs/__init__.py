import importlib.util
from pathlib import Path
import inspect
import json
import os
import sys

import discord
from discord.ext import commands


def generate_cogs_dict():
    """returns a dictionary of CogName: Cog items. No longer used but good to have around"""
    dict = {}
    cogs_dir = os.path.dirname(__file__)
    cog_paths = [
        os.path.join(root, file)
        for root, _, files in os.walk(cogs_dir)
        for file in files
        if file.endswith("index.py")
    ]

    for cog_path in cog_paths:
        cog_name = os.path.basename(os.path.dirname(cog_path))

        spec = importlib.util.spec_from_file_location(cog_name, cog_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        name, cog = [
            class_
            for class_ in inspect.getmembers(module, inspect.isclass)
            if class_[1].__module__ == module.__name__
            and str(type(class_[1])) == "<class 'discord.ext.commands.cog.CogMeta'>"
        ][0]

        dict[name] = cog

    return dict


# cogs_dict = generate_cogs_dict()


def cogs_list():
    """returns a list of cog paths (in the form of cog.{cog_name}.index) to be used in load_extension"""
    cogs_dir = os.path.dirname(__file__)
    return [
        f"cogs.{Path(root).stem}.index"
        for root, _, files in os.walk(cogs_dir)
        for file in files
        if file.endswith("index.py")
    ]
