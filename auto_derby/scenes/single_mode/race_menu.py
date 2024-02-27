# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations

import time
from typing import Iterator, Tuple


from ...single_mode import Context, Race, Course
from ... import (
    action,
    single_mode,
    templates,
    app,
    imagetools,
    ocr,
    mathtools,
    template,
    texttools,
)
from ..scene import Scene, SceneHolder
from ..vertical_scroll import VerticalScroll
from .command import CommandScene
from PIL.Image import Image
import numpy as np
import cv2


class RaceTurnsIncorrect(ValueError):
    def __init__(self) -> None:
        super().__init__("race turns incorrect")


def _race_by_course(ctx: Context, course: Course) -> Iterator[Race]:
    year, month, half = ctx.date
    for i in Race.repository.find():
        if year not in i.years:
            continue
        if ctx.date == (1, 0, 0) and i.grade != Race.GRADE_DEBUT:
            continue
        if (month, half) not in ((i.month, i.half), (0, 0)):
            continue
        if i.is_available(ctx) is False:
            continue
        if course not in i.courses:
            continue
        if course.no1_fan_count and i.fan_counts[0] != course.no1_fan_count:
            continue
        yield i


_TURN_TRACK_SPEC = {
    "左·内": (Course.TURN_LEFT, Course.TRACK_IN),
    "右·内": (Course.TURN_RIGHT, Course.TRACK_IN),
    "左": (Course.TURN_LEFT, Course.TRACK_MIDDLE),
    "右": (Course.TURN_RIGHT, Course.TRACK_MIDDLE),
    "左·外": (Course.TURN_LEFT, Course.TRACK_OUT),
    "右·外": (Course.TURN_RIGHT, Course.TRACK_OUT),
    "直線": (Course.TURN_NONE, Course.TRACK_MIDDLE),
    "右·外→内": (Course.TURN_RIGHT, Course.TRACK_OUT_TO_IN),
}


def _recognize_course(img: Image) -> Course:
    cv_img = imagetools.cv_image(imagetools.resize(img.convert("L"), height=32))
    cv_img = imagetools.level(
        cv_img, np.percentile(cv_img, 1), np.percentile(cv_img, 90)
    )
    _, binary_img = cv2.threshold(cv_img, 60, 255, cv2.THRESH_BINARY_INV)
    app.log.image("spec", cv_img, level=app.DEBUG, layers={"binary": binary_img})
    text = ocr.text(imagetools.pil_image(binary_img))
    stadium, text = text[:2], text[2:]
    if text[0] == "芝":
        text = text[1:]
        ground = Course.GROUND_TURF
    elif text[0] == "ダ":
        text = text[3:]
        ground = Course.GROUND_DART
    else:
        raise ValueError("_recognize_spec: invalid spec: %s", text)

    distance, text = int(text[:4]), text[10:]

    turn, track = _TURN_TRACK_SPEC[texttools.choose(text, _TURN_TRACK_SPEC.keys())]

    return Course(
        stadium=stadium,
        ground=ground,
        distance=distance,
        track=track,
        turn=turn,
    )


def _menu_item_bbox(
    ctx: Context, fan_icon_pos: Tuple[int, int], rp: mathtools.ResizeProxy
):
    _, y = fan_icon_pos

    if ctx.scenario == ctx.SCENARIO_CLIMAX:
        return (
            rp.vector(23, 540),
            y - rp.vector(72, 540),
            rp.vector(515, 540),
            y + rp.vector(33, 540),
        )

    return (
        rp.vector(23, 540),
        y - rp.vector(51, 540),
        rp.vector(515, 540),
        y + rp.vector(46, 540),
    )


def _course_bbox(ctx: Context, rp: mathtools.ResizeProxy):
    if ctx.scenario == ctx.SCENARIO_CLIMAX:
        return rp.vector4((221, 21, 477, 41), 492)
    return rp.vector4((221, 12, 488, 30), 492)


def _vs_rival_icon_bbox(rp: mathtools.ResizeProxy):
    return rp.vector4((354, 3, 369, 15), 492)


def _recognize_rival(img: Image) -> bool:
    res = tuple(template.match(img, templates.SINGLE_MODE_CLIMAX_VS_RIVAL_ICON))
    return len(res) == 1


def _no1_fan_count_bbox(ctx: Context, rp: mathtools.ResizeProxy):
    if ctx.scenario == ctx.SCENARIO_CLIMAX:
        return rp.vector4((208, 78, 361, 95), 492)
    return rp.vector4((207, 54, 360, 72), 492)


def _recognize_fan_count(img: app.Image) -> int:
    cv_img = imagetools.cv_image(imagetools.resize(img.convert("L"), height=32))
    cv_img = imagetools.level(
        cv_img, np.percentile(cv_img, 1), np.percentile(cv_img, 90)
    )
    _, binary_img = cv2.threshold(cv_img, 60, 255, cv2.THRESH_BINARY_INV)
    app.log.image(
        "fan count",
        cv_img,
        level=app.DEBUG,
        layers={
            "binary": binary_img,
        },
    )
    text = ocr.text(imagetools.pil_image(binary_img))
    return int(text.rstrip("人").replace(",", ""))


def _recognize_menu(
    ctx: Context, screenshot: imagetools.Image
) -> Iterator[Tuple[Course, Tuple[int, int], bool]]:
    app.log.image("race menu", screenshot, level=app.DEBUG)
    rp = mathtools.ResizeProxy(screenshot.width)
    for _, pos in template.match(
        screenshot,
        templates.SINGLE_MODE_RACE_MENU_FAN_ICON,
        templates.SINGLE_MODE_RACE_MENU_FAN_ICON_LARK,
    ):
        bbox = _menu_item_bbox(ctx, pos, rp)
        item_img = screenshot.crop(bbox)
        app.log.image("race menu item", item_img, level=app.DEBUG)
        item_rp = mathtools.ResizeProxy(item_img.width)

        course_bbox = _course_bbox(ctx, item_rp)
        course_img = item_img.crop(course_bbox)
        app.log.image("race menu item course", course_img, level=app.DEBUG)
        course = _recognize_course(course_img)

        vs_rival_icon_bbox = _vs_rival_icon_bbox(item_rp)
        with_rival = False
        if ctx.scenario == ctx.SCENARIO_CLIMAX:
            with_rival = _recognize_rival(item_img.crop(vs_rival_icon_bbox))

        no1_fan_count_bbox = _no1_fan_count_bbox(ctx, item_rp)
        fan_count_img = item_img.crop(no1_fan_count_bbox)
        app.log.image("race menu item fan count", fan_count_img, level=app.DEBUG)
        course.no1_fan_count = _recognize_fan_count(fan_count_img)

        yield course, pos, with_rival


class RaceMenuScene(Scene):
    def __init__(self) -> None:
        super().__init__()
        rp = action.resize_proxy()
        self._scroll = VerticalScroll(
            origin=rp.vector2((15, 600), 540),
            page_size=100,
            max_page=15,
        )

    @classmethod
    def name(cls):
        return "single-mode-race-menu"

    @classmethod
    def _enter(cls, ctx: SceneHolder) -> Scene:
        CommandScene.enter(ctx)
        tmpl, pos = action.wait_image(
            templates.SINGLE_MODE_COMMAND_RACE,
            templates.SINGLE_MODE_FORMAL_RACE_BANNER,
            templates.SINGLE_MODE_URA_FINALS,
            templates.SINGLE_MODE_SCHEDULED_RACE_OPENING_BANNER,
            templates.SINGLE_MODE_GRAND_MASTERS,
        )
        x, y = pos
        rp = action.resize_proxy()
        if tmpl.name == templates.SINGLE_MODE_FORMAL_RACE_BANNER:
            y += rp.vector(60, 540)
        app.device.tap(action.template_rect(tmpl, (x, y)))
        if tmpl.name == templates.SINGLE_MODE_SCHEDULED_RACE_OPENING_BANNER:
            action.wait_tap_image(templates.SINGLE_MODE_GO_TO_SCHEDULED_RACE_BUTTON)
        tmpl, _ = action.wait_image(
            templates.SINGLE_MODE_RACE_START_BUTTON,
            templates.SINGLE_MODE_CONTINUOUS_RACE_TITLE,
        )
        if tmpl.name == templates.SINGLE_MODE_CONTINUOUS_RACE_TITLE:
            if isinstance(ctx, single_mode.Context) and ctx.continuous_race_count() < 3:
                ctx.race_turns.update(range(ctx.turn_count() - 3, ctx.turn_count()))
                action.wait_tap_image(templates.CANCEL_BUTTON)
                raise RaceTurnsIncorrect()
            action.wait_tap_image(templates.GREEN_OK_BUTTON)
        action.wait_image(
            templates.SINGLE_MODE_RACE_MENU_FAN_ICON,
            templates.SINGLE_MODE_RACE_MENU_FAN_ICON_LARK,
        )
        return cls()

    def visible_courses(self, ctx: Context) -> Iterator[Tuple[Course, Tuple[int, int]]]:
        for course, pos, _ in _recognize_menu(ctx, app.device.screenshot()):
            yield course, pos

    def first_race(self, ctx: single_mode.Context) -> Race:
        return next(_race_by_course(ctx, next(self.visible_courses(ctx))[0]))

    def choose_race(self, ctx: single_mode.Context, race: Race) -> None:
        time.sleep(0.2)  # wait animation
        rp = action.resize_proxy()
        while self._scroll.next():
            for course, pos in self.visible_courses(ctx):
                if course.no1_fan_count != race.fan_counts[0]:
                    continue
                if course not in race.courses:
                    continue
                app.device.tap((*pos, *rp.vector2((200, 20), 540)))
                return
        raise ValueError("not found: %s" % race)

    def find_race_with_rival(self, ctx: single_mode.Context) -> list[Race]:
        races: list[Race] = []
        next_races: list[Race] = []
        prev_races: list[Race] = []
        while self._scroll.next():
            for course, _, with_rival in _recognize_menu(ctx, app.device.screenshot()):
                if with_rival:
                    race = next(_race_by_course(ctx, course))
                    race.with_rival = True
                    next_races.append(race)
            next_races.sort(key=lambda x: x.name)
            for r in next_races:
                if r.name not in [i.name for i in races]:
                    races.append(r)
            if next_races == prev_races:
                break
            if any([r for r in next_races if r.grade > Race.GRADE_G3]):
                break
            prev_races = next_races

        self._scroll.on_end()
        self._scroll.complete()
        return races
