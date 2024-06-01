# -*- coding=UTF-8 -*-
# pyright: strict

from __future__ import annotations

from ... import mathtools
from .globals import g
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .. import Context
    from .training import Training


def compute(ctx: Context, trn: Training) -> float:
    t_now = ctx.turn_count_v2()

    max_speed_list = [
        int(ctx.max_speed * 0.8),
        int(ctx.max_speed * 0.9),
    ]

    spd = mathtools.integrate(
        ctx.speed,
        trn.speed,
        (
            (0, 2.0),
            (300, 1.0),
            (600, 0.8),
            (900, 0.7),
            (max_speed_list[0], 0.5),
            (max_speed_list[1], 0.1),
        ),
    )
    if ctx.speed < t_now / 24 * 300:
        spd *= 1.5

    max_stamina_list = [
        int(ctx.max_stamina * 0.8),
        int(ctx.max_stamina * 0.9),
    ]
    sta = mathtools.integrate(
        ctx.stamina,
        trn.stamina,
        (
            (0, 2.0),
            (300, ctx.speed / 600 + 0.3 * ctx.date[0] if ctx.speed > 600 else 1.0),
            (
                600,
                ctx.speed / 900 * 0.6 + 0.1 * ctx.date[0] if ctx.speed > 900 else 0.6,
            ),
            (max_stamina_list[0], ctx.speed / 900 * 0.3),
            (max_stamina_list[1], 0.1),
        ),
    )

    max_power_list = [
        int(ctx.max_power * 0.8),
        int(ctx.max_power * 0.9),
    ]
    pow_ = mathtools.integrate(
        ctx.power,
        trn.power,
        (
            (0, 1.0),
            (300, 0.2 + ctx.speed / 600),
            (600, 0.1 + ctx.speed / 900),
            (max_power_list[0], ctx.speed / 900 / 3),
            (max_power_list[1], 0.1),
        ),
    )

    max_guts_list = [
        int(ctx.max_guts * 0.8),
        int(ctx.max_guts * 0.9),
    ]
    gut = mathtools.integrate(
        ctx.guts,
        trn.guts,
        (
            (0, 2.0),
            (300, 1.0 * ctx.speed / 400),
            (400, 0.6 * ctx.speed / 400),
            (600, 0.2 * ctx.speed / 400),
            (max_guts_list[0], 0.1 * ctx.speed / 400),
            (max_guts_list[1], 0.1),
        ),
    )
    if ctx.guts > 300 and ctx.speed < min(1120, 400 / 24 * t_now):
        gut *= 0.5

    max_wisdom_list = [
        int(ctx.max_wisdom * 0.8),
        int(ctx.max_wisdom * 0.9),
    ]
    wis = mathtools.integrate(
        ctx.wisdom,
        trn.wisdom,
        (
            (0, 2.0),
            (300, 0.8),
            (600, 0.5),
            (max_wisdom_list[0], 0.3),
            (max_wisdom_list[1], 0.1),
        ),
    )
    if ctx.wisdom > 300 and ctx.speed < min(1120, 300 / 24 * t_now):
        wis *= 0.1

    vit = mathtools.clamp(trn.vitality, 0, 1 - ctx.vitality) * ctx.max_vitality * 0.6
    if ctx.date[1:] in ((6, 1),):
        vit *= 1.2
    if ctx.date[1:] in ((6, 2), (7, 1), (7, 2), (8, 1)):
        vit *= 1.5
    if ctx.date[0] == 4:
        vit *= 0.3

    live_performance = 0
    if ctx.scenario == ctx.SCENARIO_GRAND_LIVE:
        avg = (trn.dance + trn.passion + trn.vocal + trn.visual + trn.mental) / 5
        value_map = (
            (0, 4.0),
            (round(avg), 2.0),
            (round(avg * 1.5), 0.1),
        )
        live_performance += mathtools.integrate(
            ctx.dance,
            trn.dance,
            value_map,
        )
        live_performance += mathtools.integrate(
            ctx.passion,
            trn.passion,
            value_map,
        )
        live_performance += mathtools.integrate(
            ctx.vocal,
            trn.vocal,
            value_map,
        )
        live_performance += mathtools.integrate(
            ctx.visual,
            trn.visual,
            value_map,
        )
        live_performance += mathtools.integrate(
            ctx.mental,
            trn.mental,
            value_map,
        )
        if ctx.date[0] == 4:
            live_performance *= 0.3

    skill = trn.skill * 0.5

    success_rate = 1 - trn.failure_rate

    partner = 0
    for i in trn.partners:
        partner += i.score(ctx)

    target_level = g.target_levels.get(trn.type, trn.level)
    target_level_score = 0
    if ctx.scenario == ctx.SCENARIO_UAF_READY_GO:
        if ctx.date[0] != 4 and trn.type in trn.ALL_TYPES_UAF:
            genre = (int(trn.type) - 2) // 5
            trainings = [i for i in ctx.trainings if (int(i.type) - 2) // 5 == genre]
            target_level_score = sum(
                mathtools.integrate(
                    i.level,
                    i.level_up,
                    (
                        (1, 4.0),
                        (50, 2.0),
                        (60, 0.8),
                        (100, 0.1),
                    ),
                )
                for i in trainings
            )
            genre_sum = {1: ctx.sphere_sum, 2: ctx.fight_sum, 3: ctx.free_sum}[genre]
            all_genre_avg = (ctx.sphere_sum + ctx.fight_sum + ctx.free_sum) / 3
            target_level_score += mathtools.interpolate(
                int(genre_sum - all_genre_avg),
                (
                    (-50, 25),
                    (-30, 10),
                    (0, 0),
                    (30, -10),
                    (50, -25),
                ),
            )
    elif ctx.is_summer_camp:
        pass
    elif trn.level < target_level:
        target_level_score += mathtools.interpolate(
            t_now,
            (
                (0, 5),
                (24, 3),
                (48, 2),
                (72, 0),
            ),
        )
    elif trn.level > target_level:
        target_level_score -= (trn.level - target_level) * 5

    fail_penalty = 0
    if ctx.scenario == ctx.SCENARIO_UAF_READY_GO and trn.type != trn.TYPE_WISDOM:
        fail_penalty = mathtools.interpolate(
            t_now,
            (
                (0, 30),
                (72, 60),
            ),
        )

    has_hint = any(i for i in trn.partners if i.has_hint)
    hint = 3 if has_hint else 0
    return (
        (
            spd
            + sta
            + pow_
            + gut
            + wis
            + skill
            + partner
            + target_level_score
            + hint
            + live_performance
        )
        * success_rate
        + vit
        - fail_penalty * trn.failure_rate
    )
