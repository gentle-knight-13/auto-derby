from typing import List, Set

import auto_derby
from auto_derby.constants import TrainingType
from auto_derby.single_mode.commands import Command, TrainingCommand, RaceCommand
from auto_derby.single_mode import Context, condition
from auto_derby.single_mode.item import EffectSummary
from auto_derby.single_mode.item.item import Item
from auto_derby.single_mode.item.effect_summary import BuffList

import logging

_LOGGER = logging.getLogger(__name__)


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        item_score_list = ExpansionItemScoreFactory.create()

        class Item(auto_derby.config.single_mode_item_class):
            def print_effect(self, summary: EffectSummary):
                explain = f"print effect:\n"
                explain += f"- speed:        {summary.speed}\n"
                explain += f"- statmia:      {summary.statmia}\n"
                explain += f"- power:        {summary.power}\n"
                explain += f"- guts:         {summary.guts}\n"
                explain += f"- wisdom:       {summary.wisdom}\n"
                explain += f"- vitality:     {summary.vitality}\n"
                explain += f"- max_vitality: {summary.max_vitality}\n"
                explain += f"- mood:         {summary.mood}\n"
                explain += f"- condition add:{summary.condition_add}\n"
                explain += f"- use whistle:  {summary.training_partner_reassign}\n"
                explain += f"- use amulet:   {summary.training_no_failure}\n"
                for key, value in summary.training_effect_buff.items():
                    explain += f"- training buff {key.name}: {value.total_rate()}\n"
                    for buff in value:
                        explain += (
                            f"  - buff: rate {buff.rate}, turn {buff.turn_count}\n"
                        )
                for key, value in summary.training_vitality_debuff.items():
                    explain += f"- training debuff {key.name}: {value.total_rate()}\n"
                    for buff in value:
                        explain += (
                            f"  - buff: rate {buff.rate}, turn {buff.turn_count}\n"
                        )
                    explain += f"- race buff: {summary.race_reward_buff.total_rate()}\n"
                    for buff in summary.race_reward_buff:
                        explain += (
                            f"  - buff: rate {buff.rate}, turn {buff.turn_count}\n"
                        )
                _LOGGER.info(explain)

            # high exchange score means high exchange priority
            def exchange_score(self, ctx: Context) -> float:
                ret = super().exchange_score(ctx)

                for i in item_score_list:
                    ret = i.exchange_score(ret, self, ctx)
                # _LOGGER.info(f"exchange item score:\n item: {self.name}, score: {ret}")

                return ret

            # effect score will be added to command score.
            # all items that effect score greater than expected effect score
            # will be used before command execute.
            # also affect default exchange score.
            def effect_score(
                self, ctx: Context, command: Command, summary: EffectSummary
            ) -> float:
                ret = super().effect_score(ctx, command, summary)

                # _LOGGER.info(f"print context:\n{ctx}")
                # self.print_effect(summary)
                for i in item_score_list:
                    ret = i.effect_score(ret, self, ctx, command, summary)
                # _LOGGER.info(f"effect item score:\n item: {self.name}, score: {ret}")

                return ret

            def should_use_directly(self, ctx: Context) -> bool:
                for i in item_score_list:
                    if self.name in i.item_names and i.use_directly:
                        # _LOGGER.info(f"use directly item:\n item: {self.name}")
                        return True

                return super().should_use_directly(ctx)

        auto_derby.config.single_mode_item_class = Item


auto_derby.plugin.register(__name__, Plugin())


_MAX_SCENARIO_TURN = 78
_MAX_QUANTITY = 5
_DEFAULT_SCORE = 20
_STATUS_THRESHOLD = 1130
_TRAINING_THRESHOLD = 25
_TRAINING_FAILURE_THRESHOLD = 0.20
_MAX_TRAINING_LEVEL = 5


def _get_owned_item_quantity_by_name(ctx: Context, name: str) -> int:
    return next((i for i in ctx.items if i.name == name), Item()).quantity


class ExpansionItemScore:
    def __init__(
        self,
        item_names: Set[str],
        quantity: int = _MAX_QUANTITY,
        turn: int = _MAX_SCENARIO_TURN,
        score: int = _DEFAULT_SCORE,
        use_directly: bool = False,
    ) -> None:
        self.item_names = item_names
        self.quantity = quantity
        self.turn = turn
        self.score = score
        self.use_directly = use_directly

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        return base_score

    def effect_score(
        self,
        base_score: int,
        item: Item,
        ctx: Context,
        command: Command,
        summary: EffectSummary,
    ) -> int:
        return base_score


class ExpansionItemScoreFactory:
    @classmethod
    def create(cls) -> List[ExpansionItemScore]:
        return [
            FriendshipUpItemScore(),
            CharmItemScore(),
            SharpItemScore(),
            SpeedUpItemScore(),
            StaminaUpItemScore(),
            PowerUpItemScore(),
            GutsUpItemScore(),
            WisdomUpItemScore(),
            SpeedTrainingLevelUpItemScore(),
            StaminaTrainingLevelUpItemScore(),
            PowerTrainingLevelUpItemScore(),
            GutsTrainingLevelUpItemScore(),
            WisdomTrainingLevelUpItemScore(),
            SpeedAnkleItemScore(),
            StaminaAnkleItemScore(),
            PowerAnkleItemScore(),
            GutsAnkleItemScore(),
            SpartaMegaphoneItemScore(),
            BootCampMegaphoneItemScore(),
            AmuletItemScore(),
            VitalItemScore(),
            MoodItemScore(),
            DebuffRecoveryItemScore(),
            KiwamiHummerItemScore(),
            TakumiHummerItemScore(),
            IgnoreItemScore(),
        ]


class FriendshipUpItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "にんじんBBQセット",
            },
            turn=49,  # senior 01 month first half
            score=30,
            use_directly=True,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if ctx.turn_count_v2() <= self.turn:
            return base_score + self.score
        return 0


class CharmItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "プリティーミラー",
            },
            quantity=1,
            turn=49,  # senior 01 month first half
            score=10,
            use_directly=True,
        )
        self.condition = "愛嬌○"

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score

        conditions = [condition.get(i).name for i in ctx.conditions]
        if (
            ctx.turn_count_v2() <= self.turn
            and self.condition not in conditions
            and ctx.items.get(item.id).quantity < self.quantity
        ):
            return base_score + self.score
        return 0


class SharpItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "博学帽子",
            },
            quantity=1,
            score=10,
            use_directly=True,
        )
        self.condition = "切れ者"

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score

        conditions = [condition.get(i).name for i in ctx.conditions]
        if (
            ctx.turn_count_v2() < self.turn
            and self.condition not in conditions
            and ctx.items.get(item.id).quantity < self.quantity
        ):
            return base_score + self.score
        return 0


class SpeedUpItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "スピード戦術書",
                "スピード秘伝書",
            },
            score=10,
            use_directly=True,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if ctx.speed < _STATUS_THRESHOLD:
            return base_score + self.score
        return 0


class StaminaUpItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "スタミナ戦術書",
                "スタミナ秘伝書",
            },
            score=10,
            use_directly=True,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if ctx.stamina < _STATUS_THRESHOLD:
            return base_score + self.score
        return 0


class PowerUpItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "パワー戦術書",
                "パワー秘伝書",
            },
            score=10,
            use_directly=True,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if ctx.power < _STATUS_THRESHOLD:
            return base_score + self.score
        return 0


class GutsUpItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "根性戦術書",
                "根性秘伝書",
            },
            score=10,
            use_directly=True,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if ctx.guts < _STATUS_THRESHOLD:
            return base_score + self.score
        return 0


class WisdomUpItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "賢さ戦術書",
                "賢さ秘伝書",
            },
            score=10,
            use_directly=True,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if ctx.wisdom < _STATUS_THRESHOLD:
            return base_score + self.score
        return 0


class SpeedTrainingLevelUpItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "スピードトレーニング嘆願書",
            },
            score=20,
            use_directly=True,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if (
            ctx.speed < _STATUS_THRESHOLD
            and ctx.training_levels[TrainingType.SPEED] < _MAX_TRAINING_LEVEL
        ):
            return base_score + self.score
        return 0


class StaminaTrainingLevelUpItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "スタミナトレーニング嘆願書",
            },
            score=20,
            use_directly=True,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if (
            ctx.stamina < _STATUS_THRESHOLD
            and ctx.training_levels[TrainingType.STAMINA] < _MAX_TRAINING_LEVEL
        ):
            return base_score + self.score
        return 0


class PowerTrainingLevelUpItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "パワートレーニング嘆願書",
            },
            score=20,
            use_directly=True,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if (
            ctx.power < _STATUS_THRESHOLD
            and ctx.training_levels[TrainingType.POWER] < _MAX_TRAINING_LEVEL
        ):
            return base_score + self.score
        return 0


class GutsTrainingLevelUpItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "根性トレーニング嘆願書",
            },
            score=20,
            use_directly=True,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if (
            ctx.guts < _STATUS_THRESHOLD
            and ctx.training_levels[TrainingType.GUTS] < _MAX_TRAINING_LEVEL
        ):
            return base_score + self.score
        return 0


class WisdomTrainingLevelUpItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "賢さトレーニング嘆願書",
            },
            score=20,
            use_directly=True,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if (
            ctx.wisdom < _STATUS_THRESHOLD
            and ctx.training_levels[TrainingType.WISDOM] < _MAX_TRAINING_LEVEL
        ):
            return base_score + self.score
        return 0


class SpeedAnkleItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "スピードアンクルウェイト",
            },
            quantity=5,
            score=20,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if ctx.items.get(item.id).quantity < self.quantity:
            return base_score + self.score
        return 0

    def effect_score(
        self,
        base_score: int,
        item: Item,
        ctx: Context,
        command: Command,
        summary: EffectSummary,
    ) -> int:
        if item.name not in self.item_names or not isinstance(command, TrainingCommand):
            return base_score

        if (
            command.training.type == TrainingType.SPEED
            and _TRAINING_THRESHOLD < command.training.speed
        ):
            buff_list = next(
                (
                    v
                    for k, v in summary.training_effect_buff.items()
                    if k == TrainingType.SPEED
                ),
                BuffList(),
            )
            if all([i.rate != 0.5 for i in buff_list]):
                return base_score + self.score
        return 0


class StaminaAnkleItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "スタミナアンクルウェイト",
            },
            quantity=3,
            score=20,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if ctx.items.get(item.id).quantity < self.quantity:
            return base_score + self.score
        return 0

    def effect_score(
        self,
        base_score: int,
        item: Item,
        ctx: Context,
        command: Command,
        summary: EffectSummary,
    ) -> int:
        if item.name not in self.item_names or not isinstance(command, TrainingCommand):
            return base_score
        if (
            command.training.type == TrainingType.STAMINA
            and _TRAINING_THRESHOLD < command.training.stamina
        ):
            buff_list = next(
                (
                    v
                    for k, v in summary.training_effect_buff.items()
                    if k == TrainingType.STAMINA
                ),
                BuffList(),
            )
            if all([i.rate != 0.5 for i in buff_list]):
                return base_score + self.score
        return 0


class PowerAnkleItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "パワーアンクルウェイト",
            },
            quantity=3,
            score=20,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if ctx.items.get(item.id).quantity < self.quantity:
            return base_score + self.score
        return 0

    def effect_score(
        self,
        base_score: int,
        item: Item,
        ctx: Context,
        command: Command,
        summary: EffectSummary,
    ) -> int:
        if item.name not in self.item_names or not isinstance(command, TrainingCommand):
            return base_score
        if (
            command.training.type == TrainingType.POWER
            and _TRAINING_THRESHOLD < command.training.power
        ):
            buff_list = next(
                (
                    v
                    for k, v in summary.training_effect_buff.items()
                    if k == TrainingType.POWER
                ),
                BuffList(),
            )
            if all([i.rate != 0.5 for i in buff_list]):
                return base_score + self.score
        return 0


class GutsAnkleItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "根性アンクルウェイト",
            },
            quantity=3,
            score=20,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if ctx.items.get(item.id).quantity < self.quantity:
            return base_score + self.score
        return 0

    def effect_score(
        self,
        base_score: int,
        item: Item,
        ctx: Context,
        command: Command,
        summary: EffectSummary,
    ) -> int:
        if item.name not in self.item_names or not isinstance(command, TrainingCommand):
            return base_score
        if (
            command.training.type == TrainingType.GUTS
            and _TRAINING_THRESHOLD < command.training.guts
        ):
            buff_list = next(
                (
                    v
                    for k, v in summary.training_effect_buff.items()
                    if k == TrainingType.GUTS
                ),
                BuffList(),
            )
            if all([i.rate != 0.5 for i in buff_list]):
                return base_score + self.score
        return 0


class SpartaMegaphoneItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "スパルタメガホン",
            },
            score=30,
            turn=61,  # senior 07 month first half
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if ctx.turn_count_v2() <= self.turn:
            return base_score + self.score
        return base_score

    def effect_score(
        self,
        base_score: int,
        item: Item,
        ctx: Context,
        command: Command,
        summary: EffectSummary,
    ) -> int:
        if item.name not in self.item_names or not isinstance(command, TrainingCommand):
            return base_score
        if len(summary.training_effect_buff) < 5:
            return base_score
        return 0


class BootCampMegaphoneItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "ブートキャンプメガホン",
            },
            score=30,
            turn=64,  # senior 08 month second half
        )
        self.min_quantity = 2

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if ctx.turn_count_v2() <= self.turn:
            return base_score + self.score
        return base_score

    def effect_score(
        self,
        base_score: int,
        item: Item,
        ctx: Context,
        command: Command,
        summary: EffectSummary,
    ) -> int:
        if item.name not in self.item_names or not isinstance(command, TrainingCommand):
            return base_score
        if ctx.is_summer_camp and len(summary.training_effect_buff) < 5:
            return base_score + self.score
        elif (
            self.min_quantity < ctx.items.get(item.id).quantity
            or self.turn < ctx.turn_count_v2()
        ):
            return base_score
        return 0


class AmuletItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "健康祈願のお守り",
            },
            score=30,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        return base_score + self.score

    def effect_score(
        self,
        base_score: int,
        item: Item,
        ctx: Context,
        command: Command,
        summary: EffectSummary,
    ) -> int:
        if item.name not in self.item_names or not isinstance(command, TrainingCommand):
            return base_score
        if (
            _TRAINING_FAILURE_THRESHOLD <= command.training.failure_rate
            and summary.vitality == 0
            and not summary.training_no_failure
            and (
                _TRAINING_THRESHOLD < command.training.speed
                or _TRAINING_THRESHOLD < command.training.stamina
                or _TRAINING_THRESHOLD < command.training.power
                or _TRAINING_THRESHOLD < command.training.guts
                or _TRAINING_THRESHOLD < command.training.wisdom
            )
        ):
            return base_score + self.score
        return 0


class VitalItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "バイタル20",
                "バイタル40",
                "バイタル65",
                "ロイヤルビタージュース",
                "エネドリンクMAX",
            },
            score=0,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        return base_score + self.score

    def effect_score(
        self,
        base_score: int,
        item: Item,
        ctx: Context,
        command: Command,
        summary: EffectSummary,
    ) -> int:
        if (
            item.name not in self.item_names
            or not isinstance(command, TrainingCommand)
            or not summary.training_no_failure
        ):
            return base_score
        return 0


class MoodItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "プレーンカップケーキ",
                "スイートカップケーキ",
            },
            score=20,
        )
        self.extra_quantity = 2
        self.bitter_juice_vitality = 100

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score

        max_quantity = (
            _get_owned_item_quantity_by_name(ctx, "ロイヤルビタージュース") + self.extra_quantity
        )
        plane_cake_quantity = _get_owned_item_quantity_by_name(ctx, "プレーンカップケーキ")
        sweet_cake_quantity = _get_owned_item_quantity_by_name(ctx, "スイートカップケーキ")
        total_cake_quantity = plane_cake_quantity + sweet_cake_quantity

        if total_cake_quantity < max_quantity and total_cake_quantity < self.quantity:
            return base_score + self.score

        return base_score

    def effect_score(
        self,
        base_score: int,
        item: Item,
        ctx: Context,
        command: Command,
        summary: EffectSummary,
    ) -> int:
        if item.name not in self.item_names or not isinstance(command, TrainingCommand):
            return base_score

        bitter_juice_quantity = _get_owned_item_quantity_by_name(ctx, "ロイヤルビタージュース")
        is_mood_down = summary.mood < 0
        if is_mood_down and summary.vitality == self.bitter_juice_vitality:
            return base_score + self.score
        elif (
            ctx.mood != ctx.MOOD_VERY_GOOD
            and bitter_juice_quantity < ctx.items.get(item.id).quantity
        ):
            return base_score + self.score
        return 0


class DebuffRecoveryItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                # "すやすや安眠枕",
                # "練習改善DVD",
                # "アロマディフューザー",
                "うるおいハンドクリーム",
                # "ポケットスケジュール帳",
                # "ナンデモナオール",
            },
            quantity=2,
            score=10,
            turn=49,  # senior 01 month second half
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if (
            ctx.turn_count_v2() <= self.turn
            and ctx.items.get(item.id).quantity < self.quantity
        ):
            return base_score + self.score
        return 0


class KiwamiHummerItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "蹄鉄ハンマー・極",
            },
            quantity=5,
            score=20,
            turn=72,  # ura qualifying first half
        )
        self.year = 4
        self.min_quantity = 3

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if (
            ctx.turn_count_v2() < self.turn
            and ctx.items.get(item.id).quantity < self.quantity
        ):
            return base_score + self.score
        return 0

    def effect_score(
        self,
        base_score: int,
        item: Item,
        ctx: Context,
        command: Command,
        summary: EffectSummary,
    ) -> int:
        if item.name not in self.item_names or not isinstance(command, RaceCommand):
            return base_score

        year = ctx.date[0]
        if year == self.year and summary.race_reward_buff.total_rate() == 0.0:
            return base_score + self.score
        elif (
            command.race.grade == command.race.GRADE_G1
            and self.min_quantity < ctx.items.get(item.id).quantity
            and summary.race_reward_buff.total_rate() == 0.0
        ):
            return base_score + self.score
        return 0


class TakumiHummerItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "蹄鉄ハンマー・匠",
            },
            quantity=5,
            score=10,
            turn=72,  # ura qualifying first half
        )
        self.year = 4

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        if (
            ctx.turn_count_v2() < self.turn
            and ctx.items.get(item.id).quantity < self.quantity
        ):
            return base_score + self.score
        return 0

    def effect_score(
        self,
        base_score: int,
        item: Item,
        ctx: Context,
        command: Command,
        summary: EffectSummary,
    ) -> int:
        if item.name not in self.item_names or not isinstance(command, RaceCommand):
            return base_score

        year = ctx.date[0]
        if year == self.year and summary.race_reward_buff.total_rate() == 0.0:
            return base_score + self.score
        elif (
            command.race.grade == command.race.GRADE_G1
            and summary.race_reward_buff.total_rate() == 0.0
        ):
            return base_score + self.score
        return 0


class IgnoreItemScore(ExpansionItemScore):
    def __init__(self) -> None:
        super().__init__(
            item_names={
                "スピードのメモ帳",
                "スタミナのメモ帳",
                "パワーのメモ帳",
                "根性のメモ帳",
                "賢さのメモ帳",
                "スピード戦術書",
                # "スタミナ戦術書",
                # "パワー戦術書",
                # "根性戦術書",
                # "賢さ戦術書",
                "スピード秘伝書",
                # "スタミナ秘伝書",
                # "パワー秘伝書",
                # "根性秘伝書",
                # "賢さ秘伝書",
                # "バイタル20",
                # "バイタル40",
                # "バイタル65",
                # "ロイヤルビタージュース",
                "エネドリンクMAX",
                "ロングエネドリンクMAX",
                # "プレーンカップケーキ",
                # "スイートカップケーキ",
                "おいしい猫缶",
                # "にんじんBBQセット",
                # "プリティーミラー",
                "名物記者の双眼鏡",
                "効率練習のススメ",
                # "博学帽子",
                # "すやすや安眠枕",
                # "ポケットスケジュール帳",
                # "うるおいハンドクリーム",
                # "スリムスキャナー",
                # "アロマディフューザー",
                # "練習改善DVD",
                # "ナンデモナオール",
                # "スピードトレーニング嘆願書",
                "スタミナトレーニング嘆願書",
                # "パワートレーニング嘆願書",
                "根性トレーニング嘆願書",
                "賢さトレーニング嘆願書",
                "リセットホイッスル",
                "チアメガホン",
                # "スパルタメガホン",
                # "ブートキャンプメガホン",
                # "スピードアンクルウェイト",
                "スタミナアンクルウェイト",
                # "パワーアンクルウェイト",
                "根性アンクルウェイト",
                # "健康祈願のお守り",
                # "蹄鉄ハンマー・匠",
                # "蹄鉄ハンマー・極",
                "三色ペンライト",
            },
            quantity=0,
            turn=0,
        )

    def exchange_score(self, base_score: int, item: Item, ctx: Context) -> int:
        if item.name not in self.item_names:
            return base_score
        return 0
