from typing import Callable, List
import auto_derby
from auto_derby.single_mode import Context


_NAME = "都留岐涼花"

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

## 意外な素顔？（お出かけ1）
# 体力+30~48
_VIT[0] = 48
# やる気アップ
_MOOD[0] = 1
# スピード+10~12
_SPD[0] = 12
# 賢さ+10~12
_WIS[0] = 12
# すべての競技Lv+1
# 都留岐涼花の絆ゲージ+5


## 『貴方のおっしゃる通りでした』（お出かけ2）
# 体力+30~48
_VIT[1] = 48
# やる気アップ
_MOOD[1] = 1
# スピード+10~12
_SPD[1] = 12
# 賢さ+10~12
_WIS[1] = 12
# すべての競技Lv+1
# 都留岐涼花の絆ゲージ+5

## 貴方の胸にも灯を（お出かけ3）
### すごくカワイイカリスマがいて……
# 体力+50~80
_VIT[2] = 80
# やる気アップ
_MOOD[2] = 1
# すべての競技Lv+1
# 都留岐涼花の絆ゲージ+5
### センスが爆発している子がいて……
# やる気アップ
# スピード+45~56
# すべての競技Lv+1
# 都留岐涼花の絆ゲージ+5

## きっと何色の未来でも（お出かけ4）
# 体力+30~48
_VIT[3] = 48
# やる気アップ
_MOOD[3] = 1
# スピード+25~32
_SPD[3] = 32
# すべての競技Lv+1
# 都留岐涼花の絆ゲージ+5


## 胸の内を少しだけ（お出かけ5）
### 大成功時：
# 体力+40~64
_VIT[4] = 64
# やる気アップ
_MOOD[4] = 1
# スピード+30~37
_SPD[4] = 37
# 『機先の勝負』のヒントLv+3
# すべての競技Lv+1
# 都留岐涼花の絆ゲージ+5
### 成功時：
# 体力+35~56
# スピード+15~18
# 『機先の勝負』のヒントLv+1
# すべての競技レベル+1
# 都留岐涼花の絆ゲージ+5


class Plugin(auto_derby.Plugin):
    """
    Use this when friend cards include SSR都留岐涼花.
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
