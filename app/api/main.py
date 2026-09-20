"""
FastAPI 主程式 (Slide 04 系統架構 / Demo 流程 ①~⑬)

    POST /analyze/{stock_id}   → 跑完整流程並回傳 Dashboard 用 JSON
    GET  /stocks/{stock_id}/latest → 讀取最近一次分析結果 (免重新擷取)

實際的擷取/計分/LLM/回測邏輯都在 app/pipeline.py，
方便 Gradio Demo (app/ai_demo/gradio_app.py) 共用同一套邏輯。
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.models import AIAnalysis, Stock
from app.pipeline import run_full_analysis

app = FastAPI(title="Python AI 財經交易實戰 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/")
def root():
    return {"service": "twstock-ai-platform", "status": "ok"}


@app.post("/analyze/{stock_id}")
def analyze(stock_id: str, stock_name: Optional[str] = None, notify: bool = True,
            db: Session = Depends(get_db)):
    try:
        return run_full_analysis(stock_id, stock_name=stock_name, notify=notify, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/stocks/{stock_id}/latest")
def latest_analysis(stock_id: str, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="尚未分析過此股票，請先呼叫 /analyze/{stock_id}")
    ai_record = (
        db.query(AIAnalysis).filter(AIAnalysis.stock_id == stock.id)
        .order_by(AIAnalysis.created_at.desc()).first()
    )
    if not ai_record:
        raise HTTPException(status_code=404, detail="尚無分析紀錄")
    return {
        "stock_id": stock_id,
        "stock_name": stock.name,
        "technical_score": ai_record.technical_score,
        "fundamental_score": ai_record.fundamental_score,
        "news_score": ai_record.news_score,
        "overall_score": ai_record.overall_score,
        "view": ai_record.view,
        "reasons": json.loads(ai_record.reasons or "[]"),
        "risks": json.loads(ai_record.risks or "[]"),
        "report_text": ai_record.report_text,
        "created_at": ai_record.created_at.isoformat(),
    }
