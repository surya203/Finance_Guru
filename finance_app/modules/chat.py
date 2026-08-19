from __future__ import annotations

from typing import Any

from config import llm_ready
from services import db
from services.insights import financial_snapshot, snapshot_text
from services.llm import complete, load_prompt


def get_history(user_id: str, *, limit: int = 40) -> list[dict[str, Any]]:
    rows = db.select_rows(
        "chat_history",
        filters={"user_id": user_id},
        order="created_at",
        desc=True,
        limit=limit,
    )
    return list(reversed(rows))


def save_turn(user_id: str, user_message: str, ai_response: str) -> dict[str, Any]:
    return db.insert_row(
        "chat_history",
        {
            "user_id": user_id,
            "user_message": user_message.strip(),
            "ai_response": ai_response.strip(),
        },
    )


def _history_text(history: list[dict[str, Any]], *, last_n: int = 8) -> str:
    lines: list[str] = []
    for row in history[-last_n:]:
        user_message = (row.get("user_message") or "").strip()
        ai_response = (row.get("ai_response") or "").strip()
        if user_message:
            lines.append(f"User: {user_message}")
        if ai_response:
            lines.append(f"Assistant: {ai_response}")
    return "\n".join(lines) if lines else "No earlier conversation."


def _fallback_reply(question: str, snapshot: dict[str, Any]) -> str:
    totals = snapshot["totals"]
    spent = totals["spent"]
    income = totals["income"]
    leftover = income - spent
    q = question.lower()
    if "save" in q or "saving" in q:
        return (
            f"This month you have spent {spent:,.0f} and have about {leftover:,.0f} of income left. "
            "Park a fixed amount (even ₹500–₹1000) into a goal as soon as money comes in."
        )
    if "budget" in q or "overspend" in q:
        overs = [row["category"] for row in snapshot["budgets"] if row["over"]]
        if overs:
            return f"You are over budget in {', '.join(overs)}. Cut those categories first before adding new spends."
        return "Set a monthly limit for your top 3 categories. That is usually enough to stop leaks."
    if "goal" in q:
        if snapshot["goals"]:
            goal = snapshot["goals"][0]
            return (
                f"{goal['name']} still needs about {goal['monthly_needed']:,.0f} per month. "
                "Treat that transfer like a bill."
            )
        return "Create one goal with a target amount and a deadline, then add money to it each payday."
    if income:
        return (
            f"You have spent {spent:,.0f} of {income:,.0f} income this month. "
            "Keep essentials first, then savings, then wants."
        )
    return "Add your income and a few expenses so I can answer with your real numbers."


def ask(user_id: str, question: str) -> dict[str, Any]:
    question = question.strip()
    snapshot = financial_snapshot(user_id)
    history = get_history(user_id, limit=16)

    if llm_ready():
        try:
            prompt = (
                snapshot_text(snapshot)
                + "\n\nRecent chat:\n"
                + _history_text(history)
                + "\n\nLatest question:\n"
                + question
            )
            reply = complete(
                system=load_prompt("chat_prompt.txt"),
                user=prompt,
                temperature=0.4,
            )
        except Exception:
            reply = _fallback_reply(question, snapshot)
    else:
        reply = _fallback_reply(question, snapshot)

    return save_turn(user_id, question, reply)
