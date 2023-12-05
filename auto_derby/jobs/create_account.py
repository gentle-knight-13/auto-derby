# -*- coding=UTF-8 -*-
# pyright: strict

import base64
import email
import imaplib
from selenium import webdriver
import re
from imap_tools import MailBox, AND
import io
import os
import time
from typing import Any, Dict, List, Text, Union
from selenium.webdriver.common.by import By
from PIL import Image
import requests
import numpy as np

from auto_derby import app, clients, imagetools, template
from random_username.generate import generate_username


# from auto_derby import template

from .. import action, templates, terminal


class tmple:
    LAUNCH_SCREEN_CRIWARE = "launch_screen_criware.png"
    LAUNCH_SCREEN_MENU_BUTTON = "launch_screen_menu_button.png"
    LAUNCH_SCREEN_GOOGLE_PLAY = "launch_screen_google_play.png"
    LAUNCH_SCREEN_LINK_ACCOUNT = "launch_screen_link_account.png"
    LAUNCH_SCREEN_LINK_LATER = "launch_screen_link_later.png"
    LIVE_MENU_BUTTON = "launch_screen_menu_button.png"
    SKIP_BUTTON = template.Specification("skip_button_custom.png", threshold=0.8)
    LIVE_SKIP_BUTTON = "live_skip_button.png"
    ZHHANT_AGREEMENT = "zhhant_agreement.png"
    HOME_GIFT_BUTTON = "home_gift_button.png"
    HOME_BUTTON_NOT_FOCUS = "home_button_not_focus.png"
    GACHA_BUTTON = "gacha_button.png"
    STORY_BUTTON = "story_button.png"
    STRENGTHEN_BUTTON = "strengthen_button.png"
    GACHA_FREE = "gacha_free.png"
    GACHA_ONCE = "gacha_once.png"
    GACHA_PRETTY_DERBY = "gacha_pretty_derby.png"
    GACHA_SUPPORT_CARD = "gacha_support_card.png"
    GACHA_TEN_TIMES = "gacha_ten_times.png"
    HOME_MENU_DIRECTORY_BUTTON = "home_menu_directory_button.png"
    HOME_MENU_SUPPORT_BUTTON = "home_menu_support_button.png"
    GO_TO_GACHA = "go_to_gacha.png"
    COLLECT_ALL_REWARD = "collect_all_reward.png"
    TUTORIAL_SKIP_BUTTON = "tutorial_skip_button.png"
    TRAINER_NAME_LABEL = "trainer_name_label.png"
    GACHA_SSR_ONLY = "gacha_ssr_only.png"
    GACHA_SSR_ONLY_TICKET = "gacha_ssr_only_ticket.png"
    GACHA_AGAIN_BUTTON = "gacha_again_button.png"
    GACHA_CARD_NEW = "gacha_card_new.png"
    GACHA_CARD_R = "gacha_card_r.png"
    GACHA_CARD_SR = "gacha_card_sr.png"
    GACHA_CARD_SSR = "gacha_card_ssr.png"
    GACHA_NOT_ENOUGH_GEM = "gacha_not_enough_gem.png"
    STRENGTHEN_CARD_BUTTON = "strengthen_card_button.png"
    STRENGTHEN_DERBY_BUTTON = "strengthen_derby_button.png"
    STRENGTHEN_DERBY_OVERVIEW_BUTTON = "strengthen_derby_overview_button.png"
    STRENGTHEN_CARD_OVERVIEW_BUTTON = "strengthen_card_overview_button.png"
    STRENGTHEN_CARD_BREAK_LIMIT_BUTTON = "strengthen_card_break_limit_button.png"
    STRENGTHEN_DERBY_OVERVIEW_STAR = "strengthen_derby_overview_star.png"
    BREAK_LIMIT_BUTTON = "break_limit_button.png"
    OVERVIEW_CARD_SR = "overview_card_sr.png"
    OVERVIEW_CARD_SSR = "overview_card_ssr.png"
    STRENGTHEN_DERBY_OVERVIEW_BREAK = "strengthen_derby_overview_break.png"
    HOME_MENU_BUTTON = "home_menu_button.png"
    HOME_MENU_USER_CENTER = "home_menu_user_center.png"
    HOME_MENU_LOGOUT_BUTTON = "home_menu_logout_button.png"
    KOMOE_ACCOUNT_LOGIN_BUTTON = "komoe_account_login_button.png"
    KOMOE_ACCOUNT_SIGNUP_BUTTON = "komoe_account_signup_button.png"
    KOMOE_ACCOUNT_SIGNUP_NEXT_BUTTON = "komoe_account_signup_next_button.png"
    KOMOE_ACCOUNT_SIGNUP_TITLE = "komoe_account_signup_title.png"
    KOMOE_ACCOUNT_SIGNUP_CONFIRM = "komoe_account_signup_confirm.png"
    STRENGTHEN_CARD_PIECE = "strengthen_card_piece.png"
    CLOSE_BUTTON = template.Specification(templates.CLOSE_BUTTON, threshold=0.8)
    LARGE_RETURN_BUTTON = "large_return_button.png"


class Task:
    def __init__(self) -> None:
        self.signup = True
        self.get_gift = True
        self.get_reward = True
        self.gacha_support_card = True
        self.gacha_pretty_derby = False
        self.view_pretty_derby = True
        self.exit_view_pretty_derby = False
        self.limit_break_support_card = True
        self.view_support_card = True
        self.logout = False

        self.result_img: List[Image.Image] = []

    def add_img(self, img: Image.Image) -> None:
        self.result_img.insert(0, img)

    def to_img(self):
        images = self.result_img
        if len(images) == 0:
            raise ValueError("Need 0 or more images")

        if isinstance(images[0], np.ndarray):
            images = [Image.fromarray(img) for img in images]
        width = max([img.size[0] for img in images])
        height = sum([img.size[1] for img in images])
        stacked = Image.new(images[0].mode, (width, height))

        y_pos = 0
        for img in images:
            stacked.paste(img, (0, y_pos))
            y_pos += img.size[1]
        return stacked


class TmplList:
    def __init__(
        self,
        *tmpl: Union[Text, template.Specification],
    ) -> None:
        self._list: List[template.Specification] = []
        self.extend(*tmpl)

    def append(self, tmpl: Union[Text, template.Specification]) -> None:
        if not isinstance(tmpl, template.Specification):
            tmpl = template.Specification(tmpl)
        self._list.append(tmpl)

    def extend(self, *tmpl: Union[Text, template.Specification]) -> None:
        for t in tmpl:
            self.append(t)

    def to_list(self) -> List[template.Specification]:
        return self._list


SERVER = "imap.gmail.com"
USER = "smallkumc@gmail.com"
PASSWORD = "yvdoaxesbwfbeboa"


def create_account():
    rp = action.resize_proxy()

    username = os.getenv("AUTO_DERBY_USERNAME")
    if not username:
        username_list: List[Text] = generate_username()
        username = username_list[0]
        os.environ["AUTO_DERBY_USERNAME"] = username
    print(username)

    task = Task()

    driver = webdriver.Firefox()
    driver.implicitly_wait(time_to_wait=10)
    driver.get("about:blank")
    app.log.text("WebDriver started")

    card_img = None
    derby_img = None
    overview_img = None
    ssr_count = 0
    c = clients.current()
    gacha_occurrence: Dict[Text, int] = {
        tmple.GACHA_PRETTY_DERBY: 0,
        tmple.GACHA_SUPPORT_CARD: 0,
    }

    while True:
        time.sleep(0.3)
        task.logout = not task.view_pretty_derby and not task.view_support_card
        tmpls = TmplList(
            templates.CONNECTING,
            # tmple.LIVE_SKIP_BUTTON,
            # tmple.LAUNCH_SCREEN_GOOGLE_PLAY,
            # tmple.LAUNCH_SCREEN_LINK_LATER,
            # tmple.HOME_MENU_SUPPORT_BUTTON,
        )
        if not task.logout:
            tmpls.append(templates.CLOSE_BUTTON)
        tmpls.extend(
            tmple.GACHA_SSR_ONLY_TICKET,
            tmple.GACHA_FREE,
            tmple.GO_TO_GACHA,
        )
        if task.signup:
            tmpls.extend(
                tmple.LAUNCH_SCREEN_CRIWARE,
                tmple.ZHHANT_AGREEMENT,
                tmple.TUTORIAL_SKIP_BUTTON,
                tmple.KOMOE_ACCOUNT_LOGIN_BUTTON,
            )
        if task.get_gift or task.get_reward:
            tmpls.append(templates.HOME_BUTTON)
            # tmpls.append(tmple.HOME_GIFT_BUTTON)
            # tmpls.append(tmple.COLLECT_ALL_REWARD)
            # tmpls.append(templates.RETURN_BUTTON)
        if task.gacha_support_card or task.gacha_pretty_derby:
            tmpls.extend(
                tmple.GACHA_TEN_TIMES,
                tmple.GACHA_NOT_ENOUGH_GEM,
                tmple.STORY_BUTTON,
            )
        if (
            task.view_pretty_derby
            or task.limit_break_support_card
            or task.view_support_card
        ):
            tmpls.append(tmple.STRENGTHEN_BUTTON)
        if task.view_pretty_derby:
            tmpls.append(tmple.STRENGTHEN_DERBY_BUTTON)
            tmpls.append(tmple.STRENGTHEN_DERBY_OVERVIEW_BREAK)
            tmpls.append(tmple.STRENGTHEN_DERBY_OVERVIEW_BUTTON)
        if task.exit_view_pretty_derby:
            tmpls.extend(
                tmple.STORY_BUTTON,
            )
        if task.limit_break_support_card or task.view_support_card:
            tmpls.append(templates.RETURN_BUTTON)
            tmpls.append(tmple.STRENGTHEN_CARD_BUTTON)
        if task.limit_break_support_card:
            tmpls.append(tmple.STRENGTHEN_CARD_BREAK_LIMIT_BUTTON)
        if task.view_support_card:
            tmpls.append(tmple.STRENGTHEN_CARD_OVERVIEW_BUTTON)
        if task.logout:
            tmpls.append(tmple.HOME_MENU_BUTTON)
            tmpls.append(tmple.HOME_MENU_SUPPORT_BUTTON)
            tmpls.append(tmple.HOME_MENU_USER_CENTER)
            tmpls.append(tmple.HOME_MENU_LOGOUT_BUTTON)
        tmpls.extend(
            tmple.GACHA_AGAIN_BUTTON,
            templates.HOME_BUTTON,
            templates.GREEN_OK_BUTTON,
            # templates.SKIP_BUTTON,
            tmple.SKIP_BUTTON,
            templates.CANCEL_BUTTON,
            tmple.LARGE_RETURN_BUTTON,
        )
        tmpl_list: List[template.Specification] = tmpls.to_list()
        tmpl, pos = action.wait_image(*tmpl_list)
        name = tmpl.name
        if name == templates.CONNECTING:
            time.sleep(1)
        elif name == templates.CHAMPIONS_MEETING_ENTRY_BUTTON_DISABLED:
            exit(0)
        elif name == tmple.LAUNCH_SCREEN_GOOGLE_PLAY:
            action.wait_tap_image(templates.CANCEL_BUTTON)
        elif name == templates.HOME_BUTTON:
            app.log.text("Start process")
            while True:  # tutorial
                _tmpl, _pos = action.wait_image(
                    tmple.CLOSE_BUTTON, tmple.HOME_GIFT_BUTTON
                )
                if _tmpl.name == tmple.HOME_GIFT_BUTTON:
                    break
                action.tap(_pos)

            # Get gift first
            action.wait_tap_image(tmple.HOME_GIFT_BUTTON)
            tmpl, pos = action.wait_image_stable(
                tmple.SKIP_BUTTON, tmple.CLOSE_BUTTON, duration=0.4
            )
            if tmpl.name == tmple.SKIP_BUTTON:
                action.tap(pos)
                action.wait_image_stable(tmple.CLOSE_BUTTON)
            tmpl, pos = action.wait_image_stable(
                tmple.COLLECT_ALL_REWARD, tmple.CLOSE_BUTTON
            )
            if tmpl.name == tmple.COLLECT_ALL_REWARD:
                action.tap(pos)
                action.wait_tap_image(tmple.CLOSE_BUTTON)
                time.sleep(2)
            action.wait_tap_image(tmple.CLOSE_BUTTON)
            task.get_gift = False
            # Get task rewards
            tmpl, pos = action.wait_image(tmple.HOME_GIFT_BUTTON)
            pos = (pos[0], pos[1] - rp.vector(45, 540))
            action.tap(pos)
            time.sleep(10)
            while True:
                tmpl, pos = action.wait_image(
                    tmple.SKIP_BUTTON, templates.RETURN_BUTTON
                )
                if tmpl.name == templates.RETURN_BUTTON:
                    break
                action.tap(pos)
            tmpl, pos = action.wait_image_stable(
                tmple.COLLECT_ALL_REWARD, templates.RETURN_BUTTON
            )
            if tmpl.name == tmple.COLLECT_ALL_REWARD:
                action.tap(pos)
                action.wait_tap_image(tmple.CLOSE_BUTTON)
                time.sleep(2)
            action.tap(rp.vector2((335, 610), 900))
            time.sleep(0.5)
            tmpl, pos = action.wait_image_stable(
                tmple.COLLECT_ALL_REWARD, templates.RETURN_BUTTON
            )
            if tmpl.name == tmple.COLLECT_ALL_REWARD:
                action.tap(pos)
                action.wait_tap_image(tmple.CLOSE_BUTTON)
            task.get_reward = False
            # action.wait_tap_image(templates.RETURN_BUTTON)
            action.wait_tap_image(tmple.GACHA_BUTTON)

            # occurrence: Dict[Text, int] = {
            #     tmple.GACHA_PRETTY_DERBY: 0,
            #     tmple.GACHA_SUPPORT_CARD: 0,
            #     tmple.GACHA_SSR_ONLY_TICKET: 0,
            # }

            # support_card_gacha = True
            # pretty_derby_gacha = False
            # ssr_count = 0

            # while True:
            #     tmpl, pos = action.wait_image(
            #         tmple.GACHA_FREE,
            #         tmple.GACHA_SSR_ONLY,
            #         tmple.GACHA_PRETTY_DERBY,
            #         tmple.GACHA_SUPPORT_CARD,
            #         tmple.STORY_BUTTON,
            #     )
            #     if tmpl.name in occurrence:
            #         occurrence[tmpl.name] += 1
            #         if sum(occurrence.values()) > len(occurrence):
            #             break
            #     if tmpl.name == tmple.GACHA_FREE:
            #         action.tap(pos)
            #         action.wait_tap_image(tmple.GO_TO_GACHA)
            #         action.wait_tap_image(tmple.SKIP_BUTTON)
            #         while True:
            #             _tmpl, _pos = action.wait_image(
            #                 templates.GREEN_OK_BUTTON, tmple.SKIP_BUTTON
            #             )
            #             action.tap(_pos)
            #             if _tmpl.name == templates.GREEN_OK_BUTTON:
            #                 break
            #         tmpl, pos = action.wait_image(
            #             tmple.CLOSE_BUTTON,
            #             tmple.STORY_BUTTON,
            #         )
            #         if tmpl.name == tmple.CLOSE_BUTTON:
            #             action.tap(pos)
            #     elif tmpl.name == tmple.GACHA_SUPPORT_CARD:
            #         if ssr_count > 2:
            #             pretty_derby_gacha = True
            #             support_card_gacha = False
            #             occurrence[tmple.GACHA_PRETTY_DERBY] = 0
            #             time.sleep(0.2)
            #             action.tap(rp.vector2((510, 580), 540))
            #             continue
            #         action.wait_tap_image(tmple.GACHA_TEN_TIMES)
            #         while support_card_gacha:
            #             tmpl, pos = action.wait_image(
            #                 tmple.GO_TO_GACHA, tmple.GACHA_NOT_ENOUGH_GEM
            #             )
            #             if tmpl.name == tmple.GO_TO_GACHA:
            #                 action.tap(pos)
            #             else:
            #                 action.wait_tap_image(templates.CANCEL_BUTTON)
            #                 tmpl, pos = action.wait_image(
            #                     tmple.GACHA_TEN_TIMES, tmple.GACHA_AGAIN_BUTTON
            #                 )
            #                 if tmpl.name == tmple.GACHA_AGAIN_BUTTON:
            #                     action.tap((pos[0] - rp.vector(200, 540), pos[1]))
            #                 time.sleep(0.2)
            #                 action.tap(rp.vector2((510, 580), 540))
            #                 break
            #             time.sleep(2)
            #             while True:
            #                 _tmpl, _pos = action.wait_image(
            #                     tmple.GACHA_AGAIN_BUTTON, tmple.SKIP_BUTTON
            #                 )
            #                 if _tmpl.name == tmple.GACHA_AGAIN_BUTTON:
            #                     break
            #                 action.tap(_pos)

            #     elif tmpl.name == tmple.GACHA_PRETTY_DERBY:
            #         if pretty_derby_gacha:
            #             action.wait_tap_image(tmple.GACHA_TEN_TIMES)
            #             while pretty_derby_gacha:
            #                 tmpl, pos = action.wait_image(
            #                     tmple.GO_TO_GACHA, tmple.GACHA_NOT_ENOUGH_GEM
            #                 )
            #                 if tmpl.name == tmple.GO_TO_GACHA:
            #                     action.tap(pos)
            #                 else:
            #                     action.wait_tap_image(templates.CANCEL_BUTTON)
            #                     tmpl, pos = action.wait_image(
            #                         tmple.GACHA_TEN_TIMES, tmple.GACHA_AGAIN_BUTTON
            #                     )
            #                     if tmpl.name == tmple.GACHA_AGAIN_BUTTON:
            #                         action.tap((pos[0] - rp.vector(200, 540), pos[1]))
            #                     time.sleep(0.2)
            #                     action.tap(rp.vector2((510, 580), 540))
            #                     break
            #                 time.sleep(2)
            #                 while True:
            #                     _tmpl, _pos = action.wait_image(
            #                         tmple.GACHA_AGAIN_BUTTON, tmple.SKIP_BUTTON
            #                     )
            #                     if _tmpl.name == tmple.GACHA_AGAIN_BUTTON:
            #                         template.screenshot().save(
            #                             "debug.gacha/gacha/%s.png" % time.time()
            #                         )
            #                         break
            #                     action.tap(_pos)

            #                 # terminal.prompt(
            #                 #     "Check derbys/ New: %d / R: %d SR: %d SSR: %d"
            #                 #     % (0, 0, 0, 0)
            #                 # )
            #                 action.wait_tap_image(tmple.GACHA_AGAIN_BUTTON)
            #             while True:
            #                 _tmpl, _pos = action.wait_image(
            #                     tmple.CLOSE_BUTTON, tmple.STORY_BUTTON
            #                 )
            #                 if _tmpl.name == tmple.STORY_BUTTON:
            #                     break
            #                 action.tap(_pos)
            #             time.sleep(0.2)
            #             action.tap(rp.vector2((510, 580), 540))
            #         else:
            #             action.tap(rp.vector2((510, 580), 540))
            #     else:
            #         action.tap(rp.vector2((510, 580), 540))

        elif name == tmple.GACHA_NOT_ENOUGH_GEM:
            app.log.text("GACHA_NOT_ENOUGH_GEM")
            try:
                if next(template.match(app.device.screenshot(), tmple.GO_TO_GACHA)):
                    continue
            except StopIteration:
                pass
            if task.gacha_support_card:
                task.gacha_support_card = False
                task.gacha_pretty_derby = True
            elif task.gacha_pretty_derby:
                task.gacha_pretty_derby = False
            action.wait_tap_image(templates.CANCEL_BUTTON)
            tmpl, pos = action.wait_image(
                tmple.GACHA_TEN_TIMES, tmple.GACHA_AGAIN_BUTTON
            )
            if tmpl.name == tmple.GACHA_AGAIN_BUTTON:
                app.device.tap(
                    (
                        pos[0] - rp.vector(220, 540),
                        pos[1] + rp.vector(10, 540),
                        pos[0] - rp.vector(180, 540),
                        pos[1] - rp.vector(10, 540),
                    )
                )  # (pos[0] - rp.vector(200, 540), pos[1])
            time.sleep(0.2)
            app.device.tap(rp.vector4((500, 570, 520, 590), 540))  # (510, 580)

        elif name == tmple.GACHA_TEN_TIMES or tmpl.name == tmple.GACHA_FREE:
            app.log.text("GACHA_TEN_TIMES")
            _tmpl, _ = action.wait_image(
                tmple.GACHA_SUPPORT_CARD,
                tmple.GACHA_PRETTY_DERBY,
            )
            if tmpl.name in gacha_occurrence:
                gacha_occurrence[_tmpl.name] += 1
                if sum(gacha_occurrence.values()) > len(gacha_occurrence):
                    task.gacha_support_card = False
                    task.gacha_pretty_derby = False
            if (
                tmpl.name == tmple.GACHA_FREE
                or (_tmpl.name == tmple.GACHA_SUPPORT_CARD and task.gacha_support_card)
                or (_tmpl.name == tmple.GACHA_PRETTY_DERBY and task.gacha_pretty_derby)
            ):
                action.tap(pos)
            else:
                action.tap(rp.vector2((510, 580), 540))
        elif name == tmple.GACHA_AGAIN_BUTTON and task.gacha_support_card:
            app.log.text("GACHA_AGAIN_BUTTON")
            card_count = 0
            r_card = []
            sr_card = []
            ssr_card = []
            # new_card = []
            for _ in range(50):
                r_card = list(template.match(template.screenshot(), tmple.GACHA_CARD_R))
                sr_card = list(
                    template.match(template.screenshot(), tmple.GACHA_CARD_SR)
                )
                ssr_card = list(
                    template.match(template.screenshot(), tmple.GACHA_CARD_SSR)
                )
                # new_card = list(
                #     template.match(
                #         template.screenshot(), tmple.GACHA_CARD_NEW
                #     )
                # )
                card_count = len(r_card) + len(sr_card) + len(ssr_card)
                if card_count == 10:
                    ssr_count += len(ssr_card)
                    break
            template.screenshot().save("debug.gacha/gacha/%s.png" % time.time())
            # terminal.prompt(
            #     "Check cards/ New: %d / R: %d SR: %d SSR: %d"
            #     % (len(new_card), len(r_card), len(sr_card), len(ssr_card))
            # )
            if ssr_count > 2:
                task.gacha_pretty_derby = True
                task.gacha_support_card = False
                gacha_occurrence[tmple.GACHA_PRETTY_DERBY] = 0
                tmpl, pos = action.wait_image(tmple.GACHA_AGAIN_BUTTON)
                action.tap((pos[0] - rp.vector(200, 540), pos[1]))
                time.sleep(0.2)
                action.tap(rp.vector2((510, 580), 540))
            else:
                action.wait_tap_image(tmple.GACHA_AGAIN_BUTTON)
        elif name == tmple.STORY_BUTTON and (
            task.gacha_support_card or task.gacha_pretty_derby
        ):
            app.log.text("STORY_BUTTON")
            action.tap(rp.vector2((510, 580), 540))
        elif name == tmple.GACHA_SSR_ONLY_TICKET:
            app.log.text("GACHA_SSR_ONLY_TICKET")
            ssr_count += 1
            action.tap(pos)

        elif name == tmple.LAUNCH_SCREEN_CRIWARE:
            app.log.text("LAUNCH_SCREEN_CRIWARE")
            x, y = pos
            y -= rp.vector(60, 540)
            action.tap((x, y))
        elif (
            name == tmple.STRENGTHEN_DERBY_OVERVIEW_BREAK
            or name == templates.RETURN_BUTTON
        ) and task.view_pretty_derby:
            if name == templates.RETURN_BUTTON:
                try:
                    _, pos = next(
                        template.match(
                            template.screenshot(), tmple.STRENGTHEN_DERBY_OVERVIEW_BREAK
                        )
                    )
                except StopIteration:
                    continue
            app.log.text("STRENGTHEN_DERBY_OVERVIEW_BREAK")
            # _, break_pos = action.wait_image(tmple.STRENGTHEN_DERBY_OVERVIEW_BREAK)
            derby_img = template.screenshot()
            derby_img = derby_img.crop(
                (
                    0,
                    rp.vector(70, 540),
                    c.width - 1,
                    pos[1] - rp.vector(5, 540),
                )
            )
            task.add_img(derby_img)
            # imagetools.show(derby_img)
            # action.wait_tap_image(tmple.STORY_BUTTON)
            task.view_pretty_derby = False
            task.exit_view_pretty_derby = True

        elif name == tmple.STORY_BUTTON and task.exit_view_pretty_derby:
            app.log.text("STORY_BUTTON EXIT")
            action.tap((pos[0] + rp.vector(55, 540), pos[1]))
            task.exit_view_pretty_derby = False

        elif name == templates.RETURN_BUTTON and task.limit_break_support_card:
            app.log.text("RETURN_BUTTON BREAK")
            # Only first 2 rows
            cards_pos_x = [70, 170, 270, 370, 470]
            cards_pos_y = [550, 690]

            # while True:  # tutorial
            #     _tmpl, _pos = action.wait_image(
            #         tmple.CLOSE_BUTTON, templates.RETURN_BUTTON
            #     )
            #     if _tmpl.name == templates.RETURN_BUTTON:
            #         break
            #     action.tap(_pos)
            # _, pos = action.wait_image(templates.RETURN_BUTTON)
            pos = (pos[0] + rp.vector(200, 540), pos[1])
            for y in cards_pos_y:
                for x in cards_pos_x:
                    action.tap(rp.vector2((x, y), 540))
                    action.tap(pos)
                    while True:
                        _tmpl, _pos = action.wait_image_stable(
                            tmple.BREAK_LIMIT_BUTTON,
                            templates.RETURN_BUTTON,
                            duration=0.4,
                        )
                        if _tmpl.name == tmple.BREAK_LIMIT_BUTTON:
                            action.tap(_pos)
                            action.wait_tap_image(tmple.BREAK_LIMIT_BUTTON)
                            action.wait_image_disappear(tmple.BREAK_LIMIT_BUTTON)
                            action.wait_tap_image(tmple.STRENGTHEN_CARD_PIECE)
                            time.sleep(3)
                        else:
                            action.tap(_pos)
                            break
            action.wait_tap_image(tmple.STORY_BUTTON)
            time.sleep(0.4)
            task.limit_break_support_card = False

        elif name == templates.RETURN_BUTTON and task.view_support_card:
            app.log.text("RETURN_BUTTON SUP")
            cards = list(
                template.match(
                    template.screenshot(),
                    tmple.OVERVIEW_CARD_SR,
                    tmple.OVERVIEW_CARD_SSR,
                )
            )
            cards_pos_y = list(map(lambda x: x[1][1], cards))
            # print(cards_pos_y)
            min_y = min(cards_pos_y) - rp.vector(5, 540)
            max_y = max(cards_pos_y) + rp.vector(120, 540)
            card_img = template.screenshot()
            card_img = card_img.crop((0, min_y, c.width - 1, max_y))
            task.add_img(card_img)
            # imagetools.show(card_img)

            # overview_img = Image.new(
            #     "RGB",
            #     (
            #         c.width,
            #         card_img.height + derby_img.height,  #
            #     ),
            #     (0, 0, 0),
            # )
            # overview_img.paste(card_img, (0, 0))
            # overview_img.paste(derby_img, (0, card_img.height))
            # imagetools.show(overview_img)

            action.wait_tap_image(tmple.STORY_BUTTON)
            task.view_support_card = False

        elif name == tmple.HOME_MENU_LOGOUT_BUTTON:
            app.log.text("HOME_MENU_LOGOUT_BUTTON")

            overview_img = task.to_img()
            # imagetools.show(overview_img)
            in_mem_file = io.BytesIO()
            overview_img.save(in_mem_file, format="PNG")
            # reset file pointer to start
            in_mem_file.seek(0)
            img_bytes = in_mem_file.read()

            url = "https://litterbox.catbox.moe/resources/internals/api.php"
            files = {"fileToUpload": ("%s.png" % username, img_bytes, "image/png")}
            values = {"reqtype": "fileupload", "time": "72h"}
            res = requests.post(url, files=files, data=values)
            print(res.text)
            img_url = res.text

            webhook_url = "https://discord.com/api/webhooks/991689085519413298/z9Aro8iHDwnadSzC8QuHVEdVupjnPcHcxygY8JAVPWPCSkAd_LzydEE0jCMjJ23fRg9v"
            requests.post(
                webhook_url,
                json={
                    "content": "Username: %s\nSSR: %d" % (username, ssr_count),
                    # "username": "custom username",
                    "embeds": [{"image": {"url": img_url}}],
                },
            )

            task = Task()
            ssr_count = 0
            username_list: List[Text] = generate_username()
            username = username_list[0]
            os.environ["AUTO_DERBY_USERNAME"] = username

            # terminal.prompt("Logged out")
            action.tap((pos[0], pos[1] + rp.vector(90, 540)))

        elif name == tmple.KOMOE_ACCOUNT_LOGIN_BUTTON:
            app.log.text("KOMOE_ACCOUNT_LOGIN_BUTTON")
            action.tap(pos)
            action.wait_tap_image(tmple.KOMOE_ACCOUNT_SIGNUP_BUTTON)
            _, _pos = action.wait_image(tmple.KOMOE_ACCOUNT_SIGNUP_TITLE)

            while True:
                action.tap(
                    (_pos[0] + rp.vector(110, 540), _pos[1] + rp.vector(90, 540))
                )
                if isinstance(c, clients.ADBClient):
                    c.device.shell("input text smallkumc+%s" % username)

                    action.tap(
                        (_pos[0] + rp.vector(110, 540), _pos[1] + rp.vector(150, 540))
                    )
                    c.device.shell("input text ku2605")

                action.tap(
                    (_pos[0] + rp.vector(110, 540), _pos[1] + rp.vector(220, 540))
                )

                try:
                    _, pos = next(
                        template.match(
                            template.screenshot(), tmple.KOMOE_ACCOUNT_SIGNUP_TITLE
                        )
                    )
                except StopIteration:
                    break
            # time.sleep(0.5)

            try:
                while True:
                    time.sleep(2)
                    with MailBox(SERVER).login(USER, PASSWORD) as mailbox:
                        msg_list = list(
                            mailbox.fetch(
                                AND(to="smallkumc+{}@gmail.com".format(username))
                            )
                        )
                        if msg_list:
                            for msg in msg_list:
                                url = set(
                                    re.findall(
                                        "https?:\\/\\/www\\.komoejoy\\.com\\/email_verify\\/result\\.html\\?type=reg&ticket=[0-9a-z]+&code=[0-9a-z]+&account_domain=\\d+&lang=\\w+",
                                        msg.text or msg.html,
                                    )
                                )
                                # print(url.pop())
                            driver.execute_script("window.open('');")
                            driver.switch_to.window(driver.window_handles[1])
                            driver.get(url.pop())
                            driver.switch_to.window(driver.window_handles[0])
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])

                            driver.find_element(By.CLASS_NAME, "success")
                            break
            except BaseException as e:
                terminal.prompt("Email verify: %s" % e)
            action.tap((_pos[0] + rp.vector(110, 540), _pos[1] + rp.vector(220, 540)))
            _, _pos = action.wait_image(tmple.KOMOE_ACCOUNT_SIGNUP_CONFIRM)
            action.tap((_pos[0], _pos[1] + rp.vector(220, 540)))
        elif name == tmple.TUTORIAL_SKIP_BUTTON:
            app.log.text("TUTORIAL_SKIP_BUTTON")
            action.tap(pos)
            tmpl, pos = action.wait_image(tmple.TRAINER_NAME_LABEL)
            x, y = pos
            x += rp.vector(200, 540)
            action.tap((x, y))

            if isinstance(c, clients.ADBClient):
                c.device.shell("input text %s" % username)
                time.sleep(0.5)
                action.tap((x, y))
            else:
                terminal.prompt("Enter user name")

            y += rp.vector(200, 540)
            time.sleep(0.5)
            action.tap((x, y))
            # action.wait_tap_image(tmple.LAUNCH_SCREEN_MENU_BUTTON)
        else:
            action.tap(pos)
    driver.quit()
