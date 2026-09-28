from app.models import Watch
from app.watch_manager import WatchManager
from app.watch_scheduler import WatchScheduler


class WatchService:
    """
    Coordinates persistent watch management and
    runtime scheduling.

    This is the application/service layer between
    the API and the lower-level components.
    """

    def __init__(
        self,
        watch_manager: WatchManager,
        scheduler: WatchScheduler,
    ) -> None:

        self.watch_manager = watch_manager
        self.scheduler = scheduler

    # -----------------------------------------------------
    # Create
    # -----------------------------------------------------

    def create_watch(
        self,
        watch_id: str,
        watch: Watch,
    ) -> Watch:

        created = (
            self.watch_manager.create_watch(
                watch_id=watch_id,
                watch=watch,
            )
        )

        started = self.scheduler.start_watch(
            watch_id
        )

        if not started:

            self.watch_manager.delete_watch(
                watch_id
            )

            raise RuntimeError(
                "Watch was created but could not be started."
            )

        return created

    # -----------------------------------------------------
    # Get
    # -----------------------------------------------------

    def get_watch(
        self,
        watch_id: str,
    ):
        return self.watch_manager.get_watch_record(
            watch_id
        )

    # -----------------------------------------------------
    # Current state
    # -----------------------------------------------------

    def get_watch_state(
        self,
        watch_id: str,
    ):

        record = self.get_watch(
            watch_id
        )

        if record is None:
            raise ValueError(
                f"Watch not found: {watch_id}"
            )

        return self.scheduler.get_watch_state(
            watch_id
        )

    # -----------------------------------------------------
    # Health
    # -----------------------------------------------------

    def get_watch_health(
        self,
        watch_id: str,
    ):

        record = self.get_watch(
            watch_id
        )

        if record is None:
            raise ValueError(
                f"Watch not found: {watch_id}"
            )

        return self.scheduler.get_watch_health(
            watch_id
        )

    # -----------------------------------------------------
    # Notification history
    # -----------------------------------------------------

    def get_watch_history(
        self,
        watch_id: str,
    ):

        record = self.get_watch(
            watch_id
        )

        if record is None:
            raise ValueError(
                f"Watch not found: {watch_id}"
            )

        return self.scheduler.get_watch_history(
            watch_id
        )

    # -----------------------------------------------------
    # List
    # -----------------------------------------------------

    def list_watches(self):
        return (
            self.watch_manager
            .list_watch_records()
        )

    # -----------------------------------------------------
    # Update
    # -----------------------------------------------------

    def update_watch(
        self,
        watch_id: str,
        watch: Watch,
    ) -> Watch:
        """
        Update a persisted watch.

        If the watch is currently running, stop the
        existing runner before updating it.

        Active watches are restarted automatically
        after the update.
        """

        watch_id = watch_id.strip()

        record = self.get_watch(
            watch_id
        )

        if record is None:
            raise ValueError(
                f"Watch not found: {watch_id}"
            )

        current_watch = record.watch

        was_active = current_watch.active

        was_running = (
            self.scheduler.is_running(
                watch_id
            )
        )

        if was_running:
            self.scheduler.stop_watch(
                watch_id
            )

        try:

            saved = (
                self.watch_manager.update_watch(
                    watch_id=watch_id,
                    watch=watch,
                )
            )

            if was_active:

                started = (
                    self.scheduler.start_watch(
                        watch_id
                    )
                )

                if not started:
                    raise RuntimeError(
                        "Updated watch could not be restarted."
                    )

            return saved

        except Exception:

            """
            Best-effort recovery.

            If the update/restart fails, attempt to
            restore the previous watch configuration.
            """

            try:

                self.watch_manager.update_watch(
                    watch_id=watch_id,
                    watch=current_watch,
                )

                if (
                    was_active
                    and not self.scheduler.is_running(
                        watch_id
                    )
                ):

                    self.scheduler.start_watch(
                        watch_id
                    )

            except Exception:
                pass

            raise

    # -----------------------------------------------------
    # Pause
    # -----------------------------------------------------

    def pause_watch(
        self,
        watch_id: str,
    ) -> Watch:

        record = self.get_watch(
            watch_id
        )

        if record is None:
            raise ValueError(
                f"Watch not found: {watch_id}"
            )

        self.scheduler.stop_watch(
            watch_id
        )

        return self.watch_manager.pause_watch(
            watch_id
        )

    # -----------------------------------------------------
    # Resume
    # -----------------------------------------------------

    def resume_watch(
        self,
        watch_id: str,
    ) -> Watch:

        record = self.get_watch(
            watch_id
        )

        if record is None:
            raise ValueError(
                f"Watch not found: {watch_id}"
            )

        watch = self.watch_manager.resume_watch(
            watch_id
        )

        if not self.scheduler.is_running(
            watch_id
        ):

            started = self.scheduler.start_watch(
                watch_id
            )

            if not started:

                self.watch_manager.pause_watch(
                    watch_id
                )

                raise RuntimeError(
                    "Watch could not be started."
                )

        return watch

    # -----------------------------------------------------
    # Delete
    # -----------------------------------------------------

    def delete_watch(
        self,
        watch_id: str,
    ) -> bool:

        watch_id = watch_id.strip()

        watch = self.watch_manager.get_watch(
            watch_id
        )

        if watch is None:
            return False

        self.scheduler.stop_watch(
            watch_id
        )

        # Remove current monitoring state.
        self.scheduler.clear_watch_state(
            watch_id
        )

        # Remove notification history.
        self.scheduler.clear_watch_history(
            watch_id
        )

        # Remove watch health information.
        self.scheduler.clear_watch_health(
            watch_id
        )

        # Finally remove the persistent Watch record.
        return self.watch_manager.delete_watch(
            watch_id
        )