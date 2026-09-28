from datetime import date

from app.models import Watch
from app.postgres_watch_repository import PostgreSQLWatchRepository
from app.postgres_watch_state import PostgreSQLWatchStateStore


watch_id = "postgres-state-test"

watch_repository = PostgreSQLWatchRepository()

watch = Watch(
    movie="PostgreSQL State Test Movie",
    target_date=date(2026, 12, 31),
    city="Hyderabad",
    cinemas=["Test Cinema"],
    movie_event_code="STATE_TEST_EVENT",
    active=True,
    completed=False,
)


print("1. Creating temporary watch...")

watch_repository.create(
    watch_id=watch_id,
    watch=watch,
)

print("   WATCH CREATE successful")


store = PostgreSQLWatchStateStore(
    watch_id=watch_id
)


print("2. Loading initial state...")

state = store.load()

print("   Initial state:", state)

assert state == {}


print("3. Saving state...")

test_state = {
    "PVR": {
        "19:30": "AVAILABLE",
        "21:00": "SOLD_OUT",
    }
}

store.save(test_state)

print("   SAVE successful")


print("4. Loading saved state...")

loaded = store.load()

print("   Loaded state:", loaded)

assert loaded == test_state

print("   LOAD successful")


print("5. Updating state...")

updated_state = {
    "PVR": {
        "19:30": "SOLD_OUT",
        "21:00": "AVAILABLE",
    }
}

store.save(updated_state)

loaded_again = store.load()

assert loaded_again == updated_state

print("   UPDATE successful")


print("6. Clearing state...")

store.clear()

cleared_state = store.load()

print("   State after CLEAR:", cleared_state)

assert cleared_state == {}

print("   CLEAR successful")


print("7. Deleting temporary watch...")

deleted = watch_repository.delete(watch_id)

assert deleted is True

print("   WATCH DELETE successful")


print()
print("PostgreSQL Watch State test PASSED.")