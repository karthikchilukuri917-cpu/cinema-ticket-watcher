from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import Event
from typing import Callable, Dict, Optional

from app.models import Watch
from app.sources.base import CinemaSource
from app.sources.result import SourceResult, SourceStatus
from app.watcher import run_monitor

from app.postgres_watch_health import PostgreSQLWatchHealthStore
from app.postgres_watch_history import PostgreSQLWatchHistoryStore
from app.postgres_watch_state import PostgreSQLWatchStateStore

from app.watch_health import WatchHealthStore
from app.watch_history import WatchHistoryStore
from app.watch_state import WatchStateStore


class WatchRunner:
    """
    Runs one Watch through the monitoring engine.

    Production:
        Uses PostgreSQL for state, history and health.

    Tests/local isolated runs:
        When state_directory is explicitly supplied,
        uses the JSON stores.
    """

    def __init__(
        self,
        watch_id: str,
        source_factory: Callable[
            [Watch],
            CinemaSource,
        ],
        on_change: Callable[[Dict], None],
        state_directory: Optional[Path] = None,
    ) -> None:

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        self.watch_id = watch_id
        self.source_factory = source_factory
        self.on_change = on_change

        # ---------------------------------------------------------
        # Production persistence
        # ---------------------------------------------------------

        if state_directory is None:

            self.state_store = (
                PostgreSQLWatchStateStore(
                    watch_id=watch_id,
                )
            )

            self.history_store = (
                PostgreSQLWatchHistoryStore(
                    watch_id=watch_id,
                )
            )

            self.health_store = (
                PostgreSQLWatchHealthStore(
                    watch_id=watch_id,
                )
            )

        # ---------------------------------------------------------
        # Test / explicit local persistence
        # ---------------------------------------------------------

        else:

            state_directory = Path(
                state_directory
            )

            self.state_store = WatchStateStore(
                watch_id=watch_id,
                directory=state_directory,
            )

            self.history_store = WatchHistoryStore(
                watch_id=watch_id,
                directory=state_directory,
            )

            self.health_store = WatchHealthStore(
                watch_id=watch_id,
                directory=state_directory,
            )

    # =========================================================
    # HEALTH
    # =========================================================

    def _record_health(
        self,
        status: SourceStatus,
        message: Optional[str] = None,
    ) -> None:
        """
        Persist the latest source health.

        Health persistence must never stop the watcher.
        """

        status_value = (
            status.value
            if hasattr(status, "value")
            else str(status)
        )

        health = {
            "last_checked": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
            "status": status_value,
            "message": message,
        }

        try:

            self.health_store.save(
                health
            )

        except Exception:
            # Health storage must never crash
            # the monitoring loop.
            pass

    # =========================================================
    # SOURCE FETCH
    # =========================================================

    def _fetch_availability(
        self,
        source,
        watch: Watch,
    ) -> SourceResult:
        """
        Fetch availability and record source health.

        This method is intentionally used by run_monitor()
        so every monitoring cycle updates PostgreSQL health.
        """

        try:

            result = source.get_availability(
                watch
            )

            self._record_health(
                result.status,
                result.message,
            )

            return result

        except Exception as exc:

            self._record_health(
                SourceStatus.ERROR,
                str(exc),
            )

            raise

    # =========================================================
    # CHANGE HANDLING
    # =========================================================

    def _handle_change(
        self,
        changes: Dict,
    ) -> None:
        """
        Persist availability changes to history and
        then execute the notification callback.
        """

        if not changes:
            return

        try:

            self.history_store.add(
                changes
            )

        except Exception:
            # History persistence must never prevent
            # notifications from being sent.
            pass

        self.on_change(
            changes
        )

    # =========================================================
    # RUN
    # =========================================================

    def run(
        self,
        watch: Watch,
        max_cycles: int | None = None,
        stop_event=None,
    ) -> bool:

        source = self.source_factory(
            watch
        )

        return run_monitor(
            watch=watch,

            # IMPORTANT:
            # Do NOT call source.get_availability()
            # directly here.
            #
            # _fetch_availability() records health
            # before returning the SourceResult.
            fetch_availability=lambda: (
                self._fetch_availability(
                    source,
                    watch,
                )
            ),

            on_change=self._handle_change,

            load_state=(
                self.state_store.load
            ),

            save_state=(
                self.state_store.save
            ),

            max_cycles=max_cycles,

            stop_event=stop_event,
        )

    # =========================================================
    # STATE
    # =========================================================

    def get_state(self) -> Dict:
        return self.state_store.load()

    def clear_state(self) -> None:
        self.state_store.clear()

    # =========================================================
    # HISTORY
    # =========================================================

    def get_history(self) -> list:
        return self.history_store.load()

    def clear_history(self) -> None:
        self.history_store.clear()

    # =========================================================
    # HEALTH
    # =========================================================

    def get_health(self) -> Dict:
        return self.health_store.load()

    def clear_health(self) -> None:
        self.health_store.clear()