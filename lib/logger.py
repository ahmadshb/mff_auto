import logging
import sys

LOGS_FOLDER = "logs"

root = logging.getLogger()
root.setLevel(logging.DEBUG)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh = logging.FileHandler("logs/debug.log", mode='a')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

root.addHandler(ch)
root.addHandler(fh)


def get_logger(name):
    return logging.getLogger(name)
