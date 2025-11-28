# backend/app/db.py
import sqlite3
import json
import os
import logging
from typing import Any, Dict, List, Optional
from app.config import DB_PATH

logger = logging.getLogger(__name__)

# ensure directory exists for DB
db_dir = os.path.dirname(DB_PATH) or "."
os.makedirs(db_dir, exist_ok=True)

# internal flag to avoid repeated init attempts
_db_initialized = False

def _conn():
    """Return a sqlite3 connection (not thread-local)."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def _ensure_db():
    """Create DB and tables if not already created. Safe to call multiple times."""
    global _db_initialized
    if _db_initialized:
        return
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            country TEXT,
            domain TEXT,
            year INTEGER,
            data_json TEXT
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            task_id TEXT PRIMARY KEY,
            status_json TEXT
        );
        """)
        conn.commit()
        conn.close()
        _db_initialized = True
    except Exception as e:
        # log but don't raise — caller functions will handle errors gracefully
        logger.exception("Failed to initialize DB at %s: %s", DB_PATH, e)
        _db_initialized = False

def upsert_item(source: str, country: str, domain: str, year: Optional[int], data: Dict[str, Any]):
    try:
        _ensure_db()
        conn = _conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO items (source, country, domain, year, data_json) VALUES (?, ?, ?, ?, ?)",
            (source, country, domain, year, json.dumps(data, ensure_ascii=False))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.exception("upsert_item failed: %s", e)

def get_items(country: str, domain: str, year_from: Optional[int] = None) -> List[Dict]:
    try:
        _ensure_db()
        conn = _conn()
        cur = conn.cursor()
        if year_from:
            rows = cur.execute("SELECT * FROM items WHERE country=? AND domain=? AND year>=? ORDER BY year DESC",
                               (country, domain, year_from)).fetchall()
        else:
            rows = cur.execute("SELECT * FROM items WHERE country=? AND domain=? ORDER BY year DESC",
                               (country, domain)).fetchall()
        out = []
        for r in rows:
            d = json.loads(r["data_json"])
            out.append(d)
        conn.close()
        return out
    except Exception as e:
        logger.exception("get_items failed: %s", e)
        return []

def save_analysis(task_id: str, status: Dict[str, Any]):
    try:
        _ensure_db()
        conn = _conn()
        cur = conn.cursor()
        cur.execute("REPLACE INTO analyses (task_id, status_json) VALUES (?, ?)", (task_id, json.dumps(status, ensure_ascii=False)))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.exception("save_analysis failed: %s", e)

def get_analysis(task_id: str) -> Optional[Dict[str, Any]]:
    try:
        _ensure_db()
        conn = _conn()
        cur = conn.cursor()
        row = cur.execute("SELECT status_json FROM analyses WHERE task_id=?", (task_id,)).fetchone()
        conn.close()
        if row and row[0]:
            return json.loads(row[0])
        return None
    except Exception as e:
        logger.exception("get_analysis failed: %s", e)
        return None
