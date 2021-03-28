import os
import sys
import time

import discord
from dotenv import load_dotenv

from client import Client
from utils.logger import init_discord_log, init_error_log


def main():
    load_dotenv()
    init_discord_log()
    init_error_log()
    Client().start_bot()


if __name__ == "__main__":
    main()
