# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0

import os
import threading
import requests
import requests.adapters
from twisted.internet import threads, reactor
from enigma import gRGB
from Components.config import config
from Components.Pixmap import Pixmap
from Tools.LoadPixmap import LoadPixmap
from .Debug import logger
from .Utils import temp_dir
from .WebRequests import WebRequests
from .FileUtils import deleteFile

_download_session = None
_download_session_lock = threading.Lock()


def _getDownloadSession():
    # One session for all picture downloads: the cover and the backdrop come from the same host, and scrolling through
    # a list asks for a new pair on every stop, so the connection (and its TLS handshake) is reused.
    global _download_session  # pylint: disable=global-statement
    with _download_session_lock:
        if _download_session is None:
            _download_session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(pool_connections=2, pool_maxsize=8)
            _download_session.mount("http://", adapter)
            _download_session.mount("https://", adapter)
        return _download_session


class BackdropPixmap(Pixmap):
    """The backdrop widget. The dimming is not part of the picture: it is a translucent label of the skin ("backdropdim") over
    the backdrop, which is shown and hidden together with it. How dark it is, is the setting "backdrop_dim" (percent)."""

    def __init__(self, dim):
        # Pixmap.__init__ already calls show()/hide() (GUIComponent.setVisible), which use self.dim
        self.dim = dim
        Pixmap.__init__(self)
        config.plugins.tmdbcockpit.backdrop_dim.addNotifier(self.applyDim, initial_call=False)

    def destroy(self):
        config.plugins.tmdbcockpit.backdrop_dim.removeNotifier(self.applyDim)
        Pixmap.destroy(self)

    def applyDim(self, *_args):
        """The color of the haze: black, as opaque as the setting says. The alpha of a color is the transparency: 0 is opaque."""
        instance = self.dim.instance
        if instance:
            alpha = round(255 * (100 - int(config.plugins.tmdbcockpit.backdrop_dim.value)) / 100)
            instance.setBackgroundColor(gRGB(alpha << 24))
            instance.invalidate()

    def show(self):
        Pixmap.show(self)
        self.applyDim()
        self.dim.show()

    def hide(self):
        Pixmap.hide(self)
        self.dim.hide()


class Picture(WebRequests):
    def __init__(self):
        WebRequests.__init__(self)
        self.ident = None

    def showPicture(self, widget, atype, ident, url):
        logger.info("atype: %s, ident: %s, url: %s", atype, ident, url)
        self.ident = ident
        path = os.path.join(temp_dir, f"{atype}{ident}.jpg")
        if url and not url.endswith("None") and not os.path.isfile(path):
            threads.deferToThread(self.downloadPicture, widget, ident, atype, url, path)
        else:
            self.displayPicture(ident, widget, path)

    def downloadFile(self, url, path):
        """Stream download of a picture.

        The file is written next to its destination and moved into place when complete: a cover/backdrop that
        is already in the cache is shown as it is, so a download that failed halfway (or is still running when
        the same picture is asked for again) must never leave a truncated file under the final name."""
        logger.info("url: %s, path: %s", url, path)
        headers = {"user-agent": self.getUserAgent()}
        part = path + ".part"
        response = _getDownloadSession().get(url, headers=headers, stream=True, allow_redirects=True, verify=False, timeout=30)
        try:
            logger.debug("response.url: %s", response.url)
            logger.debug("response.status_code: %s", response.status_code)
            response.raise_for_status()
            with open(part, 'wb') as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:  # filter out keep-alive chunks
                        f.write(chunk)
            os.replace(part, path)
        except BaseException:
            deleteFile(part)
            raise
        finally:
            response.close()
        return True

    def downloadPicture(self, widget, ident, atype, url, path):
        logger.info("atype: %s, ident: %s, url: %s, path: %s", atype, ident, url, path)
        try:
            self.downloadFile(url, path)
        except Exception as e:
            logger.error("Error downloading picture: %s", str(e))
        finally:
            reactor.callFromThread(self.displayPicture, ident, widget, path)

    def displayPicture(self, ident, widget, path):
        logger.info("...")
        if widget and widget.instance and ident == self.ident:
            if path and os.path.isfile(path):
                # Release the currently displayed picture's accelerated
                # surface before decoding+loading the new one instead of
                # letting both exist in accelerated/ION memory at once for
                # the duration of the swap - each cover/backdrop is a
                # full-screen-sized decoded image, and on a device with a
                # small ION pool, rapid list navigation (a new picture per
                # selection change) can otherwise exhaust it and crash
                # (seen as repeated "[gAccel] alloc failed" followed by a
                # segfault once ION_IOC_ALLOC itself fails).
                widget.instance.setPixmap(None)
                widget.instance.setPixmap(LoadPixmap(path))
                widget.show()
            else:
                logger.debug("picture does not exist: %s", path)
                widget.hide()
