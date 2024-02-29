# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations

import time
from typing import Text

from auto_derby import templates

from ... import action, app
from ...scenes import UnknownScene
from ...scenes.single_mode import TrainingScene
from .. import Context, Training, item
from .command import Command
from .globals import g


class TrainingCommand(Command):
    def __init__(self, training: Training):
        self.training = training

    def name(self) -> Text:
        return str(self.training)

    def execute(self, ctx: Context) -> None:
        g.on_command(ctx, self)
        TrainingScene.enter(ctx)
        x, y = self.training.confirm_position
        rp = action.resize_proxy()
        w, h = rp.vector2((30, 80), 540)
        action.wait_image(
            templates.SINGLE_MODE_TRAINING_CONFIRM, templates.SINGLE_MODE_TRAINING_CONFIRM_LARK
        )
        current_training = Training.from_training_scene_v2(ctx, app.device.screenshot())
        if current_training.type != self.training.type:
            app.device.tap((x, y - h, w, h))
            time.sleep(0.1)
        app.device.tap((x, y - h, w, h))
        if ctx.scenario == ctx.SCENARIO_UAF_READY_GO:
            trainings = ctx.trainings
            genre = (int(self.training.type) - 2) // 5  # 0 sphere / 1 fight / 2 free
            trainings = [i for i in trainings if (int(i.type) - 2) // 5 == genre]
            for trn in trainings:
                if trn.type not in ctx.training_levels:
                    ctx.training_levels[trn.type] = 0
                ctx.training_levels[trn.type] += trn.level_up

        ctx.training_history.append(ctx, current_training)
        UnknownScene.enter(ctx)

    def score(self, ctx: Context) -> float:
        return self.training.score(ctx)


def _item_can_improve_failure_rate(i: item.Item):
    es = i.effect_summary()
    return es.vitality > 0 or es.training_no_failure


def default_ignore_training_commands(ctx: Context) -> bool:
    if any(_item_can_improve_failure_rate(i) for i in ctx.items):
        return False
    if ctx.vitality < 0.2:
        return True
    return False


g.ignore_training_commands = default_ignore_training_commands
