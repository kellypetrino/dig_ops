import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "returns.db"


def init_db(history_csv_path=None):
    """Create the DB and returns table if they don't exist.
    On first run (empty table), seed from the history CSV."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS returns (
            return_id    TEXT PRIMARY KEY,
            customer     TEXT,
            item         TEXT,
            category     TEXT,
            return_reason TEXT,
            risk_score   REAL,
            decision     TEXT,
            hard_rule    TEXT,
            submitted_at TEXT,
            source       TEXT DEFAULT 'live'
        )
    """)
    conn.commit()

    if history_csv_path and Path(history_csv_path).exists():
        count = conn.execute("SELECT COUNT(*) FROM returns").fetchone()[0]
        if count == 0:
            df = pd.read_csv(history_csv_path)
            df["source"] = "seed"
            df["hard_rule"] = df["hard_rule"].fillna("")
            df.to_sql("returns", conn, if_exists="append", index=False)

    conn.close()


def save_return(record: dict):
    """Insert a new return record. Silently replaces on duplicate return_id."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT OR REPLACE INTO returns
            (return_id, customer, item, category, return_reason,
             risk_score, decision, hard_rule, submitted_at, source)
        VALUES
            (:return_id, :customer, :item, :category, :return_reason,
             :risk_score, :decision, :hard_rule, :submitted_at, 'live')
        """,
        record,
    )
    conn.commit()
    conn.close()


def load_returns() -> pd.DataFrame:
    """Return all returns as a DataFrame, newest first."""
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM returns ORDER BY submitted_at DESC", conn)
    conn.close()
    return df


def count_live_returns() -> int:
    """Count returns submitted through the live UI (not seeded history)."""
    if not DB_PATH.exists():
        return 0
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute(
        "SELECT COUNT(*) FROM returns WHERE source = 'live'"
    ).fetchone()[0]
    conn.close()
    return count


def reset_live_returns():
    """Delete all live (non-seed) returns. Used for demo reset."""
    if not DB_PATH.exists():
        return
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM returns WHERE source = 'live'")
    conn.commit()
    conn.close()
