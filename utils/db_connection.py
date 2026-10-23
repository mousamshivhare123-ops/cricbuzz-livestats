"""Centralised SQLite connection handling (swap the body for MySQL/PostgreSQL if needed)."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("DB_PATH", ROOT / "data" / "cricbuzz.db"))
if not DB_PATH.is_absolute():
    DB_PATH = ROOT / DB_PATH
SCHEMA_FILE = ROOT / "database" / "schema.sql"


class DatabaseError(Exception):
    """Raised for any database failure, with a user-friendly message."""


@contextmanager
def get_connection():
    """Yield a connection with foreign keys on; commit on success, rollback on error."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        raise DatabaseError(str(exc)) from exc
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables/indexes from schema.sql (idempotent)."""
    with get_connection() as conn:
        conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def db_is_ready() -> bool:
    """True if the database exists and contains matches."""
    if not DB_PATH.exists():
        return False
    try:
        with get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0] > 0
    except Exception:
        return False


def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run a read query and return a DataFrame."""
    with get_connection() as conn:
        try:
            return pd.read_sql_query(sql, conn, params=params)
        except Exception as exc:  # pandas wraps sqlite errors
            raise DatabaseError(str(exc)) from exc


def execute(sql: str, params: tuple = ()) -> int:
    """Run INSERT/UPDATE/DELETE inside a transaction; return affected rows."""
    with get_connection() as conn:
        return conn.execute(sql, params).rowcount
