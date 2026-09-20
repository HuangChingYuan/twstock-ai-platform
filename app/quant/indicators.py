"""
③ 技術指標計算 (Slide 07)

純 pandas/numpy 實作，不依賴 TA-Lib，避免部署環境編譯問題。
輸入: 包含 open/high/low/close/volume 欄位、依日期排序的 DataFrame。
輸出: 附加各指標欄位的 DataFrame。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def moving_averages(df: pd.DataFrame, windows=(5, 20, 60)) -> pd.DataFrame:
    for w in windows:
        df[f"ma{w}"] = df["close"].rolling(window=w, min_periods=1).mean()
    return df


def rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi14"] = 100 - (100 / (1 + rs))
    df["rsi14"] = df["rsi14"].fillna(50)
    return df


def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    return df


def kd(df: pd.DataFrame, period: int = 9, k_smooth: int = 3, d_smooth: int = 3) -> pd.DataFrame:
    low_min = df["low"].rolling(window=period, min_periods=1).min()
    high_max = df["high"].rolling(window=period, min_periods=1).max()
    rsv = (df["close"] - low_min) / (high_max - low_min).replace(0, np.nan) * 100
    rsv = rsv.fillna(50)
    df["k"] = rsv.ewm(alpha=1 / k_smooth, adjust=False).mean()
    df["d"] = df["k"].ewm(alpha=1 / d_smooth, adjust=False).mean()
    return df


def bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    mid = df["close"].rolling(window=window, min_periods=1).mean()
    std = df["close"].rolling(window=window, min_periods=1).std().fillna(0)
    df["bb_middle"] = mid
    df["bb_upper"] = mid + num_std * std
    df["bb_lower"] = mid - num_std * std
    return df


def atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df["atr14"] = tr.ewm(alpha=1 / period, adjust=False).mean()
    return df


def compute_all_indicators(price_df: pd.DataFrame) -> pd.DataFrame:
    """一次計算所有技術指標，price_df 需含 date/open/high/low/close/volume。"""
    df = price_df.sort_values("date").reset_index(drop=True).copy()
    df = moving_averages(df)
    df = rsi(df)
    df = macd(df)
    df = kd(df)
    df = bollinger_bands(df)
    df = atr(df)
    return df
