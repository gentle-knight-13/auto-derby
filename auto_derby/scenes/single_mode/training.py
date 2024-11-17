# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations

import traceback
from concurrent import futures
import re
from typing import Callable, Iterator, Optional, Tuple, List, Union

import cast_unknown as cast
import cv2
import numpy as np
from PIL.Image import Image
from PIL.Image import fromarray as image_from_array

from ... import action, app, imagetools, mathtools, ocr, template, templates
from ...constants import TrainingType
from ...single_mode import Context, Training, training
from ...single_mode.training import Partner
from ..scene import Scene, SceneHolder
from .command import CommandScene

_CONFIRM_TMPL = (
    template.Specification(templates.SINGLE_MODE_TRAINING_CONFIRM, threshold=0.8),
    templates.SINGLE_MODE_TRAINING_CONFIRM_LARK,
)
_CONFIRM_TMPL_NAME = [
    tmpl.name if isinstance(tmpl, template.Specification) else tmpl
    for tmpl in _CONFIRM_TMPL
]


def _gradient(colors: Tuple[Tuple[Tuple[int, int, int], int], ...]) -> np.ndarray:
    ret = np.linspace((0, 0, 0), colors[0][0], colors[0][1])
    for index, i in enumerate(colors[1:], 1):
        color, stop = i
        prev_color, prev_stop = colors[index - 1]
        g = np.linspace(prev_color, color, stop - prev_stop + 1)
        ret = np.concatenate((ret, g[1:]))
    return ret


def _recognize_base_effect(img: Image) -> int:
    cv_img = imagetools.cv_image(imagetools.resize(img, height=32))
    sharpened_img = imagetools.sharpen(cv_img)
    sharpened_img = imagetools.mix(sharpened_img, cv_img, 0.4)

    white_outline_img = imagetools.constant_color_key(
        sharpened_img,
        (255, 255, 255),
        (235, 216, 217),
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
        (44, 91, 167),
        threshold=0.80,
    )
    _, non_brown_img = cv2.threshold(brown_img, 125, 255, cv2.THRESH_BINARY_INV)
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
    hash100 = [
        "000000000000006600ee00ff00ff00ff004e0000000000000000000000000000",
        "00000000000000000066007e007e007e007e005e005a00420000000000000000",  # mumu 12 1080p
    ]
    text_img_hash = imagetools.image_hash(imagetools.pil_image(text_img))
    hash_sim = max(
        map(lambda lst: imagetools.compare_hash(text_img_hash, lst), hash100)
    )
    app.log.image(f"hash100<{hash_sim}>{text_img_hash}", text_img, level=app.DEBUG)
    if hash_sim > 0.9:
        return 100
    text = ocr.text(image_from_array(text_img))
    if not text or text == "+":
        return 0
    return int(text.lstrip("+"))


def _recognize_red_effect(img: Image) -> int:
    cv_img = imagetools.cv_image(
        imagetools.resize(
            imagetools.resize(img, height=24),
            height=48,
        )
    )
    sharpened_img = cv2.filter2D(
        cv_img,
        8,
        np.array(
            (
                (0, -1, 0),
                (-1, 5, -1),
                (0, -1, 0),
            )
        ),
    )
    sharpened_img = imagetools.mix(sharpened_img, cv_img, 0.5)

    white_outline_img = imagetools.constant_color_key(
        sharpened_img,
        (255, 255, 255),
        (222, 220, 237),
        (252, 254, 202),
        (236, 249, 105),
        (243, 220, 160),
    )

    masked_img = imagetools.inside_outline(cv_img, white_outline_img)

    red_outline_img_base = imagetools.constant_color_key(
        cv_img,
        (15, 18, 216),
        (34, 42, 234),
        (56, 72, 218),
        (20, 18, 181),
        (27, 35, 202),
        (123, 131, 238),  # When outline too thin
        (101, 107, 232),  # When outline too thin
        threshold=0.95,
    )
    red_outline_img_extra = imagetools.constant_color_key(
        cv_img,
        # uaf
        (0, 10, 177),
        (9, 14, 196),
        (10, 22, 173),
        (22, 29, 200),
        (29, 29, 220),
        (29, 34, 182),
        (33, 49, 186),
        (37, 57, 207),
        (38, 47, 222),
        (36, 49, 202),
        (45, 60, 230),
        (47, 54, 196),
        (53, 60, 229),
        (57, 64, 201),
        (57, 75, 234),
        (66, 83, 227),
        (90, 95, 222),
        threshold=0.9,
    )
    red_outline_img = np.array(np.maximum(red_outline_img_base, red_outline_img_extra))
    red_outline_img = cv2.morphologyEx(
        red_outline_img,
        cv2.MORPH_CLOSE,
        np.ones((3, 3)),
    )

    masked_img = imagetools.inside_outline(cv_img, red_outline_img)

    height = cv_img.shape[0]
    fill_gradient = _gradient(
        (
            ((129, 211, 255), 0),
            ((126, 188, 255), round(height * 0.5)),
            ((82, 134, 255), round(height * 0.75)),
            ((36, 62, 211), height),
        )
    ).astype(np.uint8)
    fill_img = np.repeat(np.expand_dims(fill_gradient, 1), cv_img.shape[1], axis=1)
    assert fill_img.shape == cv_img.shape

    text_img_base = imagetools.color_key(masked_img, fill_img)
    imagetools.fill_area(text_img_base, (0,), size_lt=8)

    text_img_extra = imagetools.constant_color_key(
        masked_img,
        (128, 196, 253),
        (136, 200, 255),
        (144, 214, 255),
        (58, 116, 255),
        (64, 111, 238),
        (114, 174, 251),
        (89, 140, 240),
        (92, 145, 244),
        (91, 143, 238),
        (140, 228, 254),
        threshold=0.95,
    )
    text_img = np.array(np.maximum(text_img_base, text_img_extra))
    h = cv_img.shape[0]
    imagetools.fill_area(text_img, (0,), size_lt=round(h * 0.2**2))

    app.log.image(
        "red effect",
        cv_img,
        level=app.DEBUG,
        layers={
            "sharpened": sharpened_img,
            "white_outline": white_outline_img,
            "red_outline": red_outline_img,
            "masked": masked_img,
            "fill": fill_img,
            "text_base": text_img_base,
            "text_extra": text_img_extra,
            "text": text_img,
        },
    )
    text = ocr.text(image_from_array(text_img))
    if not text or text == "+":
        return 0
    return int(text.lstrip("+"))


def _recognize_light_gold_effect(img: Image) -> int:
    cv_img = imagetools.cv_image(imagetools.resize(img, height=32))

    height = cv_img.shape[0]
    outline_gradient = _gradient(
        (
            ((128, 207, 240), 0),
            ((128, 207, 240), round(height * 0.2)),
            ((62, 151, 191), round(height * 0.5)),
            ((31, 109, 162), round(height * 0.9)),
            ((31, 109, 162), height),
        )
    ).astype(np.uint8)
    outline_img = np.repeat(
        np.expand_dims(outline_gradient, 1), cv_img.shape[1], axis=1
    )
    assert outline_img.shape == cv_img.shape

    brown_outline_img_base = imagetools.color_key(cv_img, outline_img)
    brown_outline_img_extra = imagetools.constant_color_key(
        cv_img,
        (22, 103, 163),
        threshold=0.85,
    )
    brown_outline_img = np.array(
        np.maximum(brown_outline_img_base, brown_outline_img_extra)
    )
    masked_img = imagetools.inside_outline(cv_img, brown_outline_img)

    height = masked_img.shape[0]
    fill_gradient = _gradient(
        (
            ((255, 255, 255), 0),
            ((184, 255, 255), round(height * 0.5)),
            ((88, 215, 251), round(height * 0.75)),
            ((80, 192, 247), height),
        )
    ).astype(np.uint8)
    fill_img = np.repeat(np.expand_dims(fill_gradient, 1), masked_img.shape[1], axis=1)
    assert fill_img.shape == masked_img.shape

    text_img = imagetools.color_key(masked_img, fill_img)
    imagetools.fill_area(text_img, (0,), size_lt=8)

    app.log.image(
        "gold effect with light outline",
        cv_img,
        level=app.DEBUG,
        layers={
            "outline": outline_img,
            "brown_outline_base": brown_outline_img_base,
            "brown_outline_extra": brown_outline_img_extra,
            "brown_outline": brown_outline_img,
            "masked": masked_img,
            "fill": fill_img,
            "text": text_img,
        },
    )
    text = ocr.text(image_from_array(text_img), offset=1)
    if not text or text == "+":
        return 0
    return int(text.lstrip("+")) * 2


def _recognize_dark_gold_effect(img: Image) -> int:
    cv_img = imagetools.cv_image(
        imagetools.resize(
            imagetools.resize(img, height=24),
            height=48,
        )
    )
    sharpened_img = cv2.filter2D(
        cv_img,
        8,
        np.array(
            (
                (0, -1, 0),
                (-1, 5, -1),
                (0, -1, 0),
            )
        ),
    )
    sharpened_img = imagetools.mix(sharpened_img, cv_img, 0.5)

    white_outline_img = imagetools.constant_color_key(
        sharpened_img,
        (255, 255, 255),
        (203, 231, 248),
        # threshold=0.9,
    )

    masked_img = imagetools.inside_outline(cv_img, white_outline_img)

    height = cv_img.shape[0]
    outline_gradient = _gradient(
        (
            ((40, 134, 183), 0),
            # ((40, 134, 183), round(height * 0.25)),
            # ((184, 255, 255), round(height * 0.5)),
            # ((88, 215, 251), round(height * 0.75)),
            ((32, 74, 106), height),
        )
    ).astype(np.uint8)
    outline_img = np.repeat(
        np.expand_dims(outline_gradient, 1), cv_img.shape[1], axis=1
    )
    assert outline_img.shape == cv_img.shape

    brown_outline_img_base = imagetools.color_key(cv_img, outline_img)
    brown_outline_img_extra = imagetools.constant_color_key(
        cv_img,
        (73, 122, 157),
        threshold=0.9,
    )
    brown_outline_img = np.array(
        np.maximum(brown_outline_img_base, brown_outline_img_extra)
    )
    masked_img = imagetools.inside_outline(cv_img, brown_outline_img)

    height = masked_img.shape[0]
    fill_gradient = _gradient(
        (
            ((203, 246, 255), 0),
            ((203, 246, 255), round(height * 0.25)),
            ((121, 238, 255), round(height * 0.5)),
            # ((88, 215, 251), round(height * 0.75)),
            ((81, 186, 231), height),
        )
    ).astype(np.uint8)
    fill_img = np.repeat(np.expand_dims(fill_gradient, 1), masked_img.shape[1], axis=1)
    assert fill_img.shape == masked_img.shape

    text_img = imagetools.color_key(masked_img, fill_img)
    imagetools.fill_area(text_img, (0,), size_lt=8)

    app.log.image(
        "gold effect with dark outline",
        cv_img,
        level=app.DEBUG,
        layers={
            "sharpened": sharpened_img,
            "white_outline": white_outline_img,
            "outline": outline_img,
            "brown_outline": brown_outline_img,
            "masked": masked_img,
            "fill": fill_img,
            "text": text_img,
        },
    )
    text = ocr.text(image_from_array(text_img), offset=1)
    if not text or text == "+":
        return 0
    return int(text.lstrip("+")) * 2


def _recognize_level(rgb_color: Tuple[int, ...]) -> int:
    if imagetools.compare_color((49, 178, 22), rgb_color) > 0.9:
        return 1
    if imagetools.compare_color((46, 139, 244), rgb_color) > 0.9:
        return 2
    if imagetools.compare_color((255, 134, 0), rgb_color) > 0.9:
        return 3
    if imagetools.compare_color((244, 69, 132), rgb_color) > 0.9:
        return 4
    if imagetools.compare_color((165, 78, 255), rgb_color) > 0.9:
        return 5
    raise ValueError("_recognize_level: unknown level color: %s" % (rgb_color,))


def _recognize_uaf_genre(rgb_color: Tuple[int, ...]) -> int:
    if imagetools.compare_color((52, 122, 247), rgb_color) > 0.9:
        return 1  # sphere
    if imagetools.compare_color((255, 72, 77), rgb_color) > 0.9:
        return 2  # fight
    if imagetools.compare_color((255, 147, 0), rgb_color) > 0.9:
        return 3  # free
    raise ValueError("_recognize_uaf_genre: unknown uaf genre color: %s" % (rgb_color,))


def _recognize_failure_rate(
    ctx: Context, rp: mathtools.ResizeProxy, trn: Training, img: Image
) -> float:
    x, y = trn.confirm_position
    bbox = (
        x + rp.vector(15, 540),
        y
        + rp.vector(-139 if ctx.scenario == ctx.SCENARIO_DAIHOSHOKUSAI else -155, 540),
        x + rp.vector(75, 540),
        y + rp.vector(-107, 540),
    )
    rate_img = imagetools.cv_image(imagetools.resize(img.crop(bbox), height=48))
    outline_img = imagetools.constant_color_key(
        rate_img,
        (252, 150, 14),
        (255, 183, 89),
        (0, 150, 255),
        (0, 69, 255),
    )
    fg_img = imagetools.inside_outline(rate_img, outline_img)
    text_img = imagetools.constant_color_key(
        fg_img,
        (255, 255, 255),
        (255, 235, 208),
        (18, 218, 255),
        (195, 230, 255),
    )
    app.log.image(
        "failure rate",
        rate_img,
        level=app.DEBUG,
        layers={
            "outline": outline_img,
            "fg": fg_img,
            "text": text_img,
        },
    )
    text = ocr.text(imagetools.pil_image(text_img))
    return int(re.sub("[^0-9]", "", text)) / 100


def _recognize_uaf_level(rp: mathtools.ResizeProxy, trn: Training, img: Image) -> int:
    x, y = trn.confirm_position
    bbox = (
        x + rp.vector(14, 540),
        y + rp.vector(-106, 540),
        x + rp.vector(53, 540),
        y + rp.vector(-87, 540),
    )
    cv_img = imagetools.cv_image(imagetools.resize(img.crop(bbox), height=32))
    outline_img = imagetools.constant_color_key(
        cv_img,
        # sphere
        (255, 98, 68),
        (255, 133, 114),
        # fight
        (94, 84, 255),
        (61, 46, 255),
        # free
        (0, 153, 255),
        (33, 149, 255),
    )
    masked_img = imagetools.inside_outline(cv_img, outline_img)

    text_img = imagetools.constant_color_key(
        masked_img, (255, 255, 255), threshold=0.85
    )
    app.log.image(
        "uaf: training level",
        cv_img,
        level=app.DEBUG,
        layers={
            "outline": outline_img,
            "masked": masked_img,
            "text": text_img,
        },
    )

    text = ocr.text(imagetools.pil_image(text_img))
    if text:
        return int(re.sub("[^0-9]", "", text))

    # +100 has different color
    max_bbox = (
        x + rp.vector(14, 540),
        y + rp.vector(-100, 540),
        x + rp.vector(28, 540),
        y + rp.vector(-90, 540),
    )
    hash100 = [
        "0f0f9f0f9f0f9f0f9f0f9f8f9f8f9f8f938fb38ef3c4f3c462c4624400000000",
    ]
    max_img = img.crop(max_bbox)
    max_img_hash = imagetools.image_hash(max_img)
    hash_sim = max(map(lambda lst: imagetools.compare_hash(max_img_hash, lst), hash100))
    app.log.image(f"hash100<{hash_sim}>{max_img_hash}", max_img, level=app.DEBUG)
    if hash_sim > 0.9:
        return 100

    raise ValueError("_recognize_uaf_level: unknown uaf level")


def _recognize_uaf_level_up(
    rp: mathtools.ResizeProxy, trn: Training, img: Image
) -> int:
    x, y = trn.confirm_position
    bbox = (
        x + rp.vector(-6, 540),
        y + rp.vector(-122, 540),
        x + rp.vector(12, 540),
        y + rp.vector(-107, 540),
    )
    cv_img = imagetools.cv_image(imagetools.resize(img.crop(bbox), height=32))
    white_img = imagetools.constant_color_key(
        cv_img, (255, 255, 255), (191, 178, 180), threshold=0.85
    )
    white_img_extra = imagetools.constant_color_key(
        cv_img,
        ((87, 107, 177), 0.99),
        (139, 110, 131),
        (151, 110, 119),
        (166, 121, 119),
        (201, 143, 119),
        threshold=0.95,
    )
    text_img = white_img + white_img_extra
    app.log.image(
        "uaf: training level up",
        cv_img,
        level=app.DEBUG,
        layers={
            "text": text_img,
            "white": white_img,
            "text_extra": white_img_extra,
        },
    )
    text = ocr.text(imagetools.pil_image(text_img))
    return int(re.sub("[^0-9]", "", text))


def _estimate_vitality(ctx: Context, trn: Training) -> float:
    # https://gamewith.jp/uma-musume/article/show/257432
    vit_data = {
        trn.TYPE_SPEED: (-21, -22, -23, -25, -27),
        trn.TYPE_STAMINA: (-19, -20, -21, -23, -25),
        trn.TYPE_POWER: (-20, -21, -22, -24, -26),
        trn.TYPE_GUTS: (-22, -23, -24, -26, -28),
        trn.TYPE_WISDOM: (5, 5, 5, 5, 5),
    }

    if trn.type not in vit_data:
        return 0
    return vit_data[trn.type][trn.level - 1] / ctx.max_vitality


def _iter_training_type(ctx: Context) -> List[TrainingType]:
    if ctx.scenario == ctx.SCENARIO_PROJECT_LARK:
        return Training.ALL_TYPES_LARK  # type: ignore
    return Training.ALL_TYPES  # type: ignore


def _iter_training_confirm_pos(ctx: Context) -> List[Tuple[int, int]]:
    rp = action.resize_proxy()
    if ctx.scenario == ctx.SCENARIO_PROJECT_LARK:
        return [
            rp.vector2((33, 835), 540),
            rp.vector2((121, 835), 540),
            rp.vector2((209, 835), 540),
            rp.vector2((297, 835), 540),
            rp.vector2((385, 835), 540),
            rp.vector2((473, 835), 540),
        ]
    if ctx.scenario == ctx.SCENARIO_DAIHOSHOKUSAI:
        return [
            rp.vector2((33, 835), 540),
            rp.vector2((121, 835), 540),
            rp.vector2((209, 835), 540),
            rp.vector2((297, 835), 540),
            rp.vector2((385, 835), 540),
        ]
    return [
        rp.vector2((78, 850), 540),
        rp.vector2((171, 850), 540),
        rp.vector2((268, 850), 540),
        rp.vector2((367, 850), 540),
        rp.vector2((461, 850), 540),
    ]


def _iter_training_images(ctx: Context, static: bool):
    rp = action.resize_proxy()
    radius = rp.vector(30, 540)
    tmpl, first_confirm_pos = (
        action.wait_image(*_CONFIRM_TMPL)
        if not static
        else next(template.match(app.device.screenshot(), *_CONFIRM_TMPL))
    )
    yield app.device.screenshot(), first_confirm_pos
    if static:
        return
    seen_confirm_pos = {
        first_confirm_pos,
    }
    for pos in _iter_training_confirm_pos(ctx):
        if mathtools.distance(first_confirm_pos, pos) < radius:
            continue
        app.device.tap((*pos, *rp.vector2((20, 20), 540)))
        _, pos = (
            action.wait_image_stable(tmpl, duration=0.12)
            if ctx.scenario == ctx.SCENARIO_UAF_READY_GO
            else action.wait_image(tmpl)
        )
        if pos not in seen_confirm_pos:
            yield app.device.screenshot(), pos
            seen_confirm_pos.add(pos)


def _recognize_type_color(rp: mathtools.ResizeProxy, icon_img: Image) -> int:
    type_pos = rp.vector2((2, 2), 540)
    type_colors = (
        ((36, 170, 255), Partner.TYPE_SPEED),
        ((255, 106, 86), Partner.TYPE_STAMINA),
        ((241, 128, 112), Partner.TYPE_STAMINA),
        ((255, 151, 27), Partner.TYPE_POWER),
        ((255, 96, 156), Partner.TYPE_GUTS),
        ((3, 191, 126), Partner.TYPE_WISDOM),
        ((254, 215, 133), Partner.TYPE_FRIEND),
        ((151, 211, 154), Partner.TYPE_GROUP),
    )
    for color, v in type_colors:
        if (
            imagetools.compare_color_near(
                imagetools.cv_image(icon_img), type_pos, color[::-1]
            )
            > 0.9
        ):
            return v
    return Partner.TYPE_OTHER


def _recognize_has_hint(rp: mathtools.ResizeProxy, icon_img: Image) -> bool:
    bbox = rp.vector4((50, 0, 58, 8), 540)
    hint_mark_color = (127, 67, 255)
    hint_mark_img = icon_img.crop(bbox)
    hint_mask = imagetools.constant_color_key(
        imagetools.cv_image(hint_mark_img), hint_mark_color
    )
    return np.average(hint_mask) > 200


def _recognize_has_training(
    ctx: Context, rp: mathtools.ResizeProxy, icon_img: Image
) -> bool:
    if ctx.scenario != ctx.SCENARIO_AOHARU:
        return False
    bbox = rp.vector4((52, 0, 65, 8), 540)
    mark_img = icon_img.crop(bbox)
    mask = imagetools.constant_color_key(
        imagetools.cv_image(mark_img),
        (67, 131, 255),
        (82, 171, 255),
        threshold=0.9,
    )

    mask_avg = np.average(mask)
    ret = mask_avg > 80
    app.log.image(
        "has training: %s mask_avg=%0.2f" % (ret, mask_avg),
        icon_img,
        level=app.DEBUG,
        layers={
            "mark": mask,
        },
    )
    return ret


def _recognize_has_soul_burst(
    ctx: Context, rp: mathtools.ResizeProxy, icon_img: Image
) -> bool:
    if ctx.scenario != ctx.SCENARIO_AOHARU:
        return False
    bbox = rp.vector4((52, 0, 65, 8), 540)
    mark_img = imagetools.cv_image(icon_img.crop(bbox))
    mask = imagetools.constant_color_key(
        mark_img,
        (198, 255, 255),
        threshold=0.9,
    )

    mask_avg = np.average(mask)
    ret = mask_avg > 80
    app.log.image(
        "has soul burst: %s mask_avg=%s" % (ret, mask_avg),
        icon_img,
        level=app.DEBUG,
        layers={
            "mark": mark_img,
            "mark_mask": mask,
        },
    )
    return ret


def _recognize_partner_level(rp: mathtools.ResizeProxy, icon_img: Image) -> int:
    pos = (
        rp.vector2((10, 65), 540),  # level 1
        rp.vector2((20, 65), 540),  # level 2
        rp.vector2((33, 65), 540),  # level 3
        rp.vector2((43, 65), 540),  # level 4
        rp.vector2((55, 65), 540),  # level 5
    )
    colors = (
        (109, 108, 119),  # empty
        (42, 192, 255),  # level 1
        (42, 192, 255),  # level 2
        (162, 230, 30),  # level 3
        (255, 173, 30),  # level 4
        (255, 235, 120),  # level 5
    )
    spec: Tuple[Tuple[Tuple[Tuple[int, int], Tuple[int, int, int]], ...], ...] = (
        # level 0
        (
            (pos[0], colors[0]),
            (pos[1], colors[0]),
            (pos[2], colors[0]),
            (pos[3], colors[0]),
            (pos[4], colors[0]),
        ),
        # level 1
        (
            (pos[0], colors[1]),
            (pos[1], colors[0]),
            (pos[2], colors[0]),
            (pos[3], colors[0]),
            (pos[4], colors[0]),
        ),
        # level 2
        (
            (pos[0], colors[2]),
            (pos[1], colors[2]),
            (pos[3], colors[0]),
            (pos[4], colors[0]),
        ),
        # level 3
        (
            (pos[0], colors[3]),
            (pos[1], colors[3]),
            (pos[2], colors[3]),
            (pos[4], colors[0]),
        ),
        # level 4
        (
            (pos[0], colors[4]),
            (pos[1], colors[4]),
            (pos[2], colors[4]),
            (pos[3], colors[4]),
        ),
        # level 5
        (
            (pos[0], colors[5]),
            (pos[4], colors[5]),
        ),
    )

    for level, s in enumerate(spec):
        if all(
            imagetools.compare_color_near(
                imagetools.cv_image(icon_img),
                pos,
                color[::-1],
            )
            > 0.95
            for pos, color in s
        ):
            return level
    return -1


def _recognize_soul(
    rp: mathtools.ResizeProxy, screenshot: Image, icon_bbox: Tuple[int, int, int, int]
) -> float:
    right_bottom_icon_bbox = (
        icon_bbox[0] + rp.vector(49, 540),
        icon_bbox[1] + rp.vector(32, 540),
        icon_bbox[0] + rp.vector(74, 540),
        icon_bbox[1] + rp.vector(58, 540),
    )

    right_bottom_icon_img = screenshot.crop(right_bottom_icon_bbox)
    is_full = any(
        template.match(right_bottom_icon_img, templates.SINGLE_MODE_AOHARU_SOUL_FULL)
    )
    if is_full:
        return 1

    soul_bbox = (
        icon_bbox[0] - rp.vector(35, 540),
        icon_bbox[1] + rp.vector(33, 540),
        icon_bbox[0] + rp.vector(2, 540),
        icon_bbox[3] - rp.vector(0, 540),
    )
    img = screenshot.crop(soul_bbox)
    img = imagetools.resize(img, height=40)
    cv_img = imagetools.cv_image(img)
    blue_outline_img = imagetools.constant_color_key(
        cv_img,
        (251, 109, 0),
        (255, 178, 99),
        threshold=0.6,
    )
    bg_mask1 = imagetools.border_flood_fill(blue_outline_img)
    fg_mask1 = 255 - bg_mask1
    masked_img = cv2.copyTo(cv_img, fg_mask1)
    sharpened_img = imagetools.mix(imagetools.sharpen(masked_img, 1), masked_img, 0.5)
    white_outline_img = imagetools.constant_color_key(
        sharpened_img,
        (255, 255, 255),
        (252, 251, 251),
        (248, 227, 159),
        (254, 245, 238),
        (253, 233, 218),
        threshold=0.9,
    )
    bg_mask2 = imagetools.border_flood_fill(white_outline_img)
    fg_mask2 = 255 - bg_mask2
    imagetools.fill_area(fg_mask2, (0,), size_lt=100)
    fg_img = cv2.copyTo(masked_img, fg_mask2)
    empty_mask = imagetools.constant_color_key(fg_img, (126, 121, 121))
    app.log.image(
        "soul",
        img,
        level=app.DEBUG,
        layers={
            "sharpened": sharpened_img,
            "right_bottom_icon": right_bottom_icon_img,
            "blue_outline": blue_outline_img,
            "white_outline": white_outline_img,
            "fg_mask1": fg_mask1,
            "fg_mask2": fg_mask2,
            "empty_mask": empty_mask,
        },
    )

    fg_avg = np.average(fg_mask2)
    if fg_avg < 100:
        return -1
    empty_avg = np.average(empty_mask)
    outline_avg = 45
    return max(0, min(1, 1 - (empty_avg / (fg_avg - outline_avg))))


def _recognize_gear(rp: mathtools.ResizeProxy, trn: Training, img: Image) -> bool:
    x, y = trn.confirm_position
    bbox = (
        x + rp.vector(-27, 540),
        y + rp.vector(-120, 540),
        x + rp.vector(0, 540),
        y + rp.vector(-90, 540),
    )

    gear_img = img.crop(bbox)
    app.log.image(
        "mecha gear",
        gear_img,
        level=app.DEBUG,
    )

    return any(
        template.match(
            gear_img,
            template.Specification(
                templates.SINGLE_MODE_MECHA_UMAMUSUME_GEAR, threshold=0.75
            ),
        )
    )


def _recognize_partner_icon(
    ctx: Context, img: Image, bbox: Tuple[int, int, int, int]
) -> Optional[training.Partner]:
    rp = mathtools.ResizeProxy(img.width)
    icon_img = img.crop(bbox)
    level = _recognize_partner_level(rp, icon_img)
    app.log.image("partner icon (%s)" % level, icon_img, level=app.DEBUG)

    soul = -1
    has_training = False
    has_soul_burst = False
    if ctx.scenario == ctx.SCENARIO_AOHARU:
        has_soul_burst = _recognize_has_soul_burst(ctx, rp, icon_img)
        if has_soul_burst:
            has_training = True
            soul = 1
        else:
            has_training = _recognize_has_training(ctx, rp, icon_img)
            soul = _recognize_soul(rp, img, bbox)

    if level < 0 and soul < 0:
        return None
    self = Partner.new()
    self.icon_bbox = bbox
    self.level = level
    self.soul = soul
    self.has_hint = _recognize_has_hint(rp, icon_img)
    self.has_training = has_training
    self.has_soul_burst = has_soul_burst
    if self.has_soul_burst:
        self.has_training = True
        self.soul = 1
    self.type = _recognize_type_color(rp, icon_img)
    if soul >= 0 and self.type == Partner.TYPE_OTHER:
        self.type = Partner.TYPE_TEAMMATE
    app.log.text("partner: %s" % self, level=app.DEBUG)
    return self


def _recognize_partners(ctx: Context, img: Image) -> Iterator[training.Partner]:
    rp = mathtools.ResizeProxy(img.width)

    icon_bbox, icon_y_offset = {
        ctx.SCENARIO_URA: (
            rp.vector4((448, 146, 516, 220), 540),
            rp.vector(90, 540),
        ),
        ctx.SCENARIO_AOHARU: (
            rp.vector4((448, 147, 516, 220), 540),
            rp.vector(86, 540),
        ),
        ctx.SCENARIO_CLIMAX: (
            rp.vector4((448, 147, 516, 220), 540),
            rp.vector(90, 540),
        ),
        ctx.SCENARIO_GRAND_MASTERS: (
            rp.vector4((448, 147, 516, 220), 540),
            rp.vector(90, 540),
        ),
        ctx.SCENARIO_GRAND_LIVE: (  # Todo: check correctness
            rp.vector4((448, 147, 516, 220), 540),
            rp.vector(86, 540),
        ),
        ctx.SCENARIO_PROJECT_LARK: (  # Todo: check correctness
            rp.vector4((448, 147, 516, 220), 540),
            rp.vector(86, 540),
        ),
        ctx.SCENARIO_UAF_READY_GO: (  # Todo: check correctness
            rp.vector4((448, 147, 516, 220), 540),
            rp.vector(86, 540),
        ),
        ctx.SCENARIO_DAIHOSHOKUSAI: (  # Todo: check correctness
            rp.vector4((448, 147, 516, 220), 540),
            rp.vector(86, 540),
        ),
        ctx.SCENARIO_MECHA_UMAMUSUME: (  # Todo: check correctness
            rp.vector4((448, 147, 516, 220), 540),
            rp.vector(86, 540),
        ),
    }[ctx.scenario]
    icons_bottom = rp.vector(578, 540)
    while icon_bbox[2] < icons_bottom:
        v = _recognize_partner_icon(ctx, img, icon_bbox)
        if not v:
            break
        yield v
        icon_bbox = (
            icon_bbox[0],
            icon_bbox[1] + icon_y_offset,
            icon_bbox[2],
            icon_bbox[3] + icon_y_offset,
        )


_Vector4 = Tuple[int, int, int, int]


def _effect_recognitions(
    ctx: Context, rp: mathtools.ResizeProxy
) -> Iterator[
    Tuple[
        Tuple[_Vector4, _Vector4, _Vector4, _Vector4, _Vector4, _Vector4],
        Callable[[Image], int],
    ]
]:
    def _bbox_groups(t: int, b: int):
        return (
            rp.vector4((18, t, 104, b), 540),
            rp.vector4((104, t, 190, b), 540),
            rp.vector4((190, t, 273, b), 540),
            rp.vector4((273, t, 358, b), 540),
            rp.vector4((358, t, 441, b), 540),
            rp.vector4((448, t, 521, b), 540),
        )

    if ctx.scenario == ctx.SCENARIO_URA:
        yield _bbox_groups(582, 616), _recognize_base_effect
    elif ctx.scenario == ctx.SCENARIO_AOHARU:
        yield _bbox_groups(597, 625), _recognize_base_effect
        yield _bbox_groups(570, 595), _recognize_red_effect
    elif ctx.scenario in (
        ctx.SCENARIO_CLIMAX,
        ctx.SCENARIO_GRAND_LIVE,
        ctx.SCENARIO_GRAND_MASTERS,
        ctx.SCENARIO_PROJECT_LARK,
        ctx.SCENARIO_UAF_READY_GO,
        ctx.SCENARIO_MECHA_UMAMUSUME,
    ):
        yield _bbox_groups(595, 623), _recognize_base_effect
        yield _bbox_groups(568, 593), _recognize_red_effect
    elif ctx.scenario == ctx.SCENARIO_DAIHOSHOKUSAI:
        yield _bbox_groups(595, 623), _recognize_base_effect
    else:
        raise NotImplementedError(ctx.scenario)
    if ctx.scenario in (
        ctx.SCENARIO_UAF_READY_GO,
        ctx.SCENARIO_MECHA_UMAMUSUME,
    ):
        yield _bbox_groups(595, 623), _recognize_light_gold_effect
        yield _bbox_groups(568, 593), _recognize_dark_gold_effect


def _recognize_training(
    ctx: Context, img_pair: Tuple[Image, Tuple[int, int]]
) -> Training:
    img = img_pair[0]
    try:
        rp = mathtools.ResizeProxy(img.width)

        self = Training.new()
        self.confirm_position = img_pair[1]
        rp.vector(40, 540)
        min_dist: Union[int, None] = None
        for t, center in zip(
            _iter_training_type(ctx),
            _iter_training_confirm_pos(ctx),
        ):
            x_dist = abs(self.confirm_position[0] - center[0])
            if min_dist is None or x_dist < min_dist:
                self.type = t
                min_dist = x_dist

        if ctx.scenario == ctx.SCENARIO_UAF_READY_GO:
            sport_genre = _recognize_uaf_genre(
                tuple(cast.list_(img.getpixel(rp.vector2((10, 200), 540)), int))  # type: ignore
            )
            self.type = TrainingType(sport_genre * 5 + int(self.type) + 1)
            self.level = (
                _recognize_uaf_level(rp, self, img)
                if self.type not in ctx.training_levels
                or ctx.training_levels[self.type] != 100
                else 100
            )
            self.level_up = (
                _recognize_uaf_level_up(rp, self, img) if self.level != 100 else 0
            )
        elif self.type != TrainingType.SS_MATCH:
            self.level = _recognize_level(
                tuple(cast.list_(img.getpixel(rp.vector2((10, 200), 540)), int))  # type: ignore
            )

        for bbox_group, recognize in _effect_recognitions(ctx, rp):
            self.speed += recognize(img.crop(bbox_group[0]))
            self.stamina += recognize(img.crop(bbox_group[1]))
            self.power += recognize(img.crop(bbox_group[2]))
            self.guts += recognize(img.crop(bbox_group[3]))
            self.wisdom += recognize(img.crop(bbox_group[4]))
            self.skill += recognize(img.crop(bbox_group[5]))

        if ctx.scenario == ctx.SCENARIO_GRAND_LIVE:
            left, right = rp.vector2((88, 146), 540)

            def _recognize(t: int, b: int):
                return _recognize_base_effect(
                    img.crop((left, rp.vector(t, 540), right, rp.vector(b, 540)))
                )

            self.dance += _recognize(265, 292)
            self.passion += _recognize(314, 341)
            self.vocal += _recognize(363, 390)
            self.visual += _recognize(412, 439)
            self.mental += _recognize(461, 488)

        if ctx.scenario == ctx.SCENARIO_MECHA_UMAMUSUME:
            self.gear = _recognize_gear(rp, self, img)
            # TODO: Recognize the level of research

        # TODO: recognize vitality
        # plugin hook
        self._use_estimate_vitality = True  # type: ignore
        self.vitality = _estimate_vitality(ctx, self)
        if self.type != TrainingType.SS_MATCH:
            self.failure_rate = _recognize_failure_rate(ctx, rp, self, img)
            self.partners = tuple(_recognize_partners(ctx, img))
        # TODO: recognize SS match partners
        app.log.image("%s" % self, img, level=app.DEBUG)
    except:
        app.log.image(
            ("training recognition failed: %s" % traceback.format_exc()),
            img,
            level=app.ERROR,
        )
        raise
    return self


class TrainingScene(Scene):
    @classmethod
    def name(cls):
        return "single-mode-training"

    @classmethod
    def _enter(cls, ctx: SceneHolder) -> Scene:
        CommandScene.enter(ctx)
        while True:
            tmpl, pos = action.wait_image(
                templates.SINGLE_MODE_COMMAND_TRAINING,
                templates.SINGLE_MODE_COMMAND_TRAINING_LARK,
                *_CONFIRM_TMPL,
            )
            if tmpl.name in _CONFIRM_TMPL_NAME:
                break
            app.device.tap(action.template_rect(tmpl, pos))
        return cls()

    def __init__(self):
        self.trainings: Tuple[Training, ...] = ()

    def recognize(self) -> None:
        # TODO: remove old api at next major version
        import warnings

        warnings.warn(
            "use recognize_v2 instead",
            DeprecationWarning,
        )
        ctx = Context()
        ctx.scenario = ctx.SCENARIO_URA
        return self.recognize_v2(ctx)

    def recognize_v2(self, ctx: Context, static: bool = False) -> None:
        with futures.ThreadPoolExecutor() as pool:
            self.trainings = tuple(
                i.result()
                for i in [
                    pool.submit(_recognize_training, ctx, j)
                    for j in _iter_training_images(ctx, static)
                ]
            )
        assert len(set(i.type for i in self.trainings)) == len(
            self.trainings
        ), "duplicated trainings"
        ctx.trainings = self.trainings
        if not ctx.is_summer_camp:
            ctx.training_levels = {i.type: i.level for i in self.trainings}
