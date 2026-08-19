from __future__ import annotations

import json
from datetime import date
from typing import Any

from config import llm_ready
from modules.budgets import compare_budget_vs_actual, total_budget
from modules.expenses import get_transactions, spending_by_category, total_spending, txn_date
from modules.goals import enrich_goal, get_goals
from modules.users import display_name, get_user
from services import db
from services.llm import complete, load_prompt
from utils import format_inr, month_label, parse_date, to_float


def financial_snapshot(user_id: str, month: date | None = None) -> dict[str, Any]:
    user = get_user(user_id) or {}
    spent_map = spending_by_category(user_id, month)
    comparisons = compare_budget_vs_actual(user_id, month)
    goals = [enrich_goal(goal) for goal in get_goals(user_id)]
    recent = get_transactions(user_id, month=month, limit=12)
    income = to_float(user.get("monthly_income"))
    spent = total_spending(user_id, month)
    budget = total_budget(user_id, month)
    return {
        "user": {
            "id": user_id,
            "name": display_name(user) if user else "there",
            "monthly_income": income,
        },
        "month": month_label(month),
        "totals": {
            "income": income,
            "spent": spent,
            "budget": budget,
            "remaining_budget": budget - spent,
            "unspent_income": income - spent,
        },
        "by_category": spent_map,
        "budgets": comparisons,
        "goals": [
            {
                "name": g["name"],
                "target": g["target_amount"],
                "saved": g["current_amount"],
                "progress_pct": round(g["progress_pct"], 1),
                "monthly_needed": round(g["monthly_needed"], 0),
                "remaining_months": g["remaining_months"],
            }
            for g in goals
        ],
        "recent_transactions": [
            {
                "date": txn_date(row),
                "category": row.get("category"),
                "amount": to_float(row.get("amount")),
                "description": row.get("description") or "",
            }
            for row in recent
        ],
    }


def snapshot_text(snapshot: dict[str, Any]) -> str:
    totals = snapshot["totals"]
    lines = [
        f"User: {snapshot['user']['name']}",
        f"Month: {snapshot['month']}",
        f"Monthly income: {format_inr(totals['income'])}",
        f"Spent this month: {format_inr(totals['spent'])}",
        f"Total budget: {format_inr(totals['budget'])}",
        f"Budget remaining: {format_inr(totals['remaining_budget'])}",
        "",
        "Spending by category:",
    ]
    if snapshot["by_category"]:
        for category, amount in snapshot["by_category"].items():
            share = (amount / totals["spent"] * 100) if totals["spent"] else 0
            lines.append(f"- {category}: {format_inr(amount)} ({share:.0f}% of spend)")
    else:
        lines.append("- No expenses recorded this month.")

    lines.append("")
    lines.append("Budgets vs actual:")
    if snapshot["budgets"]:
        for row in snapshot["budgets"]:
            status = "OVER" if row["over"] else f"{row['pct_used']:.0f}% used"
            lines.append(
                f"- {row['category']}: spent {format_inr(row['spent'])} of "
                f"{format_inr(row['limit'])} ({status})"
            )
    else:
        lines.append("- No budgets set.")

    lines.append("")
    lines.append("Goals:")
    if snapshot["goals"]:
        for goal in snapshot["goals"]:
            lines.append(
                f"- {goal['name']}: {format_inr(goal['saved'])} / {format_inr(goal['target'])} "
                f"({goal['progress_pct']}%). Needs about {format_inr(goal['monthly_needed'])}/month."
            )
    else:
        lines.append("- No savings goals yet.")

    lines.append("")
    lines.append("Recent transactions:")
    if snapshot["recent_transactions"]:
        for txn in snapshot["recent_transactions"]:
            lines.append(
                f"- {txn['date']} | {txn['category']} | {format_inr(txn['amount'])} | {txn['description']}"
            )
    else:
        lines.append("- None")
    return "\n".join(lines)


def _heuristic_insights(snapshot: dict[str, Any]) -> list[dict[str, str]]:
    insights: list[dict[str, str]] = []
    totals = snapshot["totals"]
    spent = totals["spent"]
    income = totals["income"]

    for row in snapshot["budgets"]:
        if row["over"]:
            over_by = row["spent"] - row["limit"]
            insights.append(
                {
                    "type": "overspending",
                    "content": (
                        f"You overspent on {row['category']} by {format_inr(over_by)} this month. "
                        f"Pause non-essential {row['category'].lower()} spends for the rest of the month."
                    ),
                }
            )
        elif row["limit"] and row["pct_used"] >= 80:
            insights.append(
                {
                    "type": "budget",
                    "content": (
                        f"{row['category']} is at {row['pct_used']:.0f}% of its budget. "
                        f"You have {format_inr(row['remaining'])} left."
                    ),
                }
            )

    if spent and snapshot["by_category"]:
        top_category, top_amount = next(iter(snapshot["by_category"].items()))
        share = top_amount / spent * 100
        if share >= 35:
            target_share = 25
            save = top_amount - (spent * target_share / 100)
            insights.append(
                {
                    "type": "saving",
                    "content": (
                        f"You spent {share:.0f}% on {top_category} this month. "
                        f"Try bringing it closer to {target_share:.0f}% to save about {format_inr(save)}."
                    ),
                }
            )

    if income:
        leftover = income - spent
        insights.append(
            {
                "type": "saving",
                "content": (
                    f"After expenses you have {format_inr(leftover)} of income left. "
                    "Move at least 20% of leftover money into a savings goal this week."
                ),
            }
        )
    elif not spent:
        insights.append(
            {
                "type": "budget",
                "content": "Add this month's expenses and a monthly income so I can give you personalised advice.",
            }
        )

    if snapshot["goals"]:
        goal = snapshot["goals"][0]
        insights.append(
            {
                "type": "goal",
                "content": (
                    f"{goal['name']} needs about {format_inr(goal['monthly_needed'])} per month "
                    f"to stay on track over the next {goal['remaining_months']} months."
                ),
            }
        )

    return insights[:5] or [
        {
            "type": "budget",
            "content": "Start by adding a few expenses and category budgets. I will then flag overspending and savings ideas.",
        }
    ]


def _parse_llm_insights(raw: str) -> list[dict[str, str]]:
    data = json.loads(raw)
    items = data.get("insights") if isinstance(data, dict) else data
    parsed: list[dict[str, str]] = []
    allowed = {"overspending", "saving", "budget", "goal"}
    for item in items or []:
        insight_type = str(item.get("type") or "budget").lower().strip()
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        if insight_type not in allowed:
            insight_type = "budget"
        parsed.append({"type": insight_type, "content": content})
    return parsed


def get_insights(user_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
    return db.select_rows(
        "ai_insights",
        filters={"user_id": user_id},
        order="created_at",
        desc=True,
        limit=limit,
    )


def insights_generated_today(user_id: str) -> bool:
    today = date.today().isoformat()
    for row in get_insights(user_id, limit=8):
        created = parse_date(row.get("created_at"))
        if created and created.isoformat() == today:
            return True
    return False


def store_insights(user_id: str, insights: list[dict[str, str]]) -> list[dict[str, Any]]:
    saved: list[dict[str, Any]] = []
    for item in insights:
        saved.append(
            db.insert_row(
                "ai_insights",
                {
                    "user_id": user_id,
                    "insight_type": item["type"],
                    "insight_text": item["content"],
                    "metadata": {"month": month_label()},
                },
            )
        )
    return saved


def generate_insights(user_id: str, *, force: bool = False) -> list[dict[str, Any]]:
    if not force and insights_generated_today(user_id):
        return get_insights(user_id)

    snapshot = financial_snapshot(user_id)
    insights: list[dict[str, str]]
    if llm_ready():
        try:
            raw = complete(
                system=load_prompt("insight_prompt.txt"),
                user=snapshot_text(snapshot),
                temperature=0.3,
                json_mode=True,
            )
            insights = _parse_llm_insights(raw) or _heuristic_insights(snapshot)
        except Exception:
            insights = _heuristic_insights(snapshot)
    else:
        insights = _heuristic_insights(snapshot)

    store_insights(user_id, insights)
    return get_insights(user_id)
