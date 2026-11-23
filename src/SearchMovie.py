# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0

from Components.config import config
from . import tmdbsimple as tmdb
from .__init__ import _
from .Debug import logger
from .Json import Json
from .Parsers import Parsers


class SearchMovie(Parsers, Json):
    def __init__(self):
        Parsers.__init__(self)
        Json.__init__(self)

    def getInfo(self, ident, media, lang):
        if media == "movie":
            return tmdb.Movies(ident).info(language=lang, append_to_response="videos,credits,releases")
        return tmdb.TV(ident).info(language=lang, append_to_response="videos,credits,content_ratings")

    def getResult(self, result, ident, media):
        logger.debug("ident: %s, media: %s", ident, media)
        keys_movie = ["title", "original_title", "overview", "year", "vote_average", "vote_count", "runtime", "production_countries",
                      "production_companies", "genres", "tagline", "release_date", "seasons", "videos", "credits", "releases"]
        keys_tv = keys_movie + ["name", "first_air_date", "origin_country", "created_by",
                                "networks", "number_of_seasons", "number_of_episodes", "credits", "content_ratings"]
        if media not in {"movie", "tv"}:
            return result
        self.parseJson(result, self.getInfo(ident, media, config.plugins.tmdbcockpit.lang.value), keys_movie if media == "movie" else keys_tv)
        for key in ("title", "original_title", "name", "overview", "tagline"):
            if result.get(key) == "None":
                result[key] = ""
        if not result["overview"]:
            # nothing in the selected language: the texts (and only those) in english
            english = {}
            self.parseJson(english, self.getInfo(ident, media, "en"), ["overview", "tagline"])
            for key in ("overview", "tagline"):
                if not result[key] and english[key] != "None":
                    result[key] = english[key]

        # base for movie and tv series
        result["year"] = self.year(result["release_date"])
        result["rating"] = f"{self.number(result['vote_average']):.1f}"
        result["votes"] = str(result["vote_count"])
        result["votes_brackets"] = f"({str(result['vote_count'])})"
        min_label = _("min")
        result["runtime"] = f"{result['runtime']} {min_label}" if self.number(result["runtime"]) > 0 else ""

        self.parseCountry(result)
        self.parseGenre(result)
        self.parseCast(result)
        self.parseCrew(result)
        self.parseStudio(result)
        self.parseFsk(result, media)

        if media == "movie":
            result["seasons"] = ""
            self.parseMovieVideos(result)

        elif media == "tv":
            # modify data for TV/Series
            result["year"] = self.year(result["first_air_date"])

            self.parseTVCountry(result)
            self.parseTVCrew(result)
            self.parseTVStudio(result)
            self.parseTVSeasons(result)

        result["fulldescription"] = \
            f"{result['tagline']}\n" \
            + f"{result['genre']}, {result['country']}, {result['year']}\n\n" \
            + f"{result['overview']} \n\n" \
            + f"{result['cast']}\n{result['crew']}\n{result['seasons']}\n"
        logger.debug("result: %s", result)
        return result
