from __future__ import annotations

import streamlit as st

from modules.goals import add_to_goal, create_goal, delete_goal, enrich_goal, get_goals, update_progress
from utils import format_inr


def render_goals(user_id: str) -> None:
    st.title("Goals")
    st.caption("Name a target, set a timeline, and track how much you have saved.")

    with st.form("create_goal", clear_on_submit=True):
        name = st.text_input("Goal name", placeholder="Emergency fund, laptop, trip…")
        c1, c2, c3 = st.columns(3)
        target = c1.number_input("Target amount (₹)", min_value=1.0, step=1000.0, format="%.2f")
        duration = c2.number_input("Duration (months)", min_value=1, max_value=120, value=6, step=1)
        starting = c3.number_input("Already saved (₹)", min_value=0.0, step=500.0, format="%.2f")
        created = st.form_submit_button("Create goal", type="primary", use_container_width=True)
        if created:
            if not name.strip():
                st.error("Give the goal a name.")
            else:
                create_goal(user_id, name, target, int(duration), starting)
                st.success(f"Goal “{name.strip()}” created.")
                st.rerun()

    goals = [enrich_goal(g) for g in get_goals(user_id)]
    if not goals:
        st.info("No goals yet. Create one to start tracking progress.")
        return

    for goal in goals:
        with st.container(border=True):
            top, actions = st.columns((3, 1.2))
            with top:
                st.markdown(f"**{goal['name']}**")
                st.caption(
                    f"{format_inr(goal['current_amount'])} of {format_inr(goal['target_amount'])} · "
                    f"{goal['remaining_months']} months left · "
                    f"{format_inr(goal['monthly_needed'])}/month needed"
                )
                st.progress(min(1.0, goal["progress_pct"] / 100), text=f"{goal['progress_pct']:.0f}%")
            with actions:
                add_amt = st.number_input(
                    "Add ₹",
                    min_value=0.0,
                    step=100.0,
                    key=f"add_{goal['id']}",
                )
                if st.button("Add savings", key=f"btn_add_{goal['id']}", use_container_width=True):
                    if add_amt > 0:
                        add_to_goal(goal["id"], add_amt)
                        st.rerun()
                new_total = st.number_input(
                    "Set total saved",
                    min_value=0.0,
                    value=float(goal["current_amount"]),
                    step=100.0,
                    key=f"set_{goal['id']}",
                )
                if st.button("Update total", key=f"btn_set_{goal['id']}", use_container_width=True):
                    update_progress(goal["id"], new_total)
                    st.rerun()
                if st.button("Delete", key=f"btn_del_{goal['id']}", use_container_width=True):
                    delete_goal(goal["id"])
                    st.rerun()
