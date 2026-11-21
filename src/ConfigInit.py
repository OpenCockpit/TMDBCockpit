# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


from Components.config import config, ConfigYesNo, ConfigSelection, ConfigSubsection
from Components.Language import language
from .LanguageSelection import LanguageSelection
from .Debug import logger


logger.info("...")
lang = language.getActiveLanguage()
logger.debug("lang: %s", lang)
lang_choices = LanguageSelection().getLangChoices(lang)
if not hasattr(config.plugins, "tmdbcockpit"):
    config.plugins.tmdbcockpit = ConfigSubsection()
# w500 is what the 480x720 cover widget needs, w1280 what the backdrop (1908x947) needs. "original" is up to 2000x3000 /
# 3840x2160: it is displayed as it is, the pixmap widget (skin: scale) scales it.
config.plugins.tmdbcockpit.cover_size = ConfigSelection(
    default="w500", choices=["w92", "w185", "w500", "original"])
config.plugins.tmdbcockpit.backdrop_size = ConfigSelection(
    default="w1280", choices=["w300", "w780", "w1280", "original"])
config.plugins.tmdbcockpit.lang = ConfigSelection(
    default=lang[:2], choices=lang_choices)
config.plugins.tmdbcockpit.skip_to_movie = ConfigYesNo(default=True)
config.plugins.tmdbcockpit.key_red = ConfigYesNo(default=True)

config.plugins.tmdbcockpit.yttrailer_best_resolution = ConfigSelection(
    default='22',
    choices=[
        ('38', '4096x3072'), ('37', '1920x1080'), ('22', '1280x720'), ('35', '854x480'),
        ('18', '640x360'), ('5', '400x240'), ('17', '176x144')
    ]
)
config.plugins.tmdbcockpit.yttrailer_useDashMP4 = ConfigYesNo(default=True)
