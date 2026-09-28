import logging
import threading
from typing import Callable, Dict, List

from app.watch_manager import WatchManager
from app.watch_runner import WatchRunner


logger = logging.getLogger(__name__)


class WatchScheduler:
    """
    Runs multiple active watches independently.

    Each active Watch receives its own WatchRunner and
    background thread.
    """

    def __init__(
        self,
        watch_manager: WatchManager,
        runner_factory: Callable[
            [str],
            WatchRunner,
        ],
    ) -> None:

        self.watch_manager = watch_manager
        self.runner_factory = runner_factory

        self._threads: Dict[
            str,
            threading.Thread,
        ] = {}

        self._stop_events: Dict[
            str,
            threading.Event,
        ] = {}

        self._lock = threading.Lock()

    # -----------------------------------------------------
    # Start one watch
    # -----------------------------------------------------

    def start_watch(
        self,
        watch_id: str,
        max_cycles: int | None = None,
    ) -> bool:

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        watch = self.watch_manager.get_watch(
            watch_id
        )

        if watch is None:

            logger.warning(
                "Cannot start unknown watch: %s",
                watch_id,
            )

            return False

        if not watch.active:

            logger.info(
                "Watch %s is inactive. "
                "It will not be started.",
                watch_id,
            )

            return False

        with self._lock:

            existing_thread = self._threads.get(
                watch_id
            )

            if (
                existing_thread is not None
                and existing_thread.is_alive()
            ):

                logger.info(
                    "Watch %s is already running.",
                    watch_id,
                )

                return False

            stop_event = threading.Event()

            runner = self.runner_factory(
                watch_id
            )

            thread = threading.Thread(
                target=self._run_watch,
                args=(
                    watch_id,
                    runner,
                    watch,
                    max_cycles,
                    stop_event,
                ),
                name=f"watch-{watch_id}",
                daemon=True,
            )

            self._threads[watch_id] = thread
            self._stop_events[watch_id] = stop_event

            thread.start()

        logger.info(
            "Started watch %s.",
            watch_id,
        )

        return True

    # -----------------------------------------------------
    # Background runner
    # -----------------------------------------------------

    def _run_watch(
        self,
        watch_id: str,
        runner: WatchRunner,
        watch,
        max_cycles: int | None,
        stop_event: threading.Event,
    ) -> None:

        completed = False

        try:

            completed = runner.run(
                watch=watch,
                max_cycles=max_cycles,
                stop_event=stop_event,
            )

            if completed:

                logger.info(
                    "Watch %s completed because "
                    "tickets became available.",
                    watch_id,
                )

                try:

                    self.watch_manager.complete_watch(
                        watch_id
                    )

                except Exception:

                    logger.exception(
                        "Failed to mark completed "
                        "watch %s as inactive.",
                        watch_id,
                    )

        except Exception:

            logger.exception(
                "Watch %s stopped because of an "
                "unexpected error.",
                watch_id,
            )

        finally:

            with self._lock:

                self._threads.pop(
                    watch_id,
                    None,
                )

                self._stop_events.pop(
                    watch_id,
                    None,
                )

            logger.info(
                "Watch %s runner stopped.",
                watch_id,
            )

    # -----------------------------------------------------
    # Start all active watches
    # -----------------------------------------------------

    def start_all(
        self,
        max_cycles: int | None = None,
    ) -> List[str]:

        started = []

        records = (
            self.watch_manager
            .list_watch_records()
        )

        for record in records:

            if not record.watch.active:
                continue

            if self.start_watch(
                record.watch_id,
                max_cycles=max_cycles,
            ):

                started.append(
                    record.watch_id
                )

        return started

    # -----------------------------------------------------
    # Stop one watch
    # -----------------------------------------------------

    def stop_watch(
        self,
        watch_id: str,
    ) -> bool:

        watch_id = watch_id.strip()

        with self._lock:

            stop_event = self._stop_events.get(
                watch_id
            )

            thread = self._threads.get(
                watch_id
            )

            if stop_event is None:
                return False

            stop_event.set()

        logger.info(
            "Stop requested for watch %s.",
            watch_id,
        )

        if thread is not None:
            thread.join()

        return True

    # -----------------------------------------------------
    # Stop all watches
    # -----------------------------------------------------

    def stop_all(self) -> None:

        with self._lock:
            watch_ids = list(
                self._stop_events.keys()
            )

        for watch_id in watch_ids:
            self.stop_watch(
                watch_id
            )

        logger.info(
            "All running watches stopped."
        )

    # -----------------------------------------------------
    # Remove runtime state
    # -----------------------------------------------------

    def remove_watch(
        self,
        watch_id: str,
    ) -> bool:
        """
        Stop a watch and remove its runtime state.

        The persistent Watch record is not deleted here.
        """

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        stopped = self.stop_watch(
            watch_id
        )

        return stopped

    # -----------------------------------------------------
    # Clear persistent watch state
    # -----------------------------------------------------

    def clear_watch_state(
        self,
        watch_id: str,
    ) -> bool:
        """
        Clear persistent monitoring state for a watch.

        The watch itself is not deleted here.
        """

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        runner = self.runner_factory(
            watch_id
        )

        runner.clear_state()

        logger.info(
            "Cleared state for watch %s.",
            watch_id,
        )

        return True

    # -----------------------------------------------------
    # Clear notification history
    # -----------------------------------------------------

    def clear_watch_history(
        self,
        watch_id: str,
    ) -> bool:
        """
        Clear persisted notification history for a watch.

        The watch itself is not deleted here.
        """

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        runner = self.runner_factory(
            watch_id
        )

        runner.clear_history()

        logger.info(
            "Cleared history for watch %s.",
            watch_id,
        )

        return True

    # -----------------------------------------------------
    # Status
    # -----------------------------------------------------

    def get_watch_state(
        self,
        watch_id: str,
    ) -> Dict:
        """
        Return the latest persisted monitoring state
        for a watch.
        """

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        runner = self.runner_factory(
            watch_id
        )

        return runner.get_state()

    # -----------------------------------------------------
    # History
    # -----------------------------------------------------

    # -----------------------------------------------------
    # Health
    # -----------------------------------------------------

    def get_watch_health(
        self,
        watch_id: str,
    ) -> Dict:
        """
        Return the latest persisted health information
        for a watch.
        """

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        runner = self.runner_factory(
            watch_id
        )

        return runner.get_health()

    def clear_watch_health(
        self,
        watch_id: str,
    ) -> bool:
        """
        Clear persisted health information for a watch.
        """

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        runner = self.runner_factory(
            watch_id
        )

        runner.clear_health()

        logger.info(
            "Cleared health for watch %s.",
            watch_id,
        )

        return True

    # -----------------------------------------------------
    # History
    # -----------------------------------------------------

    def get_watch_history(
        self,
        watch_id: str,
    ) -> list:
        """
        Return persisted notification history
        for a watch.
        """

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        runner = self.runner_factory(
            watch_id
        )

        return runner.get_history()

    # -----------------------------------------------------
    # Runtime status
    # -----------------------------------------------------

    def is_running(
        self,
        watch_id: str,
    ) -> bool:

        with self._lock:

            thread = self._threads.get(
                watch_id
            )

            return (
                thread is not None
                and thread.is_alive()
            )

    def running_watch_ids(
        self,
    ) -> List[str]:

        with self._lock:

            return [
                watch_id
                for watch_id, thread
                in self._threads.items()
                if thread.is_alive()
            ]