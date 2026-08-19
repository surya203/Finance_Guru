from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from config import CURRENCY_SYMBOL


def to_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def format_inr(amount: Any) -> str:
    value = to_float(amount)
    sign = "-" if value < 0 else ""
    return f"{sign}{CURRENCY_SYMBOL}{abs(value):,.0f}"


def month_start(when: date | None = None) -> date:
    when = when or date.today()
    return when.replace(day=1)


def next_month_start(when: date | None = None) -> date:
    start = month_start(when)
    if start.month == 12:
        return date(start.year + 1, 1, 1)
    return date(start.year, start.month + 1, 1)


def month_end(when: date | None = None) -> date:
    return next_month_start(when) - timedelta(days=1)


def month_label(when: date | None = None) -> str:
    return month_start(when).strftime("%B %Y")


def parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value)[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def months_between(start: date, end: date | None = None) -> int:
    end = end or date.today()
    return max(0, (end.year - start.year) * 12 + (end.month - start.month))
