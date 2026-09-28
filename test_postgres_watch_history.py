from datetime import date, datetime

from app.models import Watch
from app.postgres_watch_repository import PostgreSQLWatchRepository
from app.postgres_watch_history import PostgreSQLWatchHistoryStore


watch_id = "postgres-history-test"

watch_repository = PostgreSQLWatchRepository()

watch = Watch(
    movie="PostgreSQL History Test Movie",
    target_date=date(2026, 12, 31),
    city="Hyderabad",
    cinemas=["PVR", "INOX"],
    movie_event_code="HISTORY_TEST_EVENT",
    active=True,
    completed=False,
)


print("1. Creating temporary watch...")

watch_repository.create(
    watch_id=watch_id,
    watch=watch,
)

print("   WATCH CREATE successful")


store = PostgreSQLWatchHistoryStore(
    watch_id=watch_id,
)


print("2. Loading initial history...")

history = store.load()

print("   Initial history:", history)

assert history == []

print("   INITIAL LOAD successful")


print("3. Adding availability changes...")

changes = {
    "PVR": {
        "19:30": {
            "previous": "SOLD_OUT",
            "current": "AVAILABLE",
            "previous_tickets": 0,
            "current_tickets": 2,
            "show_id": "SHOW123",
        },
        "21:00": {
            "previous": "AVAILABLE",
            "current": "SOLD_OUT",
            "previous_tickets": 3,
            "current_tickets": 0,
            "show_id": "SHOW456",
        },
    },
    "INOX": {
        "20:00": {
            "previous": None,
            "current": "AVAILABLE",
            "previous_tickets": None,
            "current_tickets": 4,
            "show_id": "SHOW789",
        }
    },
}

store.add(changes)

print("   ADD successful")


print("4. Loading saved history...")

loaded = store.load()

print("   Loaded history:")

for event in loaded:
    print("   ", event)

assert len(loaded) == 3

assert loaded[0]["cinema"] == "PVR"
assert loaded[0]["show_time"] == "19:30"
assert loaded[0]["previous"] == "SOLD_OUT"
assert loaded[0]["current"] == "AVAILABLE"
assert loaded[0]["previous_tickets"] == 0
assert loaded[0]["current_tickets"] == 2
assert loaded[0]["show_id"] == "SHOW123"

assert loaded[1]["cinema"] == "PVR"
assert loaded[1]["show_time"] == "21:00"

assert loaded[2]["cinema"] == "INOX"
assert loaded[2]["show_time"] == "20:00"

for event in loaded:
    assert event["timestamp"] is not None

    datetime.fromisoformat(
        event["timestamp"]
    )

print("   LOAD successful")


print("5. Adding another event...")

second_changes = {
    "PVR": {
        "19:30": {
            "previous": "AVAILABLE",
            "current": "SOLD_OUT",
            "previous_tickets": 2,
            "current_tickets": 0,
            "show_id": "SHOW123",
        }
    }
}

store.add(second_changes)

updated_history = store.load()

assert len(updated_history) == 4

print("   APPEND successful")


print("6. Clearing history...")

store.clear()

cleared_history = store.load()

print("   History after CLEAR:", cleared_history)

assert cleared_history == []

print("   CLEAR successful")


print("7. Deleting temporary watch...")

deleted = watch_repository.delete(watch_id)

assert deleted is True

print("   WATCH DELETE successful")


print()
print("PostgreSQL Watch History test PASSED.")