from __future__ import annotations

import streamlit as st

from config import llm_ready
from modules.chat import ask, get_history


def render_chat(user_id: str) -> None:
    st.title("Chat Assistant")
    st.caption("Ask about spending, budgets, or goals. Answers use your saved data.")

    if not llm_ready():
        st.warning("OPENAI_API_KEY is missing. The assistant will use short rule-based replies until you add a key.")

    history = get_history(user_id, limit=50)
    for row in history:
        user_message = (row.get("user_message") or "").strip()
        ai_response = (row.get("ai_response") or "").strip()
        if user_message:
            with st.chat_message("user"):
                st.write(user_message)
        if ai_response:
            with st.chat_message("assistant"):
                st.write(ai_response)

    question = st.chat_input("How much did I spend on food? Can I still hit my savings goal?")
    if question:
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking with your numbers…"):
                reply = ask(user_id, question)
            st.write(reply.get("ai_response", ""))
