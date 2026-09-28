from datetime import date

from app.models import Watch
from app.watch_manager import WatchManager
from app.watch_repository import WatchRepository


def create_watch() -> Watch:
    return Watch(
        movie="Resident Evil",
        target_date=date(2026, 9, 18),
        city="Hyderabad",
        cinemas=["PVR"],
    )


def test_create_watch(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    manager = WatchManager(
        repository
    )

    watch = create_watch()

    result = manager.create_watch(
        "watch-001",
        watch,
    )

    assert result.movie == "Resident Evil"

    stored = manager.get_watch(
        "watch-001"
    )

    assert stored is not None
    assert stored.movie == "Resident Evil"


def test_list_watches(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    manager = WatchManager(
        repository
    )

    manager.create_watch(
        "watch-001",
        create_watch(),
    )

    manager.create_watch(
        "watch-002",
        Watch(
            movie="Avatar",
            target_date=date(
                2026,
                9,
                20,
            ),
            city="Hyderabad",
            cinemas=["Prasads"],
        ),
    )

    watches = manager.list_watches()

    assert len(watches) == 2


def test_update_watch(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    manager = WatchManager(
        repository
    )

    manager.create_watch(
        "watch-001",
        create_watch(),
    )

    updated = Watch(
        movie="Resident Evil",
        target_date=date(
            2026,
            9,
            19,
        ),
        city="Hyderabad",
        cinemas=["AMB Cinemas"],
    )

    manager.update_watch(
        "watch-001",
        updated,
    )

    result = manager.get_watch(
        "watch-001"
    )

    assert result is not None
    assert result.target_date == date(
        2026,
        9,
        19,
    )
    assert result.cinemas == [
        "AMB Cinemas"
    ]


def test_pause_watch(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    manager = WatchManager(
        repository
    )

    manager.create_watch(
        "watch-001",
        create_watch(),
    )

    result = manager.pause_watch(
        "watch-001"
    )

    assert result.active is False

    stored = manager.get_watch(
        "watch-001"
    )

    assert stored is not None
    assert stored.active is False


def test_resume_watch(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    manager = WatchManager(
        repository
    )

    manager.create_watch(
        "watch-001",
        create_watch(),
    )

    manager.pause_watch(
        "watch-001"
    )

    result = manager.resume_watch(
        "watch-001"
    )

    assert result.active is True

    stored = manager.get_watch(
        "watch-001"
    )

    assert stored is not None
    assert stored.active is True


def test_complete_watch(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    manager = WatchManager(
        repository
    )

    manager.create_watch(
        "watch-001",
        create_watch(),
    )

    result = manager.complete_watch(
        "watch-001"
    )

    assert result.active is False
    assert result.completed is True

    stored = manager.get_watch(
        "watch-001"
    )

    assert stored is not None
    assert stored.active is False
    assert stored.completed is True


def test_completed_watch_cannot_be_resumed(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    manager = WatchManager(
        repository
    )

    manager.create_watch(
        "watch-001",
        create_watch(),
    )

    manager.complete_watch(
        "watch-001"
    )

    try:
        manager.resume_watch(
            "watch-001"
        )
        assert False
    except ValueError as error:
        assert str(error) == (
            "Completed watches cannot be resumed"
        )


def test_delete_watch(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    manager = WatchManager(
        repository
    )

    manager.create_watch(
        "watch-001",
        create_watch(),
    )

    result = manager.delete_watch(
        "watch-001"
    )

    assert result is True

    assert manager.get_watch(
        "watch-001"
    ) is None


def test_pause_unknown_watch(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    manager = WatchManager(
        repository
    )

    try:
        manager.pause_watch(
            "does-not-exist"
        )
        assert False
    except ValueError as error:
        assert "Watch not found" in str(error)


def test_resume_unknown_watch(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    manager = WatchManager(
        repository
    )

    try:
        manager.resume_watch(
            "does-not-exist"
        )
        assert False
    except ValueError as error:
        assert "Watch not found" in str(error)


def test_empty_watch_id_is_rejected(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    manager = WatchManager(
        repository
    )

    try:
        manager.create_watch(
            "   ",
            create_watch(),
        )
        assert False
    except ValueError as error:
        assert "Watch ID cannot be empty" in str(error)