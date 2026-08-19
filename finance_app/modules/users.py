from __future__ import annotations

from typing import Any

from services import db
from utils import to_float


def display_name(user: dict[str, Any] | None) -> str:
    if not user:
        return "User"
    name = (user.get("full_name") or "").strip()
    return name or user.get("email") or "User"


def list_users() -> list[dict[str, Any]]:
    return db.select_rows("users", order="created_at", desc=True)


def get_user(user_id: str) -> dict[str, Any] | None:
    rows = db.select_rows("users", filters={"id": user_id}, limit=1)
    return rows[0] if rows else None


def create_user(
    name: str,
    monthly_income: float,
    email: str,
) -> dict[str, Any]:
    return db.insert_row(
        "users",
        {
            "full_name": name.strip(),
            "email": email.strip().lower(),
            "monthly_income": round(to_float(monthly_income), 2),
        },
    )


def update_income(user_id: str, monthly_income: float) -> dict[str, Any] | None:
    rows = db.update_rows(
        "users",
        {"monthly_income": round(to_float(monthly_income), 2)},
        id=user_id,
    )
    return rows[0] if rows else None
