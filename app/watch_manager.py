from typing import List

from app.models import Watch
from app.watch_repository import (
    WatchRecord,
    WatchRepository,
)


class WatchManager:
    """
    Manages the lifecycle of cinema ticket watches.
    """

    def __init__(
        self,
        repository: WatchRepository,
    ) -> None:
        self.repository = repository

    def create_watch(
        self,
        watch_id: str,
        watch: Watch,
    ) -> Watch:
        if not watch_id.strip():
            raise ValueError(
                "Watch ID cannot be empty."
            )

        return self.repository.create(
            watch_id=watch_id.strip(),
            watch=watch,
        )

    def get_watch(
        self,
        watch_id: str,
    ) -> Watch | None:
        return self.repository.get(
            watch_id.strip()
        )

    def get_watch_record(
        self,
        watch_id: str,
    ) -> WatchRecord | None:
        return self.repository.get_record(
            watch_id.strip()
        )

    def list_watches(
        self,
    ) -> List[Watch]:
        return self.repository.list()

    def list_watch_records(
        self,
    ) -> List[WatchRecord]:
        return self.repository.list_records()

    def update_watch(
        self,
        watch_id: str,
        watch: Watch,
    ) -> Watch:
        if not watch_id.strip():
            raise ValueError(
                "Watch ID cannot be empty."
            )

        return self.repository.update(
            watch_id=watch_id.strip(),
            watch=watch,
        )

    def pause_watch(
        self,
        watch_id: str,
    ) -> Watch:
        watch_id = watch_id.strip()

        watch = self.repository.get(
            watch_id
        )

        if watch is None:
            raise ValueError(
                f"Watch not found: {watch_id}"
            )

        if not watch.active:
            return watch

        watch.active = False

        return self.repository.update(
            watch_id=watch_id,
            watch=watch,
        )

    def resume_watch(
        self,
        watch_id: str,
    ) -> Watch:
        watch_id = watch_id.strip()

        watch = self.repository.get(
            watch_id
        )

        if watch is None:
            raise ValueError(
                f"Watch not found: {watch_id}"
            )

        if watch.completed:
            raise ValueError(
                "Completed watches cannot be resumed"
            )

        if watch.active:
            return watch

        watch.active = True

        return self.repository.update(
            watch_id=watch_id,
            watch=watch,
        )

    def complete_watch(
        self,
        watch_id: str,
    ) -> Watch:
        watch_id = watch_id.strip()

        watch = self.get_watch(
            watch_id
        )

        if watch is None:
            raise ValueError(
                f"Watch not found: {watch_id}"
            )

        watch.active = False
        watch.completed = True

        return self.repository.update(
            watch_id=watch_id,
            watch=watch,
        )

    def delete_watch(
        self,
        watch_id: str,
    ) -> bool:
        if not watch_id.strip():
            raise ValueError(
                "Watch ID cannot be empty."
            )

        return self.repository.delete(
            watch_id.strip()
        )

    def clear_watch_state(
        self,
        watch_id: str,
    ) -> bool:
        """
        Clear persistent monitoring state for a watch.

        The watch itself is not deleted here.
        """

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        watch = self.repository.get(
            watch_id
        )

        if watch is None:
            raise ValueError(
                f"Watch not found: {watch_id}"
            )

        watch.last_checked = None
        watch.last_message = None
        watch.last_result = None

        self.repository.update(
            watch_id=watch_id,
            watch=watch,
        )

        return True