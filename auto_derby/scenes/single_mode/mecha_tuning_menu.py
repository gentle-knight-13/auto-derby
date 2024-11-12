# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations

from enum import IntEnum
from typing import Any, Dict, Text

import cv2
from PIL.Image import Image

from auto_derby import imagetools, mathtools, ocr

from ... import action, app, template, templates
from ..scene import Scene, SceneHolder
from .command import CommandScene


class MechaTuning(IntEnum):
    UNKNOWN = 0
    HEAD_CORE = 1
    CHEST_CORE = 2
    LEG_CORE = 3


def _recognize(img: Image) -> MechaTuning:
    if tuple(
        template.match(
            img, templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_HEAD_CORE
        )
    ):
        return MechaTuning.HEAD_CORE
    elif tuple(
        template.match(
            img, templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_CHEST_CORE
        )
    ):
        return MechaTuning.CHEST_CORE
    elif tuple(
        template.match(img, templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_LEG_CORE)
    ):
        return MechaTuning.LEG_CORE
    else:
        return MechaTuning.UNKNOWN


def _recognize_mecha_energy(rp: mathtools.ResizeProxy, img: Image) -> int:
    _, pos = next(
        template.match(img, templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_ENERGY)
    )

    x, y = pos
    bbox = (
        x + rp.vector(160, 540),
        y + rp.vector(-4, 540),
        x + rp.vector(220, 540),
        y + rp.vector(20, 540),
    )
    crop_img = img.crop(bbox)

    # FIXME: "pt" cannot be properly recognized, so as a workaround, the image is resized and recognized.
    crop_img = imagetools.resize(crop_img, width=480, height=272)
    cv_img = imagetools.cv_image(crop_img.convert("L"))
    _, binary_img = cv2.threshold(cv_img, 120, 255, cv2.THRESH_BINARY_INV)
    app.log.image(
        "mecha energy",
        cv_img,
        layers={
            "binary": binary_img,
        },
        level=app.DEBUG,
    )

    # NOTE: If recognition is not possible, this may be due to environment-dependent OCR data correction.
    text = ocr.text(imagetools.pil_image(binary_img))
    return int(text.rstrip("m").replace(",", ""))


class MechaTuningMenu(Scene):
    def __init__(self) -> None:
        super().__init__()

        self.turning = MechaTuning.UNKNOWN
        self.mecha_energy: int = 0
        self.wisdom_research_chip: int = 0
        self.skill_hint_chip: int = 0
        self.proficiency_chip: int = 0
        self.stamina_research_chip: int = 0
        self.guts_research_chip: int = 0
        self.friendship_boost_chip: int = 0
        self.speed_research_chip: int = 0
        self.power_research_chip: int = 0
        self.skill_point_chip: int = 0

        self.can_use_proficiency_chip: bool = False
        self.can_use_friendship_boost_chip: bool = False
        self.can_use_skill_point_chip: bool = False

    def to_dict(self) -> Dict[Text, Any]:
        return {
            "turning": self.turning,
            "mechaEnergy": self.mecha_energy,
            "wisdomResearchChip": self.wisdom_research_chip,
            "skillHintChip": self.skill_hint_chip,
            "proficiencyChip": self.proficiency_chip,
            "staminaResearchChip": self.stamina_research_chip,
            "gutsResearchChip": self.guts_research_chip,
            "friendshipBoostChip": self.friendship_boost_chip,
            "speedResearchChip": self.speed_research_chip,
            "powerResearchChip": self.power_research_chip,
            "skillPointChip": self.skill_point_chip,
            "canUseProficiencyChip": int(self.can_use_proficiency_chip),
            "canUseFriendshipBoostChip": int(self.can_use_friendship_boost_chip),
            "canUseSkillPointChip": int(self.can_use_skill_point_chip),
        }

    @classmethod
    def name(cls):
        return "single-mode-mecha-tuning-menu"

    @classmethod
    def _enter(cls, ctx: SceneHolder) -> Scene:
        CommandScene.enter(ctx)
        action.wait_tap_image(
            templates.SINGLE_MODE_MECHA_UMAMUSUME_GREEN_CONFIRM_BUTTON,
        )
        # action.wait_image(templates.SINGLE_MODE_MECHA_UMAMUSUME_GREEN_COMPLETE_BUTTON)
        action.wait_tap_image(
            templates.SINGLE_MODE_MECHA_UMAMUSUME_GREEN_COMPLETE_BUTTON
        )
        return cls()

    def calculate_mecha_tuning_count(self):
        pass

    def choice_mecha_core(self, tuning: MechaTuning) -> None:
        self.recognize()
        if self.turning == tuning:
            return
        else:
            rp = action.resize_proxy()
            tuning_tab_pos = {
                MechaTuning.HEAD_CORE: rp.vector2((100, 520), 540),
                MechaTuning.CHEST_CORE: rp.vector2((280, 520), 540),
                MechaTuning.LEG_CORE: rp.vector2((450, 520), 540),
            }[tuning]
            app.device.tap((*tuning_tab_pos, 1, 1))

    def tune_mecha_core(self, tuning: MechaTuning) -> None:
        pass

    def recognize(self) -> None:
        rp = action.resize_proxy()
        img = app.device.screenshot()

        self.turning = _recognize(img)
        self.mecha_energy = _recognize_mecha_energy(rp, img)
