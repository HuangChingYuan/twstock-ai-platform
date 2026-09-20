"""
⑧ 新聞擷取 (示範用)

正式環境建議串接付費新聞 API (如 NewsAPI、聯合知識庫、CMoney) 或自建爬蟲，
並注意各來源網站的使用條款。這裡提供一個最小可用的介面：
- 有設定 NEWS_API_KEY 時走 NewsAPI
- 沒有設定時回傳空清單，讓上層流程仍可正常運作 (graceful degradation)
"""
from __future__ import annotations

import datetime as dt
from typing import List, TypedDict

import requests

from app.config import settings


class NewsItem(TypedDict):
    title: str
    source: str
    url: str
    published_at: str


def fetch_news(stock_name: str, limit: int = 10) -> List[NewsItem]:
    if not settings.NEWS_API_KEY:
        return []

    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": stock_name,
                "language": "zh",
                "sortBy": "publishedAt",
                "pageSize": limit,
                "apiKey": settings.NEWS_API_KEY,
            },
            timeout=10,
        )
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [
            NewsItem(
                title=a.get("title", ""),
                source=(a.get("source") or {}).get("name", ""),
                url=a.get("url", ""),
                published_at=a.get("publishedAt", dt.datetime.utcnow().isoformat()),
            )
            for a in articles
        ]
    except Exception as exc:  # noqa: BLE001
        print(f"[News] 擷取新聞失敗：{exc}")
        return []
