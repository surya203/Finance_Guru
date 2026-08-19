from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from modules.budgets import compare_budget_vs_actual, total_budget
from modules.expenses import get_transactions, spending_by_category, total_spending, txn_date
from modules.goals import enrich_goal, get_goals
from modules.users import display_name, get_user
from utils import format_inr, month_label, to_float

CHART_COLORS = ["#3DDC97", "#5B8DEF", "#F4B942", "#F07167", "#9B5DE5", "#00BBF9", "#FEE440", "#00F5D4"]


def render_dashboard(user_id: str) -> None:
    user = get_user(user_id) or {}
    income = to_float(user.get("monthly_income"))
    spent = total_spending(user_id)
    budget = total_budget(user_id)
    remaining = budget - spent
    leftover_income = income - spent
    goals = [enrich_goal(g) for g in get_goals(user_id)]
    by_category = spending_by_category(user_id)
    comparisons = compare_budget_vs_actual(user_id)
    transactions = get_transactions(user_id, limit=8)

    st.title("Dashboard")
    st.caption(f"{month_label()} · {display_name(user)}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Spent this month", format_inr(spent), help="Sum of all expenses this month")
    c2.metric("Budget remaining", format_inr(remaining))
    c3.metric("Income left", format_inr(leftover_income))
    c4.metric("Active goals", str(len(goals)))

    left, right = st.columns((1.1, 1))
    with left:
        st.subheader("Category breakdown")
        if by_category:
            df = pd.DataFrame(
                {"Category": list(by_category.keys()), "Amount": list(by_category.values())}
            )
            fig = px.pie(
                df,
                names="Category",
                values="Amount",
                hole=0.45,
                color_discrete_sequence=CHART_COLORS,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                legend_title_text="",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add an expense to see your spending split.")

    with right:
        st.subheader("Budget vs actual")
        budgeted = [row for row in comparisons if row["limit"] > 0]
        if budgeted:
            df = pd.DataFrame(budgeted)
            long = df.melt(
                id_vars="category",
                value_vars=["limit", "spent"],
                var_name="Type",
                value_name="Amount",
            )
            long["Type"] = long["Type"].map({"limit": "Budget", "spent": "Spent"})
            fig = px.bar(
                long,
                x="category",
                y="Amount",
                color="Type",
                barmode="group",
                color_discrete_map={"Budget": "#5B8DEF", "Spent": "#3DDC97"},
            )
            fig.update_layout(
                xaxis_title="",
                yaxis_title="₹",
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                legend_title_text="",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Set category budgets to compare against spending.")

    st.subheader("Recent expenses")
    if transactions:
        table = pd.DataFrame(
            [
                {
                    "Date": txn_date(row),
                    "Category": row.get("category"),
                    "Amount": format_inr(row.get("amount")),
                    "Description": row.get("description") or "—",
                }
                for row in transactions
            ]
        )
        st.dataframe(table, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions yet. Add your first expense from the Expenses page.")
