from app.watch_history import WatchHistoryStore


def test_new_watch_has_empty_history(tmp_path):
    store = WatchHistoryStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    assert store.load() == []


def test_add_and_load_history(tmp_path):
    store = WatchHistoryStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    changes = {
        "PVR": {
            "19:30": {
                "previous": "SOLD_OUT",
                "current": "AVAILABLE",
                "previous_tickets": 0,
                "current_tickets": 2,
                "show_id": "session-123",
            }
        }
    }

    store.add(changes)

    history = store.load()

    assert len(history) == 1

    event = history[0]

    assert event["cinema"] == "PVR"
    assert event["show_time"] == "19:30"
    assert event["previous"] == "SOLD_OUT"
    assert event["current"] == "AVAILABLE"
    assert event["previous_tickets"] == 0
    assert event["current_tickets"] == 2
    assert event["show_id"] == "session-123"
    assert "timestamp" in event


def test_history_file_uses_watch_id(tmp_path):
    store = WatchHistoryStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    store.add(
        {
            "PVR": {
                "19:30": {
                    "previous": "SOLD_OUT",
                    "current": "AVAILABLE",
                }
            }
        }
    )

    expected_file = (
        tmp_path
        / "watch-001_history.json"
    )

    assert expected_file.exists()


def test_different_watches_have_different_history_files(
    tmp_path,
):
    watch_one = WatchHistoryStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    watch_two = WatchHistoryStore(
        watch_id="watch-002",
        directory=tmp_path,
    )

    watch_one.add(
        {
            "PVR": {
                "19:30": {
                    "current": "AVAILABLE",
                }
            }
        }
    )

    watch_two.add(
        {
            "INOX": {
                "20:00": {
                    "current": "AVAILABLE",
                }
            }
        }
    )

    assert len(watch_one.load()) == 1
    assert len(watch_two.load()) == 1

    assert (
        watch_one.load()[0]["cinema"]
        == "PVR"
    )

    assert (
        watch_two.load()[0]["cinema"]
        == "INOX"
    )


def test_history_appends_events(tmp_path):
    store = WatchHistoryStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    store.add(
        {
            "PVR": {
                "19:30": {
                    "current": "AVAILABLE",
                }
            }
        }
    )

    store.add(
        {
            "PVR": {
                "21:00": {
                    "current": "AVAILABLE",
                }
            }
        }
    )

    history = store.load()

    assert len(history) == 2
    assert history[0]["show_time"] == "19:30"
    assert history[1]["show_time"] == "21:00"


def test_clear_history(tmp_path):
    store = WatchHistoryStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    store.add(
        {
            "PVR": {
                "19:30": {
                    "current": "AVAILABLE",
                }
            }
        }
    )

    assert store.load() != []

    store.clear()

    assert store.load() == []


def test_clear_nonexistent_history_does_not_fail(
    tmp_path,
):
    store = WatchHistoryStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    store.clear()

    assert store.load() == []


def test_empty_watch_id_is_rejected(tmp_path):
    try:

        WatchHistoryStore(
            watch_id="   ",
            directory=tmp_path,
        )

        assert False

    except ValueError as error:

        assert "Watch ID cannot be empty" in str(
            error
        )


def test_invalid_changes_are_rejected(tmp_path):
    store = WatchHistoryStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    try:

        store.add(
            ["invalid"]
        )

        assert False

    except ValueError as error:

        assert (
            "History changes must be a dictionary"
            in str(error)
        )


def test_invalid_json_returns_empty_history(
    tmp_path,
):
    store = WatchHistoryStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    store.file_path.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    assert store.load() == []


def test_non_list_json_returns_empty_history(
    tmp_path,
):
    store = WatchHistoryStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    store.file_path.write_text(
        '{"not": "a list"}',
        encoding="utf-8",
    )

    assert store.load() == []