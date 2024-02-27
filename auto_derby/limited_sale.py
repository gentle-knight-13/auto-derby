# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations

import time

from . import action, app, templates


def buy_first_n(n: int) -> None:
    rp = action.resize_proxy()
    action.wait_tap_image(templates.GO_TO_LIMITED_SALE)
    action.wait_image(templates.CLOSE_NOW_BUTTON)
    app.log.image("limited sale: buy first %d" % n, app.device.screenshot())
    item_count = 0
    for tmpl, pos in action.match_image_until_disappear(
        templates.EXCHANGE_BUTTON, sort=lambda x: sorted(x, key=lambda i: i[1][1])
    ):
        app.device.tap(action.template_rect(tmpl, pos))
        action.wait_tap_image(templates.EXCHANGE_CONFIRM_BUTTON)
        for _ in action.match_image_until_disappear(templates.CONNECTING):
            pass
        action.wait_tap_image(templates.CLOSE_BUTTON)
        action.wait_image(templates.CLOSE_NOW_BUTTON)
        item_count += 1
        if n > 0 and item_count >= n:
            break
        app.device.swipe(
            rp.vector4((14, 540, 6, 10), 540),
            rp.vector4((14, 500, 6, 10), 540),
            duration=0.2,
        )
        # prevent inertial scrolling
        app.device.tap(
            rp.vector4((14, 500, 6, 10), 540),
        )

    action.wait_tap_image(templates.CLOSE_NOW_BUTTON)
    action.wait_tap_image(templates.GREEN_OK_BUTTON)
    action.wait_tap_image(templates.RETURN_BUTTON)


def ignore() -> None:
    try:
        action.wait_tap_image(templates.CANCEL_BUTTON, timeout=60)
    except TimeoutError:
        pass
    time.sleep(0.5)

