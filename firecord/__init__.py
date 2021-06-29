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
        self.rr_map = {}
        self.responder_map = {}

    def initialize_bot(self, bot):
        """add discord bot client to firecord to be used. must be called for prefix map to work, and may be used in other methods"""
        self.bot = bot
        guilds_collection = self.firestore.collection("guilds")
        self.init_prefix_map(guilds_collection)
        self.init_rr(guilds_collection)
        self.init_responder(guilds_collection)

    # --------- DISCORD BOT PREFIX METHODS ---------
    def init_prefix_map(self, guilds):
        """initialize the prefix map by fetching all values from firestore and mapping them"""
        # get the guild collections
        # get snapshot from every document in the guilds collection
        guild_snapshots = map(lambda ref: ref.get(), guilds.list_documents())
        # use a dict comprehension to map guild id to prefix
        self.prefix_map = {
            str(snapshot.id): snapshot.get("prefix") for snapshot in guild_snapshots
        }
        # all the lines above could be simplified to one line, but that'd be terribly messy
        return self.prefix_map

    def update_prefix_map(self, guild_id: str, new_prefix=None):
        """should be called if a prefix will be changed. Changing the prefix, refetching all guilds prefix (in init_prefix_map) and then mapping is slower."""
        guild_id = str(guild_id)
        if new_prefix is None or new_prefix == "":
            new_prefix = DEFAULT_CONFIG.get("prefix", ">")

        self.prefix_map[guild_id] = new_prefix
        return self.prefix_map

    # --------- SINGLE GUILD RELATED METHODS ---------
    def init_guild(self, guild_id: str):
        """simply create a document in the database with the default config. returns the default config"""
        guild_id = str(guild_id)
        snapshot = self.firestore.document(f"guilds/{guild_id}")
        snapshot.set(DEFAULT_CONFIG)
        self.update_prefix_map(guild_id)
        return DEFAULT_CONFIG

    def use_guild(self, guild_id: str, get_snapshot: bool = True):
        """return a [DocumentRef, DocumentSnapshot, dict] to be used, and also if the guild id isn't in the database, create it using default settings."""
        guild_id = str(guild_id)
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
        guild_id = str(guild_id)
        return self.use_guild(guild_id)[2]

    def set_guild_data(self, guild_id: str, new_values: dict) -> dict:
        """update guild data from guild_id (str or int) parameter and an update_dict. If guild doesn't exist in firestore, create it using default values and return that.
        Ensure that the guild_id is the ID of a guild, as it will create a collection using this ID regardless of the value of guild_id.
        Update nested values in new_values parameter by using foo.bar: 1 rather than creating a nested object foo: { bar: 1 }, as described in firebase docs."""
        guild_id = str(guild_id)
        ref, *_ = self.use_guild(guild_id)
        ref.update(new_values)

        if "prefix" in new_values:
            self.update_prefix_map(guild_id, new_values["prefix"])

        # return new values from new snapshot
        return ref.get().to_dict()

    def reset_guild_data(self, guild_id: str) -> dict:
        """reset the guild data collection to default config. An alias for init_guild as they do the exact same thing."""
        guild_id = str(guild_id)
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

    # --------- GUILD PROFILE METHODS -------------
    def profile_exists(self, guild_id: str, profile_name: str):
        guild_id = str(guild_id)
        ref, *_ = self.use_guild(guild_id)
        return ref.collection("profiles").document(profile_name).get().exists

    def profile_create(self, guild_id: str, author_id, profile_name, profile_role_ids):
        guild_id = str(guild_id)
        """create a profile in specified guild"""
        ref, *_ = self.use_guild(guild_id)
        ref.collection("profiles").document(profile_name).set(
            {
                "profile_roles": profile_role_ids,
                "name": profile_name,
                "creator": author_id,
                "created": firestore.SERVER_TIMESTAMP,  # pylint: disable=no-member
            }
        )

    def profile_list(self, guild_id: str):
        """list all profiles from a guild"""
        guild_id = str(guild_id)
        ref, *_ = self.use_guild(guild_id=guild_id)
        profiles = ref.collection("profiles").stream()

        return [profile.to_dict() for profile in profiles]

    def profile_get(self, guild_id: str, profile_name: str):
        """gets the profile information of the specified profile_name profile"""
        guild_id = str(guild_id)
        ref, *_ = self.use_guild(guild_id=guild_id)
        profile = ref.collection("profiles").document(profile_name).get()

        return profile if profile.exists else None

    def profile_delete(self, guild_id: str, profile_name: str):
        """deletes profile_name profile"""
        guild_id = str(guild_id)
        ref, *_ = self.use_guild(guild_id=guild_id)
        profile = ref.collection("profiles").document(profile_name)
        return profile.delete()

    def profile_edit_roles(self, guild_id: str, profile_name: str, new_roles):
        """replaces the roles in profile_roles (in the event a role does not exist anymore)"""
        guild_id = str(guild_id)
        ref, *_ = self.use_guild(guild_id=guild_id)
        profile = ref.collection("profiles").document(profile_name)
        profile.update({"profile_roles": new_roles})
        return profile.get()

    # --------- REACTION ROLE METHODS -------------
    def init_rr(self, guilds):
        """initialize the reaction_role map by fetching all values from reaction_roles collection from guilds from firestore"""
        guild_snapshots = [ref.get() for ref in guilds.list_documents()]
        self.rr_map = {
            str(snapshot.id): {
                str(rr.id): rr.get().to_dict()
                for rr in list(
                    snapshot.reference.collection("reaction_roles").list_documents()
                )
            }
            for snapshot in guild_snapshots
        }
        return self.rr_map

    def rr_create(self, guild_id: str, channel_id: int, message_id: int, rr_info):
        """creates a reaction role map. has a strange structure.
        the key to a reaction_role map is a channel_id-message_id string, and is assigned
        to a map of emoji to a dictioanry containing 2 keys,
        type (either role or profile) and id (id of role or profile)"""
        guild_id = str(guild_id)
        ref, *_ = self.use_guild(guild_id)
        ref.collection("reaction_roles").document(f"{channel_id}-{message_id}").set(
            rr_info
        )

    def rr_delete(self, guild_id: str, channel_id: int, message_id: int):
        """
        deletes a rr_info entry from firebase
        any reaction roles that may have been deleted on discord will remain on firebase when bot is offline
        may also occur if it is a bulk delete as it may not trigger on_raw_message_delete
        """
        guild_id = str(guild_id)
        ref, *_ = self.use_guild(guild_id=guild_id)
        rr_info = ref.collection("reaction_roles").document(
            f"{channel_id}-{message_id}"
        )
        return rr_info.delete()

    # --------- RESPONDER METHODS -------------
    def init_responder(self, guilds):
        guild_snapshots = [ref.get() for ref in guilds.list_documents()]
        self.responder_map = {
            str(snapshot.id): {
                str(
                    responder.id
                ): responder.get().to_dict()  # will have some unnecesary unused values such as timestamp that won't be used alongside responder_map
                for responder in list(
                    snapshot.reference.collection("responders").list_documents()
                )
            }
            for snapshot in guild_snapshots
        }
        return self.responder_map

    def responder_create(self, guild_id: str, author_id: str, responder_info):
        guild_id = str(guild_id)
        ref, *_ = self.use_guild(guild_id)
        obj = {
            **responder_info,
            "creator": author_id,
            "created": firestore.SERVER_TIMESTAMP,  # pylint: disable=no-member
        }
        ref.collection("responders").document(responder_info["trigger"]).set(obj)

        return obj

    def responder_get(self, guild_id: str, trigger: str):
        guild_id = str(guild_id)
        ref, *_ = self.use_guild(guild_id=guild_id)
        responder = ref.collection("responders").document(trigger).get()

        return responder if responder.exists else None

    def responder_list(self, guild_id: str):
        guild_id = str(guild_id)
        ref, *_ = self.use_guild(guild_id=guild_id)
        responders = ref.collection("responders").stream()

        return [responder.to_dict() for responder in responders]

    def responder_delete(self, guild_id: str, trigger):
        guild_id = str(guild_id)
        ref, *_ = self.use_guild(guild_id=guild_id)
        return ref.collection("responders").document(trigger).delete()


firecord = Firecord()

# firecord.create_new_setting()