import os
import sys
import time

import discord
from dotenv import load_dotenv

from client import Client
from utils.logger import init_discord_log, init_error_log
from firecord import firecord


def main():
    load_dotenv()
    init_discord_log()
    init_error_log()

    client = Client()
    firecord.initialize_bot(client)
    client.start_bot()


if __name__ == "__main__":
    main()
