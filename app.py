"""Application entry point for the Streamlit banking assistant."""

import os

import streamlit as st

from views.chat_view import render_chat


def _load_streamlit_secret() -> None:
	"""Make the Streamlit Cloud secret available to the existing service layer."""
	if os.getenv("GROQ_API_KEY"):
		return
	try:
		groq_api_key = st.secrets.get("GROQ_API_KEY")
	except (FileNotFoundError, KeyError):
		groq_api_key = None
	if groq_api_key:
		os.environ["GROQ_API_KEY"] = str(groq_api_key)


_load_streamlit_secret()


render_chat()
