# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations
import logging

if True:
    import os
    import sys

    sys.path.insert(0, os.path.join(__file__, "../.."))


import argparse

import PIL.Image
from auto_derby import single_mode, app
from auto_derby.scenes.single_mode import command
from auto_derby.infrastructure.image_device_service import ImageDeviceService
from auto_derby.infrastructure.multi_log_service import MultiLogService
from auto_derby.infrastructure.web_log_service import WebLogService


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("image", default="debug/last_screenshot.png")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    if args.debug:
        logging.getLogger("auto_derby").setLevel(logging.DEBUG)
    image_path = args.image
    image = PIL.Image.open(image_path)
    app.device = ImageDeviceService(image)

    with app.cleanup as cleanup:
        app.log = MultiLogService(
            app.log,
            WebLogService(cleanup),
        )

        scene = command.CommandScene()
        ctx = single_mode.Context.new()
        scene.recognize(ctx, static=True)
        print(ctx)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(levelname)-6s[%(asctime)s]:%(name)s:%(lineno)d: %(message)s",
        level=logging.INFO,
        datefmt="%H:%M:%S",
    )
    main()
