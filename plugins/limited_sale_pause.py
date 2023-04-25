# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations

import auto_derby

from auto_derby import limited_sale
from auto_derby import terminal


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        auto_derby.config.on_limited_sale = lambda: terminal.pause(f"pause when limied sale")


auto_derby.plugin.register(__name__, Plugin())
