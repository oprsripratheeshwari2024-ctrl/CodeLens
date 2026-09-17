"""
SQLite database setup for CodeLens.
Creates tables (users, analyses, reviews) and provides simple
connection helpers. No ORM is used on purpose, to keep the local
Windows setup dependency-free (SQLite ships with Python).
"""

import sqlite3
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager

# database/codelens.db lives one level above backend/
DB_PATH = Path(__file__).resolve().parent.parent.parent / "database" / "codelens.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                language TEXT NOT NULL,
                code TEXT NOT NULL,
                summary TEXT,
                quality_score INTEGER,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                feedback TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------- users ----------

def get_or_create_user(email: str) -> int:
    with get_db() as conn:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO users (email, created_at) VALUES (?, ?)",
            (email, now_iso()),
        )
        return cur.lastrowid


# ---------- analyses ----------

def save_analysis(user_id: int, language: str, code: str, summary: str,
                   quality_score: int, result: dict) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO analyses (user_id, language, code, summary, quality_score, result_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, language, code, summary, quality_score, json.dumps(result), now_iso()),
        )
        return cur.lastrowid


def get_history(user_id: int, limit: int = 50):
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, language, summary, quality_score, created_at
            FROM analyses WHERE user_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_analysis(analysis_id: int, user_id: int):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user_id),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["result"] = json.loads(d.pop("result_json"))
        return d


def get_dashboard_stats(user_id: int):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT language, quality_score FROM analyses WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    total = len(rows)
    per_lang = {"python": 0, "java": 0, "cpp": 0, "c": 0}
    scores = []
    for r in rows:
        lang = r["language"]
        if lang in per_lang:
            per_lang[lang] += 1
        if r["quality_score"] is not None:
            scores.append(r["quality_score"])
    avg_quality = round(sum(scores) / len(scores), 1) if scores else 0
    return {
        "total_analyses": total,
        "python_analyses": per_lang["python"],
        "java_analyses": per_lang["java"],
        "cpp_analyses": per_lang["cpp"],
        "c_analyses": per_lang["c"],
        "average_quality": avg_quality,
    }


# ---------- reviews ----------

def save_review(user_id: int, rating: int, feedback: str) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO reviews (user_id, rating, feedback, created_at) VALUES (?, ?, ?, ?)",
            (user_id, rating, feedback, now_iso()),
        )
        return cur.lastrowid
