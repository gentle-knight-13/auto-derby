import auto_derby
from auto_derby import single_mode


class Plugin(auto_derby.Plugin):
    """Use this after other plugin, run g1 only."""

    def install(self) -> None:
        class Race(auto_derby.config.single_mode_race_class):
            def score(self, ctx: single_mode.Context) -> float:
                ret = super().score(ctx)
                if self.grade != Race.GRADE_G1:
                    ret = 0
                return ret

        auto_derby.config.single_mode_race_class = Race


auto_derby.plugin.register(__name__, Plugin())
