from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import api
from app.models import Watch
from app.watch_manager import WatchManager
from app.watch_repository import WatchRepository
from app.watch_service import WatchService


class FakeScheduler:
    """
    Lightweight scheduler used by API tests.

    It behaves like the part of WatchScheduler that
    WatchService and the API actually need.
    """

    def __init__(self):
        self.running = set()
        self.started_watch_ids = []
        self.stopped_watch_ids = []
        self.cleared_history_watch_ids = []

        self.watch_history = {}
        self.watch_health = {}

        self.start_result = True
        self.stop_result = True

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

        return self.stop_result

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

        self.watch_history.pop(
            watch_id,
            None,
        )

        return True

    def get_watch_state(
        self,
        watch_id,
    ):
        return {
            "session-123": {
                "movie": "Resident Evil",
                "cinema": "PVR",
                "show_date": "2026-09-18",
                "show_time": "19:30",
                "status": "AVAILABLE",
                "available_tickets": 5,
                "source_id": "session-123",
            }
        }

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

    def get_watch_history(
        self,
        watch_id,
    ):
        return self.watch_history.get(
            watch_id,
            [],
        )

    def running_watch_ids(self):
        return list(
            self.running
        )


def create_test_service(
    tmp_path,
):
    repository = WatchRepository(
        file_path=tmp_path / "watches.json"
    )

    manager = WatchManager(
        repository=repository
    )

    scheduler = FakeScheduler()

    service = WatchService(
        watch_manager=manager,
        scheduler=scheduler,
    )

    return service, manager, scheduler


@pytest.fixture
def client(
    tmp_path,
    monkeypatch,
):
    service, manager, scheduler = (
        create_test_service(
            tmp_path
        )
    )

    monkeypatch.setattr(
        api,
        "watch_service",
        service,
    )

    return (
        TestClient(api.app),
        service,
        manager,
        scheduler,
    )


def test_root(
    client,
):
    test_client, _, _, _ = client

    response = test_client.get(
        "/"
    )

    assert response.status_code == 200

    assert response.json() == {
        "name": "Cinema Ticket Watcher API",
        "status": "running",
    }


def test_create_watch_starts_scheduler(
    client,
):
    test_client, service, manager, scheduler = (
        client
    )

    response = test_client.post(
        "/watches",
        json={
            "movie": "Resident Evil",
            "target_date": "2026-09-18",
            "city": "Hyderabad",
            "cinemas": ["PVR"],
        },
    )

    assert response.status_code == 201

    data = response.json()

    watch_id = data["id"]

    assert data["movie"] == "Resident Evil"
    assert data["target_date"] == "2026-09-18"
    assert data["city"] == "Hyderabad"
    assert data["cinemas"] == ["PVR"]
    assert data["active"] is True
    assert data["running"] is True

    assert (
        watch_id
        in scheduler.started_watch_ids
    )

    stored = manager.get_watch(
        watch_id
    )

    assert stored is not None
    assert stored.movie == "Resident Evil"


def test_create_watch_rolls_back_when_scheduler_fails(
    tmp_path,
    monkeypatch,
):
    service, manager, scheduler = (
        create_test_service(
            tmp_path
        )
    )

    scheduler.start_result = False

    monkeypatch.setattr(
        api,
        "watch_service",
        service,
    )

    test_client = TestClient(
        api.app
    )

    response = test_client.post(
        "/watches",
        json={
            "movie": "Resident Evil",
            "target_date": "2026-09-18",
            "city": "Hyderabad",
            "cinemas": ["PVR"],
        },
    )

    assert response.status_code == 500

    assert (
        manager.list_watches()
        == []
    )


def test_list_watches(
    client,
):
    test_client, service, manager, scheduler = (
        client
    )

    manager.create_watch(
        "watch-1",
        Watch(
            movie="Resident Evil",
            target_date=date(
                2026,
                9,
                18,
            ),
            city="Hyderabad",
            cinemas=["PVR"],
        ),
    )

    response = test_client.get(
        "/watches"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0]["id"] == "watch-1"
    assert data[0]["movie"] == "Resident Evil"
    assert data[0]["target_date"] == "2026-09-18"
    assert data[0]["city"] == "Hyderabad"
    assert data[0]["cinemas"] == ["PVR"]
    assert data[0]["active"] is True
    assert data[0]["running"] is False


def test_get_watch(
    client,
):
    test_client, service, manager, scheduler = (
        client
    )

    manager.create_watch(
        "watch-123",
        Watch(
            movie="Resident Evil",
            target_date=date(
                2026,
                9,
                18,
            ),
            city="Hyderabad",
            cinemas=["PVR"],
        ),
    )

    response = test_client.get(
        "/watches/watch-123"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "watch-123"
    assert data["movie"] == "Resident Evil"
    assert data["target_date"] == (
        "2026-09-18"
    )
    assert data["city"] == "Hyderabad"
    assert data["cinemas"] == ["PVR"]
    assert data["active"] is True
    assert data["running"] is False


def test_get_watch_status_returns_availability(
    client,
):
    test_client, service, manager, scheduler = (
        client
    )

    manager.create_watch(
        "watch-123",
        Watch(
            movie="Resident Evil",
            target_date=date(
                2026,
                9,
                18,
            ),
            city="Hyderabad",
            cinemas=["PVR"],
        ),
    )

    scheduler.running.add(
        "watch-123"
    )

    response = test_client.get(
        "/watches/watch-123/status"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "watch-123"
    assert data["active"] is True
    assert data["running"] is True

    assert data["availability"] == {
        "session-123": {
            "movie": "Resident Evil",
            "cinema": "PVR",
            "show_date": "2026-09-18",
            "show_time": "19:30",
            "status": "AVAILABLE",
            "available_tickets": 5,
            "source_id": "session-123",
        }
    }


def test_get_watch_status_unknown_watch_returns_404(
    client,
):
    test_client, _, _, _ = client

    response = test_client.get(
        "/watches/unknown/status"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Watch not found."
    }


# =========================================================
# Watch History API
# =========================================================


def test_get_watch_history_returns_empty_history(
    client,
):
    test_client, service, manager, scheduler = (
        client
    )

    manager.create_watch(
        "watch-history-empty",
        Watch(
            movie="Resident Evil",
            target_date=date(
                2026,
                9,
                18,
            ),
            city="Hyderabad",
            cinemas=["PVR"],
        ),
    )

    response = test_client.get(
        "/watches/watch-history-empty/history"
    )

    assert response.status_code == 200

    assert response.json() == {
        "watch_id": "watch-history-empty",
        "events": [],
    }


def test_get_watch_history_returns_events(
    client,
):
    test_client, service, manager, scheduler = (
        client
    )

    manager.create_watch(
        "watch-history-1",
        Watch(
            movie="Resident Evil",
            target_date=date(
                2026,
                9,
                18,
            ),
            city="Hyderabad",
            cinemas=["PVR"],
        ),
    )

    scheduler.watch_history[
        "watch-history-1"
    ] = [
        {
            "timestamp": (
                "2026-09-20T10:30:15.123456"
            ),
            "cinema": "PVR",
            "show_time": "19:30",
            "previous": "SOLD_OUT",
            "current": "AVAILABLE",
            "previous_tickets": 0,
            "current_tickets": 42,
            "show_id": "session-123",
        },
        {
            "timestamp": (
                "2026-09-20T11:00:15.123456"
            ),
            "cinema": "AMB Cinemas",
            "show_time": "21:00",
            "previous": "UNKNOWN",
            "current": "AVAILABLE",
            "previous_tickets": None,
            "current_tickets": 18,
            "show_id": "session-456",
        },
    ]

    response = test_client.get(
        "/watches/watch-history-1/history"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["watch_id"] == (
        "watch-history-1"
    )

    assert data["events"] == [
        {
            "timestamp": (
                "2026-09-20T10:30:15.123456"
            ),
            "cinema": "PVR",
            "show_time": "19:30",
            "previous": "SOLD_OUT",
            "current": "AVAILABLE",
            "previous_tickets": 0,
            "current_tickets": 42,
            "show_id": "session-123",
        },
        {
            "timestamp": (
                "2026-09-20T11:00:15.123456"
            ),
            "cinema": "AMB Cinemas",
            "show_time": "21:00",
            "previous": "UNKNOWN",
            "current": "AVAILABLE",
            "previous_tickets": None,
            "current_tickets": 18,
            "show_id": "session-456",
        },
    ]


def test_get_watch_history_unknown_watch_returns_404(
    client,
):
    test_client, _, _, _ = client

    response = test_client.get(
        "/watches/unknown/history"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Watch not found."
    }


def test_get_unknown_watch_returns_404(
    client,
):
    test_client, _, _, _ = client

    response = test_client.get(
        "/watches/does-not-exist"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Watch not found."
    }


def test_pause_watch(
    client,
):
    test_client, service, manager, scheduler = (
        client
    )

    manager.create_watch(
        "watch-1",
        Watch(
            movie="Resident Evil",
            target_date=date(
                2026,
                9,
                18,
            ),
            city="Hyderabad",
            cinemas=["PVR"],
        ),
    )

    scheduler.running.add(
        "watch-1"
    )

    response = test_client.post(
        "/watches/watch-1/pause"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "watch-1"
    assert data["active"] is False
    assert data["running"] is False

    assert (
        "watch-1"
        in scheduler.stopped_watch_ids
    )

    stored = manager.get_watch(
        "watch-1"
    )

    assert stored is not None
    assert stored.active is False


def test_resume_watch(
    client,
):
    test_client, service, manager, scheduler = (
        client
    )

    manager.create_watch(
        "watch-1",
        Watch(
            movie="Resident Evil",
            target_date=date(
                2026,
                9,
                18,
            ),
            city="Hyderabad",
            cinemas=["PVR"],
            active=False,
        ),
    )

    response = test_client.post(
        "/watches/watch-1/resume"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "watch-1"
    assert data["active"] is True
    assert data["running"] is True

    assert (
        "watch-1"
        in scheduler.started_watch_ids
    )

    stored = manager.get_watch(
        "watch-1"
    )

    assert stored is not None
    assert stored.active is True


def test_delete_watch_stops_runner(
    client,
):
    test_client, service, manager, scheduler = (
        client
    )

    manager.create_watch(
        "watch-1",
        Watch(
            movie="Resident Evil",
            target_date=date(
                2026,
                9,
                18,
            ),
            city="Hyderabad",
            cinemas=["PVR"],
        ),
    )

    scheduler.running.add(
        "watch-1"
    )

    response = test_client.delete(
        "/watches/watch-1"
    )

    assert response.status_code == 204

    assert (
        "watch-1"
        in scheduler.stopped_watch_ids
    )

    assert (
        "watch-1"
        in scheduler.cleared_history_watch_ids
    )

    assert (
        manager.get_watch(
            "watch-1"
        )
        is None
    )


def test_pause_unknown_watch_returns_404(
    client,
):
    test_client, _, _, _ = client

    response = test_client.post(
        "/watches/unknown/pause"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Watch not found: unknown"
    }


def test_resume_unknown_watch_returns_404(
    client,
):
    test_client, _, _, _ = client

    response = test_client.post(
        "/watches/unknown/resume"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Watch not found: unknown"
    }


def test_delete_unknown_watch_returns_404(
    client,
):
    test_client, _, _, _ = client

    response = test_client.delete(
        "/watches/unknown"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Watch not found."
    }


def test_update_watch(
    client,
):
    test_client, service, manager, scheduler = (
        client
    )

    manager.create_watch(
        "watch-1",
        Watch(
            movie="Resident Evil",
            target_date=date(
                2026,
                9,
                18,
            ),
            city="Hyderabad",
            cinemas=["PVR"],
        ),
    )

    scheduler.running.add(
        "watch-1"
    )

    response = test_client.patch(
        "/watches/watch-1",
        json={
            "movie": "Resident Evil",
            "target_date": "2026-09-19",
            "city": "Hyderabad",
            "cinemas": ["AMB Cinemas"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "watch-1"
    assert data["movie"] == "Resident Evil"
    assert data["target_date"] == "2026-09-19"
    assert data["city"] == "Hyderabad"
    assert data["cinemas"] == [
        "AMB Cinemas"
    ]
    assert data["active"] is True
    assert data["running"] is True

    stored = manager.get_watch(
        "watch-1"
    )

    assert stored is not None
    assert stored.movie == "Resident Evil"
    assert stored.target_date == date(
        2026,
        9,
        19,
    )
    assert stored.cinemas == [
        "AMB Cinemas"
    ]


def test_update_unknown_watch_returns_404(
    client,
):
    test_client, _, _, _ = client

    response = test_client.patch(
        "/watches/unknown",
        json={
            "movie": "Resident Evil",
            "target_date": "2026-09-19",
            "city": "Hyderabad",
            "cinemas": ["PVR"],
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Watch not found."
    }