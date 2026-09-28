from datetime import date

from app.models import Watch
from app.sources.result import (
    SourceResult,
    SourceStatus,
)
from app.watch_runner import WatchRunner


def create_watch():
    return Watch(
        movie="Resident Evil",
        target_date=date(
            2026,
            9,
            18,
        ),
        city="Hyderabad",
        cinemas=["PVR"],
    )


class FakeSource:
    def __init__(
        self,
        watch,
    ):
        self.watch = watch

    def get_availability(
        self,
        watch,
    ):
        return SourceResult(
            status=SourceStatus.SUCCESS,
            data={},
        )


def test_runner_creates_watch_specific_state_store(
    tmp_path,
    monkeypatch,
):
    watch = create_watch()

    def source_factory(
        received_watch,
    ):
        return FakeSource(
            received_watch
        )

    captured = {}

    def fake_run_monitor(
        watch,
        fetch_availability,
        on_change,
        load_state,
        save_state,
        max_cycles,
        stop_event,
    ):
        captured["watch"] = watch
        captured["load_state"] = load_state
        captured["save_state"] = save_state
        captured["max_cycles"] = max_cycles
        captured["stop_event"] = stop_event

    monkeypatch.setattr(
        "app.watch_runner.run_monitor",
        fake_run_monitor,
    )

    runner = WatchRunner(
        watch_id="watch-001",
        source_factory=source_factory,
        on_change=lambda changes: None,
        state_directory=tmp_path,
    )

    runner.run(
        watch,
        max_cycles=3,
    )

    assert captured["watch"] is watch

    assert callable(
        captured["load_state"]
    )

    assert callable(
        captured["save_state"]
    )

    assert captured["max_cycles"] == 3

    assert captured["stop_event"] is None

    expected_state_file = (
        tmp_path
        / "watch-001.json"
    )

    assert (
        runner.state_store.file_path
        == expected_state_file
    )


def test_runner_uses_watch_specific_state(
    tmp_path,
    monkeypatch,
):
    watch = create_watch()

    def source_factory(
        received_watch,
    ):
        return FakeSource(
            received_watch
        )

    captured = {}

    def fake_run_monitor(
        watch,
        fetch_availability,
        on_change,
        load_state,
        save_state,
        max_cycles,
        stop_event,
    ):
        captured["load_state"] = load_state
        captured["save_state"] = save_state
        captured["stop_event"] = stop_event

    monkeypatch.setattr(
        "app.watch_runner.run_monitor",
        fake_run_monitor,
    )

    runner = WatchRunner(
        watch_id="watch-001",
        source_factory=source_factory,
        on_change=lambda changes: None,
        state_directory=tmp_path,
    )

    runner.run(
        watch,
        max_cycles=1,
    )

    captured["save_state"](
        {
            "show-1": {
                "status": "AVAILABLE",
            }
        }
    )

    loaded_state = (
        captured["load_state"]()
    )

    assert loaded_state == {
        "show-1": {
            "status": "AVAILABLE",
        }
    }

    assert captured["stop_event"] is None


def test_runner_passes_stop_event(
    tmp_path,
    monkeypatch,
):
    from threading import Event

    watch = create_watch()

    def source_factory(
        received_watch,
    ):
        return FakeSource(
            received_watch
        )

    captured = {}

    def fake_run_monitor(
        watch,
        fetch_availability,
        on_change,
        load_state,
        save_state,
        max_cycles,
        stop_event,
    ):
        captured["stop_event"] = stop_event

    monkeypatch.setattr(
        "app.watch_runner.run_monitor",
        fake_run_monitor,
    )

    runner = WatchRunner(
        watch_id="watch-001",
        source_factory=source_factory,
        on_change=lambda changes: None,
        state_directory=tmp_path,
    )

    stop_event = Event()

    runner.run(
        watch,
        max_cycles=1,
        stop_event=stop_event,
    )

    assert (
        captured["stop_event"]
        is stop_event
    )


def test_runner_clear_state(
    tmp_path,
):
    runner = WatchRunner(
        watch_id="watch-001",
        source_factory=lambda watch: (
            FakeSource(watch)
        ),
        on_change=lambda changes: None,
        state_directory=tmp_path,
    )

    runner.state_store.save(
        {
            "show-1": {
                "status": "AVAILABLE",
            }
        }
    )

    assert (
        runner.state_store.file_path.exists()
    )

    runner.clear_state()

    assert not (
        runner.state_store.file_path.exists()
    )


def test_runner_rejects_empty_watch_id(
    tmp_path,
):
    try:

        WatchRunner(
            watch_id="",
            source_factory=lambda watch: (
                FakeSource(watch)
            ),
            on_change=lambda changes: None,
            state_directory=tmp_path,
        )

        assert False

    except ValueError as error:

        assert str(error) == (
            "Watch ID cannot be empty."
        )


def test_runner_source_factory_receives_watch(
    tmp_path,
    monkeypatch,
):
    watch = create_watch()

    captured = {}

    def source_factory(
        received_watch,
    ):
        captured["watch"] = received_watch

        return FakeSource(
            received_watch
        )

    def fake_run_monitor(
        watch,
        fetch_availability,
        on_change,
        load_state,
        save_state,
        max_cycles,
        stop_event,
    ):
        pass

    monkeypatch.setattr(
        "app.watch_runner.run_monitor",
        fake_run_monitor,
    )

    runner = WatchRunner(
        watch_id="watch-001",
        source_factory=source_factory,
        on_change=lambda changes: None,
        state_directory=tmp_path,
    )

    runner.run(
        watch
    )

    assert (
        captured["watch"]
        is watch
    )


def test_runner_uses_watch_id_for_state_file(
    tmp_path,
):
    runner_one = WatchRunner(
        watch_id="watch-one",
        source_factory=lambda watch: (
            FakeSource(watch)
        ),
        on_change=lambda changes: None,
        state_directory=tmp_path,
    )

    runner_two = WatchRunner(
        watch_id="watch-two",
        source_factory=lambda watch: (
            FakeSource(watch)
        ),
        on_change=lambda changes: None,
        state_directory=tmp_path,
    )

    assert (
        runner_one.state_store.file_path
        != runner_two.state_store.file_path
    )

    assert (
        runner_one.state_store.file_path.name
        == "watch-one.json"
    )

    assert (
        runner_two.state_store.file_path.name
        == "watch-two.json"
    )
def test_runner_creates_watch_specific_history_store(
    tmp_path,
):
    runner = WatchRunner(
        watch_id="watch-001",
        source_factory=lambda watch: (
            FakeSource(watch)
        ),
        on_change=lambda changes: None,
        state_directory=tmp_path,
    )

    expected_history_file = (
        tmp_path
        / "watch-001_history.json"
    )

    assert (
        runner.history_store.file_path
        == expected_history_file
    )


def test_runner_get_history(
    tmp_path,
):
    runner = WatchRunner(
        watch_id="watch-001",
        source_factory=lambda watch: (
            FakeSource(watch)
        ),
        on_change=lambda changes: None,
        state_directory=tmp_path,
    )

    runner.history_store.add(
        {
            "PVR": {
                "19:30": {
                    "previous": "SOLD_OUT",
                    "current": "AVAILABLE",
                }
            }
        }
    )

    history = runner.get_history()

    assert len(history) == 1
    assert history[0]["cinema"] == "PVR"


def test_runner_clear_history(
    tmp_path,
):
    runner = WatchRunner(
        watch_id="watch-001",
        source_factory=lambda watch: (
            FakeSource(watch)
        ),
        on_change=lambda changes: None,
        state_directory=tmp_path,
    )

    runner.history_store.add(
        {
            "PVR": {
                "19:30": {
                    "current": "AVAILABLE",
                }
            }
        }
    )

    assert runner.get_history() != []

    runner.clear_history()

    assert runner.get_history() == []