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
            source       TEXT DEFAULT 'live',
            status       TEXT DEFAULT 'completed'
        )
    """)
    conn.commit()

    # Add status column to existing DBs that predate this field
    try:
        conn.execute("ALTER TABLE returns ADD COLUMN status TEXT DEFAULT 'completed'")
        conn.commit()
    except Exception:
        pass  # Column already exists

    # Set correct initial statuses for any existing flagged rows missing a status
    conn.execute("""
        UPDATE returns SET status = 'pending_inspection'
        WHERE decision = 'flagged_inspection'
        AND (status IS NULL OR status = 'completed')
    """)
    conn.commit()

    if history_csv_path and Path(history_csv_path).exists():
        count = conn.execute("SELECT COUNT(*) FROM returns").fetchone()[0]
        if count == 0:
            df = pd.read_csv(history_csv_path)
            df["source"] = "seed"
            df["hard_rule"] = df["hard_rule"].fillna("")
            df["status"] = df["decision"].apply(
                lambda d: "pending_inspection" if d == "flagged_inspection" else "completed"
            )
            df.to_sql("returns", conn, if_exists="append", index=False)

    conn.close()


def save_return(record: dict):
    """Insert a new return record. Silently replaces on duplicate return_id."""
    status = "pending_inspection" if record.get("decision") == "flagged_inspection" else "completed"
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT OR REPLACE INTO returns
            (return_id, customer, item, category, return_reason,
             risk_score, decision, hard_rule, submitted_at, source, status)
        VALUES
            (:return_id, :customer, :item, :category, :return_reason,
             :risk_score, :decision, :hard_rule, :submitted_at, 'live', :status)
        """,
        {**record, "status": status},
    )
    conn.commit()
    conn.close()


def load_pending_inspection() -> pd.DataFrame:
    """Return all flagged returns awaiting inspection, oldest first."""
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM returns WHERE status = 'pending_inspection' ORDER BY submitted_at ASC",
        conn,
    )
    conn.close()
    return df


def count_pending_inspection() -> int:
    """Count flagged returns awaiting inspection."""
    if not DB_PATH.exists():
        return 0
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute(
        "SELECT COUNT(*) FROM returns WHERE status = 'pending_inspection'"
    ).fetchone()[0]
    conn.close()
    return count


def resolve_return(return_id: str, outcome: str):
    """Mark a return as resolved. outcome must be 'inspection_approved' or 'fraud_confirmed'."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE returns SET status = ? WHERE return_id = ?",
        (outcome, return_id),
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


# ── Scoring config ─────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "threshold": 45.0,
    "w_trust": 0.40,
    "w_item": 0.35,
    "w_reason": 0.25,
}


def _ensure_config_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key   TEXT PRIMARY KEY,
            value REAL
        )
    """)
    conn.commit()


def get_config() -> dict:
    """Return the active scoring config. Falls back to defaults if unset."""
    if not DB_PATH.exists():
        return DEFAULT_CONFIG.copy()
    conn = sqlite3.connect(DB_PATH)
    _ensure_config_table(conn)
    rows = conn.execute("SELECT key, value FROM config").fetchall()
    conn.close()
    if not rows:
        return DEFAULT_CONFIG.copy()
    stored = {k: v for k, v in rows}
    # Fill in any missing keys with defaults
    return {k: stored.get(k, v) for k, v in DEFAULT_CONFIG.items()}


def save_config(config: dict):
    """Persist the scoring config. Only saves known keys."""
    conn = sqlite3.connect(DB_PATH)
    _ensure_config_table(conn)
    for key in DEFAULT_CONFIG:
        if key in config:
            conn.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                (key, float(config[key])),
            )
    conn.commit()
    conn.close()
