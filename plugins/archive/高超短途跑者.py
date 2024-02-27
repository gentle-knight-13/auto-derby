# -*- coding=UTF-8 -*-
# Code generated by auto-derby-plugin-generator 89d8649
# URL: https://natescarlet.github.io/auto-derby-plugin-generator/#/plugins/race
# Date: 2023-07-17T19:14:34.775Z

import auto_derby
from auto_derby import single_mode


from typing import Text, Dict, Tuple

_ACTION_NONE = 0
_ACTION_BAN = 1
_ACTION_LESS = 2
_ACTION_MORE = 3
_ACTION_PICK = 4

_DEFAULT_ACTION = _ACTION_NONE

_RULES: Dict[Tuple[int, Text], int] = {
    (41, "スプリンターズステークス"): _ACTION_PICK,
    (53, "高松宮記念"): _ACTION_PICK,
    (65, "スプリンターズステークス"): _ACTION_PICK,
}


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        class Race(auto_derby.config.single_mode_race_class):
            def score(self, ctx: single_mode.Context) -> float:
                ret = super().score(ctx)
                action = _RULES.get(
                    (ctx.turn_count(), self.name),
                    _DEFAULT_ACTION,
                )
                if action == _ACTION_BAN:
                    ret = 0
                elif action == _ACTION_LESS:
                    ret -= 5
                elif action == _ACTION_MORE:
                    ret += 5
                elif action == _ACTION_PICK:
                    ret += 100
                return ret

        auto_derby.config.single_mode_race_class = Race


auto_derby.plugin.register(__name__, Plugin())
