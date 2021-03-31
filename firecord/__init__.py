import firebase_admin
import os
import json
from firebase_admin import credentials
from firebase_admin import firestore

import timeit

# to get rid of pylint error
firestore.SERVER_TIMESTAMP = firestore.SERVER_TIMESTAMP


with open(os.path.join(os.path.dirname(__file__), "default_config.json")) as f:
    DEFAULT_CONFIG = json.load(f)


class Firecord:
    """A class that interacts with the Firebase's Firestore using data from Discord API like guild or user IDs."""

    def __init__(self):
        _cred = credentials.Certificate(
            os.path.join(os.path.dirname(__file__), "firebase.json")
        )
        self.app = firebase_admin.initialize_app(_cred)
        self.firestore = firestore.client(app=self.app)

    def initialize_bot(self, bot):
        """add discord bot client to firecord to be used. certain functions may not work without the use of the bot client"""
        self.bot = bot

    def init_guild(self, guild_id):
        """simply create a document in the database with the default config. returns the default config"""
        snapshot = self.firestore.document(f"guilds/{guild_id}")
        snapshot.set(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    def use_guild(self, guild_id):
        """return a [DocumentRef, DocumentSnapshot, dict] to be used, and also if the guild id isn't in the database, create it using default settings."""
        ref = self.firestore.document(f"guilds/{guild_id}")
        snapshot = ref.get()

        # perhaps write some logic here to check if guild id is a valid id

        if not snapshot.exists:
            self.init_guild(guild_id)
            snapshot = ref.get()

        return ref, snapshot, snapshot.to_dict()

    def get_guild_data(self, guild_id) -> dict:
        """get guild data from guild_id (str or int) parameter. If guild doesn't exist in firestore, create it using default values and return that.
        Ensure that the guild_id is the ID of a guild, as it will create a collection using this ID regardless of the value of guild_id"""
        return self.use_guild(guild_id)[2]

    def set_guild_data(self, guild_id, new_values) -> dict:
        """update guild data from guild_id (str or int) parameter and an update_dict. If guild doesn't exist in firestore, create it using default values and return that.
        Ensure that the guild_id is the ID of a guild, as it will create a collection using this ID regardless of the value of guild_id.
        Update nested values in new_values parameter by using foo.bar: 1 rather than creating a nested object foo: { bar: 1 }, as described in firebase docs."""
        ref, *_ = self.use_guild(guild_id)
        ref.update(new_values)

        # return new values from new snapshot
        return ref.get().to_dict()

    def reset_guild_data(self, guild_id) -> dict:
        """reset the guild data collection to default config. An alias for init_guild as they do the exact same thing."""
        return self.init_guild(guild_id)


firecord = Firecord()