import auto_derby
from auto_derby.single_mode import Context


_NAME = "祖にして導くもの"

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

## 偉大なる者と旅を(ダーレーアラビアン)（お出かけ1）
# 体力+35~45
_VIT[0] = 35
# やる気アップ
_MOOD[0] = 1
# スキルPt+20~24
_SKILL[0] = 20
#『直線巧者』のヒントLv+1
#『ウマ好み』のヒントLv+1
# 祖にして導く者の絆ゲージ+5

## まるで魔法使いのように(ゴドルフィンバルブ)（お出かけ2）
# 体力+25~32
_VIT[1] = 25
# やる気アップ
_MOOD[1] = 1
# スピード+10~12
_SPD[1] = 10
# 賢さ+10~12
_WIS[1] = 10
# バットステータス回復
_HEAL[1] = 1
# 『積極策』のヒントLv+1
# 『善後策』のヒントLv+1
# 祖にして導く者の絆ゲージ+5

## 旋風の如き強さは(バイアリーターク)（お出かけ3）
# 体力+25~32
_VIT[2] = 25
# やる気アップ
_MOOD[2] = 1
# スピード+10～12
_SPD[2] = 10
# スタミナ+7~8
_STA[2] = 7
# パワー+7~8
_POW[2] = 7
# 根性+7~8
_GUT[2] = 7
# スキルPt+15~18
_SKILL[2] = 15
# 体力の最大値+4
# 『深呼吸』のヒントLv+1
# 『ありったけ』のヒントLv+1
# 祖にして導く者の絆ゲージ+5

## 三女神から、彼女たちへ(祖にして導くもの)（お出かけ4）
### 『自由』にレースを楽しんでほしい
# 体力+35~45
_VIT[3] = 35
# やる気アップ
_MOOD[3] = 1
# 5種ステータス+8~9
_SPD[3] = 8
_STA[3] = 8
_POW[3] = 8
_GUT[3] = 8
_WIS[3] = 8
# 祖にして導く者の絆ゲージ+5
### 『自分』の走りを極めてほしい
# 体力+35~45
# やる気アップ
# スピード+20~24
# 賢さ＋20~24
# 祖にして導く者の絆ゲージ+5
### 『強靭』なウマ娘にしてあげたい
# 体力+35~45
# やる気アップ
# スタミナ+13~15
# パワー+13~15
# 根性+13~15
# 祖にして導く者の絆ゲージ+5

## 彼女たちから、あなたたちへ(祖にして導くもの)（お出かけ5）
# 体力+20~26
_VIT[4] = 20
# やる気アップ
_MOOD[4] = 1
# 5種ステータス+8~9
_SPD[4] = 8
_STA[4] = 8
_POW[4] = 8
_GUT[4] = 8
_WIS[4] = 8
# スキルPt+30~36
_SKILL[4] = 30
# 『夜ふかし気味』『なまけ癖』が治る
_HEAL[4] = 1
# 『神速』のヒントLv+3
# 『情熱ゾーン：祖にして導く者』になる
# 祖にして導く者の絆ゲージ+5

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
