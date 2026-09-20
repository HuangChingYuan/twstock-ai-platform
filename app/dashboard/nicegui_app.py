"""
⑫ Web / PWA Dashboard (Slide 12) — 用 NiceGUI 實作正式 Dashboard

啟動方式：
    python -m app.dashboard.nicegui_app

透過 httpx 呼叫 FastAPI 的 /analyze/{stock_id}，畫面對應簡報 Slide 12 的卡片式版面：
    2330 台積電
    Price 1120 / RSI 64 / MACD Bullish
    Technical 82 / Fundamental 91 / AI Score 84
    🟢 AI 觀點：偏多
"""
import httpx
from nicegui import ui

from app.config import settings

state = {"data": None}


def score_color(score: float) -> str:
    if score is None:
        return "gray"
    if score >= 70:
        return "green"
    if score >= 40:
        return "orange"
    return "red"


def view_emoji(view: str) -> str:
    return {"偏多": "🟢", "中立": "🟡", "偏空": "🔴"}.get(view, "⚪")


@ui.page("/")
def main_page():
    ui.label("台股 AI Dashboard").classes("text-2xl font-bold")

    with ui.row().classes("items-center gap-2"):
        stock_input = ui.input(label="股票代號", value="2330").classes("w-32")
        result_area = ui.column().classes("w-full max-w-xl gap-2")

        async def run_analysis():
            result_area.clear()
            with result_area:
                ui.spinner(size="lg")
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(
                        f"{settings.API_BASE_URL}/analyze/{stock_input.value}",
                        params={"notify": "false"},
                    )
                    resp.raise_for_status()
                    data = resp.json()
            except Exception as exc:  # noqa: BLE001
                result_area.clear()
                with result_area:
                    ui.label(f"⚠️ 分析失敗：{exc}").classes("text-red-600")
                return

            state["data"] = data
            render_result(result_area, data)

        ui.button("分析", on_click=run_analysis).classes("bg-blue-600 text-white")

    render_result(result_area, None)


def render_result(container, data):
    container.clear()
    with container:
        if not data:
            ui.label("輸入股票代號並按下「分析」開始 Demo 流程").classes("text-gray-500")
            return

        with ui.card().classes("w-full"):
            ui.label(f"{data['stock_id']} {data['stock_name']}").classes("text-xl font-bold")

            with ui.row().classes("gap-6"):
                ui.label(f"Price {data['price']['close']}")
                ui.label(f"RSI {data['price']['rsi14']}")
                macd_trend = "Bullish" if data["price"]["macd"] >= 0 else "Bearish"
                ui.label(f"MACD {macd_trend}")

            ui.separator()

            scores = data["scores"]
            for label, key in [("Technical", "technical"), ("Fundamental", "fundamental"), ("AI Score", "overall")]:
                val = scores.get(key)
                with ui.row().classes("items-center gap-2"):
                    ui.label(f"{label}").classes("w-32")
                    ui.linear_progress(value=(val or 0) / 100, color=score_color(val)).classes("w-48")
                    ui.label(f"{val}")

            ui.separator()
            ui.label(f"{view_emoji(data['ai_view'])} AI 觀點：{data['ai_view']}").classes("text-lg font-semibold")

            with ui.row().classes("gap-8 w-full"):
                with ui.column():
                    ui.label("主要原因").classes("font-bold")
                    for r in data["reasons"]:
                        ui.label(f"✓ {r}")
                with ui.column():
                    ui.label("風險").classes("font-bold")
                    for r in data["risks"]:
                        ui.label(f"⚠ {r}")

            ui.separator()
            ui.label("回測績效 (MA20>MA60 + RSI>50 + 法人買超)").classes("font-bold")
            bt = data["backtest"]
            with ui.row().classes("gap-6"):
                ui.label(f"總報酬 {bt['total_return']}%")
                ui.label(f"勝率 {bt['win_rate']}%")
                ui.label(f"最大回撤 {bt['max_drawdown']}%")
                ui.label(f"Sharpe {bt['sharpe_ratio']}")

            if data.get("equity_curve"):
                dates = [p["date"] for p in data["equity_curve"]]
                equity = [p["equity"] for p in data["equity_curve"]]
                ui.echart({
                    "xAxis": {"type": "category", "data": dates, "show": False},
                    "yAxis": {"type": "value"},
                    "series": [{"type": "line", "data": equity, "smooth": True}],
                }).classes("w-full h-64")

            ui.label("⚠️ 本報告僅供研究參考，非投資建議。").classes("text-xs text-gray-500")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="台股 AI Dashboard", port=8080, reload=False)
