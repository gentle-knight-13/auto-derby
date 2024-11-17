from typing import Text

import pytest

from ... import _test
from .mecha_tuning_menu import MechaTuningMenu


@pytest.mark.parametrize(
    "name",
    tuple(
        i.stem
        for i in ((_test.DATA_PATH / "single_mode").glob("mecha_tuning_menu_*.png"))
    ),
)
def test_recognize(name: Text):
    _test.use_screenshot(f"single_mode/{name}.png")
    scene = MechaTuningMenu()
    scene.recognize(static=True)
    _test.snapshot_match(
        scene,
        name=name,
    )
