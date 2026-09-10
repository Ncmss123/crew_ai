"""Controller for chat requests and presentation-safe error messages."""

from __future__ import annotations

from services.banking_service import run_banking_crew


def handle_chat_request(prompt: str) -> str:
    """Run one chat request and translate expected failures for the view."""
    try:
        return run_banking_crew(prompt)
    except Exception as error:
        message = str(error).lower()
        if "invalid api key" in message or "invalid_api_key" in message:
            return "The Groq API key is invalid or expired. Replace GROQ_API_KEY in .env with a current Groq key and restart Streamlit."
        if "429" in message or "rate limit" in message or "too many requests" in message:
            return "The banking service is temporarily busy after several retries. Please wait a moment and try again."
        if "groq_api_key" in message:
            return "The demo is not configured with a Groq API key. Set GROQ_API_KEY and restart Streamlit."
        raise
