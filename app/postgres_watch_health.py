from typing import Dict

from app.database import get_connection


class PostgreSQLWatchHealthStore:
    """
    PostgreSQL-backed health store for one specific watch.

    Keeps the same interface as the existing WatchHealthStore:

        load()
        save(health)
        clear()
    """

    def __init__(
        self,
        watch_id: str,
    ) -> None:

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        self.watch_id = watch_id

    # -----------------------------------------------------
    # Load
    # -----------------------------------------------------

    def load(self) -> Dict:
        """
        Load saved health information.

        If no health information exists, return
        an empty dictionary.
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        last_checked,
                        status,
                        message
                    FROM watch_health
                    WHERE watch_id = %s
                    """,
                    (self.watch_id,),
                )

                row = cursor.fetchone()

        if row is None:
            return {}

        last_checked, status, message = row

        return {
            "last_checked": (
                last_checked.isoformat()
                if last_checked is not None
                else None
            ),
            "status": status,
            "message": message,
        }

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    def save(
        self,
        health: Dict,
    ) -> None:
        """
        Save or replace health information.
        """

        if not isinstance(health, dict):
            raise ValueError(
                "Watch health must be a dictionary."
            )

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO watch_health (
                        watch_id,
                        last_checked,
                        status,
                        message,
                        updated_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        NOW()
                    )
                    ON CONFLICT (watch_id)
                    DO UPDATE SET
                        last_checked = EXCLUDED.last_checked,
                        status = EXCLUDED.status,
                        message = EXCLUDED.message,
                        updated_at = NOW()
                    """,
                    (
                        self.watch_id,
                        health.get("last_checked"),
                        health.get("status"),
                        health.get("message"),
                    ),
                )

            connection.commit()

    # -----------------------------------------------------
    # Clear
    # -----------------------------------------------------

    def clear(self) -> None:
        """
        Delete saved health information.

        If no health information exists, do nothing.
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    DELETE FROM watch_health
                    WHERE watch_id = %s
                    """,
                    (self.watch_id,),
                )

            connection.commit()