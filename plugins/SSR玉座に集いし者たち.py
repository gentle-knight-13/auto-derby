import auto_derby
from auto_derby.single_mode import Context


_NAME = "玉座に集いし者たち"

_VIT = [0, 0, 0, 0, 0]
_MOOD = [0, 0, 0, 0, 0]
_HEAL = [0, 0, 0, 0, 0]
_SPD = [0, 0, 0, 0, 0]
_STA = [0, 0, 0, 0, 0]
_POW = [0, 0, 0, 0, 0]
_GUT = [0, 0, 0, 0, 0]
_WIS = [0, 0, 0, 0, 0]
_SKILL = [0, 0, 0, 0, 0]


# https://gamewith.jp/uma-musume/article/show/352274

## 学生らしく（シンボリルドルフ）（お出かけ1）
# 体力+10～13
_VIT[0] = 10
# 賢さ+30～36
_WIS[0] = 30
# 『闘争心』のヒントLv+1
# 玉座に集いし者たちの絆ゲージ+5

## Emperor’s pride.（トウカイテイオー）（お出かけ2）
# 体力+10～13
_VIT[1] = 10
# やる気アップ
_MOOD[1] = 1
# スピード+20~24
_SPD[1] = 20
# 『ポジションセンス』のヒントLv+1
# 玉座に集いし者たちの絆ゲージ+5

## のんびり、歩幅を合わせて（ツルマルツヨシ）（お出かけ3）
# 体力+30～39
_VIT[2] = 30
# スキルPt+15~18
_SKILL[2] = 15
# 『フルスロットル』のヒントLv+1
# 玉座に集いし者たちの絆ゲージ+5

## カイチョーみたいに！（玉座に集いし者たち）（お出かけ4）
# 体力+20~26
_VIT[3] = 20
# スピード+10～12
_SPD[3] = 10
# 賢さ+25~30
_WIS[3] = 25
# スキルPt+15~18
_SKILL[3] = 15
# 『夜ふかし気味』『なまけ癖』が治る
_HEAL[3] = 1
# 『中山レース場◯』のヒントLv+1
# 玉座に集いし者たちの絆ゲージ+5

## 会長みたいに！（玉座に集いし者たち）（お出かけ5）
# 体力+20~26
_VIT[4] = 20
# スピード+15~18
_SPD[4] = 15
# 賢さ+30~36
_WIS[4] = 30
# スキルPt+20~24
_SKILL[4] = 20
# 『夜ふかし気味』『なまけ癖』が治る
_HEAL[4] = 1
# 『情熱ゾーン：玉座に集いし者たち』になる
# 『光芒円刃』のヒントLv+1
# 玉座に集いし者たちの絆ゲージ+5


class Plugin(auto_derby.Plugin):
    """
    Use this when friend cards include SSR樫本理子.
    Multiple friend type support card is not supported yet.
    """

    def install(self) -> None:
        auto_derby.config.single_mode_go_out_names.add(_NAME)

        class Option(auto_derby.config.single_mode_go_out_option_class):
            def heal_rate(self, ctx: Context) -> float:
                if self.name != _NAME:
                    return super().heal_rate(ctx)

                return _HEAL[self.current_group_event_count]

            def mood_rate(self, ctx: Context) -> float:
                if self.name != _NAME:
                    return super().mood_rate(ctx)

                return _MOOD[self.current_group_event_count]

            def vitality(self, ctx: Context) -> float:
                if self.name != _NAME:
                    return super().vitality(ctx)

                return _VIT[self.current_group_event_count] / ctx.max_vitality

            def score(self, ctx: Context) -> float:
                ret = super().score(ctx)
                if self.name != _NAME:
                    return ret

                t = Training()
                c = self.current_group_event_count
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
