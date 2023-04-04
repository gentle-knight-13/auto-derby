# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations

import time
from enum import IntEnum
from PIL.Image import Image

from ... import action, app, template, templates
from ...single_mode import commands, Context
from .command import CommandScene
from ..scene import Scene, SceneHolder


class GoddessWisdom(IntEnum):
    UNKNOWN = 0
    RED = 1
    BLUE = 2
    YELLOW = 3


def _recognize(img: Image) -> GoddessWisdom:
    if tuple(template.match(img, templates.SINGLE_MODE_GRAND_MASTERS_RED_WISDOM)):
        return GoddessWisdom.RED
    elif tuple(template.match(img, templates.SINGLE_MODE_GRAND_MASTERS_BLUE_WISDOM)):
        return GoddessWisdom.BLUE
    elif tuple(template.match(img, templates.SINGLE_MODE_GRAND_MASTERS_YELLOW_WISDOM)):
        return GoddessWisdom.YELLOW
    else:
        return GoddessWisdom.UNKNOWN


class KnowledgeTableMenuScene(Scene):
    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def name(cls):
        return "single-mode-knowledge-table-menu"

    @classmethod
    def _enter(cls, ctx: SceneHolder) -> Scene:
        CommandScene.enter(ctx)
        action.wait_tap_image(
            templates.SINGLE_MODE_GRAND_MASTERS_KNOWLEDGE_TABLE_BUTTON,
        )
        action.wait_image(templates.CLOSE_BUTTON)
        return cls()

    def learn_goddess_wisdom(self, ctx: Context, command: commands.Command) -> bool:
        def learn():
            action.wait_tap_image(
                templates.SINGLE_MODE_GRAND_MASTERS_LEARN_WISDOM_BUTTON
            )
            action.wait_tap_image(templates.SINGLE_MODE_GRAND_MASTERS_LEARN_BUTTON)
            time.sleep(7.5)
            action.wait_tap_image(templates.CLOSE_BUTTON)

        goddess_wisdom = _recognize(app.device.screenshot())
        if goddess_wisdom == GoddessWisdom.RED:
            learn()
            return True

        if goddess_wisdom in [GoddessWisdom.BLUE, GoddessWisdom.YELLOW] and isinstance(
            command, commands.TrainingCommand
        ):
            learn()
            return True

        action.wait_tap_image(templates.CLOSE_BUTTON)
        return False
