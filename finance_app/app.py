from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from config import DEFAULT_USER_ID, env_ready, llm_ready
from modules.users import create_user, display_name, get_user, list_users, update_income
from ui.budgets_ui import render_budgets
from ui.chat_ui import render_chat
from ui.dashboard import render_dashboard
from ui.expenses_ui import render_expenses
from ui.goals_ui import render_goals
from ui.insights_ui import render_insights
from utils import format_inr, to_float

st.set_page_config(
    page_title="Finance Guru",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 0.8rem 1rem;
      }
      .block-container { padding-top: 1.4rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

PAGES = {
    "Dashboard": render_dashboard,
    "Expenses": render_expenses,
    "Budgets": render_budgets,
    "Goals": render_goals,
    "AI Insights": render_insights,
    "Chat Assistant": render_chat,
}


def _setup_screen() -> None:
    st.title("Finance Guru")
    st.subheader("Connect Supabase to start")
    st.markdown(
        """
1. Copy `.env.example` to `.env`.
2. Add `SUPABASE_URL` and `SUPABASE_KEY` from **Supabase → Project Settings → API**.
3. Add `OPENAI_API_KEY` for live AI insights and chat (optional for a local fallback).
4. Restart the app.
        """
    )


def _ensure_user() -> str | None:
    st.sidebar.title("Finance Guru")
    st.sidebar.caption("Personal money tracker for students and early professionals.")

    try:
        users = list_users()
    except Exception as exc:
        st.error(f"Could not reach Supabase: {exc}")
        st.info("Check SUPABASE_URL / SUPABASE_KEY. If Row Level Security is on, add open policies or use the service role key.")
        return None

    if not users:
        st.sidebar.info("Create your first profile to begin.")
        with st.sidebar.form("first_user"):
            name = st.text_input("Your name")
            email = st.text_input("Email")
            income = st.number_input("Monthly income (₹)", min_value=0.0, step=1000.0)
            if st.form_submit_button("Create profile", type="primary"):
                if not name.strip() or not email.strip():
                    st.sidebar.error("Name and email are required.")
                else:
                    try:
                        user = create_user(name, income, email)
                        st.session_state["user_id"] = user["id"]
                        st.rerun()
                    except Exception as exc:
                        st.sidebar.error(f"Could not create profile: {exc}")
        st.title("Welcome")
        st.write("Add a name, email, and monthly income in the sidebar. After that you can track expenses, budgets, and goals.")
        return None

    user_ids = [row["id"] for row in users]
    labels = {
        row["id"]: f"{display_name(row)} · {format_inr(row.get('monthly_income'))}"
        for row in users
    }

    current = st.session_state.get("user_id") or DEFAULT_USER_ID
    if current not in user_ids:
        current = user_ids[0]
    current = st.sidebar.selectbox(
        "Active profile",
        options=user_ids,
        index=user_ids.index(current),
        format_func=lambda uid: labels.get(uid, uid),
    )
    st.session_state["user_id"] = current

    user = get_user(current) or {}
    with st.sidebar.expander("Update income"):
        new_income = st.number_input(
            "Monthly income (₹)",
            min_value=0.0,
            value=to_float(user.get("monthly_income")),
            step=1000.0,
            key="income_update",
        )
        if st.button("Save income"):
            update_income(current, new_income)
            st.rerun()

    with st.sidebar.expander("Add another profile"):
        with st.form("another_user"):
            name = st.text_input("Name", key="new_name")
            email = st.text_input("Email", key="new_email")
            income = st.number_input("Monthly income (₹)", min_value=0.0, step=1000.0, key="new_income")
            if st.form_submit_button("Create"):
                if name.strip() and email.strip():
                    try:
                        created = create_user(name, income, email)
                        st.session_state["user_id"] = created["id"]
                        st.rerun()
                    except Exception as exc:
                        st.sidebar.error(f"Could not create profile: {exc}")

    st.sidebar.divider()
    if llm_ready():
        st.sidebar.success("AI connected")
    else:
        st.sidebar.warning("AI fallback mode")

    page = st.sidebar.radio("Go to", list(PAGES), label_visibility="collapsed")
    st.session_state["page"] = page
    return current


def main() -> None:
    if not env_ready():
        _setup_screen()
        return

    user_id = _ensure_user()
    if not user_id:
        return

    page = st.session_state.get("page", "Dashboard")
    PAGES[page](user_id)


main()
