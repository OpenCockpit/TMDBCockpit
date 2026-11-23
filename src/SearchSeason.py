# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0

from concurrent.futures import ThreadPoolExecutor
from Components.config import config
from . import tmdbsimple as tmdb
from .Debug import logger
from .Json import Json
from .Utils import imageUrl

SEASON_WORKERS = 4


class SearchSeason(Json):
    def __init__(self):
        Json.__init__(self)

    def getSeason(self, ident, season_number, lang):
        """The details of a season, {} if the request failed (the other seasons are still shown)."""
        try:
            return tmdb.TV_Seasons(ident, season_number).info(language=lang)
        except Exception as e:
            logger.error("season %s failed: %s", season_number, str(e))
            return {}

    def getResult(self, res, ident):
        logger.info("ident: %s", ident)
        lang = config.plugins.tmdbcockpit.lang.value
        cover_size = config.plugins.tmdbcockpit.cover_size.value
        json_data = tmdb.TV(ident).info(language=lang)
        result = {}
        self.parseJson(result, json_data, ["seasons"])
        seasons = []
        for season in self.asList(result["seasons"]):
            result1a = {}
            self.parseJson(result1a, season, ["season_number", "id"])
            seasons.append(result1a)
        # one request for each season: they are made together, not one after the other
        with ThreadPoolExecutor(max_workers=SEASON_WORKERS) as executor:
            season_data = list(executor.map(lambda season: self.getSeason(ident, season["season_number"], lang), seasons))
        for season, json_data in zip(seasons, season_data):
            season_ident = season["id"]
            logger.debug("season_number: %s", season["season_number"])
            logger.debug("json_data: %s", json_data)
            result2 = {}
            self.parseJson(result2, json_data, ["name", "air_date", "title", "overview", "poster_path", "episodes"])
            year = self.year(result2["air_date"])
            title = result2["name"]
            if title != "None" and year:
                title = f"{title} ({year})"
            overview = result2["overview"] if result2["overview"] != "None" else ""
            cover_url = imageUrl(cover_size, result2["poster_path"])
            if season_ident and title != "None":
                res.append((title, cover_url, overview, season_ident))

            for names in self.asList(result2["episodes"]):
                result2a = {}
                self.parseJson(result2a, names, ["id", "name", "title", "episode_number", "overview", "still_path"])
                episode_ident = result2a["id"]
                episode_number = str(result2a["episode_number"])
                name = result2a["name"]
                episode_title = f"{episode_number:>6} {name}"
                overview = result2a["overview"] if result2a["overview"] != "None" else ""
                cover_url = imageUrl(cover_size, result2a["still_path"])
                if episode_ident and episode_ident != "None" and name != "None":
                    res.append((episode_title, cover_url, overview, episode_ident))
        return res
