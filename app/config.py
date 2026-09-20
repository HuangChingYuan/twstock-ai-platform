"""
全域設定。所有敏感資訊皆從環境變數讀取，方便 Render / HF Spaces / Cloudflare
以「Secrets」的方式注入，而不需要把金鑰寫進程式碼。
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # 資料庫：本機沒設定就退回 SQLite，方便直接跑 Demo
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./twstock.db")

    # FinMind
    FINMIND_TOKEN: str = os.getenv("FINMIND_TOKEN", "")
    FINMIND_BASE_URL: str = "https://api.finmindtrade.com/api/v4/data"

    # LLM
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # News
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")

    # API 位址 (給 NiceGUI / Gradio 呼叫用)
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")


settings = Settings()
