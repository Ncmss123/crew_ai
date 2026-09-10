"""Backward-compatible entry point for database initialization."""

from models.database import DATABASE_PATH, initialize_database

__all__ = ["DATABASE_PATH", "initialize_database"]


if __name__ == "__main__":
    print(f"Created demo database at {initialize_database()}")
