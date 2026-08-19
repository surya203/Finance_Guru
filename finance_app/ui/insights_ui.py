from __future__ import annotations

import streamlit as st

from config import llm_ready
from services.insights import generate_insights, get_insights, insights_generated_today
from utils import parse_date

TYPE_LABELS = {
    "overspending": "Overspending",
    "saving": "Saving idea",
    "budget": "Budget",
    "goal": "Goal",
}


def render_insights(user_id: str) -> None:
    st.title("AI Insights")
    st.caption("Advice is generated from your expenses, budgets, and goals, then stored in the database.")

    if not llm_ready():
        st.warning("OPENAI_API_KEY is missing. Insights will use a simple local fallback until you add a key.")

    cached_today = insights_generated_today(user_id)
    col1, col2 = st.columns((3, 1))
    with col1:
        if cached_today:
            st.info("Today's insights are already saved. Generate again only if your data changed.")
    with col2:
        if st.button("Generate insights", type="primary", use_container_width=True):
            with st.spinner("Reading your numbers and writing advice…"):
                generate_insights(user_id, force=True)
            st.success("Insights saved.")
            st.rerun()

    rows = get_insights(user_id)
    if not rows:
        st.info("No insights yet. Add a few expenses, then generate.")
        return

    for row in rows:
        created = parse_date(row.get("created_at"))
        label = TYPE_LABELS.get(row.get("insight_type"), row.get("insight_type", "Insight"))
        with st.container(border=True):
            st.markdown(f"**{label}**")
            st.write(row.get("insight_text") or row.get("content") or "")
            if created:
                st.caption(created.strftime("%d %b %Y"))
