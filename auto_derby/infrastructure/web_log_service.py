# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations

import logging
import threading
import time
import webbrowser
from typing import Optional, Text, Tuple

from .jsonl_log_service import JsonlLogService
from .. import web
from ..services.cleanup import Service as Cleanup
from ..web import Webview

_LOGGER = logging.getLogger(__name__)


class _DefaultWebview(Webview):
    def open(self, url: Text) -> None:
        webbrowser.open(url)

    def shutdown(self) -> None:
        pass


class WebLogService(JsonlLogService):
    default_webview: Webview = _DefaultWebview()
    default_port = 8400
    default_host = "127.0.0.1"

    def __init__(
        self,
        cleanup: Cleanup,
        host: Optional[Text] = None,
        port: Optional[int] = None,
        webview: Optional[web.Webview] = None,
        buffer_path: Optional[Text] = None,
        image_path: Optional[Text] = None,
    ) -> None:
        if host is None:
            host = self.default_host
        if port is None:
            port = self.default_port
        if webview is None:
            webview = self.default_webview
        if buffer_path is None:
            buffer_path = self.default_buffer_path
        if image_path is None:
            image_path = self.default_image_path
        self.image_path = image_path
        self._always_inline_image = not buffer_path or buffer_path == ":memory:"

        self._s = web.Stream(buffer_path, "text/plain; charset=utf-8")
        self._stop = threading.Event()
        ready = threading.Event()

        def _run(address: Tuple[Text, int]):
            with self._s, web.create_server(
                address,
                web.Blob(
                    web.page.render(
                        {
                            "type": "LOG",
                            "streamURL": "/log",
                        }
                    ).encode("utf-8"),
                    "text/html; charset=utf-8",
                ),
                web.page.ASSETS,
                web.Path("/log", self._s),
                web.Route("/images/", web.Dir(self.image_path)),
            ) as httpd:

                def _on_stop():
                    self._stop.wait()
                    self._s.close()
                    httpd.shutdown()

                threading.Thread(target=_on_stop).start()
                host, port = httpd.server_address
                url = f"http://{host}:{port}"
                _LOGGER.info("web log service start at:\t%s", url)
                webview.open(url)
                ready.set()
                httpd.serve_forever()

        threading.Thread(target=_run, args=((host, port),)).start()
        cleanup.add(self.stop)
        ready.wait()
        time.sleep(1)  # wait browser
