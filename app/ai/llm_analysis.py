"""
⑨⑩ LLM 整合分析、產生 AI 投資研究報告 (Slide 09-10)

有設定 ANTHROPIC_API_KEY 時呼叫 Anthropic API 產生 JSON 分析；
沒有設定時走 rule-based fallback，確保 Demo 一定能正常運作，
且回傳格式與 LLM 版本一致，方便前端/Dashboard 不需要判斷兩種情況。
"""
from __future__ import annotations

import json
from typing import Any, Dict

from app.ai.prompts import SYSTEM_PROMPT, build_user_prompt
from app.config import settings


def _rule_based_fallback(context: Dict[str, Any]) -> Dict[str, Any]:
    tech = context.get("technical_score", 50)
    fund = context.get("fundamental_score", 50)
    news_score = 50 if not context.get("news_titles") else 60
    overall = round(tech * 0.4 + fund * 0.4 + news_score * 0.2, 1)

    if overall >= 70:
        view = "偏多"
    elif overall <= 40:
        view = "偏空"
    else:
        view = "中立"

    reasons, risks = [], []
    if context.get("revenue_yoy", 0) and context["revenue_yoy"] > 0:
        reasons.append("營收年增率為正，成長動能存在")
    if context.get("foreign_net_recent", 0) and context["foreign_net_recent"] > 0:
        reasons.append("近期外資站在買方")
    if tech >= 70:
        reasons.append("技術面呈多頭排列")
    if not reasons:
        reasons.append("目前技術面與基本面數據中性，無明顯偏多訊號")

    if context.get("rsi14", 50) and context["rsi14"] > 75:
        risks.append("RSI 偏高，短線可能過熱")
    if context.get("per") and context["per"] > 30:
        risks.append("本益比偏高，估值風險需留意")
    if not risks:
        risks.append("需留意大盤系統性風險與總體經濟變數")

    return {
        "view": view,
        "news_score": news_score,
        "overall_score": overall,
        "reasons": reasons[:5],
        "risks": risks[:5],
        "summary": (
            f"{context.get('stock_id')} 綜合評分 {overall} 分，技術面 {tech} 分、"
            f"基本面 {fund} 分。目前研判為「{view}」，"
            "此為規則式 fallback 分析結果 (未設定 LLM API Key)，僅供研究參考，非投資建議。"
        ),
        "engine": "rule-based-fallback",
    }


def generate_investment_report(context: Dict[str, Any]) -> Dict[str, Any]:
    """context 需包含 technical_score / fundamental_score / 各項指標與新聞標題。"""
    if not settings.ANTHROPIC_API_KEY:
        return _rule_based_fallback(context)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(context)}],
        )
        text = "".join(block.text for block in message.content if block.type == "text").strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        result["engine"] = f"anthropic:{settings.ANTHROPIC_MODEL}"
        return result
    except Exception as exc:  # noqa: BLE001
        print(f"[LLM] 呼叫 Anthropic API 失敗，改用 rule-based fallback：{exc}")
        return _rule_based_fallback(context)
