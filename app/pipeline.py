"""
共用的「單股全流程分析」pipeline，抽出來讓 FastAPI (app/api/main.py) 與
Gradio AI Demo (app/ai_demo/gradio_app.py) 共用同一套邏輯，
避免兩邊維護兩份重複程式碼，也方便 HF Spaces 上 Gradio 獨立運作 (不依賴 Render 上的 API)。
"""
from __future__ import annotations

import json
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.ai.llm_analysis import generate_investment_report
from app.backtest.engine import run_backtest
from app.data_sources import finmind, mops, news
from app.database import SessionLocal, init_db
from app.models import (
    AIAnalysis, BacktestResult, Financial, Indicator, Institutional, News, Price, Revenue, Stock
)
from app.notify.telegram_bot import build_signal_message, send_message
from app.quant.fundamental_score import score_fundamental
from app.quant.indicators import compute_all_indicators
from app.quant.technical_score import score_technical


def get_or_create_stock(db: Session, stock_id: str, stock_name: Optional[str] = None) -> Stock:
    stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
    if not stock:
        stock = Stock(stock_id=stock_id, name=stock_name or stock_id, market="TWSE")
        db.add(stock)
        db.commit()
        db.refresh(stock)
    elif stock_name and stock.name != stock_name:
        stock.name = stock_name
        db.commit()
    return stock


def _upsert(db: Session, model, stock_id: int, df: pd.DataFrame, field_map: dict) -> None:
    if df.empty:
        return
    existing_dates = {d for (d,) in db.query(model.date).filter(model.stock_id == stock_id).all()}
    rows = [
        model(stock_id=stock_id, **{k: getattr(r, v) for k, v in field_map.items()})
        for r in df.itertuples()
        if r.date not in existing_dates
    ]
    if rows:
        db.bulk_save_objects(rows)
        db.commit()


def run_full_analysis(
    stock_id: str,
    stock_name: Optional[str] = None,
    notify: bool = False,
    db: Optional[Session] = None,
) -> dict:
    """
    Demo 流程 ①~⑬ 的完整實作，回傳一份可直接餵給 Dashboard / Gradio 顯示的 dict。
    db=None 時會自行開關一個 session (方便 Gradio / CLI 獨立呼叫)。
    """
    owns_session = db is None
    if owns_session:
        init_db()
        db = SessionLocal()

    try:
        stock = get_or_create_stock(db, stock_id, stock_name)
        start_date = finmind.default_start_date(years=2)

        # ① ② 股價 + 成交量
        price_df = finmind.fetch_price(stock_id, start_date)
        if price_df.empty:
            raise ValueError(f"無法取得 {stock_id} 股價資料 (FinMind)，請確認代號或稍後再試。")
        _upsert(db, Price, stock.id, price_df,
                {"date": "date", "open": "open", "high": "high", "low": "low",
                 "close": "close", "volume": "volume"})

        # ③ 技術指標
        indicator_df = compute_all_indicators(price_df)

        # ④ 法人
        institutional_df = finmind.fetch_institutional(stock_id, start_date)
        _upsert(db, Institutional, stock.id, institutional_df,
                {"date": "date", "foreign_investors": "foreign_investors",
                 "investment_trust": "investment_trust", "dealer": "dealer"})
        foreign_net_recent = (
            institutional_df.sort_values("date")["foreign_investors"].tail(5).sum()
            if not institutional_df.empty else None
        )

        latest = indicator_df.iloc[-1]
        tech_score = score_technical(latest, foreign_net_recent)
        db.query(Indicator).filter(Indicator.stock_id == stock.id).delete()
        indicator_rows = [
            Indicator(
                stock_id=stock.id, date=r.date, ma5=r.ma5, ma20=r.ma20, ma60=r.ma60,
                rsi14=r.rsi14, macd=r.macd, macd_signal=r.macd_signal, macd_hist=r.macd_hist,
                k=r.k, d=r.d, bb_upper=r.bb_upper, bb_middle=r.bb_middle, bb_lower=r.bb_lower,
                atr14=r.atr14,
                technical_score=tech_score if i == len(indicator_df) - 1 else None,
            )
            for i, r in enumerate(indicator_df.itertuples())
        ]
        db.bulk_save_objects(indicator_rows)
        db.commit()

        # ⑤ 月營收
        revenue_df = finmind.fetch_monthly_revenue(stock_id, start_date)
        _upsert(db, Revenue, stock.id, revenue_df,
                {"date": "date", "revenue": "revenue", "revenue_yoy": "revenue_yoy",
                 "revenue_mom": "revenue_mom"})
        latest_revenue = revenue_df.iloc[-1] if not revenue_df.empty else None

        # ⑥ 財報
        financial_df = finmind.fetch_financial_statement(stock_id, start_date)
        _upsert(db, Financial, stock.id, financial_df,
                {"date": "date", "eps": "eps", "roe": "roe", "roa": "roa",
                 "gross_margin": "gross_margin", "operating_margin": "operating_margin"})
        latest_financial = financial_df.iloc[-1] if not financial_df.empty else None
        eps_trend_up = None
        if len(financial_df) >= 2 and "eps" in financial_df.columns:
            eps_trend_up = bool(financial_df["eps"].iloc[-1] > financial_df["eps"].iloc[-2])

        def _val(series, col):
            if series is None:
                return None
            v = series.get(col)
            return float(v) if v is not None and pd.notna(v) else None

        fundamental_score = score_fundamental(
            revenue_yoy=_val(latest_revenue, "revenue_yoy"),
            eps_trend_up=eps_trend_up,
            roe=_val(latest_financial, "roe"),
            roa=_val(latest_financial, "roa"),
            gross_margin=_val(latest_financial, "gross_margin"),
            operating_margin=_val(latest_financial, "operating_margin"),
        )

        # ⑦ MOPS 公告
        mops_announcements = mops.fetch_mops_announcements(stock_id)

        # ⑧ 新聞
        news_items = news.fetch_news(stock.name)
        if news_items:
            for item in news_items:
                db.add(News(stock_id=stock.id, published_at=item["published_at"],
                             title=item["title"], source=item["source"], url=item["url"]))
            db.commit()

        # ⑨⑩ LLM 整合分析 + AI 投資研究報告
        context = {
            "stock_id": stock_id,
            "stock_name": stock.name,
            "close": float(latest["close"]),
            "technical_score": tech_score,
            "fundamental_score": fundamental_score,
            "ma5": round(float(latest["ma5"]), 2),
            "ma20": round(float(latest["ma20"]), 2),
            "ma60": round(float(latest["ma60"]), 2),
            "rsi14": round(float(latest["rsi14"]), 2),
            "macd": round(float(latest["macd"]), 3),
            "macd_signal": round(float(latest["macd_signal"]), 3),
            "k": round(float(latest["k"]), 2),
            "d": round(float(latest["d"]), 2),
            "revenue_yoy": _val(latest_revenue, "revenue_yoy"),
            "eps": _val(latest_financial, "eps"),
            "roe": _val(latest_financial, "roe"),
            "roa": _val(latest_financial, "roa"),
            "gross_margin": _val(latest_financial, "gross_margin"),
            "operating_margin": _val(latest_financial, "operating_margin"),
            "foreign_net_recent": float(foreign_net_recent) if foreign_net_recent is not None else None,
            "news_titles": "\n".join(f"- {n['title']}" for n in news_items) if news_items else None,
        }
        ai_result = generate_investment_report(context)

        db.add(AIAnalysis(
            stock_id=stock.id,
            technical_score=tech_score,
            fundamental_score=fundamental_score,
            news_score=ai_result.get("news_score", 50),
            overall_score=ai_result.get("overall_score"),
            view=ai_result.get("view"),
            reasons=json.dumps(ai_result.get("reasons", []), ensure_ascii=False),
            risks=json.dumps(ai_result.get("risks", []), ensure_ascii=False),
            report_text=ai_result.get("summary", ""),
        ))
        db.commit()

        # ⑪ 回測策略
        backtest_result = run_backtest(indicator_df, institutional_df)
        db.add(BacktestResult(
            stock_id=stock.id,
            strategy_name=backtest_result["strategy_name"],
            start_date=backtest_result["start_date"],
            end_date=backtest_result["end_date"],
            total_return=backtest_result["total_return"],
            win_rate=backtest_result["win_rate"],
            max_drawdown=backtest_result["max_drawdown"],
            sharpe_ratio=backtest_result["sharpe_ratio"],
            trade_count=backtest_result["trade_count"],
            equity_curve_json=json.dumps(backtest_result["equity_curve"]),
        ))
        db.commit()

        # ⑫ Dashboard 顯示用 JSON
        response = {
            "stock_id": stock_id,
            "stock_name": stock.name,
            "price": {
                "close": context["close"], "ma5": context["ma5"], "ma20": context["ma20"],
                "ma60": context["ma60"], "rsi14": context["rsi14"], "macd": context["macd"],
                "k": context["k"], "d": context["d"],
            },
            "scores": {
                "technical": tech_score,
                "fundamental": fundamental_score,
                "news": ai_result.get("news_score", 50),
                "overall": ai_result.get("overall_score"),
            },
            "ai_view": ai_result.get("view"),
            "reasons": ai_result.get("reasons", []),
            "risks": ai_result.get("risks", []),
            "summary": ai_result.get("summary", ""),
            "engine": ai_result.get("engine"),
            "mops_announcements": mops_announcements,
            "news": news_items,
            "backtest": {k: v for k, v in backtest_result.items() if k != "equity_curve"},
            "equity_curve": backtest_result["equity_curve"],
        }

        # ⑬ Telegram 通知
        if notify:
            send_message(build_signal_message(stock_id, stock.name, ai_result))

        return response
    finally:
        if owns_session:
            db.close()
