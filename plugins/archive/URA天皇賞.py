import auto_derby
import logging
from auto_derby import single_mode, mathtools
from typing import Tuple, Text, Dict

LOGGER = logging.getLogger(__name__)

from typing import Text, Dict, Tuple


class Training(single_mode.Training):
    def score(self, ctx: single_mode.Context) -> float:
        ret = super().score(ctx)
        success_rate = 1 - self.failure_rate
        sta = mathtools.integrate(
            ctx.stamina,
            self.stamina,
            ((0, 1.5), (400, 0.5), (500, 0.0)),
        )
        ret += sta * success_rate
        return ret


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        auto_derby.config.single_mode_training_class = Training


auto_derby.plugin.register(__name__, Plugin())
