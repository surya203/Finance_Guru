from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from config import CATEGORIES
from modules.expenses import add_transaction, delete_transaction, get_transactions, txn_date
from utils import format_inr, month_label


def render_expenses(user_id: str) -> None:
    st.title("Expenses")
    st.caption("Log every spend so the dashboard and AI insights stay accurate.")

    with st.form("add_expense", clear_on_submit=True):
        c1, c2 = st.columns(2)
        amount = c1.number_input("Amount (₹)", min_value=1.0, step=50.0, format="%.2f")
        category = c2.selectbox("Category", CATEGORIES)
        c3, c4 = st.columns(2)
        expense_date = c3.date_input("Date", value=date.today())
        description = c4.text_input("Description", placeholder="Lunch, metro card, rent…")
        submitted = st.form_submit_button("Add expense", type="primary", use_container_width=True)
        if submitted:
            add_transaction(user_id, amount, category, description, expense_date)
            st.success(f"Saved {format_inr(amount)} under {category}.")
            st.rerun()

    st.subheader(f"This month · {month_label()}")
    show_all = st.toggle("Show all transactions", value=False)
    rows = get_transactions(user_id, month=None if show_all else date.today(), limit=300)
    if not rows:
        st.info("No expenses yet.")
        return

    table = pd.DataFrame(
        [
            {
                "id": row["id"],
                "Date": txn_date(row),
                "Category": row.get("category"),
                "Amount": format_inr(row.get("amount")),
                "Description": row.get("description") or "—",
            }
            for row in rows
        ]
    )
    st.dataframe(table.drop(columns=["id"]), use_container_width=True, hide_index=True)

    with st.expander("Delete a transaction"):
        labels = {
            row["id"]: f"{txn_date(row)} · {row.get('category')} · {format_inr(row.get('amount'))}"
            for row in rows
        }
        chosen = st.selectbox("Transaction", options=list(labels), format_func=lambda key: labels[key])
        if st.button("Delete", type="secondary"):
            delete_transaction(chosen)
            st.success("Deleted.")
            st.rerun()
