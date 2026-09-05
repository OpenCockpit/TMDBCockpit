# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


from pathlib import Path
from Tools.Directories import SCOPE_SKIN
from skin import loadSkin
from .ScreenSummaryFix import patchScreenApplySkin
# from .Debug import logger


def getSkinPath(file_name):
    # logger.info("file_name: %s", file_name)
    skin_path = Path(__file__).parent / "skin" / file_name
    return str(skin_path)


def loadPluginSkin(file_name="skin.xml", session=None):
    # session= is accepted (and unused) only because Enigma2's own
    # WHERE_SKINCHANGE dispatch always calls plugin callbacks as
    # fnc(session=...) - see skin.py's _notifySkinPlugins(). Without it,
    # loadPluginSkin() crashes on every skin reload for any plugin that
    # registers it that way (TypeError: unexpected keyword argument
    # 'session'), even though the initial-boot call site never passes one.
    skin_file = getSkinPath(file_name)
    loadSkin(skin_file, scope=SCOPE_SKIN)
    patchScreenApplySkin()
