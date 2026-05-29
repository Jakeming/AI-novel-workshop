"""
db.py — Database adapter with dual implementation.

Production: PostgresDB (requires psycopg2)
Dev/Test:   SqliteDB (built-in sqlite3, zero install)

Usage:
    db = db_from_config("postgres://user:pass@host/dbname")
    # or
    db = db_from_config("sqlite:///path/to/dev.db")

    user = db.get_user(1)
    db.create_session(user_id=1, source_title="My Article")
"""
import json, os, logging
from datetime import date, datetime
from typing import Optional
from dataclasses import dataclass

_log = logging.getLogger(__name__)


# ===== Abstract interface (duck-typed) =====
# Methods all DB implementations must provide:

# User
#   get_user(user_id: int) -> dict | None
#   get_user_by_username(name: str) -> dict | None
#   create_user(username: str, stage: str = "novice") -> int
#   update_user_stage(user_id: int, stage: str) -> None
#
# Session
#   create_session(user_id: int, source_title: str = "") -> int
#   get_session(session_id: int) -> dict | None
#   update_session_node(session_id: int, node: int) -> None
#   update_session_ai_output(session_id: int, node: int, output: dict) -> None
#   update_session_verdict(session_id: int, verdict: str) -> None
#
# Draft
#   save_draft(session_id: int, content: str, verdict: str = None) -> int
#   get_drafts(session_id: int) -> list[dict]
#
# Skeleton
#   save_skeleton(session_id: int, text_skeleton: str, mermaid_code: str = "") -> int
#
# Inspiration
#   save_inspiration(user_id: int, session_id: int, text: str, note: str) -> int
#
# Probe context
#   get_probe_context(user_id: int) -> dict


# ===== SqliteDB =====

class SqliteDB:
    """Dev/test implementation using sqlite3."""

    def __init__(self, path: str = "deconstruct_dev.db"):
        import sqlite3
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_tables()

    def _init_tables(self):
        c = self._conn
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            stage TEXT DEFAULT 'novice',
            cooldown_until TIMESTAMP,
            consecutive_failures INTEGER DEFAULT 0,
            daily_submit_count INTEGER DEFAULT 0,
            last_submit_date DATE,
            reputation_score REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS deconstruct_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            source_title TEXT,
            status TEXT DEFAULT 'in_progress',
            node1_completed_at TIMESTAMP, node2_completed_at TIMESTAMP,
            node3_completed_at TIMESTAMP, node4_completed_at TIMESTAMP,
            node5_completed_at TIMESTAMP, node6_completed_at TIMESTAMP,
            node7_completed_at TIMESTAMP,
            deep_read_result TEXT, deconstruct_result TEXT, skeleton_result TEXT,
            three_answers TEXT, last_verdict TEXT,
            cooldown_triggered INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS imitation_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES deconstruct_sessions(id),
            version INTEGER DEFAULT 1,
            content TEXT NOT NULL,
            verdict TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS skeleton_library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES deconstruct_sessions(id),
            text_skeleton TEXT NOT NULL,
            mermaid_code TEXT,
            is_public INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS inspiration_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id INTEGER,
            original_text TEXT NOT NULL,
            essence_note TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS guardian_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            probe_name TEXT NOT NULL,
            severity TEXT NOT NULL,
            user_id INTEGER,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        self._conn.commit()

    def _row(self, sql: str, params=()) -> dict | None:
        r = self._conn.execute(sql, params).fetchone()
        return dict(r) if r else None

    def _rows(self, sql: str, params=()) -> list[dict]:
        return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    # --- User ---
    def get_user(self, user_id: int) -> dict | None:
        return self._row("SELECT * FROM users WHERE id = ?", (user_id,))

    def get_user_by_username(self, name: str) -> dict | None:
        return self._row("SELECT * FROM users WHERE username = ?", (name,))

    def create_user(self, username: str, stage: str = "novice") -> int:
        c = self._conn.execute(
            "INSERT INTO users (username, stage) VALUES (?, ?)", (username, stage))
        self._conn.commit()
        return c.lastrowid

    def update_user_stage(self, user_id: int, stage: str) -> None:
        self._conn.execute("UPDATE users SET stage = ? WHERE id = ?",
                          (stage, user_id))
        self._conn.commit()

    # --- Session ---
    def create_session(self, user_id: int, source_title: str = "") -> int:
        c = self._conn.execute(
            "INSERT INTO deconstruct_sessions (user_id, source_title) VALUES (?, ?)",
            (user_id, source_title))
        self._conn.commit()
        return c.lastrowid

    def get_session(self, session_id: int) -> dict | None:
        return self._row("SELECT * FROM deconstruct_sessions WHERE id = ?", (session_id,))

    def update_session_node(self, session_id: int, node: int) -> None:
        col = f"node{node}_completed_at"
        self._conn.execute(
            f"UPDATE deconstruct_sessions SET {col} = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,))
        self._conn.commit()

    def update_session_ai_output(self, session_id: int, field: str, data: dict) -> None:
        allowed = {"deep_read_result", "deconstruct_result", "skeleton_result", "three_answers"}
        if field not in allowed:
            raise ValueError(f"Field must be one of {allowed}")
        self._conn.execute(
            f"UPDATE deconstruct_sessions SET {field} = ? WHERE id = ?",
            (json.dumps(data, ensure_ascii=False), session_id))
        self._conn.commit()

    def update_session_verdict(self, session_id: int, verdict: str) -> None:
        self._conn.execute(
            "UPDATE deconstruct_sessions SET last_verdict = ? WHERE id = ?",
            (verdict, session_id))
        self._conn.commit()

    # --- Draft ---
    def save_draft(self, session_id: int, content: str, verdict: str = None) -> int:
        drafts = self._rows("SELECT version FROM imitation_drafts WHERE session_id = ? ORDER BY version DESC LIMIT 1",
                           (session_id,))
        version = (drafts[0]["version"] + 1) if drafts else 1
        c = self._conn.execute(
            "INSERT INTO imitation_drafts (session_id, version, content, verdict) VALUES (?, ?, ?, ?)",
            (session_id, version, content, verdict))
        self._conn.commit()
        return c.lastrowid

    def get_drafts(self, session_id: int) -> list[dict]:
        return self._rows("SELECT * FROM imitation_drafts WHERE session_id = ? ORDER BY version", (session_id,))

    # --- Skeleton ---
    def save_skeleton(self, session_id: int, text_skeleton: str, mermaid_code: str = "") -> int:
        c = self._conn.execute(
            "INSERT INTO skeleton_library (session_id, text_skeleton, mermaid_code) VALUES (?, ?, ?)",
            (session_id, text_skeleton, mermaid_code))
        self._conn.commit()
        return c.lastrowid

    # --- Inspiration ---
    def save_inspiration(self, user_id: int, session_id: int, text: str, note: str) -> int:
        c = self._conn.execute(
            "INSERT INTO inspiration_entries (user_id, session_id, original_text, essence_note) VALUES (?, ?, ?, ?)",
            (user_id, session_id, text, note))
        self._conn.commit()
        return c.lastrowid

    # --- Probe context ---
    def get_probe_context(self, user_id: int) -> dict:
        user = self.get_user(user_id)
        if not user:
            return {}
        recent = self._rows("""
            SELECT ds.last_verdict, COUNT(*) as cnt
            FROM deconstruct_sessions ds
            WHERE ds.user_id = ? AND ds.created_at >= datetime('now', '-2 hours')
            GROUP BY ds.last_verdict
        """, (user_id,))
        red_count = sum(r["cnt"] for r in recent if r["last_verdict"] == "red")
        return {
            "user_id": user_id,
            "consecutive_failures_2h": red_count,
            "stage": user["stage"],
            "daily_submit_count": user["daily_submit_count"],
        }


# ===== PostgresDB =====

class PostgresDB:
    """Production implementation using psycopg2."""

    def __init__(self, dsn: str):
        import psycopg2
        import psycopg2.extras
        self._conn = psycopg2.connect(dsn)
        self._conn.autocommit = True

    def _row(self, sql: str, params=()) -> dict | None:
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            r = cur.fetchone()
            return dict(r) if r else None

    def _rows(self, sql: str, params=()) -> list[dict]:
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def get_user(self, user_id: int) -> dict | None:
        return self._row("SELECT * FROM users WHERE id = %s", (user_id,))

    def get_user_by_username(self, name: str) -> dict | None:
        return self._row("SELECT * FROM users WHERE username = %s", (name,))

    def create_user(self, username: str, stage: str = "novice") -> int:
        with self._conn.cursor() as cur:
            cur.execute("INSERT INTO users (username, stage) VALUES (%s, %s) RETURNING id",
                       (username, stage))
            return cur.fetchone()[0]

    def update_user_stage(self, user_id: int, stage: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute("UPDATE users SET stage = %s WHERE id = %s",
                       (stage, user_id))

    def create_session(self, user_id: int, source_title: str = "") -> int:
        with self._conn.cursor() as cur:
            cur.execute("INSERT INTO deconstruct_sessions (user_id, source_title) VALUES (%s, %s) RETURNING id",
                       (user_id, source_title))
            return cur.fetchone()[0]

    def get_session(self, session_id: int) -> dict | None:
        return self._row("SELECT * FROM deconstruct_sessions WHERE id = %s", (session_id,))

    def update_session_node(self, session_id: int, node: int) -> None:
        col = f"node{node}_completed_at"
        with self._conn.cursor() as cur:
            cur.execute(f"UPDATE deconstruct_sessions SET {col} = NOW() WHERE id = %s",
                       (session_id,))

    def update_session_ai_output(self, session_id: int, field: str, data: dict) -> None:
        allowed = {"deep_read_result", "deconstruct_result", "skeleton_result", "three_answers"}
        if field not in allowed:
            raise ValueError(f"Field must be one of {allowed}")
        import json
        with self._conn.cursor() as cur:
            cur.execute(
                f"UPDATE deconstruct_sessions SET {field} = %s::jsonb WHERE id = %s",
                (json.dumps(data), session_id))

    def update_session_verdict(self, session_id: int, verdict: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute("UPDATE deconstruct_sessions SET last_verdict = %s WHERE id = %s",
                       (verdict, session_id))

    def save_draft(self, session_id: int, content: str, verdict: str = None) -> int:
        rows = self._rows("SELECT version FROM imitation_drafts WHERE session_id = %s ORDER BY version DESC LIMIT 1",
                         (session_id,))
        version = (rows[0]["version"] + 1) if rows else 1
        with self._conn.cursor() as cur:
            cur.execute("INSERT INTO imitation_drafts (session_id, version, content, verdict) VALUES (%s, %s, %s, %s) RETURNING id",
                       (session_id, version, content, verdict))
            return cur.fetchone()[0]

    def get_drafts(self, session_id: int) -> list[dict]:
        return self._rows("SELECT * FROM imitation_drafts WHERE session_id = %s ORDER BY version", (session_id,))

    def save_skeleton(self, session_id: int, text_skeleton: str, mermaid_code: str = "") -> int:
        with self._conn.cursor() as cur:
            cur.execute("INSERT INTO skeleton_library (session_id, text_skeleton, mermaid_code) VALUES (%s, %s, %s) RETURNING id",
                       (session_id, text_skeleton, mermaid_code))
            return cur.fetchone()[0]

    def save_inspiration(self, user_id: int, session_id: int, text: str, note: str) -> int:
        with self._conn.cursor() as cur:
            cur.execute("INSERT INTO inspiration_entries (user_id, session_id, original_text, essence_note) VALUES (%s, %s, %s, %s) RETURNING id",
                       (user_id, session_id, text, note))
            return cur.fetchone()[0]

    def get_probe_context(self, user_id: int) -> dict:
        user = self.get_user(user_id)
        if not user:
            return {}
        recent = self._rows("""
            SELECT last_verdict, COUNT(*) as cnt
            FROM deconstruct_sessions
            WHERE user_id = %s AND created_at >= NOW() - INTERVAL '2 hours'
            GROUP BY last_verdict
        """, (user_id,))
        red_count = sum(r["cnt"] for r in recent if r["last_verdict"] == "red")
        return {
            "user_id": user_id,
            "consecutive_failures_2h": red_count,
            "stage": user["stage"],
            "daily_submit_count": user["daily_submit_count"],
        }


# ===== Factory =====

def db_from_config(dsn: str = ""):
    """
    Create DB instance from connection string.
    - "sqlite:///path/to/db" -> SqliteDB
    - "postgres://..." -> PostgresDB
    - Empty -> SqliteDB with default path "deconstruct_dev.db"
    """
    dsn = dsn or os.getenv("DATABASE_URL", "")
    if not dsn:
        _log.info("No DATABASE_URL, using SQLite (deconstruct_dev.db)")
        return SqliteDB("deconstruct_dev.db")
    if dsn.startswith("sqlite:///"):
        path = dsn[len("sqlite:///"):]
        _log.info("Using SQLite: %s", path)
        return SqliteDB(path)
    if dsn.startswith("postgres"):
        _log.info("Using PostgreSQL")
        return PostgresDB(dsn)
    raise ValueError(f"Unsupported DSN scheme: {dsn}")
