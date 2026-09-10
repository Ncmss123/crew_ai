"""Mock MCP endpoints backed by the local SQLite banking dataset.

In production, these functions are the seam where MCP client calls would be
made. CrewAI tools expose the same contract to the specialized agents.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Callable, TypeVar

from crewai.tools import tool
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from models.database import DATABASE_PATH, initialize_database

T = TypeVar("T")


def _is_transient_error(error: BaseException) -> bool:
    message = str(error).lower()
    return isinstance(error, sqlite3.OperationalError) or "429" in message or "rate limit" in message


@retry(
    retry=retry_if_exception(_is_transient_error),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _run_query(query: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Execute one read-only query, retrying transient MCP/database failures."""
    initialize_database(DATABASE_PATH) if not DATABASE_PATH.exists() else None
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(query, parameters).fetchall()]


@retry(
    retry=retry_if_exception(_is_transient_error),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _run_write(query: str, parameters: tuple[Any, ...] = ()) -> int:
    """Execute one write query, retrying transient MCP/database failures."""
    initialize_database(DATABASE_PATH) if not DATABASE_PATH.exists() else None
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(query, parameters)
        connection.commit()
        return int(cursor.lastrowid)


def _json(rows: list[dict[str, Any]]) -> str:
    return json.dumps(rows, indent=2, default=str)


@tool("get_account_details")
def get_account_details(account_id: str = "ACCT-1001", user_id: str = "USER-1001") -> str:
    """Fetch balances, account types, status, and profile details for a user."""
    return _json(
        _run_query(
            """
            SELECT account_id, user_id, account_type, account_holder, balance,
                   currency, status, opened_on
            FROM accounts
            WHERE account_id = ? AND user_id = ?
            """,
            (account_id, user_id),
        )
    )


@tool("get_transaction_history")
def get_transaction_history(
    account_id: str = "ACCT-1001", user_id: str = "USER-1001", limit: int = 10
) -> str:
    """Fetch recent transactions for an account owned by the user."""
    safe_limit = max(1, min(int(limit), 50))
    return _json(
        _run_query(
            """
            SELECT t.transaction_id, t.account_id, t.transaction_date,
                   t.description, t.category, t.amount, t.transaction_type
            FROM transactions AS t
            JOIN accounts AS a ON a.account_id = t.account_id
            WHERE t.account_id = ? AND a.user_id = ?
            ORDER BY t.transaction_date DESC, t.transaction_id DESC
            LIMIT ?
            """,
            (account_id, user_id, safe_limit),
        )
    )


@tool("analyze_spending")
def analyze_spending(account_id: str = "ACCT-1001", user_id: str = "USER-1001") -> str:
    """Summarize debit spending by category for an account."""
    return _json(
        _run_query(
            """
            SELECT t.category, ROUND(SUM(ABS(t.amount)), 2) AS total_spend,
                   COUNT(*) AS transaction_count
            FROM transactions AS t
            JOIN accounts AS a ON a.account_id = t.account_id
            WHERE t.account_id = ? AND a.user_id = ? AND t.amount < 0
            GROUP BY t.category
            ORDER BY total_spend DESC
            """,
            (account_id, user_id),
        )
    )


@tool("request_statement")
def request_statement(
    account_id: str = "ACCT-1001", user_id: str = "USER-1001", statement_period: str = "last month"
) -> str:
    """Create a statement request after confirming the account belongs to the user."""
    account = _run_query(
        "SELECT account_id FROM accounts WHERE account_id = ? AND user_id = ?",
        (account_id, user_id),
    )
    if not account:
        return json.dumps({"error": "Account was not found for this user."})
    request_id = _run_write(
        """
        INSERT INTO service_requests (user_id, request_type, details, status, created_at)
        VALUES (?, 'Statement Request', ?, 'Open', date('now'))
        """,
        (user_id, f"Statement requested for {statement_period.strip()} ({account_id})"),
    )
    return json.dumps({"request_id": request_id, "status": "Open", "statement_period": statement_period})


@tool("get_service_requests")
def get_service_requests(user_id: str = "USER-1001") -> str:
    """List existing address, cheque book, and KYC service requests."""
    return _json(
        _run_query(
            """
            SELECT request_id, request_type, details, status, created_at
            FROM service_requests
            WHERE user_id = ?
            ORDER BY created_at DESC, request_id DESC
            """,
            (user_id,),
        )
    )


@tool("create_service_request")
def create_service_request(
    user_id: str = "USER-1001",
    request_type: str = "General",
    details: str = "Customer service request",
) -> str:
    """Create a service request for address, cheque book, or KYC support."""
    allowed_types = {"Address Change", "Cheque Book", "KYC Update", "General"}
    normalized_type = request_type.strip().title()
    if normalized_type not in allowed_types:
        return json.dumps({"error": f"request_type must be one of {sorted(allowed_types)}"})
    request_id = _run_write(
        """
        INSERT INTO service_requests (user_id, request_type, details, status, created_at)
        VALUES (?, ?, ?, 'Open', date('now'))
        """,
        (user_id, normalized_type, details.strip()),
    )
    return json.dumps({"request_id": request_id, "status": "Open", "request_type": normalized_type})


ACCOUNT_TOOLS = [get_account_details]
TRANSACTION_TOOLS = [get_transaction_history, analyze_spending, request_statement]
SERVICE_TOOLS = [get_service_requests, create_service_request]
