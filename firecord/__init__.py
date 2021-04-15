import json
import os

import firebase_admin
from firebase_admin import credentials, firestore

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
        self.prefix_map = {}

    def initialize_bot(self, bot):
        """add discord bot client to firecord to be used. must be called for prefix map to work, and may be used in other methods"""
        self.bot = bot
        self.init_prefix_map()

    # --------- DISCORD BOT PREFIX METHODS ---------
    def init_prefix_map(self):
        """initialize the prefix map by fetching all values from firestore and mapping them"""
        # get the guild collections
        guilds_collection = self.firestore.collection("guilds")
        # get snapshot from every document in the guilds collection
        guild_snapshots = map(lambda ref: ref.get(), guilds_collection.list_documents())
        # use a dict comprehension to map guild id to prefix
        self.prefix_map = {
            snapshot.id: snapshot.get("prefix") for snapshot in guild_snapshots
        }
        # all the lines above could be simplified to one line, but that'd be terribly messy
        return self.prefix_map

    def update_prefix_map(self, guild_id: str, new_prefix=None):
        """should be called if a prefix will be changed. Changing the prefix, refetching all guilds prefix (in init_prefix_map) and then mapping is slower."""
        if new_prefix is None or new_prefix == "":
            new_prefix = DEFAULT_CONFIG.get("prefix", ">")

        self.prefix_map[guild_id] = new_prefix
        return self.prefix_map

    # --------- SINGLE GUILD RELATED METHODS ---------
    def init_guild(self, guild_id: str):
        """simply create a document in the database with the default config. returns the default config"""
        snapshot = self.firestore.document(f"guilds/{guild_id}")
        snapshot.set(DEFAULT_CONFIG)
        self.update_prefix_map(guild_id)
        return DEFAULT_CONFIG

    def use_guild(self, guild_id: str):
        """return a [DocumentRef, DocumentSnapshot, dict] to be used, and also if the guild id isn't in the database, create it using default settings."""
        ref = self.firestore.document(f"guilds/{guild_id}")
        snapshot = ref.get()

        # perhaps write some logic here to check if guild id is a valid id

        if not snapshot.exists:
            self.init_guild(guild_id)
            snapshot = ref.get()

        return ref, snapshot, snapshot.to_dict()

    def get_guild_data(self, guild_id: str) -> dict:
        """get guild data from guild_id (str or int) parameter. If guild doesn't exist in firestore, create it using default values and return that.
        Ensure that the guild_id is the ID of a guild, as it will create a collection using this ID regardless of the value of guild_id"""
        return self.use_guild(guild_id)[2]

    def set_guild_data(self, guild_id: str, new_values: dict) -> dict:
        """update guild data from guild_id (str or int) parameter and an update_dict. If guild doesn't exist in firestore, create it using default values and return that.
        Ensure that the guild_id is the ID of a guild, as it will create a collection using this ID regardless of the value of guild_id.
        Update nested values in new_values parameter by using foo.bar: 1 rather than creating a nested object foo: { bar: 1 }, as described in firebase docs."""
        ref, *_ = self.use_guild(guild_id)
        ref.update(new_values)

        if "prefix" in new_values:
            self.update_prefix_map(guild_id, new_values["prefix"])

        # return new values from new snapshot
        return ref.get().to_dict()

    def reset_guild_data(self, guild_id: str) -> dict:
        """reset the guild data collection to default config. An alias for init_guild as they do the exact same thing."""
        return self.init_guild(guild_id)

    # # --------- MULTI GUILD RELATED METHODS ---------
    # def update_new_guild_settings(self):
    #     """update all guild settings using DEFAULT_SETTINGS"""
    #     setting_keys = DEFAULT_CONFIG.keys()

    # --------- FIRESTORE INTERACTION METHODS -------------
    def create_new_setting(self):
        """used for adding a new setting in DEFAULT_CONFIG to all of the guilds in database"""
        # returns a generator of documents in the guilds collection
        transaction = self.firestore.transaction()

        # pylint: disable=no-member
        @firestore.transactional
        def add_setting(transaction, guild_documents):
            # guilds = transaction.get_all(guild_documents)
            for guild in guild_documents:
                guild_data = guild.get(transaction=transaction).to_dict()
                # DEFAULT_CONFIG should contain the new updated settings with the new setting
                # keep in mind that it creates new ones, but doesn't delete old ones that are in firestore but not in DEFAULT_CONFIG
                new_settings = {**DEFAULT_CONFIG, **guild_data}
                transaction.set(guild, new_settings)

        add_setting(transaction, self.firestore.collection("guilds").list_documents())


firecord = Firecord()