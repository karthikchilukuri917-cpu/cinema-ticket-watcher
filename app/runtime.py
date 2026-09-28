from app.config import get_source_name
from app.notifications import notify
from app.source_factory import create_source
from app.watch_manager import WatchManager
from app.postgres_watch_repository import (
    PostgreSQLWatchRepository,
)
from app.watch_runner import WatchRunner
from app.watch_scheduler import WatchScheduler
from app.watch_service import WatchService


repository = PostgreSQLWatchRepository()

watch_manager = WatchManager(
    repository=repository,
)


def create_runner_factory():

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


scheduler = WatchScheduler(
    watch_manager=watch_manager,
    runner_factory=create_runner_factory(),
)


watch_service = WatchService(
    watch_manager=watch_manager,
    scheduler=scheduler,
)