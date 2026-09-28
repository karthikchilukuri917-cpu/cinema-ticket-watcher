import logging
import time

from app.config import (
    get_max_cycles,
    get_source_name,
)
from app.logging_config import configure_logging
from app.notifications import notify
from app.source_factory import create_source
from app.watch_manager import WatchManager
from app.watch_repository import WatchRepository
from app.watch_runner import WatchRunner
from app.watch_scheduler import WatchScheduler


logger = logging.getLogger(__name__)


def create_runner_factory():
    """
    Create the factory used by WatchScheduler.

    Each watch gets its own WatchRunner while sharing
    the configured cinema source factory and
    notification handler.
    """
    source_name = get_source_name()

    def runner_factory(
        watch_id: str,
    ) -> WatchRunner:
        return WatchRunner(
            watch_id=watch_id,
            source_factory=lambda watch: (
                create_source(source_name)
            ),
            on_change=notify,
        )

    return runner_factory


def main() -> None:
    """
    Start the multi-watch cinema ticket monitoring system.
    """
    configure_logging()

    max_cycles = get_max_cycles()

    logger.info(
        "Starting Cinema Ticket Watcher."
    )

    repository = WatchRepository()

    manager = WatchManager(
        repository=repository,
    )

    scheduler = WatchScheduler(
        watch_manager=manager,
        runner_factory=create_runner_factory(),
    )

    started = scheduler.start_all(
        max_cycles=max_cycles,
    )

    if not started:
        logger.warning(
            "No active watches found."
        )
        return

    logger.info(
        "Active watches started: %s",
        ", ".join(started),
    )

    try:

        while scheduler.running_watch_ids():
            time.sleep(1)

    except KeyboardInterrupt:

        logger.info(
            "Shutdown requested."
        )

    finally:

        scheduler.stop_all()

        logger.info(
            "All watches stopped."
        )


if __name__ == "__main__":
    main()