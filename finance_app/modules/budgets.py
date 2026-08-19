from __future__ import annotations

from datetime import date
from typing import Any

from modules.expenses import spending_by_category
from services import db
from utils import to_float


def set_budget(
    user_id: str,
    category: str,
    monthly_limit: float,
    month: date | None = None,
) -> dict[str, Any]:
    _ = month
    payload = {
        "user_id": user_id,
        "category": category,
        "monthly_limit": round(to_float(monthly_limit), 2),
    }
    existing = db.select_rows(
        "budgets",
        filters={"user_id": user_id, "category": category},
        limit=1,
    )
    if existing:
        rows = db.update_rows("budgets", {"monthly_limit": payload["monthly_limit"]}, id=existing[0]["id"])
        return rows[0] if rows else existing[0]
    return db.insert_row("budgets", payload)


def get_budgets(user_id: str, month: date | None = None) -> list[dict[str, Any]]:
    _ = month
    return db.select_rows(
        "budgets",
        filters={"user_id": user_id},
        order="category",
    )


def compare_budget_vs_actual(user_id: str, month: date | None = None) -> list[dict[str, Any]]:
    spent = spending_by_category(user_id, month)
    budgets = get_budgets(user_id)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    for budget in budgets:
        category = budget["category"]
        seen.add(category)
        limit = to_float(budget.get("monthly_limit"))
        actual = spent.get(category, 0.0)
        remaining = limit - actual
        rows.append(
            {
                "category": category,
                "limit": limit,
                "spent": actual,
                "remaining": remaining,
                "pct_used": (actual / limit * 100) if limit else 0.0,
                "over": actual > limit and limit > 0,
            }
        )

    for category, actual in spent.items():
        if category in seen:
            continue
        rows.append(
            {
                "category": category,
                "limit": 0.0,
                "spent": actual,
                "remaining": -actual,
                "pct_used": 0.0,
                "over": False,
            }
        )

    rows.sort(key=lambda item: item["spent"], reverse=True)
    return rows


def total_budget(user_id: str, month: date | None = None) -> float:
    return round(sum(to_float(row.get("monthly_limit")) for row in get_budgets(user_id, month)), 2)
