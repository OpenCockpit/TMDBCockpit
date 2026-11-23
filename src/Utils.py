# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


import os
import re
import base64
from .FileUtils import readFile
from .Debug import logger


temp_dir = "/var/volatile/tmp/TMDBCockpit/"
api_key_file = "/etc/enigma2/tmdb_key.txt"
image_base_url = "https://image.tmdb.org/t/p/"
# the cache of the pictures is in the RAM (/var/volatile): it is kept below this size while the screens are open
CACHE_MAX_BYTES = 48 * 1024 * 1024


def getApiKey():
    api_key = ""
    if os.path.isfile(api_key_file):
        api_key = readFile(api_key_file).strip()[:32]
    if not api_key:
        api_key = base64.b64decode(
            "M2I2NzAzYjg3MzRmZWUxYjU5OGRlOWVkN2JiZDNiNDc=")
    # logger.debug(api_key: %s", api_key)
    return api_key


def cleanText(text):
    logger.debug("text 1: %s", text)

    text = re.sub(r'\([^)]*\)', '', text).rstrip()  # remove (xyz)
    logger.debug("text 2: %s", text)

    unwanted = [":", "-", "_", ",", ".", "+", "[", "]", "(", ")"]
    for char in unwanted:
        text = text.replace(char, " ")
    logger.debug("text 3: %s", text)

    text = " ".join(text.split())  # remove multiple spaces
    logger.debug("text 4: >%s<", text)
    return text


def imageUrl(size, path):
    """The url of a picture of TMDB, "" if there is none (TMDB gives no path, or it is missing in the answer)."""
    if not path or path == "None":
        return ""
    return f"{image_base_url}{size}{path}"


def pruneCache(max_bytes=CACHE_MAX_BYTES):
    """Delete the oldest pictures of the cache when it is larger than max_bytes."""
    try:
        files = []
        total = 0
        for entry in os.scandir(temp_dir):
            if entry.is_file() and entry.name.startswith(("cover", "backdrop")) and entry.name.endswith(".jpg"):
                stat = entry.stat()
                files.append((stat.st_mtime, stat.st_size, entry.path))
                total += stat.st_size
        for _mtime, size, path in sorted(files):
            if total <= max_bytes:
                break
            os.remove(path)
            total -= size
    except OSError as e:
        logger.debug("cache: %s", str(e))
