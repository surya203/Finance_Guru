from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip() or None
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "").strip() or None

CURRENCY = "INR"
CURRENCY_SYMBOL = "₹"

CATEGORIES = [
    "Food",
    "Rent",
    "Transport",
    "Education",
    "Entertainment",
    "Shopping",
    "Health",
    "Utilities",
    "Subscriptions",
    "Other",
]


def env_ready() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def llm_ready() -> bool:
    return bool(OPENAI_API_KEY)
