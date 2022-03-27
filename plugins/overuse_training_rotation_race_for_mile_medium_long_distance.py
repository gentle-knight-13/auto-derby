# -*- coding=UTF-8 -*-
# Code generated by auto-derby-plugin-generator 801d0f5
# URL: https://natescarlet.github.io/auto-derby-plugin-generator/#/plugins/race
# Date: 2022-03-27T06:59:46.010Z

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
    (16, "札幌ジュニアステークス"): _ACTION_PICK,
    (18, "サウジアラビアロイヤルカップ"): _ACTION_PICK,
    (19, "アルテミスステークス"): _ACTION_PICK,
    (21, "京都ジュニアステークス"): _ACTION_PICK,
    (21, "東京スポーツ杯ジュニアステークス"): _ACTION_PICK,
    (22, "朝日杯フューチュリティステークス"): _ACTION_PICK,
    (23, "ホープフルステークス"): _ACTION_PICK,
    (25, "若駒ステークス"): _ACTION_PICK,
    (26, "きさらぎ賞"): _ACTION_PICK,
    (26, "クイーンカップ"): _ACTION_PICK,
    (26, "共同通信杯"): _ACTION_PICK,
    (28, "チューリップ賞"): _ACTION_PICK,
    (28, "弥生賞"): _ACTION_PICK,
    (29, "スプリングステークス"): _ACTION_PICK,
    (29, "フラワーカップ"): _ACTION_PICK,
    (29, "毎日杯"): _ACTION_PICK,
    (30, "皐月賞"): _ACTION_PICK,
    (32, "NHKマイルカップ"): _ACTION_PICK,
    (33, "東京優駿（日本ダービー）"): _ACTION_PICK,
    (34, "安田記念"): _ACTION_PICK,
    (40, "ローズステークス"): _ACTION_PICK,
    (40, "京成杯オータムハンデキャップ"): _ACTION_PICK,
    (40, "新潟記念"): _ACTION_PICK,
    (40, "紫苑ステークス"): _ACTION_PICK,
    (41, "オールカマー"): _ACTION_PICK,
    (41, "セントライト記念"): _ACTION_PICK,
    (41, "神戸新聞杯"): _ACTION_PICK,
    (42, "京都大賞典"): _ACTION_PICK,
    (42, "府中ウマ娘ステークス"): _ACTION_PICK,
    (42, "毎日王冠"): _ACTION_PICK,
    (43, "菊花賞"): _ACTION_PICK,
    (45, "マイルチャンピオンシップ"): _ACTION_PICK,
    (46, "ステイヤーズステークス"): _ACTION_PICK,
    (46, "ターコイズステークス"): _ACTION_PICK,
    (46, "チャレンジカップ"): _ACTION_PICK,
    (46, "中日新聞杯"): _ACTION_PICK,
    (47, "有馬記念"): _ACTION_PICK,
    (53, "大阪杯"): _ACTION_PICK,
    (55, "天皇賞（春）"): _ACTION_PICK,
    (56, "ヴィクトリアマイル"): _ACTION_NONE,
    (58, "安田記念"): _ACTION_NONE,
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
