# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


from concurrent.futures import ThreadPoolExecutor
from Components.config import config
from . import tmdbsimple as tmdb
from .Debug import logger
from .Json import Json
from .Utils import imageUrl

SEASON_WORKERS = 4


class SearchPeople(Json):
    def __init__(self):
        Json.__init__(self)

    def getSeasonCredits(self, ident, season_number, lang):
        """The cast of a season, [] if TMDB has none (a failed request is no reason to lose the other seasons)."""
        try:
            return tmdb.TV_Seasons(ident, season_number).credits(language=lang)
        except Exception as e:
            logger.error("credits of season %s failed: %s", season_number, str(e))
            return {}

    def getResult(self, res, ident, media):
        logger.info("ident: %s", ident)
        json_data = {}
        lang = config.plugins.tmdbcockpit.lang.value
        if media == "movie":
            json_data = tmdb.Movies(ident).credits(language=lang)
            logger.debug("json_data: %s", json_data)
        if media == "tv":
            json_data = tmdb.TV(ident).info(
                language=lang, append_to_response="credits")
            logger.debug("json_data: %s", json_data)

        result = {}
        self.parseJson(result, json_data, ["cast", "seasons", "credits"])
        cover_size = config.plugins.tmdbcockpit.cover_size.value

        for casts in self.asList(result["cast"]):
            result2 = {}
            keys = ["id", "name", "profile_path", "character"]
            self.parseJson(result2, casts, keys)
            cover_ident = result2["id"]
            name = result2["name"]
            title = f"{result2['name']} ({result2['character']})"
            cover_url = imageUrl(cover_size, result2["profile_path"])
            if cover_ident and name != "None":
                res.append((title, name, cover_url, cover_ident))

        if media == "tv":
            seasons = []
            for season in self.asList(result["seasons"]):
                result2 = {}
                self.parseJson(result2, season, ["season_number", "id", "name", "air_date"])
                if result2["name"] != "None":
                    seasons.append(result2)
            # one request for each season: they are made together, not one after the other
            with ThreadPoolExecutor(max_workers=SEASON_WORKERS) as executor:
                credits_list = list(executor.map(
                    lambda season: self.getSeasonCredits(ident, season["season_number"], lang), seasons))
            for season, season_credits in zip(seasons, credits_list):
                name = season["name"]
                year = self.year(season["air_date"])
                title = f"{name} ({year})" if year else name
                logger.debug("title: %s", title)
                res.append((title, name, None, ""))
                result3 = {}
                self.parseJson(result3, season_credits, ["cast"])
                for casts in self.asList(result3["cast"]):
                    result4 = {}
                    keys4 = ["id", "name", "character", "profile_path"]
                    self.parseJson(result4, casts, keys4)
                    cover_ident = result4["id"]
                    name = result4["name"]
                    title = f"    {name} ({result4['character']})"
                    cover_url = imageUrl(cover_size, result4["profile_path"])
                    if cover_ident and name != "None":
                        res.append((title, name, cover_url, cover_ident))
        logger.debug("res: %s", res)
        return res
