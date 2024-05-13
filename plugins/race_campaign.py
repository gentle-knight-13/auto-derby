# -*- coding=UTF-8 -*-

import datetime
from abc import abstractmethod
from typing import List, Text

import auto_derby
from auto_derby import app, single_mode
from auto_derby.single_mode.context import Context
from auto_derby.single_mode.race import race_result
from auto_derby.single_mode.race.race import Race

JST = datetime.timezone(datetime.timedelta(hours=9), name="JST")


class Campaign:
    def __init__(
        self,
        start: datetime.datetime,
        end: datetime.datetime,
        race_name: Text,
    ) -> None:
        self.start = start
        self.end = end
        self.race_name = race_name
        super().__init__()

    @abstractmethod
    def match(self, ctx: Context, race: Race) -> bool:
        if race.name != self.race_name:
            return False
        now = datetime.datetime.now(JST)
        if not (self.start <= now <= self.end):
            return False
        return True


class OncePerDayCampaign(Campaign):
    def __init__(
        self,
        start: datetime.datetime,
        end: datetime.datetime,
        race_name: Text,
        *,
        order_lte: int = 999,
    ) -> None:
        super().__init__(
            start,
            end,
            race_name,
        )
        self.order_lte = order_lte

    def match(self, ctx: Context, race: Race) -> bool:
        if not super().match(ctx, race):
            return False
        for r in race_result.iterate():
            if (
                r.race.name == race.name
                and r.order <= self.order_lte
                and r.time.astimezone(JST).date() == datetime.datetime.now(JST).date()
            ):
                return False

        return True


class OneTimeCampaign(Campaign):
    def __init__(
        self,
        start: datetime.datetime,
        end: datetime.datetime,
        race_name: Text,
        *,
        order_lte: int = 999,
    ) -> None:
        super().__init__(
            start,
            end,
            race_name,
        )
        self.order_lte = order_lte

    def match(self, ctx: Context, race: Race) -> bool:
        if not super().match(ctx, race):
            return False
        for r in race_result.iterate():
            if (
                r.race.name == race.name
                and r.order <= self.order_lte
                and self.start < r.time.astimezone(JST) <= self.end
            ):
                return False

        return True


_CAMPAIGNS: List[Campaign] = []


def _add_campaign(
    c: Campaign,
) -> None:
    now = datetime.datetime.now(JST)
    # include tomorrow's campaign
    if not (c.start - datetime.timedelta(days=1) <= now <= c.end):
        return

    _CAMPAIGNS.append(c)


class Plugin(auto_derby.Plugin):
    """Pick race by campaign."""

    def install(self) -> None:
        if not _CAMPAIGNS:
            app.log.text("no race campaign today")
            return

        for i in _CAMPAIGNS:
            app.log.text("race campaign: %s~%s %s" % (i.start, i.end, i.race_name))

        class Race(auto_derby.config.single_mode_race_class):
            def score(self, ctx: single_mode.Context) -> float:
                ret = super().score(ctx)
                if ret < 0:
                    return ret
                if any(i.match(ctx, self) for i in _CAMPAIGNS):
                    ret += 100
                return ret

        auto_derby.config.single_mode_race_class = Race


auto_derby.plugin.register(__name__, Plugin())


# G1 記念ミッション
#   ジャパンダートダービー応援ミッション
_start = datetime.datetime(2023, 7, 6, 5, 0, tzinfo=JST)
_end = datetime.datetime(2023, 7, 13, 4, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "ジャパンダートダービー", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "関東オークス", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "ユニコーンステークス", order_lte=1))
#   「育成報酬」ピース追加キャンペーン
_start = datetime.datetime(2023, 7, 11, 5, 0, tzinfo=JST)
_end = datetime.datetime(2023, 7, 13, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "ジャパンダートダービー", order_lte=1))


# 秋の G1 記念ミッション
#   チャンピオンズカップ応援ミッション
_start = datetime.datetime(2023, 11, 26, 15, 0, tzinfo=JST)
_end = datetime.datetime(2023, 12, 3, 14, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "チャンピオンズカップ", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "みやこステークス", order_lte=3))
_add_campaign(OneTimeCampaign(_start, _end, "武蔵野ステークス", order_lte=3))
#   阪神ジュベナイルフィリーズ応援ミッション
_start = datetime.datetime(2023, 12, 3, 22, 0, tzinfo=JST)
_end = datetime.datetime(2023, 12, 10, 14, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "阪神ジュベナイルフィリーズ", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "ファンタジーステークス", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "アルテミスステークス", order_lte=1))
#   全日本ジュニア優駿応援ミッション
_start = datetime.datetime(2023, 12, 6, 15, 0, tzinfo=JST)
_end = datetime.datetime(2023, 12, 13, 14, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "全日本ジュニア優駿", order_lte=1))
#   朝日杯フューチュリティステークス応援ミッション
_start = datetime.datetime(2023, 12, 10, 15, 0, tzinfo=JST)
_end = datetime.datetime(2023, 12, 17, 14, 59, tzinfo=JST)
_add_campaign(
    OneTimeCampaign(_start, _end, "朝日杯フューチュリティステークス", order_lte=1)
)
_add_campaign(
    OneTimeCampaign(_start, _end, "デイリー杯ジュニアステークス", order_lte=1)
)
_add_campaign(OneTimeCampaign(_start, _end, "京王杯ジュニアステークス", order_lte=1))
#   ホープフルステークス応援ミッション
_start = datetime.datetime(2023, 12, 21, 15, 0, tzinfo=JST)
_end = datetime.datetime(2023, 12, 28, 14, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "ホープフルステークス", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "京都ジュニアステークス", order_lte=1))
_add_campaign(
    OneTimeCampaign(_start, _end, "東京スポーツ杯ジュニアステークス", order_lte=1)
)
#   東京大賞典応援ミッション
_start = datetime.datetime(2023, 12, 22, 15, 0, tzinfo=JST)
_end = datetime.datetime(2023, 12, 29, 14, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "東京大賞典", order_lte=1))

#   「育成報酬」ピース追加キャンペーン
_start = datetime.datetime(2023, 12, 23, 5, 0, tzinfo=JST)
_end = datetime.datetime(2023, 12, 25, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "有馬記念", order_lte=1))
_start = datetime.datetime(2023, 12, 27, 5, 0, tzinfo=JST)
_end = datetime.datetime(2023, 12, 29, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "ホープフルステークス", order_lte=1))
_start = datetime.datetime(2023, 12, 28, 5, 0, tzinfo=JST)
_end = datetime.datetime(2023, 12, 30, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "東京大賞典", order_lte=1))


# 春の G1 記念ミッション
# 第1弾
#   フェブラリーステークス応援ミッション
_start = datetime.datetime(2024, 2, 11, 22, 0, tzinfo=JST)
_end = datetime.datetime(2024, 2, 18, 14, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "東海ステークス", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "根岸ステークス", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "フェブラリーステークス", order_lte=1))
#   高松宮記念応援ミッション
_start = datetime.datetime(2024, 3, 17, 23, 0, tzinfo=JST)
_end = datetime.datetime(2024, 3, 24, 15, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "阪急杯", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "オーシャンステークス", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "高松宮記念", order_lte=1))
#   高松宮記念応援ミッション
_start = datetime.datetime(2024, 4, 7, 16, 0, tzinfo=JST)
_end = datetime.datetime(2024, 4, 14, 15, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "皐月賞", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "スプリングステークス", order_lte=3))
_add_campaign(OneTimeCampaign(_start, _end, "弥生賞", order_lte=3))
#   天皇賞春応援ミッション
_start = datetime.datetime(2024, 4, 21, 16, 0, tzinfo=JST)
_end = datetime.datetime(2024, 4, 28, 15, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "天皇賞春", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "阪神大賞典", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "日経賞", order_lte=1))

#   「育成報酬」ピース追加キャンペーン
_start = datetime.datetime(2024, 2, 17, 5, 0, tzinfo=JST)
_end = datetime.datetime(2024, 2, 19, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "フェブラリーステークス", order_lte=1))
_start = datetime.datetime(2024, 3, 23, 5, 0, tzinfo=JST)
_end = datetime.datetime(2024, 3, 25, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "高松宮記念", order_lte=1))
_start = datetime.datetime(2024, 3, 30, 5, 0, tzinfo=JST)
_end = datetime.datetime(2024, 4, 1, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "大阪杯", order_lte=1))
_start = datetime.datetime(2024, 4, 2, 5, 0, tzinfo=JST)
_end = datetime.datetime(2024, 4, 4, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "川崎記念", order_lte=1))
_start = datetime.datetime(2024, 4, 6, 5, 0, tzinfo=JST)
_end = datetime.datetime(2024, 4, 8, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "桜花賞", order_lte=1))
_start = datetime.datetime(2024, 4, 13, 5, 0, tzinfo=JST)
_end = datetime.datetime(2024, 4, 15, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "皐月賞", order_lte=1))
_start = datetime.datetime(2024, 4, 27, 5, 0, tzinfo=JST)
_end = datetime.datetime(2024, 4, 29, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "天皇賞春", order_lte=1))
# 第2弾
#   かしわ記念応援ミッション
_start = datetime.datetime(2024, 4, 24, 23, 0, tzinfo=JST)
_end = datetime.datetime(2024, 5, 1, 15, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "かしわ記念", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "東京スプリント", order_lte=2))
#   NHKマイルカップ応援ミッション
_start = datetime.datetime(2024, 4, 28, 16, 0, tzinfo=JST)
_end = datetime.datetime(2024, 5, 5, 15, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "NHKマイルカップ", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "ニュージーランドトロフィー", order_lte=3))
_add_campaign(OneTimeCampaign(_start, _end, "アーリントンカップ", order_lte=3))
#   ヴィクトリアマイル応援ミッション
_start = datetime.datetime(2024, 5, 5, 16, 0, tzinfo=JST)
_end = datetime.datetime(2024, 5, 12, 15, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "ヴィクトリアマイル", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "阪神ウマ娘ステークス", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "福島ウマ娘ステークス", order_lte=1))
#   オークス応援ミッション
_start = datetime.datetime(2024, 5, 12, 16, 0, tzinfo=JST)
_end = datetime.datetime(2024, 5, 19, 15, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "オークス", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "フローラステークス", order_lte=2))
_add_campaign(OneTimeCampaign(_start, _end, "桜花賞", order_lte=5))
#   日本ダービー応援ミッション
_start = datetime.datetime(2023, 5, 22, 4, 0, tzinfo=JST)
_end = datetime.datetime(2023, 5, 29, 3, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "日本ダービー", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "京都新聞杯", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "皐月賞", order_lte=5))
_add_campaign(OneTimeCampaign(_start, _end, "青葉賞", order_lte=2))
#   安田記念応援ミッション
_start = datetime.datetime(2023, 5, 29, 4, 0, tzinfo=JST)
_end = datetime.datetime(2023, 6, 5, 3, 59, tzinfo=JST)
_add_campaign(OneTimeCampaign(_start, _end, "安田記念", order_lte=1))
_add_campaign(OneTimeCampaign(_start, _end, "マイラーズカップ", order_lte=3))
_add_campaign(OneTimeCampaign(_start, _end, "京王杯スプリングカップ", order_lte=3))
#   宝塚記念応援ミッション
_start = datetime.datetime(2023, 6, 19, 4, 0, tzinfo=JST)
_end = datetime.datetime(2023, 6, 26, 3, 59, tzinfo=JST)

#   「育成報酬」ピース追加キャンペーン
_start = datetime.datetime(2024, 4, 30, 5, 0, tzinfo=JST)
_end = datetime.datetime(2024, 5, 2, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "かしわ記念", order_lte=1))
_start = datetime.datetime(2024, 5, 4, 5, 0, tzinfo=JST)
_end = datetime.datetime(2024, 5, 6, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "NHKマイルカップ", order_lte=1))
_start = datetime.datetime(2024, 5, 11, 5, 0, tzinfo=JST)
_end = datetime.datetime(2024, 5, 13, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "ヴィクトリアマイル", order_lte=1))
_start = datetime.datetime(2024, 5, 18, 5, 0, tzinfo=JST)
_end = datetime.datetime(2024, 5, 20, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "オークス", order_lte=1))
_start = datetime.datetime(2024, 5, 25, 5, 0, tzinfo=JST)
_end = datetime.datetime(2024, 5, 27, 4, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "日本ダービー", order_lte=1))
_start = datetime.datetime(2023, 6, 3, 4, 0, tzinfo=JST)
_end = datetime.datetime(2023, 6, 5, 3, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "安田記念", order_lte=1))
_start = datetime.datetime(2023, 6, 24, 4, 0, tzinfo=JST)
_end = datetime.datetime(2023, 6, 26, 3, 59, tzinfo=JST)
_add_campaign(OncePerDayCampaign(_start, _end, "宝塚記念", order_lte=1))
