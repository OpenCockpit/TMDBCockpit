# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


import os
import shutil
import glob
from pathlib import Path
try:
    from .Debug import logger
except ImportError:
    from Debug import logger


def stripCutNumber(path):
    filename, ext = os.path.splitext(path)
    if len(filename) > 3:
        if filename[-4] == "_" and filename[-3:].isdigit():
            filename = filename[:-4]
        path = filename + ext
    return path


def readFile(path, mode="r"):
    data = ""
    try:
        if mode == "rb":
            with open(path, mode) as f:  # pylint: disable=unspecified-encoding
                data = f.read()
        else:
            with open(path, mode, encoding="utf-8") as f:
                data = f.read()
    except Exception as e:
        logger.info("path: %s, exception: %s", path, e)
    return data


def writeFile(path, data, mode="w"):
    """Write a file; True when it is written, False (and an error in the log) if not.

    The data goes into a file next to it, which then takes the place of the old one (os.replace is atomic): an error in the middle, a full disk or
    a power failure leaves the old file as it was. It used to be truncated first, so a .cuts file (the resume point and the marks of a recording)
    could be left empty or half written."""
    tmp = os.path.join(os.path.dirname(path) or ".", f".{os.path.basename(path)}.{os.getpid()}.tmp")
    try:
        if mode == "wb":
            with open(tmp, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
        else:
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
        if os.path.isfile(path):
            shutil.copymode(path, tmp)      # the file keeps its permissions
        os.replace(tmp, path)
        return True
    except Exception as e:
        logger.error("path: %s, exception: %s", path, e)
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False


def deleteFile(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.error("path: %s, exception: %s", path, e)


def deleteFiles(path, clear=False):
    for afile in glob.glob(path):
        if clear:
            writeFile(afile, "")
        deleteFile(afile)


def touchFile(path):
    try:
        Path(path).touch()
    except Exception as e:
        logger.error("path: %s, exception: %s", path, e)


def copyFile(src_path, dest_path):
    try:
        shutil.copy2(src_path, dest_path)
    except Exception as e:
        logger.error("src: %s, dest: %s, exception: %s", src_path, dest_path, e)


def renameFile(src_path, dest_path):
    try:
        shutil.move(src_path, dest_path)
    except Exception as e:
        logger.error("src: %s, dest: %s, exception: %s", src_path, dest_path, e)


def createDirectory(path):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        logger.error("path: %s, exception: %s", path, e)


def createSymlink(src, dst):
    try:
        os.symlink(src, dst)
    except Exception as e:
        logger.error("src: %s, dst: %s, exception: %s", src, dst, e)


def deleteDirectory(path):
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.error("path: %s, exception: %s", path, e)
