"""SQLite persistence for the demo banking dataset."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent.parent / "bank_data.db"


def initialize_database(database_path: Path = DATABASE_PATH) -> Path:
    """Create a deterministic demo database and return its path."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            DROP TABLE IF EXISTS accounts;
            DROP TABLE IF EXISTS transactions;
            DROP TABLE IF EXISTS service_requests;

            CREATE TABLE accounts (
                account_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                account_type TEXT NOT NULL,
                account_holder TEXT NOT NULL,
                balance REAL NOT NULL,
                currency TEXT NOT NULL,
                status TEXT NOT NULL,
                opened_on TEXT NOT NULL
            );

            CREATE TABLE transactions (
                transaction_id INTEGER PRIMARY KEY,
                account_id TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_type TEXT NOT NULL,
                FOREIGN KEY (account_id) REFERENCES accounts(account_id)
            );

            CREATE TABLE service_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                request_type TEXT NOT NULL,
                details TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        connection.executemany(
            """
            INSERT INTO accounts
                (account_id, user_id, account_type, account_holder, balance,
                 currency, status, opened_on)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            , [
                ("ACCT-1001", "USER-1001", "Checking", "Aarav Sharma", 8420.55, "USD", "Active", "2021-04-12"),
                ("ACCT-1002", "USER-1001", "Savings", "Aarav Sharma", 15480.00, "USD", "Active", "2021-04-12"),
                ("ACCT-2001", "USER-2001", "Checking", "Maya Patel", 3265.20, "USD", "Active", "2022-09-30"),
                ("ACCT-3001", "USER-3001", "Savings", "Noah Williams", 22100.75, "USD", "Active", "2020-01-18"),
                ("ACCT-4001", "USER-4001", "Checking", "Sofia Garcia", 910.40, "USD", "Active", "2023-06-07"),
            ],
        )
        connection.executemany(
            """
            INSERT INTO transactions
                (transaction_id, account_id, transaction_date, description,
                 category, amount, transaction_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            , [
                (1, "ACCT-1001", "2026-08-28", "Payroll deposit", "Income", 4200.00, "Credit"),
                (2, "ACCT-1001", "2026-08-30", "Rent payment", "Housing", -1800.00, "Debit"),
                (3, "ACCT-1001", "2026-09-01", "Grocery Market", "Groceries", -126.45, "Debit"),
                (4, "ACCT-1001", "2026-09-03", "Electric utility", "Utilities", -84.16, "Debit"),
                (5, "ACCT-1002", "2026-08-15", "Monthly transfer", "Savings", 500.00, "Credit"),
                (6, "ACCT-1002", "2026-09-02", "Interest payment", "Interest", 23.82, "Credit"),
                (7, "ACCT-2001", "2026-08-29", "Coffee House", "Dining", -18.75, "Debit"),
                (8, "ACCT-3001", "2026-08-31", "Brokerage transfer", "Investments", -750.00, "Debit"),
                (9, "ACCT-4001", "2026-09-04", "Pharmacy", "Health", -42.30, "Debit"),
            ],
        )
        connection.executemany(
            """
            INSERT INTO service_requests
                (user_id, request_type, details, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """
            , [
                ("USER-1001", "Address Change", "Requested address change review", "Open", "2026-08-25"),
                ("USER-1001", "Cheque Book", "Requested a 25-leaf cheque book", "In Progress", "2026-08-29"),
                ("USER-2001", "KYC Update", "Requested phone number update", "Resolved", "2026-07-14"),
                ("USER-3001", "Address Change", "Requested mailing address update", "Open", "2026-09-01"),
                ("USER-4001", "Cheque Book", "Requested first cheque book", "Open", "2026-09-03"),
            ],
        )
        connection.commit()
    return database_path


if __name__ == "__main__":
    print(f"Created demo database at {initialize_database()}")
