"""
Database Management Module
Handles SQLite operations for storing, querying, and managing scraping history.
Always closes connections cleanly to ensure Windows OS compatibility and prevent file locks.
"""

from datetime import datetime
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional
import pandas as pd

DEFAULT_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "scraping_history.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and return a SQLite database connection."""
    target_path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize the SQLite database with the required schema."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scraping_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                scrape_type TEXT NOT NULL,
                record_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                execution_time REAL NOT NULL DEFAULT 0.0,
                timestamp TEXT NOT NULL,
                error_message TEXT,
                preview_json TEXT
            );
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_history_timestamp 
            ON scraping_history(timestamp DESC);
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_history(
    url: str,
    scrape_type: str,
    record_count: int,
    status: str,
    execution_time: float,
    error_message: Optional[str] = None,
    preview_df: Optional[pd.DataFrame] = None,
    db_path: Optional[str] = None,
) -> int:
    """
    Save a completed or failed scraping job into the database.
    Stores a JSON preview of the top 5 records if data is available.
    Returns the newly inserted record ID.
    """
    init_db(db_path)

    preview_json = None
    if preview_df is not None and not preview_df.empty:
        try:
            preview_json = preview_df.head(5).to_json(orient="records", date_format="iso")
        except Exception:
            preview_json = None

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO scraping_history (
                url, scrape_type, record_count, status, execution_time, timestamp, error_message, preview_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                url,
                scrape_type,
                record_count,
                status,
                round(execution_time, 2),
                now_iso,
                error_message,
                preview_json,
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()


def get_history(
    search_query: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 100,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Retrieve scraping history with optional keyword search and status filter.
    Returns a Pandas DataFrame.
    """
    init_db(db_path)

    query = "SELECT id, timestamp, url, scrape_type, record_count, status, execution_time, error_message FROM scraping_history WHERE 1=1"
    params: List[Any] = []

    if search_query and search_query.strip():
        query += " AND (url LIKE ? OR scrape_type LIKE ?)"
        wildcard = f"%{search_query.strip()}%"
        params.extend([wildcard, wildcard])

    if status_filter and status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    conn = get_connection(db_path)
    try:
        df = pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()

    if not df.empty:
        df = df.rename(
            columns={
                "id": "Job ID",
                "timestamp": "Timestamp",
                "url": "Target URL",
                "scrape_type": "Data Type",
                "record_count": "Records",
                "status": "Status",
                "execution_time": "Time (s)",
                "error_message": "Notes / Error",
            }
        )

    return df


def get_history_by_id(record_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve full record including preview JSON by ID."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scraping_history WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()


def clear_history(db_path: Optional[str] = None) -> bool:
    """Delete all records from the scraping_history table."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scraping_history")
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def delete_history_item(item_id: int, db_path: Optional[str] = None) -> bool:
    """Delete a single history record by ID."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scraping_history WHERE id = ?", (item_id,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Calculate aggregate statistics from scraping history."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM scraping_history")
        total_scrapes = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM scraping_history WHERE status = 'Success'")
        successful = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM scraping_history WHERE status = 'Failed'")
        failed = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(record_count) FROM scraping_history WHERE status = 'Success'")
        total_records = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(execution_time) FROM scraping_history WHERE status = 'Success'")
        avg_time_raw = cursor.fetchone()[0]
        avg_time = round(avg_time_raw, 2) if avg_time_raw else 0.0

        success_rate = round((successful / total_scrapes * 100), 1) if total_scrapes > 0 else 0.0

        return {
            "total_scrapes": total_scrapes,
            "successful": successful,
            "failed": failed,
            "total_records": total_records,
            "avg_time": avg_time,
            "success_rate": success_rate,
        }
    finally:
        conn.close()
