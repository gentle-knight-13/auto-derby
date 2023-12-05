from __future__ import annotations

import argparse

import colorsys
import re
import subprocess as sp
import time

from ctypes import windll
from typing import Optional, Text, Tuple, Union

import auto_derby

import PIL.Image
import PIL.ImageGrab
import win32gui
from auto_derby import (
    action,
    app,
    imagetools,
    mathtools,
    single_mode,
    templates,
    window,
)

from auto_derby.clients.client import Client
from auto_derby.mathtools import ResizeProxy
from auto_derby.scenes import single_mode as scenes_single_mode

_IS_ADMIN = bool(windll.shell32.IsUserAnAdmin())

_action_wait = 0.1


class Padding:
    def __init__(self, bottom, left, right, top) -> None:
        """Padding of the window, following the position of bottom, left, right, top"""
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right

    @property
    def width(self) -> int:
        return self.left + self.right

    @property
    def height(self) -> int:
        return self.top + self.bottom


class MuMuNebulaClient(Client):
    def __init__(self, h_wnd: int):
        self.rp = None
        self.h_wnd = h_wnd
        self._height, self._width = 0, 0
        self._android_height, self._android_width = 0, 0
        self._resize_height = 0
        self.padding = Padding(0, 0, 0, 0)  # (53, 0, 0, 37)
        self.shell_cmd = 'E:\\Emulator\\MuMuNebula\\emulator\\nebula\\nebula\\nebula.exe --rootdir ' \
                         '"E:/Emulator/MuMuNebula/emulator/nebula/nebula/fs_static" --session-id bmVidWxh ' \
                         '--dynamicdir "E:/Emulator/MuMuNebula/emulator/nebula/nebula/fs_dynamic"'
        """Command used for interact with MuMu Nebula"""
        self.rp: ResizeProxy
        self._job: Text = ""

    @classmethod
    def find(cls) -> Optional[MuMuNebulaClient]:
        h_wnd = win32gui.FindWindow("Qt5QWindowIcon", "ウマ娘 - MuMu Nebula")
        if not h_wnd:
            h_wnd = win32gui.FindWindow(
                "Qt5QWindowIcon", "賽馬娘Pretty Derby - MuMu Nebula"
            )
        if not h_wnd:
            h_wnd = win32gui.FindWindow(
                "Qt5QWindowIcon", "MuMu Nebula"
            )
        if not h_wnd:
            return None
        return cls(h_wnd)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def android_width(self) -> int:
        return self._android_width

    @property
    def android_height(self) -> int:
        return self._android_height

    def load_windows_size(self):
        img = window.screenshot(self.h_wnd)
        self._width, self._height = img.size

        # Detect padding using the left-most column pixels
        top_padding, bottom_padding = 0, 0
        for y in range(self._height):
            if img.getpixel((0, y)) != (18, 18, 21):
                top_padding = y
                break
        for y in reversed(range(self._height)):
            if img.getpixel((0, y)) != (18, 18, 21):
                bottom_padding = self._height - y - 1
                break
        app.log.image(
            f"padding detected as ({top_padding}, {bottom_padding})", img
        )
        self.padding.top += top_padding
        self.padding.bottom += bottom_padding
        self._width -= self.padding.width
        self._height -= self.padding.height

        # Fast workaround for nebula slightly different from expected ratio without resize
        expected_ratio = self._android_width / self._android_height
        current_ratio = self._width / self._height
        if current_ratio != expected_ratio:
            padding = int((self._height - self._width / expected_ratio) / 2)
            self.padding.top += padding + int((self._height - img.size[1]) % 2)
            self.padding.bottom += padding
            app.log.text(
                f"padding changed by ({padding + int((img.size[1] - self._height) % 2)}, {padding})"
            )
            self._height -= padding

    def load_android_size(self):
        wm_proc = sp.run(
            ["powershell", "-Command", f'{self.shell_cmd} "/system/bin/wm" size'],
            stdin=sp.DEVNULL,
            stderr=sp.PIPE,
            stdout=sp.PIPE,
        )
        res = wm_proc.stdout.decode("utf-8")
        match = re.match(r"Physical size: (\d+)x(\d+)", res)
        assert match, "unexpected command result: %s" % res
        self._android_width = int(match.group(2))
        self._android_height = int(match.group(1))
        if self._android_width > self._android_height:
            # handle orientation
            self._android_height, self._android_width = (
                self._android_width,
                self._android_height,
            )
        self.rp = ResizeProxy(self.android_width)
        app.log.text(
            "device screen size: width=%d height=%d"
            % (self.android_width, self.android_height),
            level=app.DEBUG,
        )

    def _get_job(self) -> Text:
        if self._job:
            return self._job
        parser = argparse.ArgumentParser()
        parser.add_argument("job")
        args = parser.parse_args()
        self._job = args.job
        app.log.text(f"current job: {self._job}", level=app.DEBUG)
        return self._job

    def setup(self) -> None:
        if not _IS_ADMIN:
            raise PermissionError("NebulaClient: require admin permission")
        self.load_android_size()
        self.load_windows_size()
        app.log.text("game window: handle=%s" % self.h_wnd)

    def screenshot(self) -> PIL.Image.Image:
        if self._get_job() in ("team_race"):
            time.sleep(_action_wait)
        ret = window.screenshot(self.h_wnd).crop(
            (
                self.padding.left,
                self.padding.top,
                self.padding.left + self.width,
                self.padding.top + self.height,
            )
        )
        return ret

    def tap(self, point: Tuple[int, int]) -> None:
        app.log.text(f"tap: point={point}", level=app.DEBUG)
        x, y = self.rp.vector2(point, self.width)
        sp.run(
            [
                "powershell",
                "-Command",
                f'{self.shell_cmd} "/system/bin/input" tap {x} {y}',
            ],
            stdin=sp.DEVNULL,
        )
        time.sleep(_action_wait)

    def swipe(
            self, point: Tuple[int, int], *, dx: int, dy: int, duration: float = 1
    ) -> None:
        app.log.text("swipe: point=%s dx=%d dy=%d" % (point, dx, dy), level=app.DEBUG)
        x1, y1 = point
        x2, y2 = x1 + dx, y1 + dy
        duration_ms = int(duration * 1e3)
        # if duration_ms < 200:
        #     # not work if too fast
        #     dx = int(dx * 200 / duration_ms)
        #     dy = int(dy * 200 / duration_ms)
        #     duration_ms = 200
        x1, y1, x2, y2 = self.rp.vector4((x1, y1, x2, y2), self.width)
        sp.run(
            [
                "powershell",
                "-Command",
                f'{self.shell_cmd} "/system/bin/input" swipe {x1} {y1} {x2} {y2} {duration_ms}',
            ],
            stdin=sp.DEVNULL,
        )
        time.sleep(_action_wait)


# ==================#
#    Workaround    #
# ==================#

# Screenshot of after winning value has much less saturation than normal
def update_by_class_detail(self, screenshot: PIL.Image.Image) -> None:
    rp = mathtools.ResizeProxy(screenshot.width)
    winning_color_pos = rp.vector2((150, 470), 466)
    fan_count_bbox = rp.vector4((220, 523, 420, 540), 466)

    def rgb_to_hsv(color: Union[Tuple[int, ...], int]):
        if isinstance(color, int):
            app.log.text(
                "Screenshot do not contains RGB layers, but only one!", level=app.ERROR
            )
            raise RuntimeError("Incorrect layers of screenshot image")
        red, green, blue = color
        color_h, color_s, color_v = colorsys.rgb_to_hsv(
            red / 255.0, green / 255.0, blue / 255.0
        )
        return round(360 * color_h), round(100 * color_s), round(100 * color_v)

    winning_color_rgb = screenshot.getpixel(winning_color_pos)
    winning_color_hsv = rgb_to_hsv(winning_color_rgb)
    self.is_after_winning = (
            imagetools.compare_color(
                (winning_color_hsv[0], winning_color_hsv[2]),  # (48, 57, 92)
                (47, 95),  # (47, 78, 95)
            )
            > 0.95
    )
    if not self.is_after_winning and self.date[0] > 1:
        app.log.image(
            """Beware the Umamusume is detected as not after any winning after first year. 
            This may cause problem when target race is met.""",
            screenshot,
            level=app.WARN,
        )
    self.fan_count = single_mode.context._recognize_fan_count(
        screenshot.crop(fan_count_bbox)
    )


def recognize_status(self: scenes_single_mode.CommandScene, ctx: single_mode.Context):
    action.wait_tap_image(templates.SINGLE_MODE_CHARACTER_DETAIL_BUTTON)
    action.wait_image_stable(templates.SINGLE_MODE_CHARACTER_DETAIL_TITLE, duration=0.2)
    ctx.update_by_character_detail(app.device.screenshot())
    action.wait_tap_image(templates.CLOSE_BUTTON)
    action.wait_image_stable(
        templates.SINGLE_MODE_COMMAND_TRAINING,
        templates.SINGLE_MODE_FORMAL_RACE_BANNER,
        duration=_action_wait,
    )


# Code used for more friendly output to find why race unavailable
# Insert at race_menu.py _race_by_course function after `if i.is_available(ctx) == False:`
#
#                 if course in i.courses:
#                 app.log.text(
#                     f"""Race {i.name} in {course} is not available,
# Possible cause:
# - Current date {ctx.date} == (1, 0, 0) and race grade ({i.grade}) is not GRADE_DEBUT(900)
# - Current date {ctx.date[1:]} not in ({(i.month, i.half)}, (0, 0))
# - Current year {ctx.date[0]} not in {i.years}
# - Current character {"" if ctx.is_after_winning else "not "} winning any races""",
#                     level=app.DEBUG,
#                 )


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        _next_client = auto_derby.config.client

        def _client():
            _nebula_client = MuMuNebulaClient.find()
            if not _IS_ADMIN or not _nebula_client:
                return _next_client()
            return _nebula_client

        auto_derby.config.client = _client
        single_mode.context.Context.update_by_class_detail = update_by_class_detail
        scenes_single_mode.command.CommandScene.recognize_status = recognize_status


auto_derby.plugin.register(__name__, Plugin())
