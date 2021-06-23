import logging
import datetime

log = logging.getLogger("discord")
log.setLevel(logging.INFO)
handler = logging.FileHandler(
    filename=f"logs/discord-{datetime.datetime.now().strftime('%m/%d/%YT%H:%M:%S')}.log",
    encoding="utf-8",
    mode="w",
)
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
log.addHandler(handler)