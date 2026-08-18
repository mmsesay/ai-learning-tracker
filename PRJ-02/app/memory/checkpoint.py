"""SQLite checkpointing for multi-turn conversation memory.

LangGraph concept
-----------------
A **checkpointer** saves graph state after each step, keyed by ``thread_id``.
The next ``invoke`` with the same thread loads prior ``messages`` / fields so
clarification replies can continue the same conversation.
"""

from __future__ import annotations

import sqlite3
from functools import lru_cache
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from app.settings import get_settings


@lru_cache(maxsize=1)
def get_sqlite_checkpointer(path: str | None = None) -> SqliteSaver:
    """Return a process-wide SqliteSaver (connection kept open for the API).

    ``SqliteSaver.from_conn_string`` is a context manager that *closes* the DB
    when leaving ``with`` — fine for scripts, wrong for FastAPI. We open the
    connection ourselves and call ``setup()`` once.
    """
    db_path = path or get_settings().lepa_checkpoint_path
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    saver = SqliteSaver(conn)
    saver.setup()
    return saver


def make_memory_checkpointer(db_path: str = ":memory:") -> SqliteSaver:
    """Fresh checkpointer for tests (not cached)."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    saver = SqliteSaver(conn)
    saver.setup()
    return saver
