"""
基本面評分 (Slide 08): 營收 YoY / EPS 趨勢 / ROE / ROA / 毛利率 / 營益率 / PER / PBR → 0~100 分
"""
from __future__ import annotations

from typing import Optional


def _clip(score: float) -> float:
    return max(0.0, min(100.0, score))


def score_fundamental(
    revenue_yoy: Optional[float],
    eps_trend_up: Optional[bool],
    roe: Optional[float],
    roa: Optional[float],
    gross_margin: Optional[float],
    operating_margin: Optional[float],
    per: Optional[float] = None,
    pbr: Optional[float] = None,
) -> float:
    score = 50.0

    if revenue_yoy is not None:
        if revenue_yoy > 20:
            score += 15
        elif revenue_yoy > 0:
            score += 8
        elif revenue_yoy < -10:
            score -= 15
        else:
            score -= 5

    if eps_trend_up is True:
        score += 10
    elif eps_trend_up is False:
        score -= 8

    if roe is not None:
        if roe > 20:
            score += 10
        elif roe > 10:
            score += 5
        elif roe < 5:
            score -= 8

    if roa is not None:
        if roa > 10:
            score += 5
        elif roa < 2:
            score -= 5

    if gross_margin is not None and gross_margin > 30:
        score += 5

    if operating_margin is not None and operating_margin > 15:
        score += 5

    # 估值：PER/PBR 過高視為風險，適度扣分 (但不作為主要因子)
    if per is not None and per > 30:
        score -= 5
    if pbr is not None and pbr > 8:
        score -= 3

    return round(_clip(score), 1)
