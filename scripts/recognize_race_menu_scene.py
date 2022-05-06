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
from auto_derby import template
from auto_derby.single_mode import Context, race


def tuple_type(strings: str):
    strings = strings.replace("(", "").replace(")", "")
    mapped_int = map(int, strings.split(","))
    return tuple(mapped_int)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("image", default="debug/last_screenshot.png")
    parser.add_argument("-s", "--scenario", default="climax")
    parser.add_argument("-d", "--date", type=tuple_type, default="(1, 8, 2)")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    if args.debug:
        logging.getLogger("auto_derby").setLevel(logging.DEBUG)
        os.environ["DEBUG"] = "auto_derby.single_mode.race.game_data"
    image_path = args.image
    scenario = {
        "ura": Context.SCENARIO_URA,
        "aoharu": Context.SCENARIO_AOHARU,
        "climax": Context.SCENARIO_CLIMAX,
    }.get(args.scenario, args.scenario)
    date = args.date
    image = PIL.Image.open(image_path)
    template.g.screenshot_width = image.width

    ctx = Context.new()
    ctx.scenario = scenario
    ctx.date = date
    race_iter = race.find_by_race_menu_image(ctx, image)
    for _race, _pos in race_iter:
        print(f"race  : {_race}")
        print(f"pos   : {_pos}")
        print(f"rival : {_race.with_rival}")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(levelname)-6s[%(asctime)s]:%(name)s:%(lineno)d: %(message)s",
        level=logging.INFO,
        datefmt="%H:%M:%S",
    )
    main()
