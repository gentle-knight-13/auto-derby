# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations
import re

import time
from typing import Any, Dict, Text

import cv2
import numpy as np
from PIL.Image import Image
from auto_derby.single_mode.context import Context

from ... import action, imagetools, ocr, single_mode, template, templates, app
from ...scenes import Scene
from ..scene import SceneHolder

from .go_out_menu import GoOutMenuScene


def _recognize_climax_grade_point(ctx: Context):
    if ctx.date[0] == 4:
        # in year 4, grade points are replaced by rank points
        ctx.grade_point = 0
        return
    rp = action.resize_proxy()
    bbox = rp.vector4((10, 185, 119, 218), 540)
    img = app.device.screenshot().crop(bbox)
    x, _ = next(
        template.match(
            img,
            template.Specification(
                templates.SINGLE_MODE_CLIMAX_GRADE_POINT_PT_TEXT,
                threshold=0.8,
            ),
        )
    )[1]
    img = img.crop((0, 0, x, img.height))
    img = imagetools.resize(img, height=32)
    cv_img = imagetools.cv_image(img.convert("L"))
    _, binary_img = cv2.threshold(
        cv_img,
        130,
        255,
        type=cv2.THRESH_BINARY_INV,
    )
    app.log.image(
        "climax grade point",
        cv_img,
        level=app.DEBUG,
        layers={
            "binary": binary_img,
        },
    )
    text = ocr.text(imagetools.pil_image(binary_img), simple_segment=True)
    ctx.grade_point = int(text.rstrip("pt").replace(",", ""))


def _recognize_shop_coin(ctx: Context):
    rp = action.resize_proxy()
    screenshot = app.device.screenshot()
    _, pos = next(template.match(screenshot, templates.SINGLE_MODE_COMMAND_SHOP))
    x, y = pos
    bbox = (
        x + rp.vector(16, 540),
        y + rp.vector(17, 540),
        x + rp.vector(82, 540),
        y + rp.vector(32, 540),
    )
    img = screenshot.crop(bbox)
    img = imagetools.resize(img, height=32)
    cv_img = np.asarray(img.convert("L"))
    _, binary_img = cv2.threshold(cv_img, 127, 255, cv2.THRESH_BINARY_INV)
    app.log.image(
        "shop coin",
        cv_img,
        level=app.DEBUG,
        layers={
            "binary": binary_img,
        },
    )
    text = ocr.text(imagetools.pil_image(binary_img))
    ctx.shop_coin = int(text.replace(",", ""))


def _recognize_grand_live_performance(ctx: Context):
    def _recognize_property(img: Image) -> int:
        img = imagetools.resize(img, height=32)
        cv_img = np.asarray(img.convert("L"))
        _, binary_img = cv2.threshold(cv_img, 160, 255, cv2.THRESH_BINARY_INV)
        app.log.image(
            "performance", cv_img, layers={"binary": binary_img}, level=app.DEBUG
        )
        return int(ocr.text(imagetools.pil_image(binary_img)))

    rp = action.resize_proxy()
    screenshot = app.device.screenshot()

    base_x = rp.vector(37, 540)
    left, right = base_x, base_x + rp.vector(58, 540)
    dance_bbox = (left, rp.vector(267, 540), right, rp.vector(289, 540))
    passion_bbox = (left, rp.vector(316, 540), right, rp.vector(338, 540))
    vocal_bbox = (left, rp.vector(365, 540), right, rp.vector(387, 540))
    visual_bbox = (left, rp.vector(414, 540), right, rp.vector(436, 540))
    mental_bbox = (left, rp.vector(463, 540), right, rp.vector(485, 540))

    ctx.dance = _recognize_property(screenshot.crop(dance_bbox))
    ctx.passion = _recognize_property(screenshot.crop(passion_bbox))
    ctx.vocal = _recognize_property(screenshot.crop(vocal_bbox))
    ctx.visual = _recognize_property(screenshot.crop(visual_bbox))
    ctx.mental = _recognize_property(screenshot.crop(mental_bbox))


def _recognize_lark_overseas_point(ctx: Context):
    rp = action.resize_proxy()
    screenshot = app.device.screenshot()
    _, pos = next(
        template.match(
            screenshot,
            templates.SINGLE_MODE_COMMAND_OVERSEA_SHOP,
            templates.SINGLE_MODE_COMMAND_OVERSEA_SHOP_FORMAL_RACE,
        )
    )
    x, y = pos
    bbox = (
        x + rp.vector(18, 540),
        y + rp.vector(17, 540),
        x + rp.vector(84, 540),
        y + rp.vector(32, 540),
    )
    img = screenshot.crop(bbox)
    img = imagetools.resize(img, height=32)
    cv_img = np.asarray(img.convert("L"))
    _, binary_img = cv2.threshold(cv_img, 127, 255, cv2.THRESH_BINARY_INV)
    app.log.image(
        "oversea point",
        cv_img,
        level=app.DEBUG,
        layers={
            "binary": binary_img,
        },
    )
    text = ocr.text(imagetools.pil_image(binary_img))
    ctx.overseas_point = int(text.replace(",", ""))


def _recognize_uaf_level(ctx: Context):
    def _recognize_level(img: Image) -> int:
        cv_img = imagetools.cv_image(imagetools.resize(img, height=32))
        outline_img = imagetools.constant_color_key(
            cv_img,
            # sphere
            (255, 98, 68),
            (255, 133, 114),
            # fight
            (94, 84, 255),
            (61, 46, 255),
            # free
            (0, 153, 255),
            (33, 149, 255),
        )
        masked_img = imagetools.inside_outline(cv_img, outline_img)

        text_img = imagetools.constant_color_key(
            masked_img, (255, 255, 255), threshold=0.85
        )
        app.log.image(
            "uaf: level sum",
            cv_img,
            level=app.DEBUG,
            layers={
                "outline": outline_img,
                "masked": masked_img,
                "text": text_img,
            },
        )
        text = ocr.text(imagetools.pil_image(text_img), offset=2)
        return int(re.sub("[^0-9]", "", text))

    rp = action.resize_proxy()
    screenshot = app.device.screenshot()

    left, right = rp.vector2((26, 92), 540)
    sphere_lvl_bbox = (left, rp.vector(294, 540), right, rp.vector(310, 540))
    fight_lvl_bbox = (left, rp.vector(373, 540), right, rp.vector(389, 540))
    free_lvl_bbox = (left, rp.vector(452, 540), right, rp.vector(468, 540))

    ctx.sphere_sum = _recognize_level(screenshot.crop(sphere_lvl_bbox))
    ctx.fight_sum = _recognize_level(screenshot.crop(fight_lvl_bbox))
    ctx.free_sum = _recognize_level(screenshot.crop(free_lvl_bbox))


class CommandScene(Scene):
    max_recognition_retry = 3

    def __init__(self) -> None:
        super().__init__()
        self.has_health_care = False
        self.has_scheduled_race = False
        self.can_go_out_with_friend = False
        self.has_shop = False
        self.has_knowledge_table = False
        self.has_learn_wisdom = False
        self.has_lesson = False

    @classmethod
    def name(cls):
        return "single-mode-command"

    @classmethod
    def _enter(cls, ctx: SceneHolder) -> Scene:
        name = ctx.scene.name()
        if name in (
            "single-mode-training",
            "single-mode-shop",
            "single-mode-race-menu",
        ):
            action.wait_tap_image(templates.RETURN_BUTTON)
        if name == "single-mode-item-menu":
            action.wait_tap_image(templates.CLOSE_BUTTON)
        if name == "single-mode-go-out-menu":
            action.wait_tap_image(templates.CANCEL_BUTTON)

        action.wait_image(
            templates.SINGLE_MODE_COMMAND_TRAINING,
            templates.SINGLE_MODE_COMMAND_TRAINING_LARK,
            templates.SINGLE_MODE_FORMAL_RACE_BANNER,
            templates.SINGLE_MODE_URA_FINALS,
            timeout=30,
        )

        return cls()

    def to_dict(self) -> Dict[Text, Any]:
        return {
            "hasHealthCare": self.has_health_care,
            "hasScheduledRace": self.has_scheduled_race,
            "canGoOutWithFriend": self.can_go_out_with_friend,
            "hasShop": self.has_shop,
            "hasKnowledgeTable": self.has_knowledge_table,
            "hasLearnWisdom": self.has_learn_wisdom,
            "hasLesson": self.has_lesson,
        }

    def recognize_class(self, ctx: single_mode.Context):
        if action.count_image(
            templates.SINGLE_MODE_GRAND_MASTERS_RACE_CLASS_DETAIL_BUTTON
        ):
            action.wait_tap_image(
                templates.SINGLE_MODE_GRAND_MASTERS_RACE_CLASS_DETAIL_BUTTON
            )
        else:
            action.wait_tap_image(
                {
                    ctx.SCENARIO_GRAND_LIVE: templates.SINGLE_MODE_AOHARU_CLASS_DETAIL_BUTTON,
                    ctx.SCENARIO_AOHARU: templates.SINGLE_MODE_AOHARU_CLASS_DETAIL_BUTTON,
                    ctx.SCENARIO_CLIMAX: templates.SINGLE_MODE_CLIMAX_CLASS_DETAIL_BUTTON,
                    ctx.SCENARIO_GRAND_MASTERS: templates.SINGLE_MODE_GRAND_MASTERS_CLASS_DETAIL_BUTTON,
                }.get(
                    ctx.scenario,
                    templates.SINGLE_MODE_CLASS_DETAIL_BUTTON,
                )
            )
        # time.sleep(0.2)  # wait animation
        action.wait_image_stable(templates.SINGLE_MODE_CLASS_DETAIL_TITLE, duration=0.2)
        ctx.update_by_class_detail(app.device.screenshot())
        action.wait_tap_image(templates.CLOSE_BUTTON)

    def recognize_status(self, ctx: single_mode.Context):
        action.wait_tap_image(templates.SINGLE_MODE_CHARACTER_DETAIL_BUTTON)
        # time.sleep(0.2)  # wait animation
        action.wait_image_stable(
            templates.SINGLE_MODE_CHARACTER_DETAIL_TITLE, duration=0.2
        )
        ctx.update_by_character_detail(app.device.screenshot())
        action.wait_tap_image(templates.CLOSE_BUTTON)
        time.sleep(0.2)  # wait animation

    def recognize_commands(self, ctx: single_mode.Context) -> None:
        self.has_health_care = (
            action.count_image(templates.SINGLE_MODE_COMMAND_HEALTH_CARE) > 0
        )
        self.has_scheduled_race = (
            action.count_image(templates.SINGLE_MODE_SCHEDULED_RACE_OPENING_BANNER) > 0
        )
        self.can_go_out_with_friend = (
            action.count_image(templates.SINGLE_MODE_GO_OUT_FRIEND_ICON) > 0
        )
        if ctx.scenario == ctx.SCENARIO_CLIMAX:
            self.has_shop = action.count_image(templates.SINGLE_MODE_COMMAND_SHOP) > 0
        if ctx.scenario == ctx.SCENARIO_GRAND_MASTERS:
            self.has_knowledge_table = (
                action.count_image(
                    templates.SINGLE_MODE_GRAND_MASTERS_KNOWLEDGE_TABLE_BUTTON
                )
                > 0
            )
            self.has_learn_wisdom = any(
                [
                    action.count_image(
                        templates.SINGLE_MODE_GRAND_MASTERS_LEARN_WISDOM_BANNER
                    )
                    > 0,
                    action.count_image(
                        templates.SINGLE_MODE_GRAND_MASTERS_RACE_LEARN_WISDOM_BANNER
                    )
                    > 0,
                ]
            )
        if ctx.scenario == ctx.SCENARIO_GRAND_LIVE:
            self.has_lesson = (
                action.count_image(templates.SINGLE_MODE_COMMAND_LESSON) > 0
            )

    def recognize_go_out_options(self, ctx: single_mode.Context) -> None:
        if not self.can_go_out_with_friend:
            return

        action.wait_tap_image(single_mode.go_out.command_template(ctx))
        try:
            action.wait_image(
                template.Specification(
                    templates.SINGLE_MODE_GO_OUT_MENU_TITLE, threshold=0.8
                ),
                timeout=1.0,
            )
            scene = GoOutMenuScene().enter(ctx)
            scene.recognize(ctx)
            self.enter(ctx)
            ctx.scene = self
        except TimeoutError:
            return

    def recognize(self, ctx: single_mode.Context, *, static: bool = False):
        app.device.reset_size()

        # animation may not finished
        # https://github.com/NateScarlet/auto-derby/issues/201

        max_retry = 0 if static else self.max_recognition_retry

        def _recognize_static():
            ctx.update_by_command_scene(app.device.screenshot())
            self.recognize_commands(ctx)
            if self.has_shop:
                _recognize_shop_coin(ctx)
            if ctx.scenario == ctx.SCENARIO_CLIMAX:
                _recognize_climax_grade_point(ctx)
            if self.has_lesson:
                _recognize_grand_live_performance(ctx)
            if ctx.scenario == ctx.SCENARIO_PROJECT_LARK:
                _recognize_lark_overseas_point(ctx)
            if ctx.scenario == ctx.SCENARIO_UAF_READY_GO:
                _recognize_uaf_level(ctx)

        action.run_with_retry(
            _recognize_static,
            max_retry,
        )

        # menu button click animation may cover text, order is important
        if static:
            return
        if not ctx.fan_count:
            self.recognize_class(ctx)
        if ctx.turf == ctx.STATUS_NONE or ctx.date[1:] == (4, 1):
            self.recognize_status(ctx)
        if not ctx.go_out_options:
            self.recognize_go_out_options(ctx)
