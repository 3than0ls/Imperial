import logging
import datetime
import os


logdir = "./logs"
if not os.path.exists(logdir):
    os.makedirs(logdir)


log = logging.getLogger("discord")
log.setLevel(logging.INFO)
handler = logging.FileHandler(
    filename=f"logs/{datetime.datetime.now().strftime('%m-%d-%YT%H-%M-%S')}.log",
    encoding="utf-8",
    mode="w+",
)
handler.setFormatter(
    logging.Formatter("%(asctime)s\t\t%(levelname)s\t\t%(name)s\t\t%(message)s")
)
log.addHandler(handler)