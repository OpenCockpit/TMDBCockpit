# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0

import os
import threading
import requests
import requests.adapters
from twisted.internet import threads, reactor
from Components.Pixmap import Pixmap
from Tools.LoadPixmap import LoadPixmap
from .Debug import logger
from .Utils import temp_dir
from .WebRequests import WebRequests
from .FileUtils import deleteFile

# PIL is imported where it is used, in the worker thread: importing it with the plugin ran on the main thread at boot.

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
    the backdrop, which is shown and hidden together with it."""

    def __init__(self, dim):
        # Pixmap.__init__ already calls show()/hide() (GUIComponent.setVisible), which use self.dim
        self.dim = dim
        Pixmap.__init__(self)

    def show(self):
        Pixmap.show(self)
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

    @staticmethod
    def _widgetSize(widget, default=None):
        if widget and widget.instance:
            size = widget.instance.size()
            if size.width() > 0 and size.height() > 0:
                return size.width(), size.height()
        return default

    @staticmethod
    def _saveJpeg(img, path):
        # Written next to the destination and moved into place: a picture that is in the cache is displayed as it is.
        part = path + ".part"
        img.save(part, format="JPEG", quality=90)
        os.replace(part, path)

    def downloadPicture(self, widget, ident, atype, url, path):
        logger.info("atype: %s, ident: %s, url: %s, path: %s", atype, ident, url, path)
        try:
            if atype == 'backdrop':
                logger.debug("Downloading backdrop to path: %s", path)
                path_name, path_ext = os.path.splitext(path)
                path_name = os.path.basename(path_name)
                path_dir = os.path.dirname(path)
                tmp_path = os.path.join(path_dir, f"tmp_{path_name}{path_ext}")
                self.downloadFile(url, tmp_path)
                logger.debug("tmp_path: %s", tmp_path)
                try:
                    self._processBackdrop(widget, tmp_path, path)
                finally:
                    deleteFile(tmp_path)    # already gone when it was kept as the original
            else:
                logger.debug("Downloaded cover to path: %s", path)
                self.downloadFile(url, path)
                self._shrinkCover(widget, path)
        except Exception as e:
            logger.error("Error processing picture: %s", str(e))
        finally:
            reactor.callFromThread(self.displayPicture, ident, widget, path)

    def _processBackdrop(self, widget, tmp_path, path):
        """Scale the downloaded backdrop to the widget, and keep the download as the original.

        This runs on a (slow, 32 bit ARM) worker core and the result is decoded again on the main thread, so
        the cost matters:
        - JPEG draft mode decodes at 1/2, 1/4 or 1/8 size when the target is smaller (no full size decode),
        - BICUBIC with reducing_gap instead of LANCZOS,
        - one encode instead of two: the downloaded file itself is the original (".org", used by "save
          backdrop"), it used to be scaled to the widget and encoded again at quality 95."""
        from PIL import Image  # pylint: disable=import-outside-toplevel
        width, height = self._widgetSize(widget, (1920, 1080))
        logger.debug("Widget size: %dx%d", width, height)
        try:
            resample = Image.Resampling.BICUBIC
        except AttributeError:
            resample = Image.BICUBIC
        with Image.open(tmp_path) as base_img:
            base_img.draft("RGB", (width, height))
            img = base_img.convert("RGB")
        img = img.resize((width, height), resample, reducing_gap=2.0)
        logger.debug("Scaled backdrop to widget size: %dx%d", width, height)
        self._saveJpeg(img, path)
        try:
            os.replace(tmp_path, path + ".org")
        except OSError as e:
            logger.error("Error saving backdrop backup: %s", str(e))

    def _shrinkCover(self, widget, path):
        """Make sure the cover is not much larger than the widget it is displayed in.

        With the size "original" a poster is up to 2000x3000: the decode on the main thread (a 6 MP image) was
        a stall of its own. The download is kept as ".org" (used by "save cover") and the widget sized copy is
        what is displayed. A cover of the proper size (w500 for the 480x720 widget) is not touched."""
        size = self._widgetSize(widget)
        if not size:
            return
        width, height = size
        from PIL import Image  # pylint: disable=import-outside-toplevel
        with Image.open(path) as base_img:
            if base_img.width <= width * 1.25 and base_img.height <= height * 1.25:
                return
            base_img.draft("RGB", (width, height))
            img = base_img.convert("RGB")
        try:
            resample = Image.Resampling.BICUBIC
        except AttributeError:
            resample = Image.BICUBIC
        img.thumbnail((width, height), resample, reducing_gap=2.0)     # keeps the aspect ratio, never enlarges
        small = path + ".small"
        self._saveJpeg(img, small)
        os.replace(path, path + ".org")
        os.replace(small, path)
        logger.debug("Scaled cover to %dx%d", img.width, img.height)

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
