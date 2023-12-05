import auto_derby
from typing import Text, Dict, Tuple
from auto_derby import mathtools
from auto_derby.single_mode.commands.command import Command
from auto_derby.single_mode.commands.race import RaceCommand
from auto_derby.single_mode.context import Context
from auto_derby import single_mode, terminal

_ACTION_NONE = 0
_ACTION_BAN = 1
_ACTION_LESS = 2
_ACTION_MORE = 3
_ACTION_PICK = 4

_DEFAULT_ACTION = _ACTION_LESS

_RULES: Dict[Tuple[int, Text], int] = {
    (10, "ジュニア級未勝利戦"): _ACTION_NONE,
    (12, "ジュニア級未勝利戦"): _ACTION_NONE,
    (13, "ジュニア級未勝利戦"): _ACTION_NONE,
    (14, "ジュニア級未勝利戦"): _ACTION_NONE,
    (15, "ジュニア級未勝利戦"): _ACTION_NONE,
    (16, "ジュニア級未勝利戦"): _ACTION_NONE,
    (17, "ジュニア級未勝利戦"): _ACTION_NONE,
    (18, "ジュニア級未勝利戦"): _ACTION_NONE,
    (19, "ジュニア級未勝利戦"): _ACTION_NONE,
    (20, "ジュニア級未勝利戦"): _ACTION_NONE,
    (21, "ジュニア級未勝利戦"): _ACTION_NONE,
    (22, "ジュニア級未勝利戦"): _ACTION_NONE,
    (23, "ジュニア級未勝利戦"): _ACTION_NONE,
    (23, "ホープフルステークス"): _ACTION_PICK,
    (24, "クラシック級未勝利戦"): _ACTION_NONE,
    (25, "クラシック級未勝利戦"): _ACTION_NONE,
    (26, "クラシック級未勝利戦"): _ACTION_NONE,
    (27, "クラシック級未勝利戦"): _ACTION_NONE,
    (28, "クラシック級未勝利戦"): _ACTION_NONE,
    (29, "クラシック級未勝利戦"): _ACTION_NONE,
    (30, "クラシック級未勝利戦"): _ACTION_NONE,
    (30, "皐月賞"): _ACTION_PICK,
    (31, "クラシック級未勝利戦"): _ACTION_NONE,
    (32, "NHKマイルカップ"): _ACTION_MORE,
    (32, "クラシック級未勝利戦"): _ACTION_NONE,
    (33, "クラシック級未勝利戦"): _ACTION_NONE,
    (34, "クラシック級未勝利戦"): _ACTION_NONE,
    (35, "クラシック級未勝利戦"): _ACTION_NONE,
    (36, "クラシック級未勝利戦"): _ACTION_NONE,
    (37, "クラシック級未勝利戦"): _ACTION_NONE,
    (38, "クラシック級未勝利戦"): _ACTION_NONE,
    (40, "丹頂ステークス"): _ACTION_PICK,
    (43, "菊花賞"): _ACTION_PICK,
    (44, "アルゼンチン共和国杯"): _ACTION_PICK,
    (47, "有馬記念"): _ACTION_PICK,
    (55, "天皇賞（春）"): _ACTION_PICK,
    (59, "宝塚記念"): _ACTION_PICK,
    (64, "丹頂ステークス"): _ACTION_MORE,
    (67, "天皇賞（秋）"): _ACTION_PICK,
    (71, "有馬記念"): _ACTION_PICK,
}


class Race(single_mode.Race):
    def style_scores(
        self,
        ctx: single_mode.Context,
        *,
        _no_warn: bool = False,
    ) -> Tuple[float, float, float, float]:
        return (564, 0, 0, 0)

    def score(self, ctx: single_mode.Context) -> float:
        ret = super().score(ctx)
        action = _RULES.get(
            (ctx.turn_count(), self.name),
            _DEFAULT_ACTION,
        )
        if action == _ACTION_BAN:
            ret -= 15
        elif action == _ACTION_LESS:
            ret -= 5
        elif action == _ACTION_MORE:
            ret += 5
        elif action == _ACTION_PICK:
            ret += 100

        if self.distance <= 1400:
            ret = 0
        elif self.distance <= 1800:
            ret -= 5
        elif self.distance <= 2400:
            ret -= 15
        else:
            ret += 25
        return ret

    # def score(self, ctx: single_mode.Context) -> float:
    #     ret = super().score(ctx)
    #
    #     if self.distance <= 1400:
    #         ret -= (ctx.sprint_race_count - ctx.long_race_count) * 5
    #     elif self.distance <= 1800:
    #         ret -= (ctx.mile_race_count - ctx.long_race_count) * 6
    #     elif self.distance <= 2400:
    #         ret -= (ctx.intermediate_race_count - ctx.long_race_count) * 4
    #     else:
    #         ret += (max(ctx.sprint_race_count, ctx.mile_race_count, ctx.intermediate_race_count) - ctx.long_race_count) * 5.64
    #
    #     return ret


class RaceCommand(single_mode.commands.RaceCommand):
    def execute(self, ctx: single_mode.Context) -> None:
        if self.race.distance <= 1400:
            ctx.sprint_race_count += 1
        elif self.race.distance <= 1800:
            ctx.mile_race_count += 1
        elif self.race.distance <= 2400:
            ctx.intermediate_race_count += 1
        else:
            ctx.long_race_count += 1
        super().execute(ctx)


class Context(single_mode.Context):
    def __init__(self) -> None:
        super().__init__()
        self.sprint_race_count = 0
        self.mile_race_count = 0
        self.intermediate_race_count = 0
        self.long_race_count = 0


class Training(single_mode.Training):
    def score(self, ctx: single_mode.Context) -> float:
        ret = super().score(ctx)
        ret += mathtools.integrate(
            ctx.stamina,
            self.stamina,
            (
                (0, 2.0),
                (300, 0.8),
                (400, 1.2),
                (650, 0.6),
                (900, 0.1),
            ),
        )
        ret += mathtools.integrate(
            ctx.power,
            self.power,
            (
                (0, 1.75),
                (300, 0.5),
                (650, 0.4),
                (900, 0.1),
            ),
        )
        return ret


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        auto_derby.plugin.install("no_ocr_prompt")
        auto_derby.config.single_mode_race_class = Race
        auto_derby.config.single_mode_context_class = Context
        auto_derby.config.single_mode_training_class = Training
        auto_derby.config.pause_if_race_order_gt = 1


auto_derby.plugin.register(__name__, Plugin())
