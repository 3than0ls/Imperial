import logging

discord_logger = None


def init_discord_log():
    global discord_logger
    if discord_logger is None:
        discord_logger = logging.getLogger("discord")
        discord_logger.setLevel(logging.WARNING)
        handler = logging.FileHandler(
            filename="logs/discord.log", encoding="utf-8", mode="w"
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
        )
        discord_logger.addHandler(handler)


error_logger = None


def init_error_log():
    global error_logger
    if error_logger is None:
        logging.basicConfig(
            filename="logs/errors.log",
            format="%(asctime)s:%(levelname)s:%(name)s: %(message)s",
        )
