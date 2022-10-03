# -*- coding=UTF-8 -*-
# Code generated by auto-derby-plugin-generator 89d8649
# URL: https://natescarlet.github.io/auto-derby-plugin-generator/#/plugins/race
# Date: 2022-09-05T10:27:34.152Z

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
    (14, "ジュニア級未勝利戦"): _ACTION_PICK,
    (15, "新潟ジュニアステークス"): _ACTION_PICK,
    (16, "札幌ジュニアステークス"): _ACTION_PICK,
    (18, "サウジアラビアロイヤルカップ"): _ACTION_PICK,
    (19, "アルテミスステークス"): _ACTION_PICK,
    (21, "京都ジュニアステークス"): _ACTION_PICK,
    (21, "東京スポーツ杯ジュニアステークス"): _ACTION_PICK,
    (22, "阪神ジュベナイルフィリーズ"): _ACTION_PICK,
    (23, "ホープフルステークス"): _ACTION_PICK,
    (26, "きさらぎ賞"): _ACTION_PICK,
    (26, "クイーンカップ"): _ACTION_PICK,
    (26, "共同通信杯"): _ACTION_PICK,
    (28, "チューリップ賞"): _ACTION_PICK,
    (28, "弥生賞"): _ACTION_PICK,
    (29, "スプリングステークス"): _ACTION_PICK,
    (29, "フラワーカップ"): _ACTION_PICK,
    (29, "毎日杯"): _ACTION_PICK,
    (30, "桜花賞"): _ACTION_PICK,
    (32, "NHKマイルカップ"): _ACTION_PICK,
    (33, "オークス"): _ACTION_PICK,
    (35, "宝塚記念"): _ACTION_PICK,
    (36, "ジャパンダートダービー"): _ACTION_PICK,
    (41, "さざんかテレビ杯"): _ACTION_PICK,
    (41, "シリウスステークス"): _ACTION_PICK,
    (42, "マイルチャンピオンシップ南部杯"): _ACTION_PICK,
    (43, "秋華賞"): _ACTION_PICK,
    (44, "エリザベス女王杯"): _ACTION_PICK,
    (45, "マイルチャンピオンシップ"): _ACTION_PICK,
    (46, "チャンピオンズカップ"): _ACTION_PICK,
    (47, "東京大賞典"): _ACTION_PICK,
    (50, "川崎記念"): _ACTION_PICK,
    (51, "フェブラリーステークス"): _ACTION_PICK,
    (53, "大阪杯"): _ACTION_PICK,
    (54, "アンタレスステークス"): _ACTION_PICK,
    (54, "マリーンカップ"): _ACTION_PICK,
    (56, "ヴィクトリアマイル"): _ACTION_PICK,
    (58, "安田記念"): _ACTION_PICK,
    (59, "帝王賞"): _ACTION_PICK,
    (66, "マイルチャンピオンシップ南部杯"): _ACTION_PICK,
    (67, "天皇賞（秋）"): _ACTION_PICK,
    (68, "エリザベス女王杯"): _ACTION_PICK,
    (69, "ジャパンカップ"): _ACTION_PICK,
    (70, "チャンピオンズカップ"): _ACTION_PICK,
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
                    ret += 1000
                return ret

        auto_derby.config.single_mode_race_class = Race


auto_derby.plugin.register(__name__, Plugin())
