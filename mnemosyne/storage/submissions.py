from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "mnemosyne.sqlite3"
LEGACY_DB_PATH = DATA_DIR / "local_leetcode.sqlite3"


def _migrate_legacy_db_if_needed() -> None:
    if DB_PATH.exists() or not LEGACY_DB_PATH.exists():
        return
    shutil.copy2(LEGACY_DB_PATH, DB_PATH)


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_db_if_needed()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id TEXT NOT NULL,
                problem_title TEXT NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                passed INTEGER NOT NULL,
                total INTEGER NOT NULL,
                code TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_submissions_problem_id ON submissions(problem_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_submissions_created_at ON submissions(created_at)"
        )


def save_submission(
    *,
    problem_id: str,
    problem_title: str,
    mode: str,
    code: str,
    result: dict[str, Any],
) -> int:
    init_db()
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO submissions (
                problem_id,
                problem_title,
                mode,
                status,
                passed,
                total,
                code,
                result_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                problem_id,
                problem_title,
                mode,
                result.get("status", "Unknown"),
                int(result.get("passed", 0)),
                int(result.get("total", 0)),
                code,
                json.dumps(result, ensure_ascii=False),
                created_at,
            ),
        )
        return int(cur.lastrowid)


def list_submissions(problem_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    init_db()
    limit = max(1, min(limit, 500))
    with get_connection() as conn:
        if problem_id:
            rows = conn.execute(
                """
                SELECT id, problem_id, problem_title, mode, status, passed, total, created_at
                FROM submissions
                WHERE problem_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (problem_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, problem_id, problem_title, mode, status, passed, total, created_at
                FROM submissions
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return [dict(row) for row in rows]


def get_submission(submission_id: int) -> dict[str, Any] | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, problem_id, problem_title, mode, status, passed, total, code, result_json, created_at
            FROM submissions
            WHERE id = ?
            """,
            (submission_id,),
        ).fetchone()
    if row is None:
        return None
    data = dict(row)
    try:
        data["result"] = json.loads(data.pop("result_json"))
    except json.JSONDecodeError:
        data["result"] = {"status": data["status"], "error": "Stored result_json is invalid."}
    return data


def list_wrong_problems() -> list[dict[str, Any]]:
    """Return problems that have at least one non-Accepted submission.

    Includes the latest submission status and counts, so the UI can show whether
    the user later fixed the problem.
    """
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            WITH wrong AS (
                SELECT problem_id, COUNT(*) AS wrong_count
                FROM submissions
                WHERE status != 'Accepted'
                GROUP BY problem_id
            ),
            latest AS (
                SELECT s.*
                FROM submissions s
                JOIN (
                    SELECT problem_id, MAX(id) AS max_id
                    FROM submissions
                    GROUP BY problem_id
                ) m ON s.problem_id = m.problem_id AND s.id = m.max_id
            )
            SELECT
                latest.problem_id,
                latest.problem_title,
                wrong.wrong_count,
                latest.id AS latest_submission_id,
                latest.status AS latest_status,
                latest.passed AS latest_passed,
                latest.total AS latest_total,
                latest.created_at AS latest_created_at
            FROM wrong
            JOIN latest ON wrong.problem_id = latest.problem_id
            ORDER BY latest.id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]
