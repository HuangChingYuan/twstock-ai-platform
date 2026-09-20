"""
FinMind 資料擷取 (Slide 05)

FinMind 提供台股股價、月營收、財報、三大法人買賣超等資料集。
免費額度有限，設定 FINMIND_TOKEN 後額度較高。
文件: https://finmindtrade.com/analysis/#/data/api
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

import pandas as pd
import requests

from app.config import settings

_SESSION = requests.Session()


def _get_dataset(dataset: str, data_id: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
    """呼叫 FinMind /data API 並回傳 DataFrame，失敗時回傳空的 DataFrame。"""
    params = {
        "dataset": dataset,
        "data_id": data_id,
        "start_date": start_date,
    }
    if end_date:
        params["end_date"] = end_date
    if settings.FINMIND_TOKEN:
        params["token"] = settings.FINMIND_TOKEN

    try:
        resp = _SESSION.get(settings.FINMIND_BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("status") != 200:
            print(f"[FinMind] {dataset} 回應非 200：{payload.get('msg')}")
            return pd.DataFrame()
        return pd.DataFrame(payload.get("data", []))
    except Exception as exc:  # noqa: BLE001
        print(f"[FinMind] 擷取 {dataset} 失敗：{exc}")
        return pd.DataFrame()


def fetch_price(stock_id: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
    """① 股價 + ② 成交量。回傳欄位: date, open, high, low, close, volume"""
    df = _get_dataset("TaiwanStockPrice", stock_id, start_date, end_date)
    if df.empty:
        return df
    df = df.rename(columns={"Trading_Volume": "volume"})
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df[["date", "open", "high", "low", "close", "volume"]].sort_values("date").reset_index(drop=True)


def fetch_institutional(stock_id: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
    """④ 三大法人買賣超。回傳欄位: date, foreign_investors, investment_trust, dealer"""
    df = _get_dataset("TaiwanStockInstitutionalInvestorsBuySell", stock_id, start_date, end_date)
    if df.empty:
        return df
    df["net"] = df["buy"] - df["sell"]
    pivot = df.pivot_table(index="date", columns="name", values="net", aggfunc="sum").reset_index()
    pivot["date"] = pd.to_datetime(pivot["date"]).dt.date

    rename_map = {
        "Foreign_Investor": "foreign_investors",
        "Investment_Trust": "investment_trust",
        "Dealer_self": "dealer",
        "Dealer_Hedging": "dealer_hedging",
    }
    pivot = pivot.rename(columns=rename_map)
    for col in ["foreign_investors", "investment_trust", "dealer"]:
        if col not in pivot.columns:
            pivot[col] = 0.0
    return pivot[["date", "foreign_investors", "investment_trust", "dealer"]].sort_values("date").reset_index(drop=True)


def fetch_monthly_revenue(stock_id: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
    """⑤ 月營收。回傳欄位: date, revenue, revenue_yoy, revenue_mom"""
    df = _get_dataset("TaiwanStockMonthRevenue", stock_id, start_date, end_date)
    if df.empty:
        return df
    df = df.sort_values(["revenue_year", "revenue_month"]).reset_index(drop=True)
    df["revenue_mom"] = df["revenue"].pct_change() * 100
    df["revenue_yoy"] = df.get("revenue_YoY", df.get("revenue_yoy"))
    df["date"] = pd.to_datetime(
        df["revenue_year"].astype(str) + "-" + df["revenue_month"].astype(str) + "-01"
    ).dt.date
    return df[["date", "revenue", "revenue_yoy", "revenue_mom"]]


def fetch_financial_statement(stock_id: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
    """⑥ 財報 (EPS / ROE / ROA / 毛利率 / 營業利益率)。
    FinMind 的 TaiwanStockFinancialStatements 是「長表」(type/value)，這裡轉成寬表。
    """
    df = _get_dataset("TaiwanStockFinancialStatements", stock_id, start_date, end_date)
    if df.empty:
        return df

    wanted = {
        "EPS": "eps",
        "ROE": "roe",
        "ROA": "roa",
        "GrossMargin": "gross_margin",
        "OperatingMargin": "operating_margin",
    }
    df = df[df["type"].isin(wanted.keys())]
    if df.empty:
        return pd.DataFrame()

    pivot = df.pivot_table(index="date", columns="type", values="value", aggfunc="last").reset_index()
    pivot = pivot.rename(columns=wanted)
    pivot["date"] = pd.to_datetime(pivot["date"]).dt.date
    for col in wanted.values():
        if col not in pivot.columns:
            pivot[col] = None
    return pivot[["date", *wanted.values()]]


def default_start_date(years: int = 2) -> str:
    return (dt.date.today() - dt.timedelta(days=365 * years)).isoformat()
