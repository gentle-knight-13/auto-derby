# -*- coding=UTF-8 -*-
# pyright: strict
from __future__ import annotations

import copy
from typing import Tuple

from PIL.Image import Image

from ...constants import TrainingType
from ..context import Context
from . import training_score
from .globals import g
from .partner import Partner


class Training:
    TYPE_SPEED = TrainingType.SPEED
    TYPE_STAMINA = TrainingType.STAMINA
    TYPE_POWER = TrainingType.POWER
    TYPE_GUTS = TrainingType.GUTS
    TYPE_WISDOM = TrainingType.WISDOM

    TYPE_SS_MATCH = TrainingType.SS_MATCH

    ALL_TYPES = (
        TYPE_SPEED,
        TYPE_STAMINA,
        TYPE_POWER,
        TYPE_GUTS,
        TYPE_WISDOM,
    )

    ALL_TYPES_LARK = (
        TYPE_SPEED,
        TYPE_STAMINA,
        TYPE_POWER,
        TYPE_GUTS,
        TYPE_WISDOM,
        TYPE_SS_MATCH,
    )

    @staticmethod
    def new() -> Training:
        return g.training_class()

    def __init__(self):
        self.level = 0
        self.type = TrainingType.UNKNOWN

        self.speed: int = 0
        self.stamina: int = 0
        self.power: int = 0
        self.guts: int = 0
        self.wisdom: int = 0
        self.skill: int = 0
        self.vitality: float = 0.0
        self._use_estimate_vitality = False
        self.failure_rate: float = 0.0
        self.confirm_position: Tuple[int, int] = (0, 0)
        self.partners: Tuple[Partner, ...] = ()

        self.dance: int = 0
        self.passion: int = 0
        self.vocal: int = 0
        self.visual: int = 0
        self.mental: int = 0

        self.sphere: int = 0
        self.fight: int = 0
        self.free: int = 0

    def clone(self) -> Training:
        obj = copy.copy(self)
        return obj

    def __str__(self):
        named_data = (
            ("spd", self.speed),
            ("sta", self.stamina),
            ("pow", self.power),
            ("gut", self.guts),
            ("wis", self.wisdom),
            ("ski", self.skill),
            ("da", self.dance),
            ("pa", self.passion),
            ("vo", self.vocal),
            ("vi", self.visual),
            ("me", self.mental),
            ("sp", self.sphere),
            ("fi", self.fight),
            ("fr", self.free),
        )
        partner_text = ",".join(i.to_short_text() for i in self.partners)
        return (
            "Training<"
            + (
                "".join(
                    (
                        f"{name}={value} "
                        for name, value in sorted(
                            named_data, key=lambda x: x[1], reverse=True
                        )
                        if value
                    )
                )
                + (f"vit={self.vitality*100:.1f}% ")
                + (f"fail={self.failure_rate*100:.0f}% ")
                + f"lv={self.level} "
                + (f"ptn={partner_text} " if partner_text else "")
            ).strip()
            + ">"
        )

    def score(self, ctx: Context) -> float:
        return training_score.compute(ctx, self)

    @classmethod
    def from_training_scene(
        cls,
        img: Image,
    ) -> Training:
        # TODO: remove deprecated method at next major version
        import warnings

        warnings.warn(
            "use from_training_scene_v2 instead",
            DeprecationWarning,
        )
        ctx = Context()
        ctx.scenario = ctx.SCENARIO_URA
        return cls.from_training_scene_v2(ctx, img)

    @classmethod
    def from_training_scene_v2(
        cls,
        ctx: Context,
        img: Image,
    ) -> Training:
        # TODO: remove deprecated method at next major version
        import warnings

        warnings.warn(
            "use TrainingScene.recognize instead",
            DeprecationWarning,
        )
        from ... import action, template, templates
        from ...scenes.single_mode.training import _recognize_training  # type: ignore

        _, pos = action.wait_image_stable(
            template.Specification(
                templates.SINGLE_MODE_TRAINING_CONFIRM, threshold=0.8
            ),
            templates.SINGLE_MODE_TRAINING_CONFIRM_LARK,
            duration=0.1,
        )
        return _recognize_training(ctx, (img, pos))


g.training_class = Training
