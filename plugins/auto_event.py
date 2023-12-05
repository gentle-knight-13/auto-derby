import json
from typing import List, Text
import cv2

import numpy as np
import auto_derby
from auto_derby import single_mode
from auto_derby import mathtools
from auto_derby import app, ocr
from auto_derby import imagetools
from auto_derby.single_mode.event import _prompt_choice, _set, g, reload_on_demand

class g:
    event_data = None

def get_choice(event_id: Text, *, _f=single_mode.event.get_choice) -> int:
    event_screen = app.device.screenshot()
    rp = mathtools.ResizeProxy(event_screen.width)
    b_img = np.zeros((event_screen.height, event_screen.width))
    event_name_bbox = rp.vector4((75, 155, 305, 180), 466)
    options_bbox = rp.vector4((50, 200, 400, 570), 466)
    cv_event_name_img = np.asarray(event_screen.crop(event_name_bbox).convert("L"))
    _, cv_event_name_img = cv2.threshold(cv_event_name_img, 220, 255, cv2.THRESH_TOZERO)

    l, t, r, b = event_name_bbox
    b_img[t:b, l:r] = cv_event_name_img

    cv_options_img = np.asarray(event_screen.crop(options_bbox).convert("L"))

    option_rows = (cv2.reduce(cv_options_img, 1, cv2.REDUCE_MAX) == 255).astype(
        np.uint8
    )

    option_mask = np.repeat(option_rows, cv_options_img.shape[1], axis=1)

    cv_options_img = 255 - cv_options_img
    cv_options_img *= option_mask

    _, cv_options_img = cv2.threshold(cv_options_img, 128, 255, cv2.THRESH_BINARY)

    l, t, r, b = options_bbox
    b_img[t:b, l:r] = cv_options_img

    # hist = cv2.reduce(cv_options_img, 1, cv2.REDUCE_AVG).reshape(-1)

    # th = 2
    # H, W = cv_options_img.shape[:2]
    # uppers = [y for y in range(H - 1) if hist[y] <= th and hist[y + 1] > th]
    # lowers = [y for y in range(H - 1) if hist[y] > th and hist[y + 1] <= th]

    debug_layers = {
        "option_mask": option_mask,
        "event_name": cv_event_name_img,
        "options": cv_options_img,
    }

    # options_img = []
    # pil_img = imagetools.fromarray(cv_options_img)
    # for i, top in enumerate(uppers):
    #     bottom = lowers[i]
    #     options_img.insert(i, pil_img.crop((0, top, pil_img.width - 1, bottom)))
    #     debug_layers["option_%d" % i] = options_img[i]

    event_name = ocr.text(imagetools.fromarray(cv_event_name_img))
    event_id = imagetools.md5(b_img, save_path=g.event_image_path)
    # options = []
    # for img in options_img:
    #     options_img.append(ocr.text(img))

    app.log.image(
        "Event: %s" % (event_name),
        b_img.astype(np.uint8),
        layers=debug_layers,
        level=app.DEBUG,
    )

    reload_on_demand()
    if event_id in g.choices:
        ret = g.choices[event_id]
    else:
        ret = _prompt_choice(event_id)
    app.log.image("event: id=%s choice=%d" % (event_id, ret), event_screen)
    return ret


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        f = open('data/event.json', encoding='utf-8')
        g.event_data = json.load(f)
        single_mode.event.get_choice = get_choice


auto_derby.plugin.register(__name__, Plugin())
