import json
from datetime import datetime, timezone

from app.database import get_connection
from app.models import Watch
from app.watch_repository import WatchRecord


class PostgreSQLWatchRepository:
    """
    PostgreSQL implementation of the WatchRepository contract.

    The Watch ID is stored separately from the Watch object,
    matching the current JSON WatchRepository architecture.
    """

    # -----------------------------------------------------
    # Serialization
    # -----------------------------------------------------

    @staticmethod
    def _watch_to_values(watch: Watch):
        return (
            watch.movie,
            watch.movie_event_code,
            watch.target_date,
            watch.city,
            json.dumps(watch.cinemas),
            watch.active,
            watch.completed,
        )

    @staticmethod
    def _row_to_watch(row) -> Watch:
        (
            movie,
            movie_event_code,
            target_date,
            city,
            cinemas,
            active,
            completed,
        ) = row

        return Watch(
            movie=movie,
            target_date=target_date,
            city=city,
            cinemas=cinemas,
            movie_event_code=movie_event_code,
            active=active,
            completed=completed,
        )

    # -----------------------------------------------------
    # Create
    # -----------------------------------------------------

    def create(
        self,
        watch_id: str,
        watch: Watch,
    ) -> Watch:

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        now = datetime.now(timezone.utc)

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO watches (
                        id,
                        movie,
                        movie_event_code,
                        target_date,
                        city,
                        cinemas,
                        active,
                        completed,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s::jsonb,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        watch_id,
                        watch.movie,
                        watch.movie_event_code,
                        watch.target_date,
                        watch.city,
                        json.dumps(watch.cinemas),
                        watch.active,
                        watch.completed,
                        now,
                        now,
                    ),
                )

            connection.commit()

        return watch

    # -----------------------------------------------------
    # Get
    # -----------------------------------------------------

    def get(
        self,
        watch_id: str,
    ) -> Watch | None:

        watch_id = watch_id.strip()

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        movie,
                        movie_event_code,
                        target_date,
                        city,
                        cinemas,
                        active,
                        completed
                    FROM watches
                    WHERE id = %s
                    """,
                    (watch_id,),
                )

                row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_watch(row)

    # -----------------------------------------------------
    # Get record
    # -----------------------------------------------------

    def get_record(
        self,
        watch_id: str,
    ) -> WatchRecord | None:

        watch_id = watch_id.strip()

        watch = self.get(watch_id)

        if watch is None:
            return None

        return WatchRecord(
            watch_id=watch_id,
            watch=watch,
        )

    # -----------------------------------------------------
    # List
    # -----------------------------------------------------

    def list(self):
        return [
            record.watch
            for record in self.list_records()
        ]

    def list_records(self):

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        movie,
                        movie_event_code,
                        target_date,
                        city,
                        cinemas,
                        active,
                        completed
                    FROM watches
                    ORDER BY created_at
                    """
                )

                rows = cursor.fetchall()

        records = []

        for row in rows:

            (
                watch_id,
                movie,
                movie_event_code,
                target_date,
                city,
                cinemas,
                active,
                completed,
            ) = row

            watch = Watch(
                movie=movie,
                target_date=target_date,
                city=city,
                cinemas=cinemas,
                movie_event_code=movie_event_code,
                active=active,
                completed=completed,
            )

            records.append(
                WatchRecord(
                    watch_id=watch_id,
                    watch=watch,
                )
            )

        return records

    # -----------------------------------------------------
    # Update
    # -----------------------------------------------------

    def update(
        self,
        watch_id: str,
        watch: Watch,
    ) -> Watch:

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        now = datetime.now(timezone.utc)

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    UPDATE watches
                    SET
                        movie = %s,
                        movie_event_code = %s,
                        target_date = %s,
                        city = %s,
                        cinemas = %s::jsonb,
                        active = %s,
                        completed = %s,
                        updated_at = %s
                    WHERE id = %s
                    """,
                    (
                        watch.movie,
                        watch.movie_event_code,
                        watch.target_date,
                        watch.city,
                        json.dumps(watch.cinemas),
                        watch.active,
                        watch.completed,
                        now,
                        watch_id,
                    ),
                )

                if cursor.rowcount == 0:
                    raise ValueError(
                        f"Watch not found: {watch_id}"
                    )

            connection.commit()

        return watch

    # -----------------------------------------------------
    # Delete
    # -----------------------------------------------------

    def delete(
        self,
        watch_id: str,
    ) -> bool:

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    DELETE FROM watches
                    WHERE id = %s
                    """,
                    (watch_id,),
                )

                deleted = cursor.rowcount > 0

            connection.commit()

        return deleted