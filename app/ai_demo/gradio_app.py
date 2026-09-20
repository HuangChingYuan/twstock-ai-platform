"""
⑨⑩ AI / LLM Demo (Slide 09-10) — Gradio 版本，適合部署到 Hugging Face Spaces。

直接呼叫 app.pipeline.run_full_analysis()，不依賴外部 FastAPI 服務，
因此可以獨立部署在 HF Spaces 上單獨展示「一支股票走完全流程」的 AI 分析 Demo。

啟動方式：
    python -m app.ai_demo.gradio_app
"""
import gradio as gr

from app.pipeline import run_full_analysis


def analyze_stock(stock_id: str, stock_name: str):
    if not stock_id.strip():
        return "請輸入股票代號", "", "", "", None

    try:
        result = run_full_analysis(stock_id.strip(), stock_name=stock_name.strip() or None, notify=False)
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ 分析失敗：{exc}", "", "", "", None

    scores = result["scores"]
    header = (
        f"## {result['stock_id']} {result['stock_name']}\n\n"
        f"**收盤價** {result['price']['close']}　"
        f"**RSI14** {result['price']['rsi14']}　"
        f"**MACD** {'多方' if result['price']['macd'] >= 0 else '空方'}\n\n"
        f"| Technical | Fundamental | News | Overall |\n"
        f"|---|---|---|---|\n"
        f"| {scores['technical']} | {scores['fundamental']} | {scores['news']} | **{scores['overall']}** |\n\n"
        f"### AI 觀點：{result['ai_view']}"
    )

    reasons_md = "\n".join(f"- ✓ {r}" for r in result["reasons"]) or "（無）"
    risks_md = "\n".join(f"- ⚠ {r}" for r in result["risks"]) or "（無）"

    bt = result["backtest"]
    backtest_md = (
        f"**策略**：{bt['strategy_name']}\n\n"
        f"- 總報酬：{bt['total_return']}%\n"
        f"- 勝率：{bt['win_rate']}%\n"
        f"- 最大回撤：{bt['max_drawdown']}%\n"
        f"- Sharpe：{bt['sharpe_ratio']}\n"
        f"- 交易次數：{bt['trade_count']}\n"
    )

    equity_plot = None
    if result.get("equity_curve"):
        import pandas as pd
        equity_plot = pd.DataFrame(result["equity_curve"])

    return header, reasons_md, risks_md, backtest_md, equity_plot


with gr.Blocks(title="台股 AI 投資研究 Demo") as demo:
    gr.Markdown("# 📊 Python AI 財經交易實戰 — AI 投資研究報告 Demo")
    gr.Markdown(
        "輸入台股代號，系統會自動走完「股價 → 技術指標 → 法人 → 營收 → 財報 → "
        "新聞 → LLM 整合分析 → 投資研究報告 → 回測」全流程。\n\n"
        "⚠️ 僅供研究與教學展示，不構成投資建議。"
    )

    with gr.Row():
        stock_id_input = gr.Textbox(label="股票代號", value="2330", scale=1)
        stock_name_input = gr.Textbox(label="股票名稱 (選填)", value="台積電", scale=1)
        run_btn = gr.Button("開始分析", variant="primary", scale=1)

    header_md = gr.Markdown()
    with gr.Row():
        reasons_out = gr.Markdown(label="主要原因")
        risks_out = gr.Markdown(label="風險")
    backtest_out = gr.Markdown(label="回測績效")
    equity_out = gr.LinePlot(x="date", y="equity", title="策略權益曲線", height=300)

    run_btn.click(
        analyze_stock,
        inputs=[stock_id_input, stock_name_input],
        outputs=[header_md, reasons_out, risks_out, backtest_out, equity_out],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
