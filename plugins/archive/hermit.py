import auto_derby
import PIL.Image
import io
import os
import time
from typing import Text, Tuple
from auto_derby import clients
from auto_derby.clients import Client
from auto_derby import app
from auto_derby.single_mode.context import Context
import requests
import urllib.request
import tempfile


class HermitClient(Client):
    """adb client that using pure Python ADB."""

    action_wait = 0.1

    def __str__(self) -> str:
        return "hermit"

    def __init__(self, address: Text):
        _, hostname, port = address.split(":", 3)

        self.link = "http://%s:%s" % (hostname, port)
        app.log.text("link: %s" % self.link, level=app.DEBUG)

        self._height, self._width = 0, 0
        self.offset = (0, 0, 0, 0)

    def request(self, route: str, timeout=3, *args, **kwargs):
        return requests.get(self.link + route, timeout=timeout, *args, **kwargs)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def tap(self, point: Tuple[int, int]) -> None:
        x, y = point
        result = self.request("/click?x={0}&y={1}".format(x, y)).json()
        time.sleep(self.action_wait)
        if result["code"]:
            return result["msg"]
        return True

    def load_size(self):
        result = self.request("/data/screen").json()["data"]
        self._width = result["width"]
        self._height = result["height"]
        if self._width > self._height:  # handle orientation
            self._height, self._width = self._width, self._height
        app.log.text(
            "screen size: width=%d height=%d" % (self.width, self.height),
            level=app.DEBUG,
        )

    def screenshot(self) -> PIL.Image.Image:
        while True:
            result = self.request("/image/screen?t=6000", timeout=8, stream=True)
            if result.status_code == 200:
                img = PIL.Image.open(result.raw)
                return img
            elif result.status_code == 500:
                app.log.text(
                    "Cannot start already started MediaProjection",
                    level=app.WARN,
                )
                time.sleep(3)
            else:
                app.log.text(
                    "screenshot request is invalid: %s" % (result.status_code),
                    level=app.WARN,
                )

    def setup(self) -> None:
        self.load_size()

    def swipe(
        self, point: Tuple[int, int], *, dx: int, dy: int, duration: float = 1
    ) -> None:
        x1, y1 = point
        x2, y2 = x1 + dx, y1 + dy
        result = self.request(
            "/swipe?x1={0}&y1={1}&x2={2}&y2={3}".format(x1, y1, x2, y2)
        ).json()
        time.sleep(self.action_wait)
        if result["code"]:
            return False
        return True


class Plugin(auto_derby.Plugin):
    """Use hermit as client (extremely slow when a screenshot need 6 seconds)"""
    def install(self) -> None:
        _next_client = auto_derby.config.client

        def _client():
            if not auto_derby.config.ADB_ADDRESS.lower().startswith("hermit:"):
                return _next_client()
            return HermitClient(auto_derby.config.ADB_ADDRESS)

        auto_derby.config.client = _client


auto_derby.plugin.register(__name__, Plugin())
