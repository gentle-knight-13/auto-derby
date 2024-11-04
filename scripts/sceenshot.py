# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations

if True:
    import sys
    import os

    sys.path.insert(0, os.path.join(__file__, "../.."))


import argparse

from auto_derby import clients, template


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--dest",
        dest="dst",
        default="debug/last_screenshot.png",
    )
    parser.add_argument(
        "-s",
        "--separate",
        dest="separate",
        action="store_true"
    )

    args = parser.parse_args()
    dst = args.dst
    is_separate = args.separate

    c = clients.DMMClient.find()
    if not c:
        raise RuntimeError("DMM client not running")
    c.setup()
    clients.set_current(c) # type: ignore

    if is_separate:
        dirname, basename = os.path.split(dst)
        filename, ext = os.path.basename(basename).split('.', 1)
        i = 1
        while True:
            filepath = os.path.join(dirname, f"{filename}_{i}.{ext}")
            if not os.path.exists(filepath):
                template.g.last_screenshot_save_path = filepath
                break
            i += 1
    else:
        template.g.last_screenshot_save_path = dst
    template.screenshot() # type: ignore


if __name__ == "__main__":
    main()
