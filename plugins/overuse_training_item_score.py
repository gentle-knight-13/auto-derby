import auto_derby
from auto_derby.constants import TrainingType
from auto_derby.single_mode.commands import Command, TrainingCommand, RaceCommand
from auto_derby.single_mode import Context, condition
from auto_derby.single_mode.item import EffectSummary

import logging

_LOGGER = logging.getLogger(__name__)

class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        bondup_item = {
            "turn_limit" : 49, # senior  01 month second half
            "list" : ["にんじんBBQセット",],
        }

        pretty_item = {
            "turn_limit" : 49, # senior  01 month second half
            "list" : ["プリティーミラー",],
            "condition" : "愛嬌○"
        }

        speed_up_item = {
            "status_limit": 1120,
            "list" : [
                # "スピードトレーニング嘆願書",
                "スピード戦術書",
                "スピード秘伝書",
            ],
        }

        stamina_up_item = {
            "status_limit": 1120,
            "list" : [
                # "スタミナトレーニング嘆願書",
                "スタミナ戦術書",
                "スタミナ秘伝書",
            ],
        }

        power_up_item = {
            "status_limit": 1120,
            "list" : [
                "パワートレーニング嘆願書",
                "パワー戦術書",
                "パワー秘伝書",
            ],
        }

        guts_up_item = {
            "status_limit": 1120,
            "list" : [
                # "根性トレーニング嘆願書",
                "根性戦術書",
                "根性秘伝書",
            ],
        }

        wisdom_up_item = {
            "status_limit": 1120,
            "list" : [
                # "賢さトレーニング嘆願書",
                "賢さ戦術書",
                "賢さ秘伝書",
            ],
        }

        megaphone_item = {
            "list" : [
                "スパルタメガホン",
                "ブートキャンプメガホン",
            ],
        }

        amulet_item = {
            "list" : [
                "健康祈願のお守り",
            ],
        }

        vital_item = {
            "list" : [
                "バイタル20",
                "バイタル40",
                "バイタル65",
                "ロイヤルビタージュース",
                "エネドリンクMAX",
            ],
        }

        debuff_recovery_item = {
            "quantity": 1,
            "list" : [
                "すやすや安眠枕",
                "練習改善DVD",
                "アロマディフューザー",
                "うるおいハンドクリーム",
                "ナンデモナオール",
            ],
        }

        hummer_item = {
            "quantity": 3,
            "list" : [
                "蹄鉄ハンマー・極",
            ],
        }

        ignore_item = {
            "list" : [
                "根性トレーニング嘆願書",
                "根性アンクルウェイト",
                "チアメガホン",
                "三色ペンライト",
                "ロングエネドリンクMAX",
                "ポケットスケジュール帳",
                "アロマディフューザー",
                "スリムスキャナー",
            ],
        }

        class Item(auto_derby.config.single_mode_item_class):
            # high exchange score means high exchange priority
            def exchange_score(self, ctx: Context) -> float:
                ret = super().exchange_score(ctx)

                if (
                    self.name in bondup_item["list"]
                    and ctx.turn_count_v2() <= bondup_item["turn_limit"]
                ):
                    ret += 30

                condition_list = [condition.get(i).name for i in ctx.conditions]
                if (
                    self.name in pretty_item["list"]
                    and ctx.turn_count_v2() <= pretty_item["turn_limit"]
                    and pretty_item["condition"] not in condition_list
                ):
                    ret += 30
                elif (
                    self.name in pretty_item["list"]
                    and pretty_item["condition"] in condition_list
                ):
                    ret = 0

                if (
                    self.name in speed_up_item["list"]
                    and ctx.speed < speed_up_item["status_limit"]
                ):
                    ret += 30
                elif self.name in speed_up_item["list"]:
                    ret = 0

                if (
                    self.name in stamina_up_item["list"]
                    and ctx.stamina < stamina_up_item["status_limit"]
                ):
                    ret += 30
                elif self.name in stamina_up_item["list"]:
                    ret = 0

                if (
                    self.name in power_up_item["list"]
                    and ctx.power < power_up_item["status_limit"]
                ):
                    ret += 30
                elif self.name in power_up_item["list"]:
                    ret = 0

                if (
                    self.name in guts_up_item["list"]
                    and ctx.guts < guts_up_item["status_limit"]
                ):
                    ret += 30
                elif self.name in guts_up_item["list"]:
                    ret = 0

                if (
                    self.name in wisdom_up_item["list"]
                    and ctx.wisdom < wisdom_up_item["status_limit"]
                ):
                    ret += 30
                elif self.name in wisdom_up_item["list"]:
                    ret = 0

                if self.name in megaphone_item["list"]:
                    ret += 30

                if self.name in amulet_item["list"]:
                    ret += 30

                if (
                    self.name in hummer_item["list"]
                    and ctx.items.get(self.id).quantity < hummer_item["quantity"]
                ):
                    ret += 30
                elif (
                    self.name in hummer_item["list"]
                    and ctx.items.get(self.id).quantity >= hummer_item["quantity"]
                ):
                    ret = 0

                if (
                    self.name in debuff_recovery_item["list"]
                    and ctx.items.get(self.id).quantity < debuff_recovery_item["quantity"]
                ):
                    ret += 30
                elif (
                    self.name in debuff_recovery_item["list"]
                    and ctx.items.get(self.id).quantity >= debuff_recovery_item["quantity"]
                ):
                    ret = 0

                if self.name in ignore_item["list"]:
                    ret = 0

                return ret

            # effect score will be added to command score.
            # all items that effect score greater than expected effect score
            # will be used before command execute.
            # also affect default exchange score.
            def effect_score(
                self, ctx: Context, command: Command, summary: EffectSummary
            ) -> float:
                ret = super().effect_score(ctx, command, summary)

                _LOGGER.info(
                    "custom effect score: turn %d, quantity %d, name %s",
                    ctx.turn_count_v2(),
                    ctx.items.get(self.id).quantity,
                    self.name
                )

                # Use amulet for high-efficiency training and low vitality.
                if (
                    isinstance(command, TrainingCommand)
                    and self.name in amulet_item["list"]
                    and ctx.items.get(self.id).quantity > 0
                    and command.training.failure_rate >= 0.20
                    and (
                        command.training.speed > 20
                        or command.training.stamina > 20
                        or command.training.power > 20
                        or command.training.guts > 20
                        or command.training.wisdom > 20
                    )
                ):
                    _LOGGER.info(
                        "use amulet: turn %d, quantity %d, failure rate %f, score %d, name %s",
                        ctx.turn_count_v2(),
                        ctx.items.get(self.id).quantity,
                        command.training.failure_rate,
                        ret,
                        self.name
                    )
                    ret += 100

                if (
                    self.name in vital_item["list"]
                    and summary.training_no_failure
                ):
                    _LOGGER.info(
                        "unused vital: turn %d, name %s",
                        ctx.turn_count_v2(),
                        self.name
                    )
                    ret = 0

                # No hammers are used in races other than the Twinkle Star Climax Race.
                if (
                    isinstance(command, RaceCommand)
                    and self.name in hummer_item["list"]
                    and ctx.date[0] == 4
                    and ctx.items.get(self.id).quantity > 0
                ):
                    ret += 30
                elif (
                    isinstance(command, RaceCommand)
                    and self.name in hummer_item["list"]
                    and ctx.items.get(self.id).quantity <= 3
                ):
                    ret = 0

                return ret

            def should_use_directly(self, ctx: Context) -> bool:
                if self.name in bondup_item["list"]:
                    return True
                if self.name in pretty_item["list"]:
                    return True
                if (
                    self.name in speed_up_item["list"]
                    or self.name in stamina_up_item["list"]
                    or self.name in power_up_item["list"]
                    or self.name in guts_up_item["list"]
                    or self.name in wisdom_up_item["list"]
                ):
                    return True

                return super().should_use_directly(ctx)

        auto_derby.config.single_mode_item_class = Item


auto_derby.plugin.register(__name__, Plugin())
