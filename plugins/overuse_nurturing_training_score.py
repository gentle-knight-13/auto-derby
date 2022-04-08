import auto_derby
from auto_derby import single_mode
from auto_derby.single_mode.commands.globals import g

import logging

_LOGGER = logging.getLogger(__name__)

class Training(single_mode.Training):
    def score(self, ctx: single_mode.Context) -> float:
        ret = super().score(ctx)

        climax_status_limit = 1140
        if self.type == self.TYPE_SPEED:
            if ctx.speed >= climax_status_limit:
                ret -= self.speed
            # else:
            #     ret += self.speed * 0.3

            if ctx.power >= climax_status_limit:
                ret -= self.power
            # else:
            #     ret += self.power * 0.3

        elif self.type == self.TYPE_STAMINA:
            if ctx.stamina >= climax_status_limit:
                ret -= self.stamina
            # else:
            #     ret += self.stamina * 0.3
            if ctx.guts >= climax_status_limit:
                ret -= self.guts
            # else:
            #     ret += self.guts * 0.3

        elif self.type == self.TYPE_POWER:
            if ctx.power >= climax_status_limit:
                ret -= self.power
            else:
                ret += self.power * 0.3
            if ctx.stamina >= climax_status_limit:
                ret -= self.stamina
            else:
                ret += self.stamina * 0.3

        elif self.type == self.TYPE_GUTS:
            if ctx.guts >= climax_status_limit:
                ret -= self.guts
            # else:
            #     ret += self.guts * 0.3
            if ctx.speed >= climax_status_limit:
                ret -= self.speed
            # else:
            #     ret += self.speed * 0.3
            if ctx.power >= climax_status_limit:
                ret -= self.power
            # else:
            #     ret += self.power * 0.3

        elif self.type == self.TYPE_WISDOM:
            if ctx.wisdom >= climax_status_limit:
                ret -= self.wisdom
            # else:
            #     ret += self.wisdom * 0.3
            if ctx.speed >= climax_status_limit:
                ret -= self.speed
            # else:
            #     ret += self.speed * 0.3

        return ret


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        auto_derby.config.single_mode_training_class = Training


auto_derby.plugin.register(__name__, Plugin())


def _amulet_can_improve_failure_rate(i: single_mode.item.Item):
    es = i.effect_summary()
    return es.training_no_failure


def sum_item_vitality(items: single_mode.item.ItemList):
    vitality = 0
    for i in items:
        es = i.effect_summary()
        vitality += es.vitality
    return vitality


def ignore_training_commands(ctx: single_mode.Context) -> bool:
    if (
        any(_amulet_can_improve_failure_rate(i) for i in ctx.items)
        and ctx.vitality <= 0.50
    ):
        False

    estimate_vitality = ctx.vitality + (sum_item_vitality(ctx.items) / 100)
    if estimate_vitality >= 0.50:
        return False

    if ctx.vitality < 0.20:
        return True

    return False

g.ignore_training_commands = ignore_training_commands
