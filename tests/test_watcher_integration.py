from datetime import date

from app.models import Watch
from app.sources.result import (
    SourceResult,
    SourceStatus,
)
from app.watcher import run_monitor


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


def test_watcher_detects_availability_transition():
    watch = create_watch()

    responses = [
        SourceResult(
            status=SourceStatus.SUCCESS,
            data={
                "PVR": {
                    "19:30": {
                        "status": "SOLD_OUT",
                        "available_tickets": 0,
                        "source_id": "session-123",
                    }
                }
            },
        ),
        SourceResult(
            status=SourceStatus.SUCCESS,
            data={
                "PVR": {
                    "19:30": {
                        "status": "AVAILABLE",
                        "available_tickets": 5,
                        "source_id": "session-123",
                    }
                }
            },
        ),
    ]

    call_index = 0
    notifications = []
    saved_states = []
    previous_state = {}

    def fetch_availability():
        nonlocal call_index

        result = responses[call_index]
        call_index += 1

        return result

    def load_state():
        return previous_state.copy()

    def save_state(state):
        nonlocal previous_state

        previous_state = state.copy()
        saved_states.append(
            state.copy()
        )

    def on_change(changes):
        notifications.append(
            changes
        )

    run_monitor(
        watch=watch,
        fetch_availability=fetch_availability,
        on_change=on_change,
        load_state=load_state,
        save_state=save_state,
        max_cycles=2,
    )

    assert len(
        notifications
    ) == 1

    changes = notifications[0]

    assert "PVR" in changes
    assert "19:30" in changes["PVR"]

    change = changes["PVR"]["19:30"]

    assert (
        change["previous"]
        == "SOLD_OUT"
    )

    assert (
        change["current"]
        == "AVAILABLE"
    )

    assert (
        change["previous_tickets"]
        == 0
    )

    assert (
        change["current_tickets"]
        == 5
    )

    assert len(
        saved_states
    ) == 2


def test_watcher_does_not_repeat_notification():
    watch = create_watch()

    response = SourceResult(
        status=SourceStatus.SUCCESS,
        data={
            "PVR": {
                "19:30": {
                    "status": "AVAILABLE",
                    "available_tickets": 5,
                    "source_id": "session-123",
                }
            }
        },
    )

    notifications = []
    saved_states = []

    # The watcher already knows this exact show.
    #
    # Show.identity uses source_id when available, so
    # the persisted state must use "session-123" as its key.
    previous_state = {
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

    def fetch_availability():
        return response

    def load_state():
        return previous_state.copy()

    def save_state(state):
        nonlocal previous_state

        previous_state = state.copy()
        saved_states.append(
            state.copy()
        )

    def on_change(changes):
        notifications.append(
            changes
        )

    run_monitor(
        watch=watch,
        fetch_availability=fetch_availability,
        on_change=on_change,
        load_state=load_state,
        save_state=save_state,
        max_cycles=2,
    )

    # The show was already AVAILABLE before monitoring began.
    # Identical subsequent checks must not notify again.
    assert notifications == []

    assert len(saved_states) == 2


def test_watcher_notifies_when_show_becomes_available():
    watch = Watch(
        movie="Resident Evil",
        target_date=date(
            2026,
            9,
            18,
        ),
        city="Hyderabad",
        cinemas=["PVR"],
    )

    responses = [
        SourceResult(
            status=SourceStatus.SUCCESS,
            data={
                "PVR": {
                    "19:30": {
                        "status": "SOLD_OUT",
                        "available_tickets": 0,
                        "source_id": "session-123",
                    }
                }
            },
        ),
        SourceResult(
            status=SourceStatus.SUCCESS,
            data={
                "PVR": {
                    "19:30": {
                        "status": "AVAILABLE",
                        "available_tickets": 2,
                        "source_id": "session-123",
                    }
                }
            },
        ),
    ]

    call_index = 0
    notifications = []
    previous_state = {}

    def fetch_availability():
        nonlocal call_index

        result = responses[call_index]
        call_index += 1

        return result

    def load_state():
        return previous_state.copy()

    def save_state(state):
        nonlocal previous_state

        previous_state = state.copy()

    def on_change(changes):
        notifications.append(
            changes
        )

    run_monitor(
        watch=watch,
        fetch_availability=fetch_availability,
        on_change=on_change,
        load_state=load_state,
        save_state=save_state,
        max_cycles=2,
    )

    assert len(notifications) == 1
    assert "PVR" in notifications[0]
    assert "19:30" in notifications[0]["PVR"]


def test_watcher_notifies_for_all_available_shows():
    watch = Watch(
        movie="Resident Evil",
        target_date=date(
            2026,
            9,
            18,
        ),
        city="Hyderabad",
        cinemas=["PVR"],
    )

    responses = [
        SourceResult(
            status=SourceStatus.SUCCESS,
            data={
                "PVR": {
                    "17:00": {
                        "status": "SOLD_OUT",
                        "available_tickets": 0,
                        "source_id": "session-early",
                    },
                    "20:00": {
                        "status": "SOLD_OUT",
                        "available_tickets": 0,
                        "source_id": "session-target",
                    },
                }
            },
        ),
        SourceResult(
            status=SourceStatus.SUCCESS,
            data={
                "PVR": {
                    "17:00": {
                        "status": "AVAILABLE",
                        "available_tickets": 10,
                        "source_id": "session-early",
                    },
                    "20:00": {
                        "status": "AVAILABLE",
                        "available_tickets": 5,
                        "source_id": "session-target",
                    },
                }
            },
        ),
    ]

    call_index = 0
    notifications = []
    previous_state = {}

    def fetch_availability():
        nonlocal call_index

        result = responses[call_index]
        call_index += 1

        return result

    def load_state():
        return previous_state.copy()

    def save_state(state):
        nonlocal previous_state

        previous_state = state.copy()

    def on_change(changes):
        notifications.append(
            changes
        )

    run_monitor(
        watch=watch,
        fetch_availability=fetch_availability,
        on_change=on_change,
        load_state=load_state,
        save_state=save_state,
        max_cycles=2,
    )

    assert len(
        notifications
    ) == 1

    changes = notifications[0]

    assert "17:00" in changes["PVR"]
    assert "20:00" in changes["PVR"]


def test_watcher_preserves_state_when_source_fails():
    watch = create_watch()

    initial_state = {
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

    response = SourceResult(
        status=SourceStatus.ERROR,
        data={},
        message="Temporary source failure",
    )

    notifications = []
    saved_states = []

    def fetch_availability():
        return response

    def load_state():
        return initial_state.copy()

    def save_state(state):
        saved_states.append(
            state.copy()
        )

    def on_change(changes):
        notifications.append(
            changes
        )

    run_monitor(
        watch=watch,
        fetch_availability=fetch_availability,
        on_change=on_change,
        load_state=load_state,
        save_state=save_state,
        max_cycles=1,
    )

    assert notifications == []

    # Source failure must not overwrite
    # the previously known state.
    assert saved_states == []


def test_watcher_handles_no_shows():
    watch = create_watch()

    previous_state = {
        "session-123": {
            "status": "AVAILABLE",
            "available_tickets": 5,
        }
    }

    response = SourceResult(
        status=SourceStatus.NO_SHOWS,
        data={},
        message="No shows found.",
    )

    saved_states = []
    current_state = previous_state.copy()

    def fetch_availability():
        return response

    def load_state():
        return current_state.copy()

    def save_state(state):
        nonlocal current_state

        current_state = state.copy()
        saved_states.append(
            state.copy()
        )

    run_monitor(
        watch=watch,
        fetch_availability=fetch_availability,
        on_change=lambda changes: None,
        load_state=load_state,
        save_state=save_state,
        max_cycles=1,
    )

    assert len(
        saved_states
    ) == 1

    assert saved_states[0] == {}


def test_watcher_saves_current_matching_state():
    watch = create_watch()

    response = SourceResult(
        status=SourceStatus.SUCCESS,
        data={
            "PVR": {
                "19:30": {
                    "status": "AVAILABLE",
                    "available_tickets": 5,
                    "source_id": "session-123",
                }
            }
        },
    )

    saved_states = []

    def fetch_availability():
        return response

    def load_state():
        return {}

    def save_state(state):
        saved_states.append(
            state.copy()
        )

    run_monitor(
        watch=watch,
        fetch_availability=fetch_availability,
        on_change=lambda changes: None,
        load_state=load_state,
        save_state=save_state,
        max_cycles=1,
    )

    assert len(
        saved_states
    ) == 1

    state = saved_states[0]

    assert "session-123" in state

    assert (
        state["session-123"]["status"]
        == "AVAILABLE"
    )

    assert (
        state["session-123"]["available_tickets"]
        == 5
    )


def test_watcher_handles_source_exception():
    watch = create_watch()

    notifications = []

    def fetch_availability():
        raise RuntimeError(
            "temporary failure"
        )

    def load_state():
        return {}

    def save_state(state):
        raise AssertionError(
            "State should not be saved "
            "when the source raises."
        )

    def on_change(changes):
        notifications.append(
            changes
        )

    run_monitor(
        watch=watch,
        fetch_availability=fetch_availability,
        on_change=on_change,
        load_state=load_state,
        save_state=save_state,
        max_cycles=1,
    )

    assert notifications == []
