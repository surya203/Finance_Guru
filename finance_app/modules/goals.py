from __future__ import annotations

from datetime import date
from typing import Any

from services import db
from utils import months_between, parse_date, to_float


def create_goal(
    user_id: str,
    name: str,
    target_amount: float,
    duration_months: int,
    current_amount: float = 0.0,
) -> dict[str, Any]:
    return db.insert_row(
        "goals",
        {
            "user_id": user_id,
            "goal_name": name.strip(),
            "target_amount": round(to_float(target_amount), 2),
            "current_amount": round(to_float(current_amount), 2),
            "duration_months": int(duration_months),
            "start_date": date.today().isoformat(),
        },
    )


def get_goals(user_id: str) -> list[dict[str, Any]]:
    return db.select_rows("goals", filters={"user_id": user_id}, order="created_at", desc=True)


def update_progress(goal_id: str, current_amount: float) -> dict[str, Any] | None:
    rows = db.update_rows(
        "goals",
        {"current_amount": round(to_float(current_amount), 2)},
        id=goal_id,
    )
    return rows[0] if rows else None


def add_to_goal(goal_id: str, amount: float) -> dict[str, Any] | None:
    rows = db.select_rows("goals", filters={"id": goal_id}, limit=1)
    if not rows:
        return None
    current = to_float(rows[0].get("current_amount"))
    return update_progress(goal_id, current + to_float(amount))


def delete_goal(goal_id: str) -> None:
    db.delete_rows("goals", id=goal_id)


def enrich_goal(goal: dict[str, Any], today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    target = to_float(goal.get("target_amount"))
    current = to_float(goal.get("current_amount"))
    duration = int(goal.get("duration_months") or 1)
    started = parse_date(goal.get("start_date")) or parse_date(goal.get("created_at")) or today
    elapsed = months_between(started, today)
    remaining_months = max(1, duration - elapsed)
    remaining_amount = max(0.0, target - current)
    progress_pct = min(100.0, (current / target * 100) if target else 0.0)
    name = (goal.get("goal_name") or goal.get("name") or "Goal").strip()
    return {
        **goal,
        "name": name,
        "goal_name": name,
        "target_amount": target,
        "current_amount": current,
        "remaining_amount": remaining_amount,
        "progress_pct": progress_pct,
        "elapsed_months": elapsed,
        "remaining_months": remaining_months,
        "monthly_needed": remaining_amount / remaining_months,
        "completed": current >= target and target > 0,
    }
