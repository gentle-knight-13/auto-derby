from typing import Callable, List
import auto_derby
from auto_derby.single_mode import Context


_NAME = "秋川理事長"

_VIT = [0, 0, 0, 0, 0]
_MOOD = [0, 0, 0, 0, 0]
_HEAL = [0, 0, 0, 0, 0]
_SPD = [0, 0, 0, 0, 0]
_STA = [0, 0, 0, 0, 0]
_POW = [0, 0, 0, 0, 0]
_GUT = [0, 0, 0, 0, 0]
_WIS = [0, 0, 0, 0, 0]
_SKILL = [0, 0, 0, 0, 0]


# https://gamewith.jp/uma-musume/article/show/437704

## （お出かけ1）
# 体力+30~54
_VIT[0] = 54
# やる気アップ
_MOOD[0] = 1
# 根性+20~25
_GUT[0] = 25
# 秋川理事長の絆ゲージ+5

## （お出かけ2）
# 体力+30~54
_VIT[1] = 54
# やる気アップ
_MOOD[1] = 1
# スピード+10~12
_SPD[1] = 12
# 根性+10~12
_GUT[1] = 12
# 秋川理事長の絆ゲージ+5

##（お出かけ3）
###
# 体力+43~77
_VIT[2] = 77
# やる気アップ
_MOOD[2] = 1
# 秋川理事長の絆ゲージ+5

##（お出かけ4）
# 体力+30~54
_VIT[3] = 54
# やる気アップ
_MOOD[3] = 1
# 根性+25~31
_GUT[3] = 31
# 秋川理事長の絆ゲージ+5

## （お出かけ5）
### 大成功時：
# 体力+30~54
_VIT[4] = 54
# やる気アップ
_MOOD[4] = 1
# スピード+36~45
_GUT[4] = 45


class Plugin(auto_derby.Plugin):
    """
    Use this when friend cards include SSR秋川理事長.
    Multiple friend type support card is not supported yet.
    """

    def install(self) -> None:
        auto_derby.config.single_mode_go_out_names.add(_NAME)

        class Option(auto_derby.config.single_mode_go_out_option_class):
            def heal_rate(self, ctx: Context) -> float:
                if self.name != _NAME:
                    return super().heal_rate(ctx)

                return _HEAL[self.current_event_count]

            def mood_rate(self, ctx: Context) -> float:
                if self.name != _NAME:
                    return super().mood_rate(ctx)

                return _MOOD[self.current_event_count]

            def vitality(self, ctx: Context) -> float:
                if self.name != _NAME:
                    return super().vitality(ctx)

                return _VIT[self.current_event_count] / ctx.max_vitality

            def score(self, ctx: Context) -> float:
                ret = super().score(ctx)
                if self.name != _NAME:
                    return ret

                t = Training()
                c = self.current_event_count
                t.speed = _SPD[c]
                t.stamina = _STA[c]
                t.power = _POW[c]
                t.guts = _GUT[c]
                t.wisdom = _WIS[c]
                t.skill = _SKILL[c]
                ret += t.score(ctx)

                return ret

        auto_derby.config.single_mode_go_out_option_class = Option

        class Training(auto_derby.config.single_mode_training_class):
            def score(self, ctx: Context) -> float:
                return super().score(ctx)

        auto_derby.config.single_mode_training_class = Training


auto_derby.plugin.register(__name__, Plugin())
