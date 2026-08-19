from __future__ import annotations

from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from config import SUPABASE_KEY, SUPABASE_URL, env_ready


class DatabaseError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_client() -> Client:
    if not env_ready():
        raise DatabaseError(
            "Missing SUPABASE_URL or SUPABASE_KEY. Copy .env.example to .env and fill in your keys."
        )
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _data(response: Any) -> list[dict[str, Any]]:
    rows = getattr(response, "data", None)
    if rows is None:
        return []
    return rows if isinstance(rows, list) else [rows]


def select_rows(
    table: str,
    *,
    filters: dict[str, Any] | None = None,
    order: str | None = None,
    desc: bool = False,
    limit: int | None = None,
    gte: dict[str, Any] | None = None,
    lt: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    query = get_client().table(table).select("*")
    for key, value in (filters or {}).items():
        query = query.eq(key, value)
    for key, value in (gte or {}).items():
        query = query.gte(key, value)
    for key, value in (lt or {}).items():
        query = query.lt(key, value)
    if order:
        query = query.order(order, desc=desc)
    if limit:
        query = query.limit(limit)
    return _data(query.execute())


def insert_row(table: str, payload: dict[str, Any]) -> dict[str, Any]:
    rows = _data(get_client().table(table).insert(payload).execute())
    if not rows:
        raise DatabaseError(f"Insert into {table} returned no data.")
    return rows[0]


def update_rows(table: str, payload: dict[str, Any], **filters: Any) -> list[dict[str, Any]]:
    query = get_client().table(table).update(payload)
    for key, value in filters.items():
        query = query.eq(key, value)
    return _data(query.execute())


def upsert_row(
    table: str,
    payload: dict[str, Any],
    *,
    on_conflict: str,
) -> dict[str, Any]:
    rows = _data(
        get_client()
        .table(table)
        .upsert(payload, on_conflict=on_conflict)
        .execute()
    )
    if not rows:
        raise DatabaseError(f"Upsert into {table} returned no data.")
    return rows[0]


def delete_rows(table: str, **filters: Any) -> list[dict[str, Any]]:
    query = get_client().table(table).delete()
    for key, value in filters.items():
        query = query.eq(key, value)
    return _data(query.execute())
