# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations
from typing import Iterator

from ...single_mode import Context, Race, Course
from ... import (
    action,
    templates,
    app,
    imagetools,
    ocr,
    mathtools,
    texttools,
)
from ..scene import Scene, SceneHolder
from .command import CommandScene
from PIL.Image import Image
import numpy as np
import cv2

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


def _race_by_course(ctx: Context, course: Course) -> Iterator[Race]:
    for i in Race.repository.find():
        if ctx.date == (1, 0, 0) and i.grade != Race.GRADE_DEBUT:
            continue
        if course not in i.courses:
            continue
        yield i


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


def _course_bbox(ctx: Context, rp: mathtools.ResizeProxy):
    return rp.vector4((30, 304, 300, 328), 540)


def _recognize_menu(ctx: Context, screenshot: imagetools.Image) -> Course:
    app.log.image("race menu", screenshot, level=app.DEBUG)
    rp = mathtools.ResizeProxy(screenshot.width)

    course_bbox = _course_bbox(ctx, rp)
    course_img = screenshot.crop(course_bbox)
    app.log.image("race course", course_img, level=app.DEBUG)
    course = _recognize_course(course_img)
    app.log.text(
        str(course),
        level=app.DEBUG,
    )
    return course


class GrandMastersRaceMenuScene(Scene):
    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def name(cls):
        return "single-mode-grand-masters-race-menu"

    @classmethod
    def _enter(cls, ctx: SceneHolder) -> Scene:
        CommandScene.enter(ctx)
        tmpl, pos = action.wait_image(
            templates.SINGLE_MODE_GRAND_MASTERS_GUR_BUTTON,
            templates.SINGLE_MODE_GRAND_MASTERS_WBC_BUTTON,
        )
        app.device.tap(action.template_rect(tmpl, pos))
        return cls()

    def recognize(self, ctx: Context) -> Race:
        action.wait_image_stable(templates.SINGLE_MODE_RACE_START_BUTTON, duration=0.3)
        course = _recognize_menu(ctx, app.device.screenshot())
        return next(_race_by_course(ctx, course))
