import logging
import time
from typing import Any

from sqlalchemy import event  # type: ignore
from sqlalchemy.sql import Select
from sqlalchemy.sql.base import Executable

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """
    Analyzes queries for performance issues like N+1 problems or slow execution.
    """

    def __init__(self, slow_threshold_ms: float = 100.0):
        self.slow_threshold_ms = slow_threshold_ms
        self._query_count = 0
        self._enabled = False

    def enable(self, engine: Any) -> None:
        """Attach listeners to the engine."""
        if self._enabled:
            return

        # We need the sync engine for event listening
        sync_engine = engine.sync_engine if hasattr(engine, "sync_engine") else engine

        event.listen(sync_engine, "before_cursor_execute", self._before_cursor_execute)
        event.listen(sync_engine, "after_cursor_execute", self._after_cursor_execute)
        self._enabled = True

    def disable(self, engine: Any) -> None:
        """Remove listeners."""
        if not self._enabled:
            return

        sync_engine = engine.sync_engine if hasattr(engine, "sync_engine") else engine
        event.remove(sync_engine, "before_cursor_execute", self._before_cursor_execute)
        event.remove(sync_engine, "after_cursor_execute", self._after_cursor_execute)
        self._enabled = False

    def _before_cursor_execute(
        self,
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        self._query_count += 1
        context._query_start_time = time.time()

    def _after_cursor_execute(
        self,
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        duration_ms = (time.time() - context._query_start_time) * 1000

        if duration_ms > self.slow_threshold_ms:
            logger.warning(f"[SLOW QUERY] {duration_ms:.2f}ms: {statement[:200]}...")


def with_hints(stmt: Executable, hints: dict[str, str]) -> Executable:
    """
    Apply database-specific hints to a statement.
    Example: with_hints(stmt, {"postgresql": "FOR UPDATE"})
    """
    if isinstance(stmt, Select):
        # This is a simplified wrapper. Real usage often uses with_hint directly on statement.
        for dialect, hint_text in hints.items():
            stmt = stmt.with_hint(None, hint_text, dialect_name=dialect)  # type: ignore
    return stmt
