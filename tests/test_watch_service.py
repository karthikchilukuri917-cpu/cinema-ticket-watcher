from datetime import date

from app.models import Watch
from app.watch_manager import WatchManager
from app.watch_repository import WatchRepository
from app.watch_service import WatchService


class FakeScheduler:
    """
    Test scheduler used to verify the WatchService
    lifecycle without creating real background threads.
    """

    def __init__(self):
        self.running = set()

        self.started_watch_ids = []
        self.stopped_watch_ids = []
        self.cleared_history_watch_ids = []
        self.watch_health = {}

        self.start_result = True

    def start_watch(
        self,
        watch_id,
        max_cycles=None,
    ):
        if not self.start_result:
            return False

        self.started_watch_ids.append(
            watch_id
        )

        self.running.add(
            watch_id
        )

        return True

    def stop_watch(
        self,
        watch_id,
    ):
        self.stopped_watch_ids.append(
            watch_id
        )

        self.running.discard(
            watch_id
        )

        return True

    def is_running(
        self,
        watch_id,
    ):
        return watch_id in self.running

    def clear_watch_state(
        self,
        watch_id: str,
    ) -> None:
        return None

    def clear_watch_history(
        self,
        watch_id: str,
    ) -> bool:
        self.cleared_history_watch_ids.append(
            watch_id
        )

        return True

    def get_watch_health(
        self,
        watch_id,
    ):
        return self.watch_health.get(
            watch_id,
            {},
        )

    def clear_watch_health(
        self,
        watch_id,
    ):
        self.watch_health.pop(
            watch_id,
            None,
        )


def create_test_service(
    tmp_path,
):
    repository = WatchRepository(
        file_path=(
            tmp_path
            / "watches.json"
        )
    )

    manager = WatchManager(
        repository=repository
    )

    scheduler = FakeScheduler()

    service = WatchService(
        watch_manager=manager,
        scheduler=scheduler,
    )

    return (
        service,
        manager,
        scheduler,
    )


def create_watch(
    active=True,
):
    return Watch(
        movie="Resident Evil",
        target_date=date(
            2026,
            9,
            18,
        ),
        city="Hyderabad",
        cinemas=[
            "PVR",
            "AMB Cinemas",
        ],
        active=active,
    )


def test_create_watch_persists_and_starts(
    tmp_path,
):
    service, manager, scheduler = (
        create_test_service(
            tmp_path
        )
    )

    watch = create_watch()

    created = service.create_watch(
        watch_id="watch-1",
        watch=watch,
    )

    assert created is watch

    stored = manager.get_watch(
        "watch-1"
    )

    assert stored is not None
    assert stored.movie == "Resident Evil"
    assert stored.city == "Hyderabad"
    assert stored.cinemas == [
        "PVR",
        "AMB Cinemas",
    ]
    assert stored.active is True

    assert (
        "watch-1"
        in scheduler.started_watch_ids
    )

    assert scheduler.is_running(
        "watch-1"
    )


def test_create_watch_rolls_back_when_start_fails(
    tmp_path,
):
    service, manager, scheduler = (
        create_test_service(
            tmp_path
        )
    )

    scheduler.start_result = False

    watch = create_watch()

    try:
        service.create_watch(
            watch_id="watch-1",
            watch=watch,
        )
        assert False
    except RuntimeError as error:
        assert str(error) == (
            "Watch was created but could not be started."
        )

    assert (
        manager.get_watch(
            "watch-1"
        )
        is None
    )


def test_get_watch_returns_watch_record(
    tmp_path,
):
    service, manager, scheduler = (
        create_test_service(
            tmp_path
        )
    )

    manager.create_watch(
        "watch-1",
        create_watch(),
    )

    record = service.get_watch(
        "watch-1"
    )

    assert record is not None
    assert record.watch_id == "watch-1"
    assert record.watch.movie == (
        "Resident Evil"
    )


def test_get_unknown_watch_returns_none(
    tmp_path,
):
    service, _, _ = (
        create_test_service(
            tmp_path
        )
    )

    record = service.get_watch(
        "unknown"
    )

    assert record is None


def test_list_watches_returns_persisted_records(
    tmp_path,
):
    service, manager, scheduler = (
        create_test_service(
            tmp_path
        )
    )

    manager.create_watch(
        "watch-1",
        create_watch(),
    )

    manager.create_watch(
        "watch-2",
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

    records = service.list_watches()

    assert len(records) == 2

    assert records[0].watch_id == (
        "watch-1"
    )
    assert records[1].watch_id == (
        "watch-2"
    )

    assert records[0].watch.movie == (
        "Resident Evil"
    )
    assert records[1].watch.movie == (
        "Avatar"
    )


def test_update_watch_stops_and_restarts_active_watch(
    tmp_path,
):
    service, manager, scheduler = (
        create_test_service(
            tmp_path
        )
    )

    manager.create_watch(
        "watch-1",
        create_watch(),
    )

    scheduler.running.add(
        "watch-1"
    )

    updated_watch = create_watch()

    saved = service.update_watch(
        watch_id="watch-1",
        watch=updated_watch,
    )

    assert saved is updated_watch

    assert (
        "watch-1"
        in scheduler.stopped_watch_ids
    )

    assert (
        "watch-1"
        in scheduler.started_watch_ids
    )

    assert scheduler.is_running(
        "watch-1"
    )

    stored = manager.get_watch(
        "watch-1"
    )

    assert stored is not None
    assert stored.movie == "Resident Evil"
    assert stored.cinemas == [
        "PVR",
        "AMB Cinemas",
    ]
    assert stored.active is True


def test_update_watch_does_not_start_inactive_watch(
    tmp_path,
):
    service, manager, scheduler = (
        create_test_service(
            tmp_path
        )
    )

    manager.create_watch(
        "watch-1",
        create_watch(
            active=False
        ),
    )

    updated_watch = create_watch(
        active=False,
    )

    saved = service.update_watch(
        watch_id="watch-1",
        watch=updated_watch,
    )

    assert saved.active is False

    assert (
        "watch-1"
        not in scheduler.started_watch_ids
    )

    assert not scheduler.is_running(
        "watch-1"
    )


def test_update_unknown_watch_raises_error(
    tmp_path,
):
    service, _, _ = (
        create_test_service(
            tmp_path
        )
    )

    try:
        service.update_watch(
            watch_id="unknown",
            watch=create_watch(),
        )

        assert False

    except ValueError as error:
        assert str(error) == (
            "Watch not found: unknown"
        )


def test_pause_watch_stops_and_deactivates(
    tmp_path,
):
    service, manager, scheduler = (
        create_test_service(
            tmp_path
        )
    )

    manager.create_watch(
        "watch-1",
        create_watch(),
    )

    scheduler.running.add(
        "watch-1"
    )

    paused = service.pause_watch(
        "watch-1"
    )

    assert paused.active is False

    assert (
        "watch-1"
        in scheduler.stopped_watch_ids
    )

    assert not scheduler.is_running(
        "watch-1"
    )

    stored = manager.get_watch(
        "watch-1"
    )

    assert stored is not None
    assert stored.active is False


def test_pause_unknown_watch_raises_error(
    tmp_path,
):
    service, _, _ = (
        create_test_service(
            tmp_path
        )
    )

    try:
        service.pause_watch(
            "unknown"
        )

        assert False

    except ValueError as error:
        assert str(error) == (
            "Watch not found: unknown"
        )


def test_resume_watch_activates_and_starts(
    tmp_path,
):
    service, manager, scheduler = (
        create_test_service(
            tmp_path
        )
    )

    manager.create_watch(
        "watch-1",
        create_watch(
            active=False
        ),
    )

    resumed = service.resume_watch(
        "watch-1"
    )

    assert resumed.active is True

    assert (
        "watch-1"
        in scheduler.started_watch_ids
    )

    assert scheduler.is_running(
        "watch-1"
    )

    stored = manager.get_watch(
        "watch-1"
    )

    assert stored is not None
    assert stored.active is True


def test_resume_already_running_watch_does_not_start_twice(
    tmp_path,
):
    service, manager, scheduler = (
        create_test_service(
            tmp_path
        )
    )

    manager.create_watch(
        "watch-1",
        create_watch(),
    )

    scheduler.running.add(
        "watch-1"
    )

    started_before = len(
        scheduler.started_watch_ids
    )

    resumed = service.resume_watch(
        "watch-1"
    )

    assert resumed.active is True

    assert len(
        scheduler.started_watch_ids
    ) == started_before

    assert scheduler.is_running(
        "watch-1"
    )


def test_resume_unknown_watch_raises_error(
    tmp_path,
):
    service, _, _ = (
        create_test_service(
            tmp_path
        )
    )

    try:
        service.resume_watch(
            "unknown"
        )

        assert False

    except ValueError as error:
        assert str(error) == (
            "Watch not found: unknown"
        )


def test_resume_rolls_back_when_start_fails(
    tmp_path,
):
    service, manager, scheduler = (
        create_test_service(
            tmp_path
        )
    )

    manager.create_watch(
        "watch-1",
        create_watch(
            active=False
        ),
    )

    scheduler.start_result = False

    try:
        service.resume_watch(
            "watch-1"
        )

        assert False

    except RuntimeError as error:
        assert str(error) == (
            "Watch could not be started."
        )

    stored = manager.get_watch(
        "watch-1"
    )

    assert stored is not None
    assert stored.active is False


def test_delete_watch_stops_and_removes(
    tmp_path,
):
    service, manager, scheduler = (
        create_test_service(
            tmp_path
        )
    )

    manager.create_watch(
        "watch-1",
        create_watch(),
    )

    scheduler.running.add(
        "watch-1"
    )

    state_dir = tmp_path / "watches"
    state_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    state_file = state_dir / "watch-1.json"

    state_file.write_text(
        '{"last_result": "AVAILABLE"}',
        encoding="utf-8",
    )

    assert state_file.exists()

    deleted = service.delete_watch(
        "watch-1"
    )

    assert deleted is True

    assert (
        "watch-1"
        in scheduler.stopped_watch_ids
    )

    assert (
        "watch-1"
        in scheduler.cleared_history_watch_ids
    )

    assert not scheduler.is_running(
        "watch-1"
    )

    assert (
        manager.get_watch(
            "watch-1"
        )
        is None
    )


def test_delete_unknown_watch_returns_false(
    tmp_path,
):
    service, _, _ = (
        create_test_service(
            tmp_path
        )
    )

    deleted = service.delete_watch(
        "unknown"
    )

    assert deleted is False


def test_complete_watch_lifecycle(
    tmp_path,
):
    """
    Integration-style lifecycle test.

    Verifies:

        create
          ↓
        persist
          ↓
        start
          ↓
        running
          ↓
        update
          ↓
        restart
          ↓
        pause
          ↓
        stop
          ↓
        resume
          ↓
        start
          ↓
        delete
          ↓
        remove
    """

    service, manager, scheduler = (
        create_test_service(
            tmp_path
        )
    )

    # -------------------------------------------------
    # 1. CREATE
    # -------------------------------------------------

    watch = create_watch()

    created = service.create_watch(
        watch_id="resident-evil-hyd",
        watch=watch,
    )

    assert created.movie == (
        "Resident Evil"
    )

    # -------------------------------------------------
    # 2. PERSISTENCE
    # -------------------------------------------------

    stored = manager.get_watch(
        "resident-evil-hyd"
    )

    assert stored is not None
    assert stored.movie == (
        "Resident Evil"
    )
    assert stored.city == "Hyderabad"
    assert stored.cinemas == [
        "PVR",
        "AMB Cinemas",
    ]
    assert stored.active is True

    # -------------------------------------------------
    # 3. STARTED
    # -------------------------------------------------

    assert (
        "resident-evil-hyd"
        in scheduler.started_watch_ids
    )

    assert scheduler.is_running(
        "resident-evil-hyd"
    )

    # -------------------------------------------------
    # 4. UPDATE
    # -------------------------------------------------

    updated_watch = create_watch()

    updated = service.update_watch(
        watch_id="resident-evil-hyd",
        watch=updated_watch,
    )

    assert updated.movie == (
        "Resident Evil"
    )
    assert updated.cinemas == [
        "PVR",
        "AMB Cinemas",
    ]
    assert updated.active is True

    # -------------------------------------------------
    # 5. OLD RUNNER STOPPED
    # -------------------------------------------------

    assert (
        "resident-evil-hyd"
        in scheduler.stopped_watch_ids
    )

    # -------------------------------------------------
    # 6. UPDATED WATCH RESTARTED
    # -------------------------------------------------

    assert (
        scheduler.started_watch_ids.count(
            "resident-evil-hyd"
        )
        == 2
    )

    assert scheduler.is_running(
        "resident-evil-hyd"
    )

    # -------------------------------------------------
    # 7. PAUSE
    # -------------------------------------------------

    paused = service.pause_watch(
        "resident-evil-hyd"
    )

    assert paused.active is False

    assert not scheduler.is_running(
        "resident-evil-hyd"
    )

    # -------------------------------------------------
    # 8. RESUME
    # -------------------------------------------------

    resumed = service.resume_watch(
        "resident-evil-hyd"
    )

    assert resumed.active is True

    assert scheduler.is_running(
        "resident-evil-hyd"
    )

    # -------------------------------------------------
    # 9. DELETE
    # -------------------------------------------------

    deleted = service.delete_watch(
        "resident-evil-hyd"
    )

    assert deleted is True

    assert (
        "resident-evil-hyd"
        in scheduler.cleared_history_watch_ids
    )

    # -------------------------------------------------
    # 10. REMOVED FROM STORAGE
    # -------------------------------------------------

    assert (
        manager.get_watch(
            "resident-evil-hyd"
        )
        is None
    )

    # -------------------------------------------------
    # 11. RUNNER STOPPED
    # -------------------------------------------------

    assert not scheduler.is_running(
        "resident-evil-hyd"
    )

    assert (
        scheduler.stopped_watch_ids.count(
            "resident-evil-hyd"
        )
        >= 2
    )