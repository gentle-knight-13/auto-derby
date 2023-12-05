import auto_derby
import PIL.Image
import io
import re
import time
from typing import Text, Tuple
from auto_derby import clients
from auto_derby.clients import Client
from auto_derby import app
from auto_derby.single_mode.context import Context
from ppadb.client import Client as AdbClient
from ppadb.device import Device as AdbDevice


class PPADBClient(Client):
    """adb client that using pure Python ADB."""

    action_wait = 0.1

    def __str__(self) -> str:
        return self._str

    def __init__(self, address: Text):
        _, arg1, arg2 = address.split(":", 3)

        self.client = AdbClient(host="127.0.0.1", port=5037)
        self._str = "ppadb"
        app.log.text("version: %s" % self.client.version(), level=app.DEBUG)

        if arg1.lower() == "usb":
            if arg2:
                self.device: AdbDevice = self.client.device(arg2)
            else:
                devices = self.client.devices()
                self.device: AdbDevice = devices[0]
            self._str = "ppadb-usb"
        else:
            self.hostname = arg1
            self.port = int(arg2)
            self.device: AdbDevice = self.client.remote_connect(arg1, arg2)
            self._str = "ppadb-tcpip"
        app.log.text("device: %s" % self.device, level=app.DEBUG)

        self._height, self._width = 0, 0
        self.offset = (0, 0, 0, 0)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def tap(self, point: Tuple[int, int]) -> None:
        x, y = point
        command = f"input tap {x} {y}"
        app.log.text("tap: %s" % command, level=app.DEBUG)
        res = self.device.shell(command)
        assert not res, res
        time.sleep(self.action_wait)

    def start_game(self):
        self.device.shell(
            "am start -n jp.co.cygames.umamusume/jp.co.cygames.umamusume_activity.UmamusumeActivity"
        )

    def load_size(self):
        res = self.device.shell("wm size")
        match = re.match(r"Physical size: \d+x\d+\r?\nOverride size: (\d+)x(\d+)", res)
        if not match:
            match = re.match(r"Physical size: (\d+)x(\d+)", res)
        assert match, "unexpected command result: %s" % res
        self._width = int(match.group(2))
        self._height = int(match.group(1))
        if self._width > self._height:  # handle orientation
            self._height, self._width = self._width, self._height
        ratio = self._width / self._height
        if ratio != 0.5625:
            if ratio < 0.5625:  # Narrower screen
                self._height = self._width / 9 * 16
            else:  # Wider screen
                self._width = self._height * 9 / 16
            self.device.shell("wm size %dx%d" % (self._width, self._height))
            self.device.shell("input keyevent KEYCODE_APP_SWITCH")
            self.device.shell("input keyevent KEYCODE_DPAD_DOWN")
            self.device.shell("input keyevent KEYCODE_DPAD_RIGHT")
            self.device.shell("input keyevent DEL")

        app.log.text(
            "screen size: width=%d height=%d" % (self.width, self.height),
            level=app.DEBUG,
        )

    def screenshot(self) -> PIL.Image.Image:
        return PIL.Image.open(io.BytesIO(self.device.screencap()))

    def setup(self) -> None:
        self.load_size()
        self.start_game()

    def swipe(
        self, point: Tuple[int, int], *, dx: int, dy: int, duration: float = 1
    ) -> None:
        x1, y1 = point
        x2, y2 = x1 + dx, y1 + dy
        duration_ms = int(duration * 1e3)
        if duration_ms < 400:
            # not work if too fast
            dx = int(dx * 400 / duration_ms)
            dy = int(dy * 400 / duration_ms)
            duration_ms = 400
        command = f"input swipe {x1} {y1} {x2} {y2} {duration_ms}"
        app.log.text("swipe: %s" % command, level=app.DEBUG)
        res = self.device.shell(
            command,
            timeout=10 + duration,
        )
        assert not res, res
        time.sleep(self.action_wait)

    def reset(self) -> None:
        self.device.shell("wm size reset")
        self.device.shell("wm density reset")


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        _next_client = auto_derby.config.client

        def _client():
            if not auto_derby.config.ADB_ADDRESS.lower().startswith("ppadb:"):
                return _next_client()
            return PPADBClient(auto_derby.config.ADB_ADDRESS)

        auto_derby.config.client = _client

        # Reset screen when end
        _next_end = auto_derby.config.on_single_mode_end

        def _default_on_single_mode_end(ctx: Context) -> None:
            if str(auto_derby.config.client).startswith("ppadb"):
                clients.current().reset()
            _next_end(ctx)

        auto_derby.config.on_single_mode_end = _default_on_single_mode_end


auto_derby.plugin.register(__name__, Plugin())
