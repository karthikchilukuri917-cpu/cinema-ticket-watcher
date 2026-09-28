from datetime import date, datetime, timezone

from app.models import Watch
from app.postgres_watch_repository import PostgreSQLWatchRepository
from app.postgres_watch_health import PostgreSQLWatchHealthStore


watch_id = "postgres-health-test"

watch_repository = PostgreSQLWatchRepository()

watch = Watch(
    movie="PostgreSQL Health Test Movie",
    target_date=date(2026, 12, 31),
    city="Hyderabad",
    cinemas=["Test Cinema"],
    movie_event_code="HEALTH_TEST_EVENT",
    active=True,
    completed=False,
)


print("1. Creating temporary watch...")

watch_repository.create(
    watch_id=watch_id,
    watch=watch,
)

print("   WATCH CREATE successful")


store = PostgreSQLWatchHealthStore(
    watch_id=watch_id,
)


print("2. Loading initial health...")

health = store.load()

print("   Initial health:", health)

assert health == {}

print("   INITIAL LOAD successful")


print("3. Saving health...")

test_timestamp = datetime(
    2026,
    9,
    28,
    19,
    0,
    0,
    tzinfo=timezone.utc,
)

test_health = {
    "last_checked": test_timestamp.isoformat(),
    "status": "NO_SHOWS",
    "message": "No shows found.",
}

store.save(test_health)

print("   SAVE successful")


print("4. Loading saved health...")

loaded = store.load()

print("   Loaded health:", loaded)

loaded_timestamp = datetime.fromisoformat(
    loaded["last_checked"]
)

assert loaded_timestamp == test_timestamp
assert loaded["status"] == test_health["status"]
assert loaded["message"] == test_health["message"]

print("   TIMESTAMP preserved")
print("   STATUS preserved")
print("   MESSAGE preserved")
print("   LOAD successful")


print("5. Updating health...")

updated_timestamp = datetime(
    2026,
    9,
    28,
    19,
    5,
    0,
    tzinfo=timezone.utc,
)

updated_health = {
    "last_checked": updated_timestamp.isoformat(),
    "status": "SUCCESS",
    "message": "Shows found.",
}

store.save(updated_health)

loaded_again = store.load()

loaded_updated_timestamp = datetime.fromisoformat(
    loaded_again["last_checked"]
)

assert loaded_updated_timestamp == updated_timestamp
assert loaded_again["status"] == updated_health["status"]
assert loaded_again["message"] == updated_health["message"]

print("   UPDATE successful")


print("6. Clearing health...")

store.clear()

cleared_health = store.load()

print("   Health after CLEAR:", cleared_health)

assert cleared_health == {}

print("   CLEAR successful")


print("7. Deleting temporary watch...")

deleted = watch_repository.delete(watch_id)

assert deleted is True

print("   WATCH DELETE successful")


print()
print("PostgreSQL Watch Health test PASSED.")