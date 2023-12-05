import time
from typing import Callable, Optional, Text

import auto_derby
from auto_derby import action, templates, terminal, app, single_mode
from auto_derby import template
from auto_derby.single_mode import Context, Race, RaceResult
from auto_derby.single_mode.commands import race as comRace
from auto_derby.single_mode.commands.globals import g


class temp:
    LIVE_MENU_BUTTON = "live_menu_button.png"
    LIVE_SKIP_BUTTON = "live_skip_button.png"


_race_templates = [
    templates.RACE_START_BUTTON,
    templates.SKIP_BUTTON,
    # templates.GREEN_NEXT_BUTTON,
    # templates.SINGLE_MODE_RACE_NEXT_BUTTON,
    templates.CLOSE_BUTTON,
    templates.RETRY_BUTTON,
]


def _handle_race_result(ctx: Context, race: Race):
    tmpl, pos = action.wait_image(
        templates.RACE_RESULT_BUTTON,
        templates.GO_TO_RACE_BUTTON,
    )
    action.tap(pos)
    # if tmpl.name == templates.RACE_RESULT_BUTTON:
    #     break
    if tmpl.name == templates.GO_TO_RACE_BUTTON:
        time.sleep(2)
        action.wait_tap_image(templates.RACE_START_BUTTON)
        for i in range(5):
            action.wait_tap_image(templates.SKIP_BUTTON)
        while True:
            try:
                screenshot = app.device.screenshot()
                if screenshot.width == app.device.height:
                    try:
                        _tmpl, _pos = next(
                            template.match(
                                screenshot,
                                temp.LIVE_SKIP_BUTTON,
                                temp.LIVE_MENU_BUTTON,
                            )
                        )
                        app.device.tap(action.template_rect(_tmpl, _pos))
                        continue
                    except StopIteration:
                        pass
                    app.device.tap(
                        (
                            screenshot.width * 1 / 3,
                            screenshot.height * 1 / 3,
                            screenshot.width * 2 / 3,
                            screenshot.height * 2 / 3,
                        )
                    )
                if next(
                    template.match(
                        screenshot,
                        templates.CLOSE_BUTTON,
                        templates.GREEN_NEXT_BUTTON,
                        templates.SINGLE_MODE_CONTINUE,
                    )
                ):
                    break
            except StopIteration:
                continue
        _tmpl, _pos = action.wait_image(
            templates.CLOSE_BUTTON,
            templates.GREEN_NEXT_BUTTON,
            templates.SINGLE_MODE_CONTINUE,
        )
        if _tmpl.name == templates.CLOSE_BUTTON:
            app.device.tap(action.template_rect(_tmpl, _pos))

    res = RaceResult()
    res.ctx = ctx.clone()
    res.race = race

    if tmpl.name == templates.RACE_RESULT_BUTTON:
        tmpl, pos = action.wait_image(*comRace._RACE_ORDER_TEMPLATES.keys())
        order_img = template.screenshot()
        res.order = comRace._RACE_ORDER_TEMPLATES[tmpl.name]
        app.device.tap(action.template_rect(tmpl, pos))

    if ctx.scenario == ctx.SCENARIO_CLIMAX and ctx.date[0] < 4:
        tmpl, pos = action.wait_image_stable(
            templates.CLOSE_BUTTON,
            templates.SINGLE_MODE_CLIMAX_RIVAL_RACE_WIN,
            templates.SINGLE_MODE_CLIMAX_RIVAL_RACE_DRAW,
            templates.SINGLE_MODE_CLIMAX_RIVAL_RACE_LOSE,
        )
        app.device.tap(action.template_rect(tmpl, pos))
        if tmpl.name != templates.CLOSE_BUTTON:
            _, pos = action.wait_image_stable(templates.CLOSE_BUTTON)
            app.device.tap(action.template_rect(templates.CLOSE_BUTTON, pos))

    tmpl, pos = action.wait_image_stable(
        templates.GREEN_NEXT_BUTTON,
        templates.SINGLE_MODE_CONTINUE,
    )

    res.is_failed = tmpl.name == templates.SINGLE_MODE_CONTINUE
    if tmpl.name == templates.RACE_RESULT_BUTTON:
        app.log.image("race result: %s" % res, order_img)
    g.on_race_result(ctx, res)
    res.write()

    if res.order > 1:
        retry = comRace._retry_method(ctx)
        if retry and g.should_retry_race(ctx, res):
            retry()
            _handle_race_result(ctx, race)
            return

    app.device.tap(action.template_rect(tmpl, pos))
    if res.is_failed:
        ctx.mood = {
            ctx.MOOD_VERY_BAD: ctx.MOOD_BAD,
            ctx.MOOD_BAD: ctx.MOOD_NORMAL,
            ctx.MOOD_NORMAL: ctx.MOOD_GOOD,
            ctx.MOOD_GOOD: ctx.MOOD_VERY_GOOD,
            ctx.MOOD_VERY_GOOD: ctx.MOOD_VERY_GOOD,
        }[ctx.mood]
        _handle_race_result(ctx, race)


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        comRace._handle_race_result = _handle_race_result


auto_derby.plugin.register(__name__, Plugin())
