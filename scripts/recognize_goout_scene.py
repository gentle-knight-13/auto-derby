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
from auto_derby import app
from auto_derby.single_mode import Context
from auto_derby.infrastructure.image_device_service import ImageDeviceService
from auto_derby.scenes.single_mode.go_out_menu import GoOutMenuScene

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("image", default="debug/last_screenshot.png")
    parser.add_argument("-s", "--scenario", default="ura")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    if args.debug:
        logging.getLogger("auto_derby").setLevel(logging.DEBUG)
    image_path = args.image
    scenario = {
        "ura": Context.SCENARIO_URA,
        "aoharu": Context.SCENARIO_AOHARU,
        "climax": Context.SCENARIO_CLIMAX,
    }.get(args.scenario, args.scenario)

    image = PIL.Image.open(image_path)
    app.device = ImageDeviceService(image)
    ctx = Context.new()
    ctx.scenario = scenario

    scene = GoOutMenuScene()
    scene.recognize(ctx)
    for option in ctx.go_out_options:
        print(option)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(levelname)-6s[%(asctime)s]:%(name)s:%(lineno)d: %(message)s",
        level=logging.INFO,
        datefmt="%H:%M:%S",
    )
    main()