import sqlite3
from datetime import datetime
from pathlib import Path

DB_DIR = Path.home() / ".local" / "share" / "podcast2obsidian"
DB_PATH = DB_DIR / "bot.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    status_message_id INTEGER,
    transcript TEXT,
    note TEXT,
    note_path TEXT,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
"""


def get_db(path: Path = DB_PATH) -> sqlite3.Connection:
    """Get a SQLite connection, creating DB and schema if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def init_db(path: Path = DB_PATH) -> None:
    """Initialize DB and recover any interrupted tasks."""
    conn = get_db(path)
    conn.execute("UPDATE tasks SET status = 'pending' WHERE status = 'processing'")
    conn.commit()
    conn.close()


def create_task(
    conn: sqlite3.Connection,
    user_id: int,
    chat_id: int,
    url: str,
    status_message_id: int,
) -> int:
    """Create a new pending task. Returns task ID."""
    cur = conn.execute(
        "INSERT INTO tasks (user_id, chat_id, url, status_message_id) VALUES (?, ?, ?, ?)",
        (user_id, chat_id, url, status_message_id),
    )
    conn.commit()
    return cur.lastrowid


def get_next_pending(conn: sqlite3.Connection) -> dict | None:
    """Get the oldest pending task, or None."""
    row = conn.execute(
        "SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at LIMIT 1"
    ).fetchone()
    return dict(row) if row else None


def get_pending_count(conn: sqlite3.Connection) -> int:
    """Count pending tasks."""
    row = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'").fetchone()
    return row[0]


def update_status(conn: sqlite3.Connection, task_id: int, status: str) -> None:
    """Update task status."""
    if status in ("done", "error"):
        conn.execute(
            "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
            (status, datetime.now().isoformat(), task_id),
        )
    else:
        conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()


def save_result(
    conn: sqlite3.Connection,
    task_id: int,
    transcript: str,
    note: str,
    note_path: str,
) -> None:
    """Save processing result and mark as done."""
    conn.execute(
        "UPDATE tasks SET transcript = ?, note = ?, note_path = ?, status = 'done', completed_at = ? WHERE id = ?",
        (transcript, note, note_path, datetime.now().isoformat(), task_id),
    )
    conn.commit()


def save_error(conn: sqlite3.Connection, task_id: int, error: str) -> None:
    """Save error and mark task as failed."""
    conn.execute(
        "UPDATE tasks SET error = ?, status = 'error', completed_at = ? WHERE id = ?",
        (error, datetime.now().isoformat(), task_id),
    )
    conn.commit()


def cancel_user_tasks(conn: sqlite3.Connection, user_id: int) -> int:
    """Cancel all pending tasks for a user. Returns count of cancelled tasks."""
    cur = conn.execute(
        "UPDATE tasks SET status = 'cancelled', completed_at = ? WHERE user_id = ? AND status IN ('pending', 'processing')",
        (datetime.now().isoformat(), user_id),
    )
    conn.commit()
    return cur.rowcount


def get_user_history(
    conn: sqlite3.Connection, user_id: int, limit: int = 10
) -> list[dict]:
    """Get recent tasks for a user."""
    rows = conn.execute(
        "SELECT id, url, status, created_at, completed_at FROM tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]
