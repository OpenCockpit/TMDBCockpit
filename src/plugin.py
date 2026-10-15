# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


from Components.config import config
from Plugins.Plugin import PluginDescriptor
from .__init__ import _
from .Debug import logger
from .Version import VERSION
from . import ConfigInit  # noqa: F401, pylint: disable=unused-import
from .ScreenMain import ScreenMain
from .ScreenTMDB import ScreenTMDB
from .PluginUtils import WHERE_TMDB_SEARCH, WHERE_TMDB_MOVIELIST
from .SkinUtils import loadPluginSkin


loadPluginSkin("ScreenMain")


_epgPatched = False
EPG_CONFIGS = ("infobar", "single", "multi", "grid")   # the EPG screens with a configurable red button


def monkeyPatchAllEPGScreens():
    """Make the red key of the EPG screens open TMDBCockpit, without any change of the system.

    The EPG offers the red key as "TMDb Search" only if the plugin folder "tmdb" exists (isPluginInstalled("tmdb")),
    otherwise it is the IMDb search - also as the default of the configurable red button of the EPG screens. TMDBCockpit
    is no folder "tmdb", so three things are done here:
    - the search "openTMDb" of the EPG screens opens TMDBCockpit,
    - the EPG screens are told that "tmdb" is installed (the label of the key, and the red key of the screens
      that don't have a configurable one),
    - the configurable red button gets the TMDb search as its default instead of the IMDb one. A button the user has
      set himself is left alone, and the default is not stored: with the setting off it is the IMDb search again."""
    global _epgPatched
    if _epgPatched:
        return
    import Screens.EpgSelectionBase as epgBase

    def openTMDb(self):
        if hasattr(self, "closeEventViewDialog"):
            self.closeEventViewDialog()
        current = self["list"].getCurrent()
        event = current and current[0]
        if event is not None:
            event_name = event.getEventName()
            logger.info("EPG red button pressed, opening for event: %s", event_name)
            self.session.open(ScreenMain, event_name, 2)

    epgBase.EPGSelectionBase.openTMDb = openTMDb

    isPluginInstalled = epgBase.isPluginInstalled

    def tmdbInstalled(pluginname, *args, **kwargs):
        return True if pluginname == "tmdb" else isPluginInstalled(pluginname, *args, **kwargs)

    epgBase.isPluginInstalled = tmdbInstalled

    for name in EPG_CONFIGS:
        button = getattr(getattr(getattr(config, "epgselection", None), name, None), "btn_red", None)
        if button is not None and button.saved_value is None and button.default == "openIMDb":
            button.default = "openTMDb"
            button.value = "openTMDb"
    _epgPatched = True
    logger.info("EPG red key patched for TMDBCockpit (no system changes required)")


def showEventInfos(session, event="", service="", **__):
    if not service:
        service = session.nav.getCurrentlyPlayingServiceReference()
    if not event:
        info = session.nav.getCurrentService()
        if info:
            info = info.info()
            if info:
                event = info.getEvent(0)  # 0 = now, 1 = next
    event_name = event and event.getEventName() or (service and service.getName()) or ""
    session.open(ScreenMain, event_name, 2)


def queryEventInfos(search, callback, **__):
    logger.info("search: %s", search)
    ScreenTMDB(search, callback)


def movieList(session, service, **kwargs):
    logger.info("...")
    callback = kwargs["callback"] if "callback" in kwargs else None
    if callback:
        session.openWithCallback(callback, ScreenMain, service, 1)
    else:
        session.open(ScreenMain, service, 1)


def main(session, **__):
    session.open(ScreenMain, "", 3)


def autoStart(reason, **__):
    if reason == 0:  # startup
        logger.info("+++ Version: %s starts...", VERSION)
        # session = kwargs["session"]
        if config.plugins.tmdbcockpit.key_red.value:
            try:
                monkeyPatchAllEPGScreens()
            except Exception as e:
                logger.error("key red patch failed: %s", e)
    elif reason == 1:  # shutdown
        logger.info("--- shutdown")


def Plugins(**__):
    descriptors = [
        PluginDescriptor(
            where=[
                PluginDescriptor.WHERE_AUTOSTART,
                PluginDescriptor.WHERE_SESSIONSTART,
            ],
            fnc=autoStart,
            needsRestart=True
        ),
        PluginDescriptor(
            name="TMDBCockpit",
            description=_("TMDB Infos"),
            where=[
                WHERE_TMDB_MOVIELIST,
                PluginDescriptor.WHERE_MOVIELIST,
            ],
            fnc=movieList,
            needsRestart=True
        ),
        PluginDescriptor(
            name="TMDBCockpit",
            description=_("TMDB Infos"),
            where=[
                WHERE_TMDB_SEARCH,
            ],
            fnc=queryEventInfos,
            needsRestart=True
        ),
        PluginDescriptor(
            name=_("TMDB Infos"),
            description=_("TMDb Search"),
            where=[
                PluginDescriptor.WHERE_EVENTINFO,
                # PluginDescriptor.WHERE_CHANNEL_CONTEXT_MENU,
            ],
            fnc=showEventInfos,
            needsRestart=True
        ),
        PluginDescriptor(
            name=_("TMDBCockpit"),
            description=_("TMDB Infos"),
            where=[
                PluginDescriptor.WHERE_PLUGINMENU,
                PluginDescriptor.WHERE_EXTENSIONSMENU,
            ],
            icon="plugin.png",
            fnc=main,
            needsRestart=True
        ),
    ]
    try:
        descriptors += [
            PluginDescriptor(
                where=PluginDescriptor.WHERE_SKINCHANGE,
                fnc=loadPluginSkin
            )
        ]
    except Exception:
        pass

    return descriptors
