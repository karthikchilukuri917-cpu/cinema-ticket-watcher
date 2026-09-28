from pathlib import Path

from app.watch_state import WatchStateStore


def test_new_watch_has_empty_state(tmp_path):
    store = WatchStateStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    assert store.load() == {}


def test_save_and_load_state(tmp_path):
    store = WatchStateStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    state = {
        "show-001": {
            "status": "AVAILABLE",
            "available_tickets": 5,
        }
    }

    store.save(state)

    result = store.load()

    assert result == state


def test_state_file_uses_watch_id(tmp_path):
    store = WatchStateStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    store.save(
        {
            "show-001": {
                "status": "AVAILABLE"
            }
        }
    )

    expected_file = (
        tmp_path / "watch-001.json"
    )

    assert expected_file.exists()


def test_different_watches_have_different_state_files(
    tmp_path,
):
    watch_one = WatchStateStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    watch_two = WatchStateStore(
        watch_id="watch-002",
        directory=tmp_path,
    )

    watch_one.save(
        {
            "show-001": {
                "status": "AVAILABLE"
            }
        }
    )

    watch_two.save(
        {
            "show-002": {
                "status": "SOLD_OUT"
            }
        }
    )

    assert watch_one.load() == {
        "show-001": {
            "status": "AVAILABLE"
        }
    }

    assert watch_two.load() == {
        "show-002": {
            "status": "SOLD_OUT"
        }
    }


def test_watches_do_not_overwrite_each_other(
    tmp_path,
):
    watch_one = WatchStateStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    watch_two = WatchStateStore(
        watch_id="watch-002",
        directory=tmp_path,
    )

    watch_one.save(
        {
            "resident-evil": {
                "status": "AVAILABLE"
            }
        }
    )

    watch_two.save(
        {
            "avatar": {
                "status": "AVAILABLE"
            }
        }
    )

    assert "avatar" not in watch_one.load()
    assert "resident-evil" not in watch_two.load()


def test_state_persists_between_instances(
    tmp_path,
):
    file_path = Path(tmp_path)

    store_one = WatchStateStore(
        watch_id="watch-001",
        directory=file_path,
    )

    state = {
        "show-001": {
            "status": "AVAILABLE",
            "available_tickets": 4,
        }
    }

    store_one.save(state)

    # Simulate application restart.
    store_two = WatchStateStore(
        watch_id="watch-001",
        directory=file_path,
    )

    assert store_two.load() == state


def test_clear_removes_state(tmp_path):
    store = WatchStateStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    store.save(
        {
            "show-001": {
                "status": "AVAILABLE"
            }
        }
    )

    assert store.load() != {}

    store.clear()

    assert store.load() == {}


def test_clear_nonexistent_state_does_not_fail(
    tmp_path,
):
    store = WatchStateStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    store.clear()

    assert store.load() == {}


def test_empty_watch_id_is_rejected(tmp_path):
    try:

        WatchStateStore(
            watch_id="   ",
            directory=tmp_path,
        )

        assert False

    except ValueError as error:

        assert "Watch ID cannot be empty" in str(
            error
        )


def test_invalid_state_is_rejected(tmp_path):
    store = WatchStateStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    try:

        store.save(
            ["invalid", "state"]
        )

        assert False

    except ValueError as error:

        assert "Watch state must be a dictionary" in str(
            error
        )


def test_invalid_json_returns_empty_state(
    tmp_path,
):
    store = WatchStateStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    store.file_path.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    assert store.load() == {}


def test_non_dictionary_json_returns_empty_state(
    tmp_path,
):
    store = WatchStateStore(
        watch_id="watch-001",
        directory=tmp_path,
    )

    store.file_path.write_text(
        '["not", "a", "dictionary"]',
        encoding="utf-8",
    )

    assert store.load() == {}
