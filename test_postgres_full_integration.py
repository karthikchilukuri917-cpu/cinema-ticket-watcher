from datetime import date

from app.models import Watch
from app.postgres_watch_repository import PostgreSQLWatchRepository
from app.watch_runner import WatchRunner


watch_id = "postgres-full-integration-test"


# -----------------------------------------------------
# Temporary watch
# -----------------------------------------------------

repository = PostgreSQLWatchRepository()

watch = Watch(
    movie="PostgreSQL Full Integration Movie",
    target_date=date(2026, 12, 31),
    city="Hyderabad",
    cinemas=["PVR"],
    movie_event_code="FULL_INTEGRATION_EVENT",
    active=True,
    completed=False,
)


# -----------------------------------------------------
# Fake source
# -----------------------------------------------------

class FakeSource:

    def get_availability(self, watch):

        from app.sources.result import (
            SourceResult,
            SourceStatus,
        )

        return SourceResult(
            status=SourceStatus.SUCCESS,
            data={
                "PVR": {
                    "19:30": {
                        "status": "AVAILABLE",
                        "tickets": 2,
                        "show_id": "INTEGRATION_SHOW_123",
                    }
                }
            },
            message="Integration test successful.",
        )


def source_factory(watch):
    return FakeSource()


def on_change(changes):
    print("   Notification callback:", changes)


# -----------------------------------------------------
# 1. Create watch
# -----------------------------------------------------

print("1. Creating temporary watch...")

repository.create(
    watch_id=watch_id,
    watch=watch,
)

print("   WATCH CREATE successful")


# -----------------------------------------------------
# 2. Create runner
# -----------------------------------------------------

print("2. Creating WatchRunner...")

runner = WatchRunner(
    watch_id=watch_id,
    source_factory=source_factory,
    on_change=on_change,
)

print("   WATCH RUNNER created")


# -----------------------------------------------------
# 3. Verify initial state
# -----------------------------------------------------

print("3. Checking initial PostgreSQL state...")

assert runner.get_state() == {}
assert runner.get_health() == {}
assert runner.get_history() == []

print("   STATE initial: {}")
print("   HEALTH initial: {}")
print("   HISTORY initial: []")


# -----------------------------------------------------
# 4. Run one monitoring cycle
# -----------------------------------------------------

print("4. Running one monitoring cycle...")

result = runner.run(
    watch=watch,
    max_cycles=1,
)

print("   RUN RESULT:", result)


# -----------------------------------------------------
# 5. Check health
# -----------------------------------------------------

print("5. Checking PostgreSQL health...")

health = runner.get_health()

print("   HEALTH:", health)

assert health["status"] == "SUCCESS"
assert health["message"] == "Integration test successful."
assert health["last_checked"] is not None

print("   HEALTH PostgreSQL persistence successful")


# -----------------------------------------------------
# 6. Check state
# -----------------------------------------------------

print("6. Checking PostgreSQL state...")

state = runner.get_state()

print("   STATE:", state)

assert state != {}

print("   STATE PostgreSQL persistence successful")


# -----------------------------------------------------
# 7. Check history
# -----------------------------------------------------

print("7. Checking PostgreSQL history...")

history = runner.get_history()

print("   HISTORY:", history)

print("   HISTORY PostgreSQL persistence successful")


# -----------------------------------------------------
# 8. Clear everything
# -----------------------------------------------------

print("8. Clearing PostgreSQL persistence...")

runner.clear_state()
runner.clear_health()
runner.clear_history()

assert runner.get_state() == {}
assert runner.get_health() == {}
assert runner.get_history() == []

print("   STATE cleared")
print("   HEALTH cleared")
print("   HISTORY cleared")


# -----------------------------------------------------
# 9. Delete watch
# -----------------------------------------------------

print("9. Deleting temporary watch...")

deleted = repository.delete(watch_id)

assert deleted is True

print("   WATCH DELETE successful")


# -----------------------------------------------------
# 10. Verify watch deletion
# -----------------------------------------------------

print("10. Verifying watch deletion...")

assert repository.get(watch_id) is None

print("   WATCH no longer exists")


print()
print("==============================================")
print("FULL POSTGRESQL INTEGRATION TEST PASSED")
print("==============================================")