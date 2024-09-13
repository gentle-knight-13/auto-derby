# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations

import time
from typing import Optional, Text

from ... import action, templates, app
from ...scenes.single_mode.command import CommandScene
from ...scenes.single_mode.go_out_group_menu import GoOutGroupMenuScene
from .. import Context, go_out
from .command import Command
from .globals import g


def _main_option() -> go_out.Option:
    ret = go_out.Option.new()
    ret.type = ret.TYPE_MAIN
    return ret


class GoOutCommand(Command):
    def __init__(self, option: Optional[go_out.Option] = None) -> None:
        super().__init__()
        self.option = option or _main_option()

    def name(self) -> Text:
        o = self.option
        if o.type == o.TYPE_MAIN:
            return f"GoOut<main:{o.position}>"
        if o.type == o.TYPE_SUPPORT:
            return f"GoOut<support:{o.name or o.position}:{o.current_event_count}/{o.total_event_count}>"
        if o.type == o.TYPE_GROUP:
            return f"GoOut<group:{o.name or o.position}:{o.current_event_count}/{o.total_event_count}>"
        return f"GoOut<{o}>"

    def execute(self, ctx: Context) -> None:
        g.on_command(ctx, self)
        CommandScene.enter(ctx)
        _tmpl = go_out.command_template(ctx)
        while action.tap_image(_tmpl):
            time.sleep(0.5)
        try:
            action.wait_image(templates.SINGLE_MODE_GO_OUT_MENU_TITLE, timeout=0.5)
            ctx.go_out_menu = True
            rp = action.resize_proxy()
            if (
                self.option.position == (0, 0)
                and self.option.type == go_out.Option.TYPE_MAIN
            ):
                self.option = next(
                    i
                    for i in go_out.Option.from_menu(app.device.screenshot())
                    if i.type == self.option.type
                )
            app.device.tap((*self.option.position, *rp.vector2((200, 20), 540)))
            if self.option.type == self.option.TYPE_GROUP:
                scene = GoOutGroupMenuScene.enter(ctx)
                scene.recognize(ctx)
                if scene.go_out_options:
                    option = scene.go_out_options[0]
                    app.device.tap((*option.position, *rp.vector2((200, 20), 540)))
                    self.option.current_group_event_count += 1
        except TimeoutError:
            pass

        if self.option.total_event_count > 0:
            self.option.current_event_count += 1
        return

    def score(self, ctx: Context) -> float:
        return self.option.score(ctx)
