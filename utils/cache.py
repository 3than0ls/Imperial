from collections import defaultdict

##### https://stackoverflow.com/questions/19189274/nested-defaultdict-of-defaultdict


def _cache():
    return defaultdict(_cache)


# cache can be accessed by importing it from this file, alternatively it should be assigned a .cache property in client.py for cogs to access
cache = _cache()
