from __future__ import annotations

import numpy as np
import pandas as pd


def total_return(equity: pd.Series) -> float:
    if len(equity) < 2 or equity.iloc[0] == 0:
        return 0.0
    return round((equity.iloc[-1] / equity.iloc[0] - 1) * 100, 2)


def max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max
    return round(drawdown.min() * 100, 2)


def sharpe_ratio(daily_returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
    if daily_returns.std() == 0 or daily_returns.empty:
        return 0.0
    excess = daily_returns - risk_free_rate / periods_per_year
    return round(float(np.sqrt(periods_per_year) * excess.mean() / daily_returns.std()), 2)


def win_rate(trade_returns: list[float]) -> float:
    if not trade_returns:
        return 0.0
    wins = sum(1 for r in trade_returns if r > 0)
    return round(wins / len(trade_returns) * 100, 2)
