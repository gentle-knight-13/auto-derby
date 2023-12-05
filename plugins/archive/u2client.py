import re
import auto_derby
import PIL.Image
import time
import uiautomator2 as u2
from typing import Optional, Text, Tuple
from auto_derby import clients
from auto_derby import templates
from auto_derby import action
from auto_derby import terminal
from auto_derby.clients import ADBClient
from auto_derby.scenes.team_race import CompetitorMenuScene
from auto_derby import app
import signal
import atexit


class U2Client(ADBClient):
    """adb client that using UI Automator 2."""

    action_wait = 0.6

    def __str__(self) -> str:
        return self._str

    def __init__(self, address: Text):
        _, arg1, arg2 = address.split(":", 3)
        self._str = "adb"
        if arg1.lower() == "usb":
            if arg2:
                self.device = u2.connect(arg2)
            else:
                self.device = u2.connect()
            # self._str = "u2-usb"
        else:
            self.hostname = arg1
            self.port = int(arg2)
            self.device = u2.connect("%s:%s" % (arg1, arg2))
            # self._str = "u2-tcpip"
        app.log.text("device: %s" % self.device.info["productName"])

        self.device.set_new_command_timeout(300)
        self.device.implicitly_wait(60.0)
        self.device.HTTP_TIMEOUT = 60
        self.device.WAIT_FOR_DEVICE_TIMEOUT = 70
        self.device.settings["wait_timeout"] = 60
        # self.device
        # self.device
        self._height, self._width = 0, 0
        self.app_id = "jp.co.cygames.umamusume"

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def tap(self, point: Tuple[int, int]) -> None:
        x, y = point
        self.device.click(x, y)
        time.sleep(self.action_wait)

    def start_game(self):
        # print(self.device.app_list_running())
        if self.app_id not in self.device.app_list_running():
            self.device.app_start(
                self.app_id,
                "%s_activity.UmamusumeActivity" % self.app_id,
            )
        pass

    def load_size(self):
        res = self.device.shell("wm size").output
        match = re.match(
            r"Physical size: (\d+)x(\d+)\r?\nOverride size: (\d+)x(\d+)", res
        )
        phy_width = None
        phy_height = None
        if match:
            phy_width = int(match.group(2))
            phy_height = int(match.group(1))
            self._width = int(match.group(4))
            self._height = int(match.group(3))
            if phy_width > phy_height:  # handle orientation
                phy_height, phy_width = phy_width, phy_height
        else:
            res = self.device.shell("wm size").output
            match = re.match(r"Physical size: (\d+)x(\d+)", res)
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
            self.device.app_stop(self.app_id)

        if phy_width and phy_height:
            app.log.text("Using non-physical screen size: %s" % res)

            def handle_exit(*args):
                try:
                    global ans
                    ans = ""
                    while ans not in ("Y", "N"):
                        ans = terminal.prompt(
                            "Do you want to recover the screen size? (Y/N)"
                        ).upper()
                    if ans == "Y":
                        clients.current().device.shell("wm size reset")
                except BaseException as e:
                    print("Reset screen size failed: %s" % e)
                exit()

            atexit.register(handle_exit)
            signal.signal(signal.SIGTERM, handle_exit)
            signal.signal(signal.SIGINT, handle_exit)

        app.log.text(
            "screen size: width=%d height=%d" % (self.width, self.height),
            level=app.DEBUG,
        )

    def screenshot(self) -> PIL.Image.Image:
        return self.device.screenshot()

    def setup(self) -> None:
        self.load_size()
        self.start_game()

    def swipe(
        self, point: Tuple[int, int], *, dx: int, dy: int, duration: float = 1
    ) -> None:
        x1, y1 = point
        # x2, y2 = x1 + dx, y1 + dy
        x2, y2 = x1 + dx * 2.5, y1 + dy * 2.5
        if duration < 0.4:
            # not work if too fast
            dx = int(dx * 0.4 / duration)
            dy = int(dy * 0.4 / duration)
            duration = 0.4
        self.device.swipe(x1, y1, x2, y2, steps=duration * 1000 / 5)
        time.sleep(self.action_wait)


class CustomCompetitorMenuScene(CompetitorMenuScene):
    _super = CompetitorMenuScene

    @classmethod
    def name(cls):
        return "paddock"

    @classmethod
    def _enter(cls, *args, **kwargs) -> auto_derby.scenes.Scene:
        action.wait_image_stable(templates.TEAM_RACE_CHOOSE_COMPETITOR, duration=0.5)
        return cls()

    def locate_granted_reward(self) -> Optional[Tuple[int, int]]:
        return self._super.locate_granted_reward()

    def choose(self, *args, **kwargs) -> None:
        """choose competitor by index, topmost option is 0."""
        return self._super.choose(*args, **kwargs)


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        _next_client = auto_derby.config.client

        def _client():
            if not auto_derby.config.ADB_ADDRESS.lower().startswith("u2:"):
                return _next_client()
            return U2Client(auto_derby.config.ADB_ADDRESS)

        auto_derby.config.client = _client
        auto_derby.scenes.team_race.CompetitorMenuScene = CustomCompetitorMenuScene


auto_derby.plugin.register(__name__, Plugin())
