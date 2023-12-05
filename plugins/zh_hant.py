import os
from typing import Iterator, List, Text, Tuple, Any, Dict
import auto_derby
import numpy as np
import cv2
from auto_derby import (
    single_mode,
    app,
    imagetools,
    mathtools,
    ocr,
    templates,
    texttools,
)
from auto_derby import action
from auto_derby.scenes.single_mode.training import _gradient
from auto_derby.single_mode.context import Context
from auto_derby.single_mode.race.race import Course, Race
from PIL.Image import Image
from PIL.Image import fromarray as image_from_array

##############################################################
# OCR
##############################################################


def text(img: Image, *, threshold: float = 0.8, segment_only: bool = False) -> Text:
    """Recognize text line, background color should be black.

    Args:
        img (Image): Preprocessed text line.

    Returns:
        Text: Text content
    """
    ocr.reload_on_demand()
    ret = ""

    img = imagetools.auto_crop_pil(img)
    w, h = img.width, img.height
    if h * w == 0:
        app.log.text("ocr result is empty", level=app.DEBUG)
        return ""

    if img.height < ocr._LINE_HEIGHT:
        w = round(ocr._LINE_HEIGHT / h * w)
        h = ocr._LINE_HEIGHT
        img = img.resize((w, h))
    cv_img = np.asarray(img.convert("L"))
    _, binary_img = cv2.threshold(cv_img, 0, 255, cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    if len(contours) == 0:
        app.log.image("ocr result is empty", img, level=app.DEBUG)
        return ""

    contours_with_bbox = sorted(
        ((i, ocr._rect2bbox(cv2.boundingRect(i))) for i in contours),
        key=lambda x: x[1][0],
    )

    max_char_width = max(bbox[2] - bbox[0] for _, bbox in contours_with_bbox)
    max_char_height = max(bbox[3] - bbox[1] for _, bbox in contours_with_bbox)
    max_char_width = max(max_char_height - 2, max_char_width)

    char_img_list: List[Tuple[Tuple[int, int, int, int], np.ndarray]] = []
    char_parts: List[np.ndarray] = []
    char_bbox = contours_with_bbox[0][1]
    char_non_zero_bbox = contours_with_bbox[0][1]

    def _crop_char(bbox: Tuple[int, int, int, int], img: np.ndarray):
        non_zero_pos_list = cv2.findNonZero(img)
        l0, t0, r0, b0 = bbox
        _, _, w0, h0 = ocr._bbox2rect(bbox)
        non_zero_rect = cv2.boundingRect(non_zero_pos_list)
        _, _, w1, h1 = non_zero_rect

        l1, t1, r1, b1 = ocr._rect2bbox(non_zero_rect)
        ml, mt, mr, mb = l1, t1, w0 - r1, h0 - b1
        ret = img
        if w1 > max_char_width * 0.3:
            l0 += ml
            r0 -= mr
            ret = ret[:, l1:r1]
        if h1 > max_char_height * 0.5:
            t0 += mt
            b0 -= mb
            ret = ret[t1:b1]

        return (l0, t0, r0, b0), ret

    def _push_char():
        if not char_parts:
            return
        mask = np.zeros_like(binary_img)
        cv2.drawContours(mask, char_parts, -1, (255,), thickness=cv2.FILLED)
        char_img = cv2.copyTo(binary_img, mask)
        l, t, r, b = char_bbox
        char_img = char_img[t:b, l:r]
        char_img_list.append((char_bbox, char_img))

    def _get_expanded_bbox(index: int) -> Tuple[int, int, int, int]:
        _, bbox = contours_with_bbox[index]
        if index + 1 < len(contours_with_bbox):
            _, next_bbox = contours_with_bbox[index + 1]
            if next_bbox[0] - bbox[2] < 2:
                bbox = ocr._union_bbox(bbox, _get_expanded_bbox(index + 1))
        return bbox

    for index, v in enumerate(contours_with_bbox):
        i, _ = v
        bbox = _get_expanded_bbox(index)

        l, t, r, b = bbox
        is_new_char = segment_only or (
            char_parts
            and l > char_non_zero_bbox[2]
            and (
                l - char_non_zero_bbox[0] > max_char_width * 0.8
                or l - char_non_zero_bbox[2] > max_char_width * 0.3
                or r - char_non_zero_bbox[0] > max_char_width
                or (
                    # previous is punctuation
                    char_non_zero_bbox[3] - char_non_zero_bbox[1]
                    < max_char_height * 0.6
                    and (
                        r - l > max_char_width * 0.7
                        or l - char_non_zero_bbox[2] > max_char_width * 0.1
                    )
                )
                or (
                    # current is punctuation
                    b - t < max_char_height * 0.4
                    and l > char_non_zero_bbox[2] + 1
                    and l > char_non_zero_bbox[0] + max_char_width * 0.3
                )
            )
            and not ocr._bbox_contains(ocr._pad_bbox(char_bbox, 2), bbox)
        )
        if is_new_char:
            space_w = l - char_bbox[2]
            divide_x = int(l - space_w * 0.5 - 1)
            last_r = min(divide_x, char_bbox[0] + max_char_width)
            char_bbox = ocr._union_bbox(char_bbox, (last_r, t, last_r, b))
            _push_char()
            char_parts = []
            char_bbox = (
                max(last_r + 1, r - max_char_width),
                char_bbox[1],
                r,
                int(char_bbox[1] + max_char_height),
            )
            char_non_zero_bbox = bbox
        char_parts.append(i)
        char_non_zero_bbox = ocr._union_bbox(char_non_zero_bbox, bbox)
        char_bbox = ocr._union_bbox(char_bbox, bbox)
    _push_char()

    cropped_char_img_list = [_crop_char(bbox, img) for (bbox, img) in char_img_list]

    if os.getenv("DEBUG") == auto_derby.ocr.__name__:
        segmentation_img = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2BGR)
        for i in contours:
            x, y, w, h = cv2.boundingRect(i)
            cv2.rectangle(
                segmentation_img, (x, y), (x + w, y + h), (0, 0, 255), thickness=1
            )
        chars_img = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2BGR)
        for bbox, _ in char_img_list:
            l, t, r, b = bbox
            cv2.rectangle(chars_img, (l, t), (r, b), (0, 0, 255), thickness=1)
        cropped_chars_img = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2BGR)
        for bbox, _ in cropped_char_img_list:
            l, t, r, b = bbox
            cv2.rectangle(cropped_chars_img, (l, t), (r, b), (0, 0, 255), thickness=1)
        app.log.image(
            "text (segment_only)" if segment_only else "text",
            cv_img,
            level=app.DEBUG,
            layers={
                "binary": binary_img,
                "segmentation": segmentation_img,
                "chars": chars_img,
                "cropped chars": cropped_chars_img,
            },
        )
    else:
        app.log.image("text", cv_img, level=app.DEBUG, layers={"binary": binary_img})

    for _, i in cropped_char_img_list:
        ret += ocr._text_from_image(i, threshold)

    app.log.text("ocr result: %s" % ret, level=app.DEBUG)

    return ret


def _recognize_base_effect(img: Image) -> int:
    cv_img = imagetools.cv_image(imagetools.resize(img, height=32))
    sharpened_img = imagetools.sharpen(cv_img)
    sharpened_img = imagetools.mix(sharpened_img, cv_img, 0.4)

    white_outline_img = imagetools.constant_color_key(
        sharpened_img,
        (255, 255, 255),
    )
    white_outline_img_dilated = cv2.morphologyEx(
        white_outline_img,
        cv2.MORPH_DILATE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
    )
    white_outline_img_dilated = cv2.morphologyEx(
        white_outline_img_dilated,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 7)),
    )

    bg_mask_img = (
        imagetools.bg_mask_by_outline(white_outline_img_dilated) + white_outline_img
    )
    masked_img = cv2.copyTo(cv_img, 255 - bg_mask_img)

    brown_img = imagetools.constant_color_key(
        cv_img,
        (29, 62, 194),
        (24, 113, 218),
        (30, 109, 216),
        (69, 104, 197),
        (119, 139, 224),
        (103, 147, 223),
        (59, 142, 226),
        threshold=0.8,
    )
    _, non_brown_img = cv2.threshold(brown_img, 120, 255, cv2.THRESH_BINARY_INV)
    border_brown_img = imagetools.border_flood_fill(non_brown_img)
    brown_outline_img = cv2.copyTo(brown_img, 255 - border_brown_img)

    bg_mask_img = imagetools.bg_mask_by_outline(brown_outline_img)
    masked_img = cv2.copyTo(masked_img, 255 - bg_mask_img)

    fill_gradient = _gradient(
        (
            ((140, 236, 255), 0),
            ((140, 236, 255), round(cv_img.shape[0] * 0.25)),
            ((114, 229, 255), round(cv_img.shape[0] * 0.35)),
            ((113, 198, 255), round(cv_img.shape[0] * 0.55)),
            ((95, 179, 255), round(cv_img.shape[0] * 0.63)),
            ((74, 157, 255), round(cv_img.shape[0] * 0.70)),
            ((74, 117, 255), round(cv_img.shape[0] * 0.83)),
            ((74, 117, 255), cv_img.shape[0]),
        )
    ).astype(np.uint8)
    fill_img = np.repeat(np.expand_dims(fill_gradient, 1), cv_img.shape[1], axis=1)
    assert fill_img.shape == cv_img.shape

    text_img = imagetools.color_key(masked_img, fill_img)

    text_img_extra = imagetools.constant_color_key(
        masked_img,
        (175, 214, 255),
        threshold=0.95,
    )
    text_img = np.array(np.maximum(text_img, text_img_extra))
    imagetools.fill_area(text_img, (0,), size_lt=48)

    app.log.image(
        "base effect",
        img,
        level=app.DEBUG,
        layers={
            "sharpened": sharpened_img,
            "white_outline": white_outline_img,
            "white_outline_dilated": white_outline_img_dilated,
            "brown": brown_img,
            "non_brown": non_brown_img,
            "border_brown": border_brown_img,
            "brown_outline": brown_outline_img,
            "bg_mask": bg_mask_img,
            "masked": masked_img,
            "text_extra": text_img_extra,
            "text": text_img,
        },
    )

    if cv2.countNonZero(text_img) < 100:
        # ignore skin match result
        return 0

    # +100 has different color
    hash100 = "000000000000006600ee00ff00ff00ff004e0000000000000000000000000000"
    if (
        imagetools.compare_hash(
            imagetools.image_hash(imagetools.pil_image(text_img)),
            hash100,
        )
        > 0.9
    ):
        return 100
    text = ocr.text(image_from_array(text_img))
    if not text:
        return 0
    return int(text.lstrip("+"))


##############################################################
# Context
##############################################################


def _year4_date_text(ctx: Context) -> Iterator[Text]:
    if ctx.scenario in (ctx.SCENARIO_URA, ctx.SCENARIO_AOHARU, ctx.SCENARIO_UNKNOWN):
        yield "決勝系列賽舉辦中"
    if ctx.scenario in (ctx.SCENARIO_CLIMAX, ctx.SCENARIO_UNKNOWN):
        yield "巔峰賽舉辦中"  # Not localized in current verison


def _ocr_date(
    ctx: Context, img: Image, *, _f=single_mode.context._ocr_date
) -> Tuple[int, int, int]:
    img = imagetools.resize(img, height=32)
    cv_img = np.asarray(img.convert("L"))
    cv_img = imagetools.level(
        cv_img, np.percentile(cv_img, 1), np.percentile(cv_img, 90)
    )
    sharpened_img = imagetools.sharpen(cv_img)
    white_outline_img = imagetools.constant_color_key(
        sharpened_img,
        (255,),
        threshold=0.85,
    )
    white_outline_img = cv2.morphologyEx(
        white_outline_img,
        cv2.MORPH_CLOSE,
        np.ones((3, 3)),
    )
    bg_mask_img = imagetools.bg_mask_by_outline(white_outline_img)
    masked_img = cv2.copyTo(
        255 - imagetools.mix(cv_img, sharpened_img, 0.5), 255 - bg_mask_img
    )
    _, binary_img = cv2.threshold(masked_img, 200, 255, cv2.THRESH_BINARY)
    imagetools.fill_area(binary_img, (0,), size_lt=2)
    app.log.image(
        "date",
        cv_img,
        level=app.DEBUG,
        layers={
            "sharpened": sharpened_img,
            "white_outline": white_outline_img,
            "bg_mask": bg_mask_img,
            "masked": masked_img,
            "binary": binary_img,
        },
    )

    text = ocr.text(single_mode.context.image_from_array(binary_img))

    if texttools.compare(text, "新手級出道前") > 0.8:
        return (1, 0, 0)
    for i in _year4_date_text(ctx):
        if texttools.compare(text, i) > 0.8:
            return (4, 0, 0)
    year_end = text.index("級") + 1
    month_end = year_end + text[year_end:].index("月") + 1
    year_text = text[:year_end]
    month_text = text[year_end:month_end]
    date_text = text[month_end:]

    year_dict = {"新手級": 1, "經典級": 2, "資深級": 3}
    year = year_dict[texttools.choose(year_text, year_dict.keys())]
    month = int(month_text[:-1])
    date = {"前半": 1, "後半": 2}[date_text]
    return (year, month, date)


def _recognize_fan_count(img: Image) -> int:
    cv_img = imagetools.cv_image(img.convert("L"))
    cv_img = imagetools.level(
        cv_img, np.percentile(cv_img, 1), np.percentile(cv_img, 90)
    )
    _, binary_img = cv2.threshold(cv_img, 50, 255, cv2.THRESH_BINARY_INV)
    app.log.image("fan count", cv_img, level=app.DEBUG, layers={"binary": binary_img})
    text = ocr.text(imagetools.pil_image(binary_img))
    return int(text.rstrip("人").replace(",", "").replace("、", ""))


def _recognize_property(img: Image) -> int:
    img = imagetools.resize(img, height=32)
    max_match = imagetools.constant_color_key(
        imagetools.cv_image(img),
        (210, 249, 255),
        threshold=0.95,
    )
    if np.average(max_match) > 5:
        return 1200

    cv_img = np.asarray(img.convert("L"))
    _, binary_img = cv2.threshold(cv_img, 160, 255, cv2.THRESH_BINARY_INV)
    imagetools.fill_area(binary_img, (0,), size_lt=3)
    app.log.image("property", cv_img, layers={"binary": binary_img}, level=app.DEBUG)
    return int(ocr.text(imagetools.pil_image(binary_img), segment_only=True))


##############################################################
# Race
##############################################################

_TURN_TRACK_SPEC = {
    "逆·内": (Course.TURN_LEFT, Course.TRACK_IN),
    "順·内": (Course.TURN_RIGHT, Course.TRACK_IN),
    "逆": (Course.TURN_LEFT, Course.TRACK_MIDDLE),
    "順": (Course.TURN_RIGHT, Course.TRACK_MIDDLE),
    "逆·外": (Course.TURN_LEFT, Course.TRACK_OUT),
    "順·外": (Course.TURN_RIGHT, Course.TRACK_OUT),
    "直線": (Course.TURN_NONE, Course.TRACK_MIDDLE),
    "順·外→内": (Course.TURN_RIGHT, Course.TRACK_OUT_TO_IN),
}


def _recognize_course(img: Image) -> Course:
    cv_img = imagetools.cv_image(imagetools.resize(img.convert("L"), height=32))
    cv_img = imagetools.level(
        cv_img, np.percentile(cv_img, 1), np.percentile(cv_img, 90)
    )
    _, binary_img = cv2.threshold(cv_img, 60, 255, cv2.THRESH_BINARY_INV)
    app.log.image("spec", cv_img, level=app.DEBUG, layers={"binary": binary_img})
    text = ocr.text(imagetools.pil_image(binary_img))
    stadium, text = text[:2], text[2:]
    if text[0] == "草":
        text = text[2:]
        ground = Course.GROUND_TURF
    elif text[0] == "沙":
        text = text[2:]
        ground = Course.GROUND_DART
    else:
        raise ValueError("_recognize_spec: invalid spec: %s", text)

    distance, text = int(text[:4]), text[9:]

    turn, track = _TURN_TRACK_SPEC[texttools.choose(text, _TURN_TRACK_SPEC.keys())]

    return Course(
        stadium=stadium,
        ground=ground,
        distance=distance,
        track=track,
        turn=turn,
    )

def _menu_item_bbox(
    ctx: Context, fan_icon_pos: Tuple[int, int], rp: mathtools.ResizeProxy
):
    _, y = fan_icon_pos

    if ctx.scenario == ctx.SCENARIO_CLIMAX:
        return (
            rp.vector(23, 540),
            y - rp.vector(72, 540),
            rp.vector(515, 540),
            y + rp.vector(33, 540),
        )

    return (
        rp.vector(23, 540),
        y - rp.vector(50.5, 540),
        rp.vector(515, 540),
        y + rp.vector(46, 540),
    )


def _spec_bbox(ctx: Context, rp: mathtools.ResizeProxy):
    if ctx.scenario == ctx.SCENARIO_CLIMAX:
        return rp.vector4((221, 21, 477, 41), 492)
    return rp.vector4((221, 13, 488, 30), 492)


_original_from_po = single_mode.race.race.JSONLRepository._from_po

#https://umamusume.jp/news/detail.php?id=896
_REMOVE_COURSES = ["川崎", "船橋", "盛岡"]
_REMOVE_RACES = ["川崎記念", "全日本ジュニア優駿", "かしわ記念", "マイルチャンピオンシップ南部杯", "レディスプレリュード", "東京盃", "エンプレス杯", "関東オークス", "ダイオライト記念", "さざんかテレビ杯", "TCK女王盃", "東京スプリント", "スパーキングレディーカップ", "マリーンカップ", "クイーン賞", "マーキュリーカップ", "クラスターカップ"]


def _from_po(*args, **kwargs) -> Race:
    do = _original_from_po(*args, **kwargs)
    remain_courses = tuple(x for x in do.courses if x.stadium not in _REMOVE_COURSES)
    if len(do.courses) != len(remain_courses):
        app.log.text(
            "course remove: %s %s" % (do.name, [x.stadium for x in do.courses]),
            level=app.DEBUG,
        )
        do.courses = remain_courses
    if len(do.courses) < 1 or do.name in _REMOVE_RACES:
        app.log.text("race removed: %s" % do.name, level=app.DEBUG)
        # Make a invalid race
        do = Race.new()
        do.permission = 1
    # app.log.text("race: %s (%s)" % (do.name, [x.stadium for x in do.courses]))
    return do


##############################################################
# Limited Sale (Outdated)
##############################################################


def buy_first_n(n: int) -> None:
    rp = action.resize_proxy()
    action.wait_tap_image(templates.GO_TO_LIMITED_SALE)
    action.wait_image(templates.CLOSE_NOW_BUTTON)
    app.log.image("limited sale: buy first %d" % n, app.device.screenshot())
    item_count = 0
    for tmpl, pos in action.match_image_until_disappear(
        templates.EXCHANGE_BUTTON, sort=lambda x: sorted(x, key=lambda i: i[1][1])
    ):
        app.device.tap(action.template_rect(tmpl, pos))
        action.wait_tap_image(templates.EXCHANGE_CONFIRM_BUTTON)
        for _ in action.match_image_until_disappear(templates.CONNECTING):
            pass
        action.wait_tap_image(templates.GREEN_OK_BUTTON)
        action.wait_image(templates.CLOSE_NOW_BUTTON)
        item_count += 1
        if n > 0 and item_count >= n:
            break
        app.device.swipe(
            rp.vector4((14, 540, 6, 10), 540),
            rp.vector4((14, 500, 6, 10), 540),
            duration=0.2,
        )
        # prevent inertial scrolling
        app.device.tap(
            rp.vector4((14, 500, 6, 10), 540),
        )

    action.wait_tap_image(templates.CLOSE_NOW_BUTTON)
    action.wait_tap_image(templates.GREEN_OK_BUTTON)
    action.wait_image(templates.RETURN_BUTTON)
    for tmpl, pos in action.match_image_until_disappear(templates.RETURN_BUTTON):
        app.device.tap(action.template_rect(tmpl, pos))


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        single_mode.context._ocr_date = _ocr_date
        single_mode.context._recognize_fan_count = _recognize_fan_count
        single_mode.context._recognize_property = _recognize_property
        single_mode.race.game_data._recognize_course = _recognize_course
        auto_derby.scenes.single_mode.race_menu._recognize_course = _recognize_course
        auto_derby.scenes.single_mode.training._recognize_base_effect = _recognize_base_effect
        auto_derby.scenes.single_mode.race_menu._menu_item_bbox = _menu_item_bbox
        # limited_sale.buy_first_n = buy_first_n
        single_mode.race.game_data._spec_bbox = _spec_bbox
        single_mode.race.race.JSONLRepository._from_po = _from_po
        ocr.text = text


auto_derby.plugin.register(__name__, Plugin())
