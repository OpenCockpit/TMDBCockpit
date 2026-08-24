# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


from enigma import eWindow
from Screens.Screen import Screen
from skin import applyAllAttributes


# Screen.applySkin() always derives its scale/resolution reference from
# getDesktop(GUI_SKIN_ID) (the 1920x1080 GUI desktop), even for a screen
# bound to a different desktop (e.g. the LCD summary desktop) via
# setDesktop(). Since self.desktop is already the correct desktop by the
# time applySkin() runs (Session.doInstantiateDialog() calls setDesktop()
# right before applySkin()), using it here instead of the hardcoded GUI
# desktop fixes both widget position/size AND font-size scaling for LCD
# Summary screens - without it, a resolution= override in skin.xml can only
# ever fix one of the two at the expense of the other, since the (wrong)
# GUI-based bounds still feeds the font-size scale factor.
#
# This is a drop-in replacement for the original method: for a normal GUI
# screen self.desktop.size() equals getDesktop(GUI_SKIN_ID).size() anyway
# (they're opened against the GUI desktop), so patching it is a no-op there
# and only changes behaviour for screens bound to a different desktop.
def _applySkin(self):
    bounds = (self.desktop.size().width(), self.desktop.size().height())
    resolution = bounds
    zPosition = 0
    for (key, value) in self.skinAttributes:
        if key in {"resolution", "baseResolution"}:
            resolution = tuple(int(x.strip()) for x in value.split(","))
        elif key == "zPosition":
            zPosition = int(value)
    if not self.instance:
        self.instance = eWindow(self.desktop, zPosition)
    if "title" not in self.skinAttributes and self.screenTitle:
        self.skinAttributes.append(("title", self.screenTitle))
    else:
        for attribute in self.skinAttributes:
            if attribute[0] == "title":
                self.setTitle(_(attribute[1]))  # noqa: F821, pylint: disable=undefined-variable
    self.scale = ((bounds[0], resolution[0]), (bounds[1], resolution[1]))
    self.skinAttributes.sort(key=lambda a: {"position": 1}.get(a[0], 0))
    applyAllAttributes(self.instance, self.desktop, self.skinAttributes, self.scale)
    self.createGUIScreen(self.instance, self.desktop)


def patchScreenApplySkin():
    if Screen.applySkin is not _applySkin:
        Screen.applySkin = _applySkin
