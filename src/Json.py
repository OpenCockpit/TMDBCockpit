# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


from .Debug import logger


class Json():
    def __init__(self):
        return

    def parseJson(self, result, source, keys):
        for key in keys:
            self.parseJsonSingle(result, source, key)

    def parseJsonSingle(self, result, source, key):
        # a missing key (or null) is the text "None": the screens compare with it
        value = "None"
        if isinstance(source, dict) and key in source:
            value = source[key]
        if value is None:
            value = "None"
        result[key] = value

    @staticmethod
    def asList(value):
        """The entries of a list of the answer: a missing list is the text "None", which must not be looped over."""
        return value if isinstance(value, list) else []

    @staticmethod
    def year(date):
        """The year of a date "2024-05-17", "" if there is no date."""
        return date[:4] if isinstance(date, str) and date != "None" else ""

    @staticmethod
    def number(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def parseJsonList(self, result, key, separator):
        logger.info("result: %s, key: %s, separator: %s", result, key, separator)
        alist = ""
        if key in result:
            logger.debug("key: %s", result[key])
            for source in result[key]:
                # logger.debug("source: %s", source)
                text = str(source)
                if alist and text:
                    alist += separator + " "
                if text:
                    alist += text
            logger.debug("alist: %s", alist)
            result[key] = alist
        else:
            result[key] = ""
        logger.debug("result[key]: %s", result[key])
