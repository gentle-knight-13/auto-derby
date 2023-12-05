import os
from typing import List, Text, Tuple

import auto_derby
import cv2
import numpy as np
from auto_derby import (
    action,
    app,
    imagetools,
    ocr,
    scenes,
    single_mode,
    template,
    templates,
)
from auto_derby.single_mode.context import Context
from PIL.Image import fromarray, Image

##############################################################
# OCR
##############################################################


def _text_from_image(img: np.ndarray, threshold: float = 0.8) -> Text:
    hash_img = cv2.GaussianBlur(img, (7, 7), 1, borderType=cv2.BORDER_CONSTANT)
    h = imagetools.image_hash(fromarray(hash_img), save_path=ocr.g.image_path)
    if ocr._g.labels.is_empty():
        return ocr._prompt(img, h, "", 0)
    res = ocr._g.labels.query(h)
    app.log.image(
        "query label: %s by %s" % (res, h),
        img,
        level=app.DEBUG,
    )
    if res.similarity > threshold:
        return res.value
    return ocr._prompt(img, h, res.value, res.similarity)


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
    cropped_char_img_list: List[Tuple[Tuple[int, int, int, int], np.ndarray]] = []
    char_parts: List[np.ndarray] = []
    char_bbox = contours_with_bbox[0][1]
    char_non_zero_bbox = contours_with_bbox[0][1]

    new_char_msg = ""

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
            return ""
        mask = np.zeros_like(binary_img)
        cv2.drawContours(mask, char_parts, -1, (255,), thickness=cv2.FILLED)
        char_img = cv2.copyTo(binary_img, mask)
        l, t, r, b = char_bbox
        char_img = char_img[t:b, l:r]
        crop_char_bbox, crop_char_img = _crop_char(char_bbox, char_img)
        char_img_list.append((char_bbox, char_img))
        cropped_char_img_list.append((crop_char_bbox, crop_char_img))
        app.log.image(new_char_msg, crop_char_img, level=app.DEBUG)
        return _text_from_image(crop_char_img, threshold)

    def _get_expanded_bbox(index: int) -> Tuple[int, int, int, int]:
        _, bbox = contours_with_bbox[index]
        if index + 1 < len(contours_with_bbox):
            _, next_bbox = contours_with_bbox[index + 1]
            if next_bbox[0] - bbox[2] < 2:
                bbox = ocr._union_bbox(bbox, _get_expanded_bbox(index + 1))
        return bbox

    def _is_new_char(l, t, r, b) -> Tuple[Text, bool]:
        if segment_only:
            return ("Predefined as every contour as new char", True)
        if char_parts and l > char_non_zero_bbox[2]:
            if l - char_non_zero_bbox[0] > max_char_width * 0.8:
                new_char_msg = f"({l - char_non_zero_bbox[0]}) > {max_char_width * 0.8}: left of char is far enough to left of prev char"
            elif l - char_non_zero_bbox[2] > max_char_width * 0.25:
                new_char_msg = f"{l - char_non_zero_bbox[2]} > {max_char_width * 0.25}: left of char is far enough to right of prev char"
            elif r - char_non_zero_bbox[0] > max_char_width * 1.1:
                new_char_msg = f"{r - char_non_zero_bbox[0]} > {max_char_width *1.05}: right of char is far enough to left of prev char"
            elif (
                # previous is punctuation
                char_non_zero_bbox[3] - char_non_zero_bbox[1] < max_char_height * 0.6
                and (
                    r - l > max_char_width * 0.6
                    or l - char_non_zero_bbox[2] > max_char_width * 0.1
                )
            ):
                new_char_msg = f"{char_non_zero_bbox[3] - char_non_zero_bbox[1]} < {max_char_height * 0.6}: prev char is punctuation by its height\n"
                if r - l > max_char_width * 0.6:
                    new_char_msg += f"{r - l} > {max_char_width * 0.6}: width of char is large enough"
                if l - char_non_zero_bbox[2] > max_char_width * 0.1:
                    new_char_msg += f"{l - char_non_zero_bbox[2]} > {max_char_width * 0.1}: left of char is far enough to right of prev char"
            elif (
                # current is punctuation
                b - t < max_char_height * 0.4
                and l > char_non_zero_bbox[2] + 1
                and l > char_non_zero_bbox[0] + max_char_width * 0.3
            ):
                new_char_msg = (
                    f"{b - t} < {max_char_height * 0.4}: char is punctuation by its height\n"
                    + f"{l} > {char_non_zero_bbox[2] + 1}: left of char is far enough to right of prev char\n"
                    + f"{l} > {char_non_zero_bbox[0] + max_char_width * 0.3}: left of char is far enough to left of prev char"
                )
            else:
                return ("", False)
            if not ocr._bbox_contains(ocr._pad_bbox(char_bbox, 2), bbox):
                return (new_char_msg, True)
        return ("", False)

    for index, v in enumerate(contours_with_bbox):
        i, _ = v
        bbox = _get_expanded_bbox(index)

        l, t, r, b = bbox
        new_char_msg, is_new_char = _is_new_char(l, t, r, b)
        if is_new_char:
            space_w = l - char_bbox[2]
            divide_x = int(l - space_w * 0.5 - 1)
            last_r = min(divide_x, char_bbox[0] + max_char_width)
            char_bbox = ocr._union_bbox(char_bbox, (last_r, t, last_r, b))
            txt = _push_char()
            char_parts = []
            char_bbox = (
                max(last_r + 1, r - max_char_width),
                char_bbox[1],
                r,
                int(char_bbox[1] + max_char_height),
            )
            char_non_zero_bbox = bbox
            ret += txt
        char_parts.append(i)
        char_non_zero_bbox = ocr._union_bbox(char_non_zero_bbox, bbox)
        char_bbox = ocr._union_bbox(char_bbox, bbox)
    ret += _push_char()

    if os.getenv("DEBUG") == ocr.__name__:
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
    app.log.text("ocr result: %s" % ret, level=app.DEBUG)

    return ret


##############################################################
# Context
##############################################################


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


def _recognize_fan_count(img: Image) -> int:
    cv_img = imagetools.cv_image(img.convert("L"))
    cv_img = imagetools.level(
        cv_img, np.percentile(cv_img, 1), np.percentile(cv_img, 90)
    )
    _, binary_img = cv2.threshold(cv_img, 50, 255, cv2.THRESH_BINARY_INV)
    app.log.image("fan count", cv_img, level=app.DEBUG, layers={"binary": binary_img})
    text = ocr.text(imagetools.pil_image(binary_img), segment_only=True)
    return int(text.rstrip("人").replace(",", ""))


##############################################################
# Single mode
##############################################################


def _recognize_climax_grade_point(ctx: Context):
    if ctx.date[0] == 4:
        # in year 4, grade points are replaced by rank points
        ctx.grade_point = 0
        return
    rp = action.resize_proxy()
    bbox = rp.vector4((10, 185, 119, 218), 540)
    img = app.device.screenshot().crop(bbox)
    x, _ = next(
        template.match(
            img,
            template.Specification(
                templates.SINGLE_MODE_CLIMAX_GRADE_POINT_PT_TEXT,
                threshold=0.8,
            ),
        )
    )[1]
    img = img.crop((0, 0, x, img.height))
    img = imagetools.resize(img, height=32)
    cv_img = imagetools.cv_image(img.convert("L"))
    _, binary_img = cv2.threshold(
        cv_img,
        130,
        255,
        type=cv2.THRESH_BINARY_INV,
    )
    app.log.image(
        "climax grade point",
        cv_img,
        level=app.DEBUG,
        layers={
            "binary": binary_img,
        },
    )
    text = ocr.text(imagetools.pil_image(binary_img), segment_only=True)
    ctx.grade_point = int(text.rstrip("pt").replace(",", ""))


class Plugin(auto_derby.Plugin):
    def install(self) -> None:
        single_mode.context._recognize_property = _recognize_property
        single_mode.context._recognize_fan_count = _recognize_fan_count
        scenes.single_mode.command._recognize_climax_grade_point = (
            _recognize_climax_grade_point
        )
        ocr.text = text


auto_derby.plugin.register(__name__, Plugin())
