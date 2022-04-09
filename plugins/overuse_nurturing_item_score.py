from math import ceil
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
            "turn_limit" : 49, # senior 01 month second half
            "list" : ["にんじんBBQセット",],
        }

        pretty_item = {
            "turn_limit" : 49, # senior 01 month second half
            "list" : ["プリティーミラー",],
            "condition" : "愛嬌○"
        }

        speed_up_item = {
            "status_limit": 1140,
            "list" : [
                # "スピードトレーニング嘆願書",
                "スピード戦術書",
                "スピード秘伝書",
            ],
        }

        stamina_up_item = {
            "status_limit": 1140,
            "list" : [
                # "スタミナトレーニング嘆願書",
                "スタミナ戦術書",
                "スタミナ秘伝書",
            ],
        }

        power_up_item = {
            "status_limit": 1140,
            "list" : [
                "パワートレーニング嘆願書",
                "パワー戦術書",
                "パワー秘伝書",
            ],
        }

        guts_up_item = {
            "status_limit": 1140,
            "list" : [
                # "根性トレーニング嘆願書",
                "根性戦術書",
                "根性秘伝書",
            ],
        }

        wisdom_up_item = {
            "status_limit": 1140,
            "list" : [
                # "賢さトレーニング嘆願書",
                "賢さ戦術書",
                "賢さ秘伝書",
            ],
        }

        uncle_item = {
            "quantity": 4,
            "turn_limit" : 49, # senior 01 month second half
            "list" : [
                "スピードアンクルウェイト",
                # "スタミナアンクルウェイト",
                "パワーアンクルウェイト",
                # "根性アンクルウェイト",
            ],
        }

        speed_uncle_item = {
            "type" : TrainingType.SPEED,
            "list" : [
                "スピードアンクルウェイト",
            ],
        }

        stamina_uncle_item = {
            "type" : TrainingType.STAMINA,
            "list" : [
                "スタミナアンクルウェイト",
            ],
        }

        power_uncle_item = {
            "type" : TrainingType.POWER,
            "list" : [
                "パワーアンクルウェイト",
            ],
        }

        guts_uncle_item = {
            "type" : TrainingType.GUTS,
            "list" : [
                "根性アンクルウェイト",
            ],
        }

        sparta_megaphone_item = {
            "turn_limit" : 61, # senior 07 month first half
            "list" : [
                "スパルタメガホン",
            ],
        }

        camp_megaphone_item = {
            "turn_limit" : 64, # senior 08 month first half
            "list" : [
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

        mood_item = {
            "list" : [
                "プレーンカップケーキ",
                # "スイートカップケーキ",
            ]
        }

        debuff_recovery_item = {
            "quantity": 2,
            "list" : [
                # "すやすや安眠枕",
                # "練習改善DVD",
                # "アロマディフューザー",
                "うるおいハンドクリーム",
                # "ポケットスケジュール帳",
                # "ナンデモナオール",
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
                "スピードのメモ帳",
                "スタミナのメモ帳",
                "パワーのメモ帳",
                "根性のメモ帳",
                "賢さのメモ帳",
                "博学帽子",
                # "スピードトレーニング嘆願書",
                "スタミナトレーニング嘆願書",
                # "パワートレーニング嘆願書",
                "根性トレーニング嘆願書",
                "賢さトレーニング嘆願書",
                "スタミナアンクルウェイト",
                "根性アンクルウェイト",
                "チアメガホン",
                "三色ペンライト",
                "ロングエネドリンクMAX",
                # "ポケットスケジュール帳",
                # "アロマディフューザー",
                # "スリムスキャナー",
            ],
        }

        class Item(auto_derby.config.single_mode_item_class):
            def get_owned_item_quantity_by_name(self, ctx: Context, name: str):
                item_list = list(filter(lambda i : i.name == name, ctx.items))
                if item_list:
                    return item_list[0].quantity
                return 0

            def print_effect(self, ctx: Context, summary: EffectSummary):
                explain = "print effect:\n"
                explain += f"   turn:         {ctx.turn_count_v2()}\n"
                explain += f"   speed:        {summary.speed}\n"
                explain += f"   statmia:      {summary.statmia}\n"
                explain += f"   power:        {summary.power}\n"
                explain += f"   guts:         {summary.guts}\n"
                explain += f"   wisdom:       {summary.wisdom}\n"
                explain += f"   vitality:     {summary.vitality}\n"
                explain += f"   max_vitality: {summary.max_vitality}\n"
                explain += f"   mood:         {summary.mood}\n"
                explain += f"   training_partner_reassign: {summary.training_partner_reassign}\n"
                explain += f"   training_no_failure:       {summary.training_no_failure}\n"
                for key, value in summary.training_effect_buff.items():
                    explain += f"   training_effect_buff {key.name}:\t{value.total_rate()}\n"
                for key, value in summary.training_vitality_debuff.items():
                    explain += f"   training_vitality_debuff {key.name}::\t{value.total_rate()}\n"
                _LOGGER.info(explain)

            # high exchange score means high exchange priority
            def exchange_score(self, ctx: Context) -> float:
                ret = super().exchange_score(ctx)

                if (
                    self.name in bondup_item["list"]
                    and ctx.turn_count_v2() <= bondup_item["turn_limit"]
                ):
                    ret += 20

                condition_list = [condition.get(i).name for i in ctx.conditions]
                if (
                    self.name in pretty_item["list"]
                    and ctx.turn_count_v2() <= pretty_item["turn_limit"]
                    and pretty_item["condition"] not in condition_list
                ):
                    ret += 20
                elif (
                    self.name in pretty_item["list"]
                    and pretty_item["condition"] in condition_list
                ):
                    ret = 0

                if (
                    self.name in speed_up_item["list"]
                    and ctx.speed < speed_up_item["status_limit"]
                ):
                    ret += 20
                elif self.name in speed_up_item["list"]:
                    ret = 0

                if (
                    self.name in stamina_up_item["list"]
                    and ctx.stamina < stamina_up_item["status_limit"]
                ):
                    ret += 20
                elif self.name in stamina_up_item["list"]:
                    ret = 0

                if (
                    self.name in power_up_item["list"]
                    and ctx.power < power_up_item["status_limit"]
                ):
                    ret += 20
                elif self.name in power_up_item["list"]:
                    ret = 0

                if (
                    self.name in guts_up_item["list"]
                    and ctx.guts < guts_up_item["status_limit"]
                ):
                    ret += 20
                elif self.name in guts_up_item["list"]:
                    ret = 0

                if (
                    self.name in wisdom_up_item["list"]
                    and ctx.wisdom < wisdom_up_item["status_limit"]
                ):
                    ret += 20
                elif self.name in wisdom_up_item["list"]:
                    ret = 0

                if self.name in camp_megaphone_item["list"]:
                    ret += 20

                if (
                    self.name in sparta_megaphone_item["list"]
                    and ctx.turn_count_v2() <= sparta_megaphone_item["turn_limit"]
                ):
                    ret += 20
                elif self.name in sparta_megaphone_item["list"]:
                    ret = 0

                if (
                    self.name in uncle_item["list"]
                    and ctx.items.get(self.id).quantity < uncle_item["quantity"]
                    and ctx.turn_count_v2() <= uncle_item["turn_limit"]
                ):
                    ret += 20

                if self.name in amulet_item["list"]:
                    ret += 20

                if (
                    self.name in mood_item["list"]
                    and self.get_owned_item_quantity_by_name(ctx, "ロイヤルビタージュース") > ctx.items.get(self.id).quantity
                ):
                    ret += 20

                if (
                    self.name in hummer_item["list"]
                    and ctx.items.get(self.id).quantity < hummer_item["quantity"]
                ):
                    ret += 20
                elif (
                    self.name in hummer_item["list"]
                    and ctx.items.get(self.id).quantity >= hummer_item["quantity"]
                ):
                    ret = 0

                if (
                    self.name in debuff_recovery_item["list"]
                    and ctx.items.get(self.id).quantity < debuff_recovery_item["quantity"]
                ):
                    ret += 20
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

                # self.print_effect(ctx, summary)

                # Use amulet for high-efficiency training and low vitality.
                if (
                    isinstance(command, TrainingCommand)
                    and self.name in amulet_item["list"]
                    and ctx.items.get(self.id).quantity > 0
                    and command.training.failure_rate >= 0.20
                    and summary.vitality == 0
                    and (
                        command.training.speed > 25
                        or command.training.stamina > 25
                        or command.training.power > 25
                        or command.training.guts > 25
                        or command.training.wisdom > 25
                    )
                ):
                    ret += 20
                elif (
                    isinstance(command, TrainingCommand)
                    and self.name in amulet_item["list"]
                ):
                    ret = 0

                # Do not use recovery items when amulet are active
                if (
                    isinstance(command, TrainingCommand)
                    and self.name in vital_item["list"]
                    and summary.training_no_failure
                ):
                    ret = 0

                # Priority use of boot camp megaphone in summer camp
                if (
                    isinstance(command, TrainingCommand)
                    and self.name in camp_megaphone_item["list"]
                    and ctx.is_summer_camp
                    and len(summary.training_effect_buff) == 5
                    and not all([i.total_rate() >= 0.4 for i in summary.training_effect_buff.values()])
                ):
                    ret += 20
                elif (
                    isinstance(command, TrainingCommand)
                    and self.name in camp_megaphone_item["list"]
                    and ctx.items.get(self.id).quantity <= 2
                    and not ctx.is_summer_camp
                    and ctx.turn_count_v2() <= camp_megaphone_item["turn_limit"]
                ):
                    ret = 0

                # Use speed uncle
                if (
                    isinstance(command, TrainingCommand)
                    and self.name in speed_uncle_item["list"]
                    and command.training.type == speed_uncle_item["type"]
                    and command.training.speed > 25
                ):
                    ret += 20
                elif(
                    isinstance(command, TrainingCommand)
                    and self.name in speed_uncle_item["list"]
                ):
                    ret = 0

                # Use stamina uncle
                if (
                    isinstance(command, TrainingCommand)
                    and self.name in stamina_uncle_item["list"]
                    and command.training.type == stamina_uncle_item["type"]
                    and command.training.stamina > 25
                ):
                    ret += 20
                elif(
                    isinstance(command, TrainingCommand)
                    and self.name in stamina_uncle_item["list"]
                ):
                    ret = 0

                # Use power uncle
                if (
                    isinstance(command, TrainingCommand)
                    and self.name in power_uncle_item["list"]
                    and command.training.type == power_uncle_item["type"]
                    and command.training.power > 25
                ):
                    ret += 20
                elif(
                    isinstance(command, TrainingCommand)
                    and self.name in power_uncle_item["list"]
                ):
                    ret = 0

                # Use guts uncle
                if (
                    isinstance(command, TrainingCommand)
                    and self.name in guts_uncle_item["list"]
                    and command.training.type == guts_uncle_item["type"]
                    and command.training.guts > 25
                ):
                    ret += 20
                elif(
                    isinstance(command, TrainingCommand)
                    and self.name in guts_uncle_item["list"]
                ):
                    ret = 0

                # Use mood item
                if (
                    isinstance(command, TrainingCommand)
                    and self.name in mood_item["list"]
                    and summary.mood < 0
                    and summary.vitality == 100
                ):
                    ret += 20
                elif(
                    isinstance(command, RaceCommand)
                    and self.name in mood_item["list"]
                ):
                    ret = 0

                # No hammers are used in races other than the Twinkle Star Climax Race.
                if (
                    isinstance(command, RaceCommand)
                    and self.name in hummer_item["list"]
                    and ctx.date[0] == 4
                    and ctx.items.get(self.id).quantity > 0
                ):
                    ret += 20
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
