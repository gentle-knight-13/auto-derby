# -*- coding=UTF-8 -*-
# Code generated by auto-derby-plugin-generator 801d0f5
# URL: https://natescarlet.github.io/auto-derby-plugin-generator/#/plugins/race
# Date: 2022-04-03T18:41:13.152Z

import auto_derby
from auto_derby import single_mode


from typing import Text, Dict, Tuple

_ACTION_NONE = 0
_ACTION_BAN = 1
_ACTION_LESS = 2
_ACTION_MORE = 3
_ACTION_PICK = 4

_DEFAULT_ACTION = _ACTION_BAN

_RULES: Dict[Tuple[int, Text], int] = {
    (16, "ジュニア級未勝利戦"): _ACTION_PICK,
    (17, "ジュニア級未勝利戦"): _ACTION_PICK,
    (17, "芙蓉ステークス"): _ACTION_PICK,
    (18, "紫菊賞"): _ACTION_PICK,
    (20, "百日草特別"): _ACTION_PICK,
    (21, "京都ジュニアステークス"): _ACTION_PICK,
    (23, "ホープフルステークス"): _ACTION_PICK,
    (24, "京成杯"): _ACTION_PICK,
    (25, "若駒ステークス"): _ACTION_PICK,
    (27, "すみれステークス"): _ACTION_PICK,
    (28, "弥生賞"): _ACTION_PICK,
    (30, "皐月賞"): _ACTION_PICK,
    (31, "青葉賞"): _ACTION_PICK,
    (32, "京都新聞杯"): _ACTION_PICK,
    (33, "東京優駿（日本ダービー）"): _ACTION_PICK,
    (35, "宝塚記念"): _ACTION_PICK,
    (40, "新潟記念"): _ACTION_PICK,
    (41, "オールカマー"): _ACTION_PICK,
    (43, "菊花賞"): _ACTION_PICK,
    (44, "アルゼンチン共和国杯"): _ACTION_PICK,
    (45, "ジャパンカップ"): _ACTION_PICK,
    (46, "ステイヤーズステークス"): _ACTION_PICK,
    (47, "有馬記念"): _ACTION_PICK,
    (49, "アメリカJCC"): _ACTION_PICK,
    (53, "大阪杯"): _ACTION_PICK,
    (55, "天皇賞（春）"): _ACTION_PICK,
    (59, "宝塚記念"): _ACTION_PICK,
    (67, "天皇賞（秋）"): _ACTION_PICK,
    (69, "ジャパンカップ"): _ACTION_PICK,
    (71, "有馬記念"): _ACTION_PICK,
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
