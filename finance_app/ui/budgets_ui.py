from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from config import CATEGORIES
from modules.budgets import compare_budget_vs_actual, set_budget, total_budget
from modules.expenses import total_spending
from utils import format_inr, month_label


def render_budgets(user_id: str) -> None:
    st.title("Budgets")
    st.caption(f"Set monthly limits by category for {month_label()}.")

    spent = total_spending(user_id)
    budget_total = total_budget(user_id)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total budget", format_inr(budget_total))
    c2.metric("Spent", format_inr(spent))
    c3.metric("Remaining", format_inr(budget_total - spent))

    with st.form("set_budget"):
        col1, col2 = st.columns(2)
        category = col1.selectbox("Category", CATEGORIES)
        limit = col2.number_input("Monthly limit (₹)", min_value=0.0, step=500.0, format="%.2f")
        saved = st.form_submit_button("Save budget", type="primary", use_container_width=True)
        if saved:
            set_budget(user_id, category, limit, date.today())
            st.success(f"{category} budget set to {format_inr(limit)}.")
            st.rerun()

    rows = compare_budget_vs_actual(user_id)
    if not rows:
        st.info("No budgets or expenses yet.")
        return

    st.subheader("Usage vs limits")
    for row in rows:
        label = f"{row['category']} · {format_inr(row['spent'])} of {format_inr(row['limit'])}"
        if row["limit"] <= 0:
            st.caption(f"{row['category']} has spending but no budget yet ({format_inr(row['spent'])}).")
            continue
        ratio = min(1.0, row["spent"] / row["limit"]) if row["limit"] else 0
        st.progress(ratio, text=label)
        if row["over"]:
            st.warning(f"Overspent {row['category']} by {format_inr(abs(row['remaining']))}.")

    table = pd.DataFrame(
        [
            {
                "Category": row["category"],
                "Budget": format_inr(row["limit"]),
                "Spent": format_inr(row["spent"]),
                "Remaining": format_inr(row["remaining"]),
                "Used": f"{row['pct_used']:.0f}%",
            }
            for row in rows
        ]
    )
    st.dataframe(table, use_container_width=True, hide_index=True)
