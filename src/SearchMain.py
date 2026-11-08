# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0

from collections import OrderedDict
from Components.config import config
from . import tmdbsimple as tmdb
from .__init__ import _
from .Debug import logger
from .Json import Json

# TMDB delivers its result lists in pages of a fixed 20 entries. The list shows PAGE_SIZE rows, so the entries
# are regrouped here: page N of the screen is entries (N-1)*PAGE_SIZE ... N*PAGE_SIZE-1 of the TMDB sequence,
# which may need one or two TMDB pages (the ones fetched last are kept, as the next screen page
# usually needs one of them again).
PAGE_SIZE = 18
TMDB_PAGE_SIZE = 20
TMDB_PAGE_CACHE_SIZE = 6
tmdb_page_cache = OrderedDict()


class SearchMain(Json):

    def __init__(self):
        Json.__init__(self)

    def getTmdbPage(self, menu_selection, text, ident, page, lang):
        """(total pages, total results, entries) of one TMDB result page."""
        key = (menu_selection, text, ident, lang, page)
        if key in tmdb_page_cache:
            tmdb_page_cache.move_to_end(key)
            return tmdb_page_cache[key]
        if menu_selection == 1:
            json_data = tmdb.Movies().now_playing(page=page, language=lang)
        elif menu_selection == 2:
            json_data = tmdb.Movies().upcoming(page=page, language=lang)
        elif menu_selection == 3:
            json_data = tmdb.Movies().popular(page=page, language=lang)
        elif menu_selection == 4:
            json_data = tmdb.Movies(ident).similar_movies(
                page=page, language=lang)
        elif menu_selection == 5:
            json_data = tmdb.Movies(ident).recommendations(
                page=page, language=lang)
        elif menu_selection == 6:
            json_data = tmdb.Movies().top_rated(page=page, language=lang)
        else:
            json_data = tmdb.Search().multi(query=text, page=page, language=lang)
        raw = {}
        self.parseJson(raw, json_data, ["total_pages", "total_results", "results"])
        total_pages = raw["total_pages"] if isinstance(raw["total_pages"], int) else 0
        total_results = raw["total_results"] if isinstance(raw["total_results"], int) else 0
        entries = raw["results"] if isinstance(raw["results"], list) else []
        del json_data
        tmdb_page_cache[key] = (total_pages, total_results, entries)
        while len(tmdb_page_cache) > TMDB_PAGE_CACHE_SIZE:
            tmdb_page_cache.popitem(last=False)
        return total_pages, total_results, entries

    def getResult(self, res, menu_selection, text, ident, page):
        logger.info("menu_selection: %s, text: %s, ident: %s, page: %s",
                    menu_selection, text, ident, page)
        lang = config.plugins.tmdbcockpit.lang.value
        first_index = (page - 1) * PAGE_SIZE
        last_index = page * PAGE_SIZE - 1
        first_tmdb_page = first_index // TMDB_PAGE_SIZE + 1
        last_tmdb_page = last_index // TMDB_PAGE_SIZE + 1
        entries = []
        tmdb_total_pages = 0
        total_results = 0
        for tmdb_page in range(first_tmdb_page, last_tmdb_page + 1):
            if tmdb_total_pages and tmdb_page > tmdb_total_pages:
                break
            tmdb_total_pages, total_results, page_entries = self.getTmdbPage(
                menu_selection, text, ident, tmdb_page, lang)
            entries += page_entries
        offset = first_index - (first_tmdb_page - 1) * TMDB_PAGE_SIZE
        results = {"results": entries[offset:offset + PAGE_SIZE]}
        # TMDB serves at most tmdb_total_pages pages, which can be fewer than total_results suggests
        reachable = min(total_results, tmdb_total_pages * TMDB_PAGE_SIZE) if total_results else tmdb_total_pages * TMDB_PAGE_SIZE
        totalpages = -(-reachable // PAGE_SIZE)
        for entry in results["results"]:
            logger.debug("entry: %s", entry)
            result = {}
            keys = ["media_type", "id", "title", "name", "release_date",
                    "first_air_date", "poster_path", "backdrop_path", "profile_path"]
            self.parseJson(result, entry, keys)

            media = result["media_type"]
            ident = result["id"]
            title_movie = result["title"]
            title_series = result["name"]
            title_person = result["name"]
            date_movie = result["release_date"]
            date_tv = result["first_air_date"]
            cover_path = result["poster_path"]
            profile_path = result["profile_path"]
            backdrop_path = result["backdrop_path"]

            title = search_title = ""
            if media == "movie" and title_movie:
                movie_label = _("Movie")
                title = f"{title_movie} ({movie_label}, {date_movie[:4]})"
                search_title = title_movie
            elif media == "tv" and title_series:
                series_label = _("Series")
                title = f"{title_series} ({series_label}, {date_tv[:4]})"
                search_title = title_series
            elif media == "person" and title_person:
                person_label = _("Person")
                title = f"{title_person} ({person_label})"
                search_title = title_person
            elif menu_selection and title_movie:
                media = "movie"
                movie_label = _("Movie")
                title = f"{title_movie} ({movie_label}, {date_movie[:4]})"
                search_title = title_movie
            else:
                media = ""

            if media == "person":
                cover_url = f"http://image.tmdb.org/t/p/{config.plugins.tmdbcockpit.cover_size.value}{profile_path}"
            else:
                cover_url = f"http://image.tmdb.org/t/p/{config.plugins.tmdbcockpit.cover_size.value}{cover_path}"
            backdrop_url = f"http://image.tmdb.org/t/p/{config.plugins.tmdbcockpit.backdrop_size.value}{backdrop_path}"

            logger.debug("ident: %s, title: %s, media: %s",
                         ident, title, media)
            if ident and title and media:
                res.append(
                    (title, ident, media, cover_url, backdrop_url, search_title))
        return totalpages, res
