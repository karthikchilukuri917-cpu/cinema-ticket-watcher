from datetime import datetime, timezone
from typing import Dict, List

from app.database import get_connection


class PostgreSQLWatchHistoryStore:
    """
    PostgreSQL-backed history store for one specific watch.

    Keeps the same public interface as WatchHistoryStore:

        load()
        add(changes)
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

    def load(self) -> List[Dict]:
        """
        Load all saved history events for this watch.

        Events are returned in chronological order.
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        timestamp,
                        cinema,
                        show_time,
                        previous,
                        current,
                        previous_tickets,
                        current_tickets,
                        show_id
                    FROM watch_history
                    WHERE watch_id = %s
                    ORDER BY timestamp, id
                    """,
                    (self.watch_id,),
                )

                rows = cursor.fetchall()

        history = []

        for row in rows:

            (
                timestamp,
                cinema,
                show_time,
                previous,
                current,
                previous_tickets,
                current_tickets,
                show_id,
            ) = row

            history.append(
                {
                    "timestamp": (
                        timestamp.isoformat()
                        if timestamp is not None
                        else None
                    ),
                    "cinema": cinema,
                    "show_time": show_time,
                    "previous": previous,
                    "current": current,
                    "previous_tickets": previous_tickets,
                    "current_tickets": current_tickets,
                    "show_id": show_id,
                }
            )

        return history

    # -----------------------------------------------------
    # Add event
    # -----------------------------------------------------

    def add(
        self,
        changes: Dict,
    ) -> None:
        """
        Append meaningful availability changes to history.
        """

        if not isinstance(changes, dict):
            raise ValueError(
                "History changes must be a dictionary."
            )

        timestamp = datetime.now(timezone.utc)

        with get_connection() as connection:
            with connection.cursor() as cursor:

                for cinema, shows in changes.items():

                    if not isinstance(shows, dict):
                        continue

                    for show_time, change in shows.items():

                        if not isinstance(change, dict):
                            continue

                        cursor.execute(
                            """
                            INSERT INTO watch_history (
                                watch_id,
                                timestamp,
                                cinema,
                                show_time,
                                previous,
                                current,
                                previous_tickets,
                                current_tickets,
                                show_id
                            )
                            VALUES (
                                %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s
                            )
                            """,
                            (
                                self.watch_id,
                                timestamp,
                                cinema,
                                show_time,
                                change.get("previous"),
                                change.get("current"),
                                change.get(
                                    "previous_tickets"
                                ),
                                change.get(
                                    "current_tickets"
                                ),
                                change.get("show_id"),
                            ),
                        )

            connection.commit()

    # -----------------------------------------------------
    # Clear
    # -----------------------------------------------------

    def clear(self) -> None:
        """
        Delete all history for this watch.
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    DELETE FROM watch_history
                    WHERE watch_id = %s
                    """,
                    (self.watch_id,),
                )

            connection.commit()