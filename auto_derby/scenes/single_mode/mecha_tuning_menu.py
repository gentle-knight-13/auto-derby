# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations

import time
from enum import Enum, IntEnum
from typing import Any, Dict, Text

import cv2
from PIL.Image import Image

from auto_derby import imagetools, mathtools, ocr

from ... import action, app, template, templates
from ..scene import Scene, SceneHolder
from .command import CommandScene


class MechaTuningCore(IntEnum):
    UNKNOWN = 0
    HEAD = 1
    CHEST = 2
    LEG = 3


class MechaTuningChip(IntEnum):
    UNKNOWN = 0
    WISDOM_RESEARCH = 1
    SKILL_HINT = 2
    PROFICIENCY = 3
    STAMINA_RESEARCH = 4
    GUTS_RESEARCH = 5
    FRIENDSHIP_BOOST = 6
    SPEED_RESEARCH = 7
    POWER_RESEARCH = 8
    SKILL_POINT = 9


class MechaTuningEvent(Enum):
    UNKNOWN = ((0,), 0)
    FIRST = ((1,), 1)
    SECOND = ((2,), 2)
    THIRD = ((3,), 3)
    FOURTH = ((4, 5), 4)
    FIFTH_AFTER = ((5, 6, 7), 5)

    def __init__(
        self,
        result: tuple[int, ...],
        tuning_count: int,
    ):
        self.result = result
        self.tuning_count = tuning_count


MECHA_TUNING_GROUPS = {
    MechaTuningCore.HEAD: {
        MechaTuningChip.WISDOM_RESEARCH: templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_WISDOM_CHIP,
        MechaTuningChip.SKILL_HINT: templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_SKILL_HINT_CHIP,
        MechaTuningChip.PROFICIENCY: templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_PROFICIENCY_CHIP,
    },
    MechaTuningCore.CHEST: {
        MechaTuningChip.STAMINA_RESEARCH: templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_STAMINA_CHIP,
        MechaTuningChip.GUTS_RESEARCH: templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_GUTS_CHIP,
        MechaTuningChip.FRIENDSHIP_BOOST: templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_FRIEND_BOOST_CHIP,
    },
    MechaTuningCore.LEG: {
        MechaTuningChip.SPEED_RESEARCH: templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_SPEED_CHIP,
        MechaTuningChip.POWER_RESEARCH: templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_POWER_CHIP,
        MechaTuningChip.SKILL_POINT: templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_SKILL_POINT_CHIP,
    },
}

# A plan that prioritizes skill tips
DEFAULT_MECHA_TURING_PLAN = {
    MechaTuningEvent.FIRST: [
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.LEG, MechaTuningChip.SPEED_RESEARCH),
        (MechaTuningCore.LEG, MechaTuningChip.SPEED_RESEARCH),
        (MechaTuningCore.LEG, MechaTuningChip.POWER_RESEARCH),
        (MechaTuningCore.LEG, MechaTuningChip.POWER_RESEARCH),
    ],
    MechaTuningEvent.SECOND: [
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.STAMINA_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.STAMINA_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.GUTS_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
    ],
    MechaTuningEvent.THIRD: [
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.CHEST, MechaTuningChip.STAMINA_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.STAMINA_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.GUTS_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.GUTS_RESEARCH),
    ],
    MechaTuningEvent.FOURTH: [
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.CHEST, MechaTuningChip.STAMINA_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.STAMINA_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.STAMINA_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.STAMINA_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.STAMINA_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.GUTS_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.GUTS_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.GUTS_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.GUTS_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.GUTS_RESEARCH),
    ],
    MechaTuningEvent.FIFTH_AFTER: [
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.SKILL_HINT),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.WISDOM_RESEARCH),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.HEAD, MechaTuningChip.PROFICIENCY),
        (MechaTuningCore.LEG, MechaTuningChip.SPEED_RESEARCH),
        (MechaTuningCore.LEG, MechaTuningChip.SPEED_RESEARCH),
        (MechaTuningCore.LEG, MechaTuningChip.SPEED_RESEARCH),
        (MechaTuningCore.LEG, MechaTuningChip.SPEED_RESEARCH),
        (MechaTuningCore.LEG, MechaTuningChip.SPEED_RESEARCH),
        (MechaTuningCore.LEG, MechaTuningChip.POWER_RESEARCH),
        (MechaTuningCore.LEG, MechaTuningChip.POWER_RESEARCH),
        (MechaTuningCore.LEG, MechaTuningChip.POWER_RESEARCH),
        (MechaTuningCore.LEG, MechaTuningChip.POWER_RESEARCH),
        (MechaTuningCore.LEG, MechaTuningChip.POWER_RESEARCH),
        (MechaTuningCore.LEG, MechaTuningChip.SKILL_POINT),
        (MechaTuningCore.LEG, MechaTuningChip.SKILL_POINT),
        (MechaTuningCore.LEG, MechaTuningChip.SKILL_POINT),
        (MechaTuningCore.LEG, MechaTuningChip.SKILL_POINT),
        (MechaTuningCore.LEG, MechaTuningChip.SKILL_POINT),
        (MechaTuningCore.CHEST, MechaTuningChip.FRIENDSHIP_BOOST),
        (MechaTuningCore.CHEST, MechaTuningChip.FRIENDSHIP_BOOST),
        (MechaTuningCore.CHEST, MechaTuningChip.FRIENDSHIP_BOOST),
        (MechaTuningCore.CHEST, MechaTuningChip.FRIENDSHIP_BOOST),
        (MechaTuningCore.CHEST, MechaTuningChip.FRIENDSHIP_BOOST),
        (MechaTuningCore.CHEST, MechaTuningChip.STAMINA_RESEARCH),
        (MechaTuningCore.CHEST, MechaTuningChip.GUTS_RESEARCH),
    ],
}


def _validate_tuning_plan_combinations(
    tuning_plan: dict[MechaTuningEvent, list[tuple[MechaTuningCore, MechaTuningChip]]],
) -> None:
    for event in MechaTuningEvent:
        if event == MechaTuningEvent.UNKNOWN:
            continue
        if event not in tuning_plan:
            raise ValueError(f"Event {event} is not defined in the tuning plan.")
        for core, chip in tuning_plan[event]:
            if chip not in MECHA_TUNING_GROUPS.get(core, {}):
                raise ValueError(
                    f"Invalid combination: {core.name} cannot be paired with {chip.name}"
                )


def _get_template_from_tuning_groups(chip: MechaTuningChip) -> str:
    for _, chips in MECHA_TUNING_GROUPS.items():
        if chip in chips:
            return chips[chip]
    raise ValueError(
        f"Invalid combination: No template found for chip {chip} in any core."
    )


def _recognize_mecha_tuning_core(img: Image) -> MechaTuningCore:
    if tuple(
        template.match(
            img, templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_HEAD_CORE
        )
    ):
        return MechaTuningCore.HEAD
    elif tuple(
        template.match(
            img, templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_CHEST_CORE
        )
    ):
        return MechaTuningCore.CHEST
    elif tuple(
        template.match(img, templates.SINGLE_MODE_MECHA_UMAMUSUME_MECHA_TUNING_LEG_CORE)
    ):
        return MechaTuningCore.LEG
    else:
        return MechaTuningCore.UNKNOWN


def _recognize_mecha_tuning_chips(
    core: MechaTuningCore, rp: mathtools.ResizeProxy, img: Image
) -> dict[
    MechaTuningChip,
    tuple[
        int,
        bool,
    ],
]:
    mecha_tuning_group = MECHA_TUNING_GROUPS[core]
    mecha_tuning_chips: dict[
        MechaTuningChip,
        tuple[
            int,
            bool,
        ],
    ] = {}

    for chip, tmpl in mecha_tuning_group.items():
        try:
            _, pos = next(template.match(img, tmpl))
            x, y = pos
            bbox = (
                x + rp.vector(44, 540),
                y + rp.vector(58, 540),
                x + rp.vector(62, 540),
                y + rp.vector(76, 540),
            )
            crop_img = img.crop(bbox)
            cv_img = imagetools.cv_image(crop_img.convert("L"))
            _, binary_img = cv2.threshold(cv_img, 120, 255, cv2.THRESH_BINARY_INV)
            app.log.image(
                f"{chip.name} chip pt",
                cv_img,
                layers={
                    "binary": binary_img,
                },
                level=app.DEBUG,
            )

            text = ocr.text(imagetools.pil_image(binary_img))
            mecha_tuning_chips[chip] = (int(text), True)

        except StopIteration:
            mecha_tuning_chips[chip] = (0, False)

    return mecha_tuning_chips


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
        "mecha energy pt",
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

        self.INCREASED_MECH_ENERGY = 5

        self.mecha_core = MechaTuningCore.UNKNOWN
        self.mecha_event = MechaTuningEvent.UNKNOWN
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

        self.can_use_proficiency_chip = False
        self.can_use_friendship_boost_chip = False
        self.can_use_skill_point_chip = False

        self.mecha_core_groups = MECHA_TUNING_GROUPS
        self.mecha_tuning_plan = DEFAULT_MECHA_TURING_PLAN

    def to_dict(self) -> Dict[Text, Any]:
        return {
            "mechaCore": self.mecha_core,
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

    def __get_mecha_tuning_event(
        self,
    ) -> MechaTuningEvent:
        # The maximum limit of Mecha Energy varies depending on the trained umamusume and support cards.
        # Mecha Energy increases by 5-6 points at a time.
        # Divide by 5 and combine with chip release to calculate the tuning count.

        # Mecha tuning event breakdown:
        # 1st: Mecha energy range of 5-7
        # 2nd: Mecha energy range of 10-13 (Proficiency chip is released when 2nd is completed)
        # 3rd: Mecha energy range of 15-19
        # 4th: Mecha energy range of 20-26 (Friendship boost and Skill point chip is released when 4th is completed)
        # 5th: Mecha energy range of 25-31
        # 6th: Mecha energy range of 30-37

        tuning_count = self.mecha_energy // self.INCREASED_MECH_ENERGY

        if tuning_count in MechaTuningEvent.FIRST.result:
            return MechaTuningEvent.FIRST
        elif tuning_count in MechaTuningEvent.SECOND.result:
            return MechaTuningEvent.SECOND
        elif (
            tuning_count in MechaTuningEvent.THIRD.result
            and self.can_use_proficiency_chip
        ):
            return MechaTuningEvent.THIRD
        elif tuning_count in MechaTuningEvent.FOURTH.result and (
            not self.can_use_friendship_boost_chip or not self.can_use_skill_point_chip
        ):
            return MechaTuningEvent.FOURTH
        elif tuning_count in MechaTuningEvent.FIFTH_AFTER.result and (
            self.can_use_friendship_boost_chip or self.can_use_skill_point_chip
        ):
            return MechaTuningEvent.FIFTH_AFTER

        raise ValueError(f"Failed to calculate the tuning count: {tuning_count}")

    def __choice_mecha_core(
        self, mecha_core: MechaTuningCore, static: bool = False
    ) -> None:
        if static:
            return
        if self.mecha_core == mecha_core:
            return

        rp = action.resize_proxy()
        pos = {
            MechaTuningCore.HEAD: rp.vector2((100, 520), 540),
            MechaTuningCore.CHEST: rp.vector2((280, 520), 540),
            MechaTuningCore.LEG: rp.vector2((450, 520), 540),
        }[mecha_core]
        app.device.tap((*pos, 5, 5))
        # wait for switch
        time.sleep(0.1)

        img = app.device.screenshot()
        self.mecha_core = _recognize_mecha_tuning_core(img)

    def __choice_mecha_tuning_chip(
        self, chip: MechaTuningChip, static: bool = False
    ) -> None:
        if static:
            return

        chip_conditions = {
            MechaTuningChip.PROFICIENCY: self.can_use_proficiency_chip,
            MechaTuningChip.FRIENDSHIP_BOOST: self.can_use_friendship_boost_chip,
            MechaTuningChip.SKILL_POINT: self.can_use_skill_point_chip,
        }
        if not chip_conditions.get(chip, True):
            return

        tmpl = _get_template_from_tuning_groups(chip)
        _, (x, y) = next(template.match(app.device.screenshot(), tmpl))
        app.device.tap((x + 115, y + 68, 1, 1))
        time.sleep(0.1)

    def __apply_tuning_plan(self) -> None:
        _validate_tuning_plan_combinations(self.mecha_tuning_plan)

        action.wait_tap_image(
            templates.SINGLE_MODE_MECHA_UMAMUSUME_RESET_BUTTON,
        )
        time.sleep(0.1)

        self.recognize()
        for core, chip in self.mecha_tuning_plan[self.mecha_event]:
            self.__choice_mecha_core(core)
            self.__choice_mecha_tuning_chip(chip)

        # recognize updated tuning
        self.recognize()

    def apply_tuning_plan(self) -> None:
        # Use the default tuning plan.
        # Allow the tuning plan to be modified via a plugin.
        self.__apply_tuning_plan()

    def recognize(self, static: bool = False) -> None:
        _validate_tuning_plan_combinations(self.mecha_tuning_plan)
        rp = action.resize_proxy()
        img = app.device.screenshot()

        self.mecha_energy = _recognize_mecha_energy(rp, img)
        self.mecha_core = _recognize_mecha_tuning_core(img)

        self.__choice_mecha_core(MechaTuningCore.HEAD, static)
        chips = _recognize_mecha_tuning_chips(MechaTuningCore.HEAD, rp, img)
        for chip, (pt, can_use) in chips.items():
            if chip == MechaTuningChip.WISDOM_RESEARCH:
                self.wisdom_research_chip = pt
            if chip == MechaTuningChip.SKILL_HINT:
                self.skill_hint_chip = pt
            if chip == MechaTuningChip.PROFICIENCY:
                self.proficiency_chip = pt
                self.can_use_proficiency_chip = can_use

        self.__choice_mecha_core(MechaTuningCore.CHEST, static)
        chips = _recognize_mecha_tuning_chips(MechaTuningCore.CHEST, rp, img)
        for chip, (pt, can_use) in chips.items():
            if chip == MechaTuningChip.STAMINA_RESEARCH:
                self.stamina_research_chip = pt
            if chip == MechaTuningChip.GUTS_RESEARCH:
                self.guts_research_chip = pt
            if chip == MechaTuningChip.FRIENDSHIP_BOOST:
                self.friendship_boost_chip = pt
                self.can_use_friendship_boost_chip = can_use

        self.__choice_mecha_core(MechaTuningCore.LEG, static)
        chips = _recognize_mecha_tuning_chips(MechaTuningCore.LEG, rp, img)
        for chip, (pt, can_use) in chips.items():
            if chip == MechaTuningChip.SPEED_RESEARCH:
                self.speed_research_chip = pt
            if chip == MechaTuningChip.POWER_RESEARCH:
                self.power_research_chip = pt
            if chip == MechaTuningChip.SKILL_POINT:
                self.skill_point_chip = pt
                self.can_use_skill_point_chip = can_use

        self.mecha_event = self.__get_mecha_tuning_event()
