import auto_derby
import logging
from auto_derby import single_mode, mathtools
from typing import Dict, Text, Tuple

LOGGER = logging.getLogger(__name__)

_ACTION_NONE = 0
_ACTION_BAN = 1
_ACTION_LESS = 2
_ACTION_MORE = 3
_ACTION_PICK = 4

_DEFAULT_ACTION = _ACTION_NONE

_RULES: Dict[Tuple[int, Text], int] = {
    (23, "ホープフルステークス"): _ACTION_PICK,
    (47, "有馬記念"): _ACTION_PICK,
    (71, "有馬記念"): _ACTION_PICK,
}

class Race(single_mode.Race):
    def style_scores(
        self,
        ctx: single_mode.Context,
        *,
        _no_warn: bool = False,
    ) -> Tuple[float, float, float, float]:
        if not _no_warn:
            # TODO: remove old api at next major version
            import warnings

            warnings.warn(
                "use style_scores_v2 instead",
                DeprecationWarning,
            )
        if self.name == "URAファイナルズ決勝":
            return (0, 1, 0, 0)

        ret = super().style_scores(ctx)
        return ret

    def score(self, ctx: single_mode.Context) -> float:
        LOGGER.debug("%s",ctx.date)
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
        
        if self.ground != Race.GROUND_DART:
            ret += {
                Race.GRADE_G1: 5,
                Race.GRADE_G2: 0,
                Race.GRADE_G3: -10,
                Race.GRADE_OP: -20,
                Race.GRADE_PRE_OP: -30,
                Race.GRADE_NOT_WINNING: 0,
                Race.GRADE_DEBUT: 0,
            }[self.grade]
        return ret


class Context(single_mode.Context):
    def next_turn(self) -> None:
        super().next_turn()
        if auto_derby.config.user_pause_if_race_order_gt == -1:
            auto_derby.config.user_pause_if_race_order_gt = auto_derby.config.pause_if_race_order_gt
        auto_derby.config.pause_if_race_order_gt = {
            (2, 3, 1): 5,
            (2, 5, 1): 5,
            (2, 10, 1): 3,
            (3, 3, 1): 3,
            (3, 4, 1): 1,
            (3, 6, 1): 3,
            (3, 12, 1): 1,
            (5, 1, 2): 1
        }.get(self.date, auto_derby.config.user_pause_if_race_order_gt)


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        auto_derby.config.user_pause_if_race_order_gt = -1
        auto_derby.config.single_mode_race_class = Race
        auto_derby.config.single_mode_context_class = Context


auto_derby.plugin.register(__name__, Plugin())
