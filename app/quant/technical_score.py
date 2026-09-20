"""
技術面評分 (Slide 07): 綜合 MA 排列 / RSI / MACD / KD / 法人動向 → 0~100 分
規則式評分，透明可解釋，方便之後接給 LLM 當作依據。
"""
from __future__ import annotations

from typing import Optional

import pandas as pd


def _clip(score: float) -> float:
    return max(0.0, min(100.0, score))


def score_technical(latest: pd.Series, foreign_net_recent: Optional[float] = None) -> float:
    """
    latest: compute_all_indicators() 輸出的最後一列 (Series)，需含
            close, ma5, ma20, ma60, rsi14, macd, macd_signal, k, d
    foreign_net_recent: 近期(如近5日)外資買賣超合計，可為 None
    """
    score = 50.0  # 中性起點

    # 均線多頭排列: close > ma5 > ma20 > ma60
    if latest["close"] > latest["ma5"] > latest["ma20"] > latest["ma60"]:
        score += 15
    elif latest["close"] > latest["ma20"]:
        score += 7
    elif latest["close"] < latest["ma20"] < latest["ma60"]:
        score -= 15

    # RSI：50~70 偏多但未過熱；>80 過熱扣分；<30 弱勢
    rsi_val = latest["rsi14"]
    if 50 <= rsi_val <= 70:
        score += 10
    elif rsi_val > 80:
        score -= 8
    elif rsi_val < 30:
        score -= 10

    # MACD：柱狀圖翻正 / 持續放大
    if latest["macd"] > latest["macd_signal"]:
        score += 10
    else:
        score -= 5

    # KD：黃金交叉 (K > D) 且未超過 80
    if latest["k"] > latest["d"] and latest["k"] < 80:
        score += 8
    elif latest["k"] > 80 and latest["d"] > 80:
        score -= 5

    # 法人動向
    if foreign_net_recent is not None:
        if foreign_net_recent > 0:
            score += 7
        elif foreign_net_recent < 0:
            score -= 7

    return round(_clip(score), 1)
