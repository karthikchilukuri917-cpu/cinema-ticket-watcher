import time
from pathlib import Path

from app.models import Watch
from app.watch_manager import WatchManager
from app.watch_repository import WatchRepository
from app.watch_scheduler import WatchScheduler
from app.watch_runner import WatchRunner


def make_watch(
    movie: str = "Resident Evil",
) -> Watch:
    from datetime import date

    return Watch(
        movie=movie,
        target_date=date(2026, 9, 18),
        city="Hyderabad",
        cinemas=["PVR"],
    )


class FakeRunner:
    def __init__(self):
        self.run_calls = []
        self.started = False

    def run(
        self,
        watch,
        max_cycles=None,
        stop_event=None,
    ):
        self.run_calls.append(
            {
                "watch": watch,
                "max_cycles": max_cycles,
                "stop_event": stop_event,
            }
        )

        self.started = True

        # Wait until scheduler requests stop.
        if stop_event is not None:
            stop_event.wait()


def make_scheduler(
    tmp_path: Path,
):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    manager = WatchManager(
        repository
    )

    runners = {}

    def runner_factory(
        watch_id: str,
    ):
        runner = FakeRunner()
        runners[watch_id] = runner
        return runner

    scheduler = WatchScheduler(
        watch_manager=manager,
        runner_factory=runner_factory,
    )

    return (
        scheduler,
        manager,
        runners,
    )


def wait_until_running(
    scheduler,
    watch_id,
    timeout=1.0,
):
    deadline = time.time() + timeout

    while time.time() < deadline:

        if scheduler.is_running(
            watch_id
        ):
            return True

        time.sleep(0.01)

    return False


def test_start_watch(
    tmp_path,
):
    (
        scheduler,
        manager,
        runners,
    ) = make_scheduler(tmp_path)

    manager.create_watch(
        "watch-1",
        make_watch(),
    )

    started = scheduler.start_watch(
        "watch-1"
    )

    assert started is True

    assert wait_until_running(
        scheduler,
        "watch-1",
    )

    assert "watch-1" in runners

    scheduler.stop_watch(
        "watch-1"
    )


def test_unknown_watch_is_not_started(
    tmp_path,
):
    (
        scheduler,
        manager,
        runners,
    ) = make_scheduler(tmp_path)

    started = scheduler.start_watch(
        "does-not-exist"
    )

    assert started is False
    assert runners == {}


def test_inactive_watch_is_not_started(
    tmp_path,
):
    (
        scheduler,
        manager,
        runners,
    ) = make_scheduler(tmp_path)

    watch = make_watch()
    watch.active = False

    manager.create_watch(
        "watch-1",
        watch,
    )

    started = scheduler.start_watch(
        "watch-1"
    )

    assert started is False
    assert runners == {}


def test_duplicate_start_is_prevented(
    tmp_path,
):
    (
        scheduler,
        manager,
        runners,
    ) = make_scheduler(tmp_path)

    manager.create_watch(
        "watch-1",
        make_watch(),
    )

    first = scheduler.start_watch(
        "watch-1"
    )

    assert first is True

    assert wait_until_running(
        scheduler,
        "watch-1",
    )

    second = scheduler.start_watch(
        "watch-1"
    )

    assert second is False

    assert len(runners) == 1

    scheduler.stop_watch(
        "watch-1"
    )


def test_start_all_starts_only_active_watches(
    tmp_path,
):
    (
        scheduler,
        manager,
        runners,
    ) = make_scheduler(tmp_path)

    manager.create_watch(
        "watch-1",
        make_watch("Movie A"),
    )

    inactive = make_watch("Movie B")
    inactive.active = False

    manager.create_watch(
        "watch-2",
        inactive,
    )

    manager.create_watch(
        "watch-3",
        make_watch("Movie C"),
    )

    started = scheduler.start_all()

    assert set(started) == {
        "watch-1",
        "watch-3",
    }

    assert wait_until_running(
        scheduler,
        "watch-1",
    )

    assert wait_until_running(
        scheduler,
        "watch-3",
    )

    assert "watch-2" not in runners

    scheduler.stop_all()


def test_stop_watch_stops_runner(
    tmp_path,
):
    (
        scheduler,
        manager,
        runners,
    ) = make_scheduler(tmp_path)

    manager.create_watch(
        "watch-1",
        make_watch(),
    )

    scheduler.start_watch(
        "watch-1"
    )

    assert wait_until_running(
        scheduler,
        "watch-1",
    )

    stopped = scheduler.stop_watch(
        "watch-1"
    )

    assert stopped is True

    deadline = time.time() + 1.0

    while time.time() < deadline:

        if not scheduler.is_running(
            "watch-1"
        ):
            break

        time.sleep(0.01)

    assert scheduler.is_running(
        "watch-1"
    ) is False


def test_stop_unknown_watch_returns_false(
    tmp_path,
):
    (
        scheduler,
        manager,
        runners,
    ) = make_scheduler(tmp_path)

    assert (
        scheduler.stop_watch(
            "unknown"
        )
        is False
    )


def test_stop_all_stops_all_running_watches(
    tmp_path,
):
    (
        scheduler,
        manager,
        runners,
    ) = make_scheduler(tmp_path)

    manager.create_watch(
        "watch-1",
        make_watch("Movie A"),
    )

    manager.create_watch(
        "watch-2",
        make_watch("Movie B"),
    )

    scheduler.start_all()

    assert wait_until_running(
        scheduler,
        "watch-1",
    )

    assert wait_until_running(
        scheduler,
        "watch-2",
    )

    scheduler.stop_all()

    deadline = time.time() + 1.0

    while time.time() < deadline:

        if not scheduler.running_watch_ids():
            break

        time.sleep(0.01)

    assert scheduler.running_watch_ids() == []


def test_running_watch_ids(
    tmp_path,
):
    (
        scheduler,
        manager,
        runners,
    ) = make_scheduler(tmp_path)

    manager.create_watch(
        "watch-1",
        make_watch(),
    )

    manager.create_watch(
        "watch-2",
        make_watch(),
    )

    scheduler.start_all()

    assert wait_until_running(
        scheduler,
        "watch-1",
    )

    assert wait_until_running(
        scheduler,
        "watch-2",
    )

    assert set(
        scheduler.running_watch_ids()
    ) == {
        "watch-1",
        "watch-2",
    }

    scheduler.stop_all()
