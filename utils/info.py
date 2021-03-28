import json
import os
import inspect

cache = {}


def get_module_info(cog_dir_path=None):
    if cog_dir_path is None:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        cog_dir_path = os.path.dirname(calframe[1].filename)

    path = os.path.join(cog_dir_path, "module_info.json")

    if os.environ["DEV"]:
        return get_json(path)
    else:
        # needs testing
        if path not in cache:
            cache[path] = get_json(path)
        return cache[path]


def get_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None