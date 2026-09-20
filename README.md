# Python AI 財經交易實戰 — 從資料到策略實作

台股資料擷取 → 股票資料庫 → 技術/基本面因子 → LLM 財經分析 → 買賣建議 → 回測 → 儀表板 → Telegram 通知。

## 目錄結構

```
twstock-ai-platform/
├── app/
│   ├── config.py            # 環境變數 / 設定
│   ├── database.py          # SQLAlchemy engine/session
│   ├── models.py            # ORM 資料表 (Stock/Price/Revenue/Financial/Institutional/News/MOPS/Indicators/AIAnalysis/Backtest)
│   ├── data_sources/
│   │   ├── finmind.py       # FinMind API：股價/月營收/財報/法人買賣超
│   │   └── news.py          # 新聞擷取 (示範用，可換成正式新聞 API)
│   ├── quant/
│   │   ├── indicators.py    # MA / RSI / MACD / KD / Bollinger / ATR
│   │   ├── technical_score.py
│   │   └── fundamental_score.py
│   ├── ai/
│   │   ├── prompts.py
│   │   └── llm_analysis.py  # 呼叫 Anthropic API 產生投資研究報告 (無 key 時走 rule-based fallback)
│   ├── backtest/
│   │   ├── engine.py        # MA20>MA60 + RSI>50 + 法人買超 策略回測
│   │   └── metrics.py       # 報酬率/勝率/最大回撤/夏普值
│   ├── api/
│   │   └── main.py          # FastAPI：整合全流程的 /analyze/{stock_id}
│   ├── dashboard/
│   │   └── nicegui_app.py   # 正式 Dashboard (NiceGUI)
│   ├── ai_demo/
│   │   └── gradio_app.py    # AI / LLM Demo (Gradio, 適合放 HF Spaces)
│   └── notify/
│       └── telegram_bot.py  # Telegram 訊號通知
├── pwa/
│   ├── index.html           # Cloudflare Pages PWA shell (iframe 包 Render + HF Spaces)
│   ├── manifest.json
│   └── service-worker.js
├── requirements.txt
├── render.yaml               # Render 部署 (FastAPI + NiceGUI + PostgreSQL/Supabase)
├── Dockerfile.hf              # Hugging Face Spaces 部署 (Gradio Demo)
├── Procfile
└── .env.example
```

## 對應簡報架構

| 簡報 | 對應程式 |
|---|---|
| Slide 05 資料來源 | `app/data_sources/finmind.py`, `app/data_sources/news.py` |
| Slide 06 資料庫 | `app/database.py`, `app/models.py` |
| Slide 07 技術分析 | `app/quant/indicators.py`, `technical_score.py` |
| Slide 08 基本面分析 | `app/quant/fundamental_score.py` |
| Slide 09-10 AI 分析報告 | `app/ai/llm_analysis.py` |
| Slide 11 回測 | `app/backtest/engine.py`, `metrics.py` |
| Slide 12 Dashboard | `app/dashboard/nicegui_app.py` |
| Slide 13 Telegram | `app/notify/telegram_bot.py` |
| Slide 14 部署 | `render.yaml`, `Dockerfile.hf`, `pwa/` |

## 快速開始 (本機)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 填入 FINMIND_TOKEN / ANTHROPIC_API_KEY / TELEGRAM_BOT_TOKEN 等 (可留空，會走 fallback)

# 1) 啟動 API (資料擷取 + 計分 + LLM + 回測 all-in-one)
uvicorn app.api.main:app --reload --port 8000

# 2) 啟動正式 Dashboard
python -m app.dashboard.nicegui_app

# 3) 啟動 AI Demo (Gradio)
python -m app.ai_demo.gradio_app
```

呼叫 `POST http://localhost:8000/analyze/2330` 即可跑完 Demo 流程「①股價→②成交量→③技術指標→④法人→⑤月營收→⑥財報→⑦MOPS→⑧新聞→⑨LLM→⑩報告→⑪回測→⑫Dashboard→⑬Telegram」。

## 部署對應 (Slide 14)

- **Render**：`render.yaml` 部署 FastAPI (`app/api/main.py`) + NiceGUI Dashboard，資料庫接 Render/Supabase PostgreSQL。
- **Hugging Face Spaces**：`Dockerfile.hf` 部署 `app/ai_demo/gradio_app.py`，用於展示 AI 分析 Demo。
- **Cloudflare Pages**：`pwa/` 為純靜態 PWA shell，透過 iframe 包住 Render Dashboard 網址，並提供 Service Worker 離線快取。
- **Supabase**：作為正式 PostgreSQL，`DATABASE_URL` 直接指向 Supabase connection string。

## 注意事項

- FinMind 免費額度有限，正式使用需申請 Token（`FINMIND_TOKEN`）。
- LLM 分析預設呼叫 Anthropic API（`ANTHROPIC_API_KEY`），未設定時自動使用 rule-based 規則產生報告，確保 Demo 一定能跑。
- 新聞與 MOPS 擷取為示範性質（結構化欄位＋簡易抓取），正式上線建議串接付費新聞 API 或自建爬蟲並注意各網站使用條款。
- 本專案為教學/展示用途，不構成投資建議。
