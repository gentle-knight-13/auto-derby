import auto_derby
from auto_derby import single_mode, mathtools

from typing import Text, Dict, Tuple

_ACTION_NONE = 0
_ACTION_BAN = 1
_ACTION_LESS = 2
_ACTION_MORE = 3
_ACTION_PICK = 4

_DEFAULT_ACTION = _ACTION_LESS

_RULES: Dict[Tuple[int, Text], int] = {
    (21, "京都ジュニアステークス"): _ACTION_PICK,
    (23, "ホープフルステークス"): _ACTION_PICK,
    (24, "京成杯"): _ACTION_PICK,
    (28, "弥生賞"): _ACTION_PICK,
    (30, "皐月賞"): _ACTION_PICK,
    (32, "京都新聞杯"): _ACTION_PICK,
    (33, "東京優駿（日本ダービー）"): _ACTION_PICK,
    (35, "宝塚記念"): _ACTION_MORE,
    (40, "紫苑ステークス"): _ACTION_PICK,
    (41, "神戸新聞杯"): _ACTION_PICK,
    (43, "菊花賞"): _ACTION_PICK,
    (44, "エリザベス女王杯"): _ACTION_PICK,
    (47, "有馬記念"): _ACTION_MORE,
    (48, "日経新春杯"): _ACTION_PICK,
    (50, "京都記念"): _ACTION_PICK,
    (52, "金鯱賞"): _ACTION_PICK,
    (53, "大阪杯"): _ACTION_PICK,
    (55, "天皇賞（春）"): _ACTION_PICK,
    (57, "目黒記念"): _ACTION_PICK,
    (59, "宝塚記念"): _ACTION_PICK,
    (62, "小倉記念"): _ACTION_PICK,
    (64, "新潟記念"): _ACTION_PICK,
    (65, "オールカマー"): _ACTION_PICK,
    (67, "天皇賞（秋）"): _ACTION_PICK,
    (69, "ジャパンカップ"): _ACTION_PICK,
    (70, "中日新聞杯"): _ACTION_PICK,
    (71, "有馬記念"): _ACTION_PICK,
}


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        class Race(auto_derby.config.single_mode_race_class):
            def score(self, ctx: single_mode.Context) -> float:
                ret = super().score(ctx)
                if (self.ground == self.GROUND_TURF and ctx.turf <= ctx.STATUS_B) or (self.ground == self.GROUND_DART and ctx.dart <= ctx.STATUS_B):
                    return ret
                if (self.distance > 2400 and ctx.sprint <= ctx.STATUS_B) or (self.distance > 1800 and self.distance <= 2400 and ctx.intermediate <= ctx.STATUS_B) or (self.distance > 1400 and self.distance <= 1800 and ctx.mile <= ctx.STATUS_B) or (self.distance <= 1400 and ctx.sprint <= ctx.STATUS_B):
                    return ret
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
                    ret += 20
                return ret

        auto_derby.config.single_mode_race_class = Race


auto_derby.plugin.register(__name__, Plugin())
