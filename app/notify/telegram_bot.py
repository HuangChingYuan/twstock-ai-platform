"""
⑬ Telegram 即時通知 (Slide 13)

價格突破 → Technical Engine → AI Engine → Signal → Telegram

使用 Telegram Bot HTTP API 直接 POST，不需要額外跑 polling process，
適合在 FastAPI 分析完成後「順便」推播一則訊息。
"""
from __future__ import annotations

import requests

from app.config import settings


def send_message(text: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        print("[Telegram] 未設定 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID，略過推播。")
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[Telegram] 推播失敗：{exc}")
        return False


def build_signal_message(stock_id: str, stock_name: str, ai_result: dict) -> str:
    reasons = "\n".join(f"✓ {r}" for r in ai_result.get("reasons", [])[:3])
    return (
        f"📢 <b>{stock_id} {stock_name}</b> AI 訊號更新\n"
        f"AI View：{ai_result.get('view')}\n"
        f"Overall Score：{ai_result.get('overall_score')}\n"
        f"{reasons}\n"
        f"⚠️ 僅供研究參考，非投資建議"
    )
