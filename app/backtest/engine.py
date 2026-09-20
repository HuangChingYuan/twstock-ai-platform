"""
⑪ 策略回測 (Slide 11)

策略規則：
    MA20 > MA60  AND  RSI14 > 50  AND  Foreign_Buy > 0  → 持有 (多方)
    其餘情況 → 空手

簡化為單一部位、全額進出、不含手續費/滑價的向量化回測，
方便教學展示；正式量化系統建議改用 backtrader / vectorbt 等框架並加入交易成本。
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from app.backtest import metrics as m

STRATEGY_NAME = "MA20>MA60 + RSI>50 + ForeignBuy>0"


def run_backtest(
    indicator_df: pd.DataFrame,
    institutional_df: Optional[pd.DataFrame] = None,
    initial_capital: float = 1_000_000.0,
) -> dict:
    """
    indicator_df: 需含 date, close, ma20, ma60, rsi14 (已由 compute_all_indicators 產生)
    institutional_df: 需含 date, foreign_investors (可為 None，此時忽略法人條件)
    """
    df = indicator_df.copy().sort_values("date").reset_index(drop=True)

    if institutional_df is not None and not institutional_df.empty:
        df = df.merge(institutional_df[["date", "foreign_investors"]], on="date", how="left")
        df["foreign_investors"] = df["foreign_investors"].fillna(0)
        foreign_ok = df["foreign_investors"] > 0
    else:
        foreign_ok = pd.Series(True, index=df.index)  # 沒有法人資料時不設限制

    df["signal"] = (
        (df["ma20"] > df["ma60"]) & (df["rsi14"] > 50) & foreign_ok
    ).astype(int)

    # 訊號延遲一天才進場，避免用到未來資訊 (以隔日開盤/收盤價成交)
    df["position"] = df["signal"].shift(1).fillna(0)

    df["daily_return"] = df["close"].pct_change().fillna(0)
    df["strategy_return"] = df["daily_return"] * df["position"]

    df["equity"] = initial_capital * (1 + df["strategy_return"]).cumprod()

    # 逐筆交易報酬 (進場到出場的一段區間報酬)，用來算勝率
    trade_returns = []
    in_trade = False
    entry_equity = None
    for _, row in df.iterrows():
        if row["position"] == 1 and not in_trade:
            in_trade = True
            entry_equity = row["equity"]
        elif row["position"] == 0 and in_trade:
            in_trade = False
            if entry_equity:
                trade_returns.append(row["equity"] / entry_equity - 1)
    if in_trade and entry_equity:
        trade_returns.append(df["equity"].iloc[-1] / entry_equity - 1)

    result = {
        "strategy_name": STRATEGY_NAME,
        "start_date": df["date"].iloc[0] if not df.empty else None,
        "end_date": df["date"].iloc[-1] if not df.empty else None,
        "total_return": m.total_return(df["equity"]),
        "win_rate": m.win_rate(trade_returns),
        "max_drawdown": m.max_drawdown(df["equity"]),
        "sharpe_ratio": m.sharpe_ratio(df["strategy_return"]),
        "trade_count": len(trade_returns),
        "equity_curve": [
            {"date": str(d), "equity": round(float(e), 2)}
            for d, e in zip(df["date"], df["equity"])
        ],
    }
    return result
