import logging
import os

# configuring custom logger used throughout code

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

try:
    os.mkdir("./logs")
except FileExistsError:
    pass

handler = logging.FileHandler("./logs/logs.log")
handler.setLevel(logging.DEBUG)

format = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
handler.setFormatter(format)

logger.addHandler(handler)
