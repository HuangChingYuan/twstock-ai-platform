"""
⑦ MOPS 公開資訊觀測站 (示範用)

MOPS 網站有反爬蟲與使用條款限制，正式環境建議：
1. 優先用 FinMind 的 TaiwanStockNews / 財報公告類資料集
2. 或申請 MOPS 開放資料 / 合法授權管道

這裡先提供介面與資料結構，預設回傳空清單，不做直接爬蟲，避免違反使用條款。
"""
from __future__ import annotations

from typing import List, TypedDict


class MopsItem(TypedDict):
    date: str
    subject: str
    category: str
    url: str


def fetch_mops_announcements(stock_id: str, limit: int = 10) -> List[MopsItem]:
    """回傳近期重大訊息公告。示範版本回傳空清單 (graceful degradation)。"""
    return []
