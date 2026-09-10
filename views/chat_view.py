"""Streamlit view for the banking assistant."""

from __future__ import annotations

import streamlit as st

from controllers.chat_controller import handle_chat_request
from models.database import DATABASE_PATH, initialize_database


def render_chat() -> None:
    """Render the banking chat page and dispatch submitted prompts."""
    st.set_page_config(page_title="Northstar Banking Assistant", page_icon="[bank]", layout="centered")
    if not DATABASE_PATH.exists():
        initialize_database()

    st.title("Northstar Banking Assistant")
    st.caption("Demo mode · user USER-1001 · account ACCT-1001")
    st.info("Ask about your balance, recent transactions, spending, or a service request.")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello. I can help with account details, transactions, spending analysis, and service requests.",
            }
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("How much did I spend on groceries?")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Routing your request to the right specialist..."):
            try:
                answer = handle_chat_request(prompt)
            except Exception as error:
                answer = "I could not complete that request. Please try again with a shorter banking question."
                st.error(f"Technical detail: {error}")
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
