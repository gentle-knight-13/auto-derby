# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations

import traceback
from typing import Iterator, Text, Tuple

import cv2
from PIL.Image import Image

from ... import action, app, imagetools, mathtools, ocr, template, templates
from ...single_mode import Context, go_out
from ..scene import Scene, SceneHolder
from ..vertical_scroll import VerticalScroll


def _recognize_name(img: Image) -> Text: # type: ignore
    img = imagetools.resize(img, height=48)
    cv_img = imagetools.cv_image(img.convert("L"))
    _, binary_img = cv2.threshold(cv_img, 120, 255, cv2.THRESH_BINARY_INV)

    app.log.image(
        "name",
        cv_img,
        layers={
            "binary": binary_img,
        },
        level=app.DEBUG,
    )

    # FIXME: OCR is not accurate good enough for names
    return ocr.text(imagetools.pil_image(binary_img))


def _recognize_item(rp: mathtools.ResizeProxy, img: Image) -> go_out.Option:
    try:
        v = go_out.Option.new()
        rp = mathtools.ResizeProxy(img.width)
        v.type = go_out.Option.TYPE_SUPPORT
        event1_pos = rp.vector2((338 - 18, 353 - 286), 500)
        event2_pos = rp.vector2((375 - 18, 353 - 286), 500)
        event3_pos = rp.vector2((413 - 18, 353 - 286), 500)
        event4_pos = rp.vector2((450 - 18, 353 - 286), 500)
        event5_pos = rp.vector2((489 - 18, 353 - 286), 500)

        v.current_event_count = 0
        v.total_event_count = 5
        for pos in (
            event1_pos,
            event2_pos,
            event3_pos,
            event4_pos,
            event5_pos,
        ):
            is_gray = imagetools.compare_color(img.getpixel(pos), (231, 227, 225)) > 0.9
            if not is_gray:
                v.current_event_count += 1
        name_bbox = rp.vector4((95, 16, 316, 40), 540)
        v.name = _recognize_name(img.crop(name_bbox))
        app.log.image("recognize: %s" % v, img, level=app.DEBUG)
        return v
    except:
        app.log.image(
            "recognition failed: %s" % traceback.format_exc(), img, level=app.ERROR
        )
        raise


def _recognize_menu(img: Image) -> Iterator[go_out.Option]:
    rp = mathtools.ResizeProxy(img.width)
    item_pos: set[Tuple[int, int]] = set()
    for _, pos in template.match(img, templates.SINGLE_MODE_GO_OUT_OPTION_LEFT_TOP):
        item_pos.add(pos)
    for _, pos in template.match(
        img, templates.SINGLE_MODE_GO_OUT_OPTION_EVENT_PROCESS
    ):
        x, y = pos
        x -= rp.vector(138, 540)
        y -= rp.vector(71, 540)
        if not any((x - x2) ** 2 + (y - y2) ** 2 < 9 for x2, y2 in item_pos):
            item_pos.add((x, y))
    for x, y in item_pos:
        bbox = (
            x,
            y,
            x + rp.vector(500, 540),
            y + rp.vector(100, 540),
        )
        option = _recognize_item(rp, img.crop(bbox))
        option.position = (x + rp.vector(102, 540), y + rp.vector(46, 540))
        option.bbox = bbox
        yield option


class GoOutGroupMenuScene(Scene):
    def __init__(self) -> None:
        super().__init__()
        rp = action.resize_proxy()
        self._scroll = VerticalScroll(
            origin=rp.vector2((17, 540), 540),
            page_size=150,
            max_page=2,
        )
        self.go_out_options: Tuple[go_out.Option, ...] = ()

    @classmethod
    def name(cls):
        return "single-mode-go-out-group-menu"

    @classmethod
    def _enter(cls, ctx: SceneHolder) -> Scene:
        action.wait_image_stable(
            templates.SINGLE_MODE_GO_OUT_OPTION_EVENT_PROCESS, duration=0.2
        )
        return cls()

    def recognize(self, ctx: Context, static: bool = False) -> None:
        while self._scroll.next():
            new_go_out_options = tuple(
                i
                for i in _recognize_menu(app.device.screenshot())
                if i.name not in [i.name for i in self.go_out_options]
            )
            if not new_go_out_options:
                self._scroll.on_end()
                self._scroll.complete()
                break
            self.go_out_options += new_go_out_options
            if static:
                break
