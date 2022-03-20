import auto_derby
from auto_derby.single_mode.commands import Command, RaceCommand
from auto_derby.single_mode import Context
from auto_derby.single_mode.item import EffectSummary


class Plugin(auto_derby.Plugin):
    # Note: If you have set a plugin that uses "auto_derby.config.single_mode_item_class" in addition to this plugin,
    #       it will be overwritten by the plugin of "auto_derby.config.single_mode_item_class" that is loaded later.
    #       So, please use by merging the plugins of "auto_derby.config.single_mode_item_class".

    def install(self) -> None:
        hummer_name = "蹄鉄ハンマー・極"
        hummer_purchase_limit = 3

        class Item(auto_derby.config.single_mode_item_class):
            # high exchange score means high exchange priority
            def exchange_score(self, ctx: Context) -> float:
                ret = super().exchange_score(ctx)

                if (
                    self.name == hummer_name
                    and ctx.items.get(self.id).quantity < hummer_purchase_limit
                ):
                    ret += 30
                elif (
                    self.name == hummer_name
                    and ctx.items.get(self.id).quantity >= hummer_purchase_limit
                ):
                    ret -= 50

                return ret

            # effect score will be added to command score.
            # all items that effect score greater than expected effect score
            # will be used before command execute.
            # also affect default exchange score.
            def effect_score(
                self, ctx: Context, command: Command, summary: EffectSummary
            ) -> float:
                ret = super().effect_score(ctx, command, summary)

                # No hammers are used in races other than the Twinkle Star Climax Race.
                if (
                    isinstance(command, RaceCommand)
                    and self.name == hummer_name
                    and ctx.date[0] == 4
                    and ctx.items.get(self.id).quantity > 0
                ):
                    ret += 30
                elif (
                    isinstance(command, RaceCommand)
                    and self.name == hummer_name
                    and ctx.items.get(self.id).quantity <= hummer_purchase_limit
                ):
                    ret -= 50

                return ret

        auto_derby.config.single_mode_item_class = Item


auto_derby.plugin.register(__name__, Plugin())
