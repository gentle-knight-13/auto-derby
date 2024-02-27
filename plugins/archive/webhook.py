import auto_derby
import argparse
import cast_unknown as cast
import configparser
import os
import requests
import json
import jaconvV2
import types

from auto_derby import single_mode, app
from auto_derby.scenes import scene
from auto_derby.services.log import Level
from auto_derby.single_mode.commands.race import RaceResult
from auto_derby.single_mode.context import Context
from texttable import *
from typing import Dict, Generator, List, Text, Tuple, Type, TypeVar
from auto_derby.scenes import Scene
from auto_derby.scenes.scene import AbstractScene, Scene, SceneHolder, T
from abc import ABC, abstractmethod

custom_config_path = os.getenv(
    "AUTO_DERBY_PLUGIN_CONFIG_PATH", "data/plugin_config.ini"
)


class Webhook:
    sort = [
        "scene",
        "turn",
        "chara",
        "list",
    ]

    def __init__(self, url, last_msg_id) -> None:
        # Init variable
        self.url = url
        self.json = {
            "content": "Auto-derby started",
            "embeds": [],
        }
        self.current_order = []
        self._embeds = {}
        self._content = ""
        self.edit_count = 0

        # Remove unused message
        if last_msg_id:
            last_msg_req = requests.get(url=self.url + "/messages/" + last_msg_id)
            last_msg = json.loads(last_msg_req.text)
            if last_msg["content"] == "Auto-derby started":
                last_msg_req = requests.delete(url=self.url + "/messages/" + last_msg_id)

        # Execute webhook
        req = requests.post(url=self.url + "?wait=true", json=self.json)
        if req.status_code != 200:
            raise LookupError(
                "Please fill in a correct webhook URL in %s" % custom_config_path
            )
        response = json.loads(req.text)
        self.last_msg_id = response["id"]

    def update_discord_msg(self) -> None:
        """Edit Webhook Message with updated info"""
        self.edit_count += 1
        self.json["content"] = self._content + "\nEdited times: %d" % self.edit_count
        requests.patch(url=self.url + "/messages/" + self.last_msg_id, json=self.json)

    def update_content(self, value: Text) -> None:
        """Edit the internal value of content"""
        self._content = value

    def update_embed(self, name: Text, value: Dict) -> None:
        """Edit embeds with name markers
        Fields are overridden by values from update_embed_field()"""
        self._embed_check(name)
        self._update_embed(name, value)

    def _embed_check(self, name: Text) -> None:
        if name not in self.sort:
            app.log.text("Embed name is not expected, append at last", level=Level.WARN)
            self.sort.append(name)
        if name not in self._embeds:
            self._embeds[name] = {}

    def _update_embed(self, name: Text, value: Dict) -> None:
        if "fields" in value:
            app.log.text("Field in embed will be overridden", level=Level.WARN)
            del value["fields"]
        if len(self._embeds[name]) > 0:
            value["fields"] = list(self._embeds[name].values())
        if name not in self.current_order:
            self.current_order = [value for value in self.sort if value in self._embeds]
            self.json["embeds"].insert(self.current_order.index(name), value)
        else:
            self.json["embeds"][self.current_order.index(name)] = value

    def update_embed_field(
        self, embed_name: Text, field_name: Text, value: Dict
    ) -> None:
        """Edit fields in embeds with name markers"""
        self._embed_check(embed_name)
        self._embeds[embed_name][field_name] = value
        if embed_name not in self.current_order:
            self.current_order = [value for value in self.sort if value in self._embeds]
            order = self.current_order.index(embed_name)
            self.json["embeds"].insert(order, {})
        else:
            order = self.current_order.index(embed_name)
        self.json["embeds"][order]["fields"] = list(self._embeds[embed_name].values())

class WebhookJob(ABC):
    @abstractmethod
    def __init__(self, hook: Webhook) -> None:
        self._hook = hook
    @abstractmethod
    def recover(self, last_msg: Dict) -> bool:
        """Return True when Webhook reuse last message ID"""
        return False
    @abstractmethod
    def update(self) -> None:
        pass

class WebhookNurturing(WebhookJob):
    def __init__(self, hook: Webhook) -> None:
        super().__init__(hook=hook)

    def recover(self, last_msg: Dict) -> bool:
        return False

    def update(self) -> None:
        pass

class CustomTable(Texttable):
    def __init__(self, max_width=68, col=2, vertical=False):
        super().__init__(max_width)
        self.set_deco(Texttable.VLINES)
        self.set_cols_dtype(["a" for i in range(col)])
        self.set_cols_align(["c" for i in range(col)])
        if vertical:
            self.set_deco(Texttable.VLINES)
            self.set_chars([" ", "|", " ", " "])
            if col == 2:
                self.set_cols_align(["r", "l"])
        else:
            self.set_deco(Texttable.HLINES)
            self.set_chars([" ", " ", " ", " "])


def _date_to_text(ctx: single_mode.Context) -> Text:
    if ctx.date == (1, 0, 0):
        return "ジュニア級デビュー前"
    if ctx.date == (4, 0, 0):
        if ctx.scenario in (
            ctx.SCENARIO_URA,
            ctx.SCENARIO_AOHARU,
            ctx.SCENARIO_UNKNOWN,
        ):
            return "ファイナルズ開催中"
        if ctx.scenario in (ctx.SCENARIO_CLIMAX, ctx.SCENARIO_UNKNOWN):
            return "クライマックス開催中"
    year_dict = {1: "ジュニア級", 2: "クラシック級", 3: "シニア級"}
    return "%s %d月%s" % (
        year_dict[ctx.date[0]],
        ctx.date[1],
        {1: "前半", 2: "後半"}[ctx.date[2]],
    )


def _status_to_emoji(status: Tuple[int, Text]) -> Text:
    if status == Context.STATUS_NONE:
        return ":blue_square:"
    return ":regional_indicator_%s:" % status[1][0].lower()


def _mood_to_text(ctx: single_mode.Context) -> Text:
    if ctx.mood == ctx.MOOD_VERY_GOOD:
        return "絕好調"
    elif ctx.mood == ctx.MOOD_GOOD:
        return "好調"
    elif ctx.mood == ctx.MOOD_NORMAL:
        return "普通"
    elif ctx.mood == ctx.MOOD_BAD:
        return "不調"
    elif ctx.mood == ctx.MOOD_VERY_BAD:
        return "絕不調"
    return "UNKNOWN"


def _shorten_name(text: Text) -> Text:
    if len(text) > 8:
        return jaconvV2.z2h(text)
    return text


def _wh_msg(func):
    """Decorator for updating msg"""

    def update(*args, update_msg=True, **kwargs):
        ret = func(*args, **kwargs)
        if update_msg:
            WebhookPlugin.webhook.update_discord_msg()
        return ret

    return update


class Context(single_mode.Context):
    def __init__(self) -> None:
        self.race_results: List[List[str]] = []
        """Race results stored as turn, result, and race name"""
        super().__init__()

    @_wh_msg
    def _wh_update_race(self) -> None:
        """Update info about race history to webhook"""
        if len(self.race_turns) > 0:
            race_info = CustomTable(col=2, vertical=True)
            race_info.add_rows([["N", "Race"]])
            race_info.add_rows(self.race_results, header=False)
            WebhookPlugin.webhook.update_embed_field(
                "list",
                "race",
                {
                    "name": "比賽資訊",
                    "value": "```{}```".format(race_info.draw()),
                    "inline": True,
                },
            )

    @_wh_msg
    def _wh_update_turn(self) -> None:
        """Update info about turn to webhook"""
        turn_info_rows = [
            ["やる気", "ファン數"],
            [_mood_to_text(self), "%d人" % self.fan_count],
        ]
        if self.scenario == self.SCENARIO_CLIMAX:
            turn_info_rows[0].extend(["成績pt", "Sコイン"])
            turn_info_rows[1].extend(["%dpt" % self.grade_point, "%d" % self.shop_coin])
        turn_info = CustomTable(col=len(turn_info_rows[0]))
        turn_info.add_rows(turn_info_rows)
        WebhookPlugin.webhook.update_embed(
            "turn",
            {
                "title": "回合資訊",
                "description": "**ターン**\n{}\n```{}```".format(
                    _date_to_text(self), turn_info.draw()
                ),
            },
        )

    @_wh_msg
    def _wh_update_chara(self) -> None:
        """Update info about character to webhook"""
        chara_info = CustomTable(col=5)
        chara_info.add_rows(
            [
                ["スピード", "スタミナ", "パワー", "根性", "賢さ"],
                [self.speed, self.stamina, self.power, self.guts, self.wisdom],
            ]
        )
        WebhookPlugin.webhook.update_embed(
            "chara",
            {
                "title": "角色資訊",
                "description": "```{}```".format(chara_info.draw()),
            },
        )

    @_wh_msg
    def _wh_update_chara_status(self) -> None:
        WebhookPlugin.webhook.update_embed_field(
            "chara",
            "status",
            {
                "name": "適性",
                "value": "バ場適性 |　　芝　%s　ダート%s\n距離適性 |　短距離%s　マイル%s　中距離%s　長距離%s\n脚質適性 |　　逃げ%s　　先行%s　　差し%s　　追込%s"
                % tuple(
                    map(
                        lambda x: _status_to_emoji(x),
                        [
                            self.turf,
                            self.dart,
                            self.sprint,
                            self.mile,
                            self.intermediate,
                            self.long,
                            self.lead,
                            self.head,
                            self.middle,
                            self.last,
                        ],
                    )
                ),
            },
        )

    @_wh_msg
    def _wh_update_item(self) -> None:
        """Update info about item to webhook"""
        if self.items:
            item_info = CustomTable(col=2, vertical=True)
            item_info_rows = [["Item", "No"]]
            for item in self.items:
                item_info_rows.append([_shorten_name(item.name), "x%d" % item.quantity])
            item_info.add_rows(item_info_rows)
            WebhookPlugin.webhook.update_embed_field(
                "list",
                "item",
                {
                    "name": "物品資訊",
                    "value": "```{}```".format(item_info.draw()),
                    "inline": True,
                },
            )

    def _wh_update(self) -> None:
        self._wh_update_turn(update_msg=False)
        self._wh_update_chara(update_msg=False)
        self._wh_update_chara_status(update_msg=False)
        self._wh_update_item(update_msg=False)
        self._wh_update_race(update_msg=False)
        WebhookPlugin.webhook.update_content("**%s**" % self.scenario)
        WebhookPlugin.webhook.update_discord_msg()

    def next_turn(self) -> None:
        super().next_turn()
        WebhookPlugin.webhook.update_content("**%s**" % self.scenario)
        self._wh_update_item()

    def update_by_command_scene(self, *args, **kwargs) -> None:
        super().update_by_command_scene(*args, **kwargs)
        self._wh_update_turn()
        self._wh_update_chara()

    def update_by_class_detail(self, *args, **kwargs) -> None:
        super().update_by_class_detail(*args, **kwargs)
        self._wh_update_turn()

    def update_by_character_detail(self, *args, **kwargs) -> None:
        super().update_by_character_detail(*args, **kwargs)
        self._wh_update_chara_status()


class CustomConfigParser(configparser.ConfigParser):
    def getlist(self, section, option):
        value = self.get(section, option)
        return list(filter(None, (x.strip() for x in value.splitlines())))


class WebhookPlugin(auto_derby.Plugin):
    webhook: Webhook = None
    webhook_jobs: List[str] = ["nurturing"]
    """Jobs that supported with webhook"""

    def install(self) -> None:
        # Read job from program argument
        parser = argparse.ArgumentParser()
        parser.add_argument("job")
        args = parser.parse_args()

        # Read config
        config = CustomConfigParser()
        config.read_dict(
            {
                "webhook": {
                    "url": "https://discord.com/api/webhooks/id/token",
                    "last_msg_id": "",
                },
            }
        )
        config.read(custom_config_path)

        # Save config when default values are applied
        with open(custom_config_path, "w") as config_file:
            config.write(config_file)

        # Check if jobs are supported for webhook
        app.log.text("Job: %s" % args.job)
        if args.job in WebhookPlugin.webhook_jobs:
            WebhookPlugin.webhook = Webhook(config.get("webhook", "url"), config.get("webhook", "last_msg_id"))
            config["webhook"]["last_msg_id"] = WebhookPlugin.webhook.last_msg_id

        # Save config after retreive the msg ID
        with open(custom_config_path, "w") as config_file:
            config.write(config_file)

        # Add support for scene records
        def scene_subclass(scene: Type[T]) -> Type[T]:
            """Generator of subclasses of Scene"""
            for subclass in scene.__subclasses__():
                yield subclass
                yield from scene_subclass(subclass)
        enter_methods = {scene: scene.enter for scene in list(scene_subclass(Scene))}
        @classmethod
        def scene_enter(cls: Type[T], ctx: SceneHolder, *, _f=enter_methods) -> T:
            app.log.text("Entering scene %s from %s" % (cls.name(), ctx.scene.name()))
            return _f[cls](ctx)
        Scene.enter = scene_enter

        # Add support for race records
        auto_derby.config.single_mode_context_class = Context
        _next = auto_derby.config.on_single_mode_race_result

        def _handle(ctx: Context, result: RaceResult):
            ctx.race_results.append(
                ["%d" % result.order, _shorten_name(result.race.name)]
            )
            ctx._wh_update_race()
            _next(ctx, result)

        auto_derby.config.on_single_mode_race_result = _handle


auto_derby.plugin.register(__name__, WebhookPlugin())
