import auto_derby
from auto_derby import single_mode, mathtools

class Plugin(auto_derby.Plugin):
    """Tries to suppress any value to become MAX"""
    def install(self) -> None:
        class Training(single_mode.Training):
            def score(self, ctx: single_mode.Context) -> float:
                ret = super().score(ctx)
                if not ctx.is_after_winning:
                    ret += 5 * len(self.partners)
                ret += mathtools.integrate(
                    ctx.speed,
                    self.speed,
                    (
                        (0, 0.0),
                        (900, 0.0),
                        (1120, -0.2),
                        (1150, -5.0),
                    ),
                )
                ret += mathtools.integrate(
                    ctx.stamina,
                    self.stamina,
                    (
                        (0, 0.0),
                        (800, 0.0),
                        (1120, -0.2),
                        (1150, -5.0),
                    ),
                )
                ret += mathtools.integrate(
                    ctx.power,
                    self.power,
                    (
                        (0, 0.0),
                        (800, 0.0),
                        (1120, -0.2),
                        (1150, -5.0),
                    ),
                )
                ret += mathtools.integrate(
                    ctx.guts,
                    self.guts,
                    (
                        (0, 0.0),
                        (800, 0.0),
                        (1120, -0.2),
                        (1150, -5.0),
                    ),
                )
                ret += mathtools.integrate(
                    ctx.wisdom,
                    self.wisdom,
                    (
                        (0, 0.0),
                        (800, 0.0),
                        (1120, -0.2),
                        (1150, -5.0),
                    ),
                )
                return ret

        class Item(auto_derby.config.single_mode_item_class):
            def exchange_score(self, ctx: single_mode.Context) -> float:
                ret = super().exchange_score(ctx)
                if self.name.endswith("メモ帳") or self.name.endswith("戦術書") or self.name.endswith("秘伝書"):
                    ret += 5
                return ret

        auto_derby.config.single_mode_training_class = Training
        auto_derby.config.single_mode_item_class = Item


auto_derby.plugin.register(__name__, Plugin())
