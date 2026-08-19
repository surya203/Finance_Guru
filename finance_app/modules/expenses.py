from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from services import db
from utils import month_start, next_month_start, to_float


def add_transaction(
    user_id: str,
    amount: float,
    category: str,
    description: str,
    txn_date: date,
) -> dict[str, Any]:
    return db.insert_row(
        "transactions",
        {
            "user_id": user_id,
            "amount": round(to_float(amount), 2),
            "category": category,
            "description": (description or "").strip(),
            "transaction_date": txn_date.isoformat(),
        },
    )


def get_transactions(
    user_id: str,
    *,
    month: date | None = None,
    limit: int | None = 200,
) -> list[dict[str, Any]]:
    filters: dict[str, Any] = {"user_id": user_id}
    gte = lt = None
    if month is not None:
        start = month_start(month)
        gte = {"transaction_date": start.isoformat()}
        lt = {"transaction_date": next_month_start(start).isoformat()}
    return db.select_rows(
        "transactions",
        filters=filters,
        gte=gte,
        lt=lt,
        order="transaction_date",
        desc=True,
        limit=limit,
    )


def delete_transaction(transaction_id: str) -> None:
    db.delete_rows("transactions", id=transaction_id)


def txn_date(row: dict[str, Any]) -> str:
    value = row.get("transaction_date") or row.get("date") or ""
    return str(value)[:10]


def spending_by_category(user_id: str, month: date | None = None) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for row in get_transactions(user_id, month=month, limit=1000):
        totals[row.get("category") or "Other"] += to_float(row.get("amount"))
    return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))


def total_spending(user_id: str, month: date | None = None) -> float:
    return round(sum(spending_by_category(user_id, month).values()), 2)
