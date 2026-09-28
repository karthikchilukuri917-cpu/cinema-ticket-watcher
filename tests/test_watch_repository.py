from datetime import date

from app.models import Watch
from app.watch_repository import WatchRepository


def create_test_watch() -> Watch:
    return Watch(
        movie="Resident Evil",
        target_date=date(2026, 9, 18),
        city="Hyderabad",
        cinemas=[
            "PVR",
            "AMB Cinemas",
        ],
    )


def test_create_and_get_watch(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    watch = create_test_watch()

    repository.create(
        watch_id="watch-001",
        watch=watch,
    )

    result = repository.get(
        "watch-001"
    )

    assert result is not None
    assert result.movie == "Resident Evil"
    assert result.target_date == date(
        2026,
        9,
        18,
    )
    assert result.city == "Hyderabad"
    assert result.cinemas == [
        "PVR",
        "AMB Cinemas",
    ]
    assert result.active is True


def test_get_unknown_watch_returns_none(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    result = repository.get(
        "does-not-exist"
    )

    assert result is None


def test_list_watches(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    watch_one = create_test_watch()

    watch_two = Watch(
        movie="Avatar",
        target_date=date(2026, 9, 20),
        city="Hyderabad",
        cinemas=["Prasads"],
    )

    repository.create(
        "watch-001",
        watch_one,
    )

    repository.create(
        "watch-002",
        watch_two,
    )

    watches = repository.list()

    assert len(watches) == 2

    movies = {
        watch.movie
        for watch in watches
    }

    assert movies == {
        "Resident Evil",
        "Avatar",
    }


def test_update_watch(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    watch = create_test_watch()

    repository.create(
        "watch-001",
        watch,
    )

    updated_watch = Watch(
        movie="Resident Evil",
        target_date=date(2026, 9, 19),
        city="Hyderabad",
        cinemas=["PVR"],
    )

    repository.update(
        "watch-001",
        updated_watch,
    )

    result = repository.get(
        "watch-001"
    )

    assert result is not None
    assert result.target_date == date(
        2026,
        9,
        19,
    )
    assert result.cinemas == ["PVR"]


def test_delete_watch(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    watch = create_test_watch()

    repository.create(
        "watch-001",
        watch,
    )

    deleted = repository.delete(
        "watch-001"
    )

    assert deleted is True
    assert repository.get(
        "watch-001"
    ) is None


def test_delete_unknown_watch_returns_false(tmp_path):
    repository = WatchRepository(
        tmp_path / "watches.json"
    )

    deleted = repository.delete(
        "does-not-exist"
    )

    assert deleted is False


def test_repository_persists_between_instances(tmp_path):
    file_path = (
        tmp_path / "watches.json"
    )

    repository_one = WatchRepository(
        file_path
    )

    watch = create_test_watch()

    repository_one.create(
        "watch-001",
        watch,
    )

    # Simulate application restart by creating
    # a completely new repository instance.
    repository_two = WatchRepository(
        file_path
    )

    result = repository_two.get(
        "watch-001"
    )

    assert result is not None
    assert result.movie == "Resident Evil"
    assert result.target_date == date(
        2026,
        9,
        18,
    )
    assert result.city == "Hyderabad"
    assert result.cinemas == [
        "PVR",
        "AMB Cinemas",
    ]
    assert result.active is True