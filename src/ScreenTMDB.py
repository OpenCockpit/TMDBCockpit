# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0

from twisted.internet import threads, reactor
from . import tmdbsimple as tmdb
from .Utils import cleanText
from .Debug import logger
from .SearchTMDB import SearchTMDB
from .SearchMovie import SearchMovie
from .Utils import getApiKey


class ScreenTMDB():
    def __init__(self, text, callback):
        tmdb.API_KEY = getApiKey()

        self.result1 = []
        self.result2 = {}
        self.callback = callback
        self.text = cleanText(text)
        logger.debug("text: %s", self.text)
        self.search_iteration = 0
        self.search_words = self.text.split(" ")
        if self.text:
            self.search([])
        else:
            self.callback({})

    def search(self, result):
        if self.search_iteration and self.search_words:
            del self.search_words[-1]
            text = " ".join(self.search_words)
        else:
            text = self.text
        if not result and text:
            self.search_iteration += 1
            logger.debug("iteration: %s, text: >%s<",
                         self.search_iteration, text)
            threads.deferToThread(self.getData, text, self.search)
        else:
            self.gotData(result)

    def getData(self, text, callback):
        try:
            result = SearchTMDB().getResult(self.result1, text)
        except Exception as e:
            logger.error("search failed: %s", e)
            result = []
        reactor.callFromThread(callback, result)

    def gotData(self, result):
        logger.info("result: %s", result)
        if result:
            current = result[0][0]
            logger.debug("current: %s", current)
            # the details are another request to TMDB: not on the main thread
            threads.deferToThread(self.getDetails, current[1], current[2], current[3])
        else:
            self.callback({})

    def getDetails(self, ident, media, cover_url):
        result = {}
        try:
            result = SearchMovie().getResult(self.result2, ident, media)
            result["cover_url"] = cover_url
        except Exception as e:
            logger.error("details of %s failed: %s", ident, e)
            result = {}
        logger.debug("result: %s", result)
        reactor.callFromThread(self.callback, result)
