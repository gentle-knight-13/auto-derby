# -*- coding=UTF-8 -*-
# pyright: strict

from .. import action, templates, config, app


def legend_race():
    while True:
        tmpl, pos = action.wait_image(
            templates.CONNECTING,
            templates.RETRY_BUTTON,
            templates.GREEN_NEXT_BUTTON,
            templates.RACE_START_BUTTON,
            templates.LEGEND_RACE_RACE_BUTTON,
            templates.LEGEND_RACE_START_BUTTON,
            templates.LEGEND_RACE_CONFIRM_BUTTON,
            templates.SKIP_BUTTON,
            templates.LIMITED_SALE_OPEN,
            templates.LEGEND_RACE_REWARD,
            templates.LEGEND_RACE_COLLECT_ALL_REWARD,
            templates.GREEN_RETURN_BUTTON,
            templates.RACE_RESULT_NO1,
            templates.RACE_RESULT_NO2,
            templates.RACE_RESULT_NO3,
            templates.RACE_RESULT_NO4,
            templates.RACE_RESULT_NO5,
            templates.RACE_RESULT_NO6,
            templates.RACE_RESULT_NO8,
            templates.RACE_RESULT_NO10,
        )
        name = tmpl.name
        if name == templates.CONNECTING:
            pass
        elif name == templates.LIMITED_SALE_OPEN:
            config.on_limited_sale()
        elif name == templates.LEGEND_RACE_COLLECT_ALL_REWARD:
            app.device.tap(action.template_rect(tmpl, pos))
            return
        elif name == templates.GREEN_RETURN_BUTTON:
            return
        else:
            app.device.tap(action.template_rect(tmpl, pos))
