import auto_derby
from auto_derby import single_mode

import logging

_LOGGER = logging.getLogger(__name__)

class Training(single_mode.Training):
    def score(self, ctx: single_mode.Context) -> float:
        ret = super().score(ctx)

        climax_status_limit = 1120
        if self.type == self.TYPE_SPEED:
            if ctx.speed >= climax_status_limit:
                ret -= self.speed
            if ctx.power >= climax_status_limit:
                ret -= self.power

        elif self.type == self.TYPE_STAMINA:
            if ctx.stamina >= climax_status_limit:
                ret -= self.stamina
            if ctx.guts >= climax_status_limit:
                ret -= self.guts

        elif self.type == self.TYPE_POWER:
            if ctx.power >= climax_status_limit:
                ret -= self.power
            if ctx.stamina >= climax_status_limit:
                ret -= self.stamina

        elif self.type == self.TYPE_GUTS:
            if ctx.guts >= climax_status_limit:
                ret -= self.guts
            if ctx.speed >= climax_status_limit:
                ret -= self.speed
            if ctx.power >= climax_status_limit:
                ret -= self.power

        elif self.type == self.TYPE_WISDOM:
            if ctx.wisdom >= climax_status_limit:
                ret -= self.wisdom
            if ctx.speed >= climax_status_limit:
                ret -= self.speed

        return ret


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        auto_derby.config.single_mode_training_class = Training


auto_derby.plugin.register(__name__, Plugin())
