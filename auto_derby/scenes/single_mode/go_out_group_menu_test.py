from typing import Text
from .go_out_group_menu import GoOutGroupMenuScene

from ... import _test
import pytest

from ...single_mode import Context


@pytest.mark.parametrize(
    "name",
    tuple(
        i.stem for i in ((_test.DATA_PATH / "single_mode").glob("go_out_group_menu_*.png"))
    ),
)
def test_recognize(name: Text):
    _test.use_screenshot(f"single_mode/{name}.png")
    ctx = Context.new()
    scene = GoOutGroupMenuScene()
    scene.recognize(ctx, static=True)
    _test.snapshot_match(
        {"options": scene.go_out_options},
        name=name,
    )
