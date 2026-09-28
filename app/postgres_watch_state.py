from typing import Dict

from app.database import get_connection


class PostgreSQLWatchStateStore:
    """
    PostgreSQL-backed state store for one specific watch.

    Keeps the same interface as the existing WatchStateStore:

        load()
        save(state)
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
        Load the saved state for this watch.

        If no state exists, return an empty dictionary.
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT state
                    FROM watch_state
                    WHERE watch_id = %s
                    """,
                    (self.watch_id,),
                )

                row = cursor.fetchone()

        if row is None:
            return {}

        state = row[0]

        if not isinstance(state, dict):
            return {}

        return state

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    def save(
        self,
        state: Dict,
    ) -> None:
        """
        Save or replace the state for this watch.
        """

        if not isinstance(state, dict):
            raise ValueError(
                "Watch state must be a dictionary."
            )

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO watch_state (
                        watch_id,
                        state,
                        updated_at
                    )
                    VALUES (
                        %s,
                        %s::jsonb,
                        NOW()
                    )
                    ON CONFLICT (watch_id)
                    DO UPDATE SET
                        state = EXCLUDED.state,
                        updated_at = NOW()
                    """,
                    (
                        self.watch_id,
                        __import__("json").dumps(state),
                    ),
                )

            connection.commit()

    # -----------------------------------------------------
    # Clear
    # -----------------------------------------------------

    def clear(self) -> None:
        """
        Delete the saved state for this watch.

        If no state exists, do nothing.
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    DELETE FROM watch_state
                    WHERE watch_id = %s
                    """,
                    (self.watch_id,),
                )

            connection.commit()
            