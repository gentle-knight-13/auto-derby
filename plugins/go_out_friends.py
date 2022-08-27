from mimetypes import init
from typing import Callable, List, Tuple
import auto_derby
from auto_derby import mathtools
from auto_derby.single_mode import Context
from auto_derby.__version__ import VERSION
from auto_derby import version


def generate_friend_dict() -> dict:
    friend_dict = {}

    name, effect = generate_friend_for_hayakawa_tazuna()
    friend_dict[name] = effect

    name, effect = generate_friend_for_kashimoto_riko()
    friend_dict[name] = effect

    name, effect = generate_friend_for_light_halo()
    friend_dict[name] = effect

    return friend_dict


def generate_friend_for_hayakawa_tazuna() -> Tuple[str, dict]:
    vit = [0, 0, 0, 0, 0]
    mood = [0, 0, 0, 0, 0]
    heal = [0, 0, 0, 0, 0]
    spd = [0, 0, 0, 0, 0]
    sta = [0, 0, 0, 0, 0]
    pow = [0, 0, 0, 0, 0]
    gut = [0, 0, 0, 0, 0]
    wis = [0, 0, 0, 0, 0]
    skill = [0, 0, 0, 0, 0]

    # https://gamewith.jp/uma-musume/article/show/257441

    ## 牛乳ときどきリンゴ（お出かけ1）
    # 体力+25~40
    vit[0] = 30
    # スピード+5~6
    spd[0] = 5
    # やる気アップ
    mood[0] = 1
    # 駿川たづなの絆ゲージ+5

    ## 驚異の逃げ脚？（お出かけ2）
    # 体力+25~40
    vit[1] = 32
    # 駿川たづなの絆ゲージ+5
    # バッドコンディションが治る
    heal[1] = 1

    ## キネマの思ひ出（お出かけ3）
    ### 『200億の女～キケンな専業主婦～』
    # 体力+25~40
    vit[2] = 32
    # スタミナ+5~6
    sta[2] = 5
    # やる気アップ
    mood[2] = 1
    # 駿川たづなの絆ゲージ+5
    ### 『白球ひと筋、空へ――熱血野球部物語！』
    # スタミナ+10~13
    # 根性+10~13
    # やる気アップ
    # 駿川たづなの絆ゲージ+5

    ### ため息と絆創膏（お出かけ4）
    # 体力+35~56
    vit[3] = 45
    # 賢さ+5~6
    wis[3] = 5
    # やる気アップ
    mood[3] = 1
    # 駿川たづなの絆ゲージ+5
    # バッドコンディションが治る
    heal[3] = 1

    ###ひと休みサプライズ（お出かけ5）
    # 体力+35~56
    vit[4] = 45
    # スキルpt+30~40
    skill[4] = 35
    # やる気2段階アップ
    mood[4] = 2
    # 駿川たづなの絆ゲージ+5
    # 以下からランダムで獲得
    # 『集中力』のヒントlv+1
    # 『コンセントレーション』のヒントlv+1

    return "駿川たづな", {
        "vit": vit,
        "mood": mood,
        "heal": heal,
        "spd": spd,
        "sta": sta,
        "pow": pow,
        "gut": gut,
        "wis": wis,
        "skill": skill,
    }


def generate_friend_for_kashimoto_riko() -> Tuple[str, dict]:
    vit = [0, 0, 0, 0, 0]
    mood = [0, 0, 0, 0, 0]
    heal = [0, 0, 0, 0, 0]
    spd = [0, 0, 0, 0, 0]
    sta = [0, 0, 0, 0, 0]
    pow = [0, 0, 0, 0, 0]
    gut = [0, 0, 0, 0, 0]
    wis = [0, 0, 0, 0, 0]
    skill = [0, 0, 0, 0, 0]

    # https://gamewith.jp/uma-musume/article/show/292758

    ## 歌には想いを乗せて（お出かけ1）
    # 体力+30～32
    vit[0] = 30
    # やる気アップ
    mood[0] = 1
    # スタミナ+12～13
    sta[0] = 12
    # 樫本理子の絆ゲージ+5

    ## ひとときの休息を（お出かけ2）
    # 体力+24～26
    vit[1] = 25
    # やる気アップ
    mood[1] = 1
    # スタミナ+12～13
    sta[1] = 12
    # 根性+12～13
    gut[1] = 12
    # 樫本理子の絆ゲージ+5

    ## 喜ぶ顔を思い浮かべて（お出かけ3）
    ### ここは『大容量ハチミルク』で！
    # 体力+24～26
    vit[2] = 25
    # やる気アップ
    mood[2] = 1
    # スタミナ+12～13
    sta[2] = 12
    # 根性+6
    gut[2] = 6
    # 樫本理子の絆ゲージ+5
    ### やはり『ウマスタ映えソーダ』で！
    # スキルpt+37～40
    # やる気アップ
    # 樫本理子の絆ゲージ+5

    ## 向けられる想いと戸惑い（お出かけ4）
    # 体力+24～26
    vit[3] = 25
    # やる気アップ
    mood[3] = 1
    # スピード+12～13
    spd[3] = 12
    # スタミナ+6
    sta[3] = 6
    # パワー+6
    pow[3] = 6
    # 樫本理子の絆ゲージ+5

    ## 胸の内を少しだけ（お出かけ5）
    ### 成功時：
    # 体力+30～32
    vit[4] = 31
    # やる気アップ
    mood[4] = 1
    # スタミナ+12～13
    sta[4] = 12
    # 根性+12～13
    gut[4] = 12
    # 『一陣の風』のヒントlv+3
    # 樫本理子の絆ゲージ+5
    ### 失敗時：
    # 体力+30～32
    # やる気アップ
    # スタミナ+6
    # 根性+6
    # 『一陣の風』のヒントlv+1
    # 樫本理子の絆ゲージ+5

    return "樫本理子", {
        "vit": vit,
        "mood": mood,
        "heal": heal,
        "spd": spd,
        "sta": sta,
        "pow": pow,
        "gut": gut,
        "wis": wis,
        "skill": skill,
    }


def generate_friend_for_light_halo() -> Tuple[str, dict]:
    vit = [0, 0, 0, 0, 0]
    mood = [0, 0, 0, 0, 0]
    heal = [0, 0, 0, 0, 0]
    spd = [0, 0, 0, 0, 0]
    sta = [0, 0, 0, 0, 0]
    pow = [0, 0, 0, 0, 0]
    gut = [0, 0, 0, 0, 0]
    wis = [0, 0, 0, 0, 0]
    skill = [0, 0, 0, 0, 0]

    # https://gamewith.jp/uma-musume/article/show/359859

    ## 嵐の大洋で、まどろみ（お出かけ1）
    # 体力最大値+4
    # 体力+25~40
    vit[0] = 25
    # やる気アップ
    mood[0] = 1
    # ライトハローの絆ゲージ+5

    ## ティコの輝き（お出かけ2）
    # 体力+25~40
    vit[1] = 25
    # やる気アップ
    mood[1] = 1
    # 根性+10~13
    gut[1] = 10
    # ライトハローの絆ゲージ+5

    ## レゴリスで隠して（お出かけ3）
    ### 恥ずかしくないですよ
    # 体力+50~80
    vit[2] = 50
    # やる気アップ
    mood[2] = 1
    # ライトハローの絆ゲージ+?
    ### わかりました！
    # やる気アップ
    # スピード+15~20
    # 根性+15~20
    # ライトハローの絆ゲージ+?

    ## ホイヘンス山、超えし君（お出かけ4）
    # 体力+30~48
    vit[3] = 30
    # やる気アップ
    mood[3] = 1
    # 根性+10~13
    gut[3] = 10
    # ライトハローの絆ゲージ+?

    ## 虹の入り江にて（お出かけ5）
    ### 大成功時：
    # 体力+30~48
    vit[4] = 30
    # やる気アップ
    mood[4] = 1
    # スピード+10~13
    spd[4] = 10
    # 根性+10~13
    gut[4] = 10
    # 『お先に失礼っ！』のヒントLv+3
    # ライトハローの絆ゲージ+5
    ### 成功時：
    # やる気アップ
    # 体力+20~32
    # スピード+5~6
    # 根性+5~6
    # 『お先に失礼っ！』のヒントLv+1
    # ライトハローの絆ゲージ+5

    return "ライトハロー", {
        "vit": vit,
        "mood": mood,
        "heal": heal,
        "spd": spd,
        "sta": sta,
        "pow": pow,
        "gut": gut,
        "wis": wis,
        "skill": skill,
    }


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        friend_dict = generate_friend_dict()
        for name in friend_dict.keys():
            auto_derby.config.single_mode_go_out_names.add(name)

        class Option(auto_derby.config.single_mode_go_out_option_class):
            def heal_rate(self, ctx: Context) -> float:
                if self.name not in friend_dict.keys():
                    return super().heal_rate(ctx)

                return friend_dict[self.name]["heal"][self.current_event_count]

            def mood_rate(self, ctx: Context) -> float:
                if self.name not in friend_dict.keys():
                    return super().mood_rate(ctx)

                return friend_dict[self.name]["mood"][self.current_event_count]

            def vitality(self, ctx: Context) -> float:
                if self.name not in friend_dict.keys():
                    return super().vitality(ctx)

                return (
                    friend_dict[self.name]["vit"][self.current_event_count]
                    / ctx.max_vitality
                )

            def score(self, ctx: Context) -> float:
                ret = super().score(ctx)
                if self.name not in friend_dict.keys():
                    return ret

                t = Training()
                c = self.current_event_count
                t.speed = friend_dict[self.name]["spd"][c]
                t.stamina = friend_dict[self.name]["sta"][c]
                t.power = friend_dict[self.name]["pow"][c]
                t.guts = friend_dict[self.name]["gut"][c]
                t.wisdom = friend_dict[self.name]["wis"][c]
                t.skill = friend_dict[self.name]["skill"][c]
                ret += t.score(ctx)

                return ret

        auto_derby.config.single_mode_go_out_option_class = Option

        class Training(auto_derby.config.single_mode_training_class):
            def score(self, ctx: Context) -> float:
                try:
                    next(i for i in self.partners if i.type == i.TYPE_FRIEND)
                except StopIteration:
                    return super().score(ctx)

                cleanup: List[Callable[[], None]] = []
                # assume lv 50 effect
                # https://github.com/NateScarlet/auto-derby/issues/160
                if getattr(self, "_use_estimate_vitality", False) and self.vitality < 0:
                    _orig_vit = self.vitality

                    def _c1():
                        self.vitality = _orig_vit

                    self.vitality *= 0.9

                    cleanup.append(_c1)

                # https://github.com/NateScarlet/auto-derby/issues/152
                if getattr(self, "_use_estimate_failure_rate", False):
                    _orig_failure = self.failure_rate

                    def _c2():
                        self.failure_rate = _orig_failure

                    self.failure_rate *= 0.7

                    cleanup.append(_c2)

                ret = super().score(ctx)
                for i in cleanup:
                    i()

                return ret

        auto_derby.config.single_mode_training_class = Training


auto_derby.plugin.register(__name__, Plugin())
