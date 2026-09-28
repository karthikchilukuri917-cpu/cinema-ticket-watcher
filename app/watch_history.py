import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


DEFAULT_WATCH_HISTORY_DIRECTORY = Path(
    "data/watches"
)


class WatchHistoryStore:
    """
    Persistent history store for one specific watch.

    History is stored separately from the current
    availability state.

    Example:

        data/watches/
            watch-001.json
            watch-001_history.json
    """

    def __init__(
        self,
        watch_id: str,
        directory: Path = DEFAULT_WATCH_HISTORY_DIRECTORY,
    ) -> None:

        watch_id = watch_id.strip()

        if not watch_id:
            raise ValueError(
                "Watch ID cannot be empty."
            )

        self.watch_id = watch_id
        self.directory = Path(directory)

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.file_path = (
            self.directory
            / f"{self.watch_id}_history.json"
        )

    # -----------------------------------------------------
    # Load
    # -----------------------------------------------------

    def load(self) -> List[Dict]:
        """
        Load the saved history for this watch.

        If no history exists yet, return an empty list.
        """

        if not self.file_path.exists():
            return []

        try:

            with self.file_path.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

        except (
            json.JSONDecodeError,
            OSError,
        ):

            return []

        if not isinstance(data, list):
            return []

        return data

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

        history = self.load()

        timestamp = datetime.now().isoformat()

        for cinema, shows in changes.items():

            if not isinstance(shows, dict):
                continue

            for show_time, change in shows.items():

                if not isinstance(change, dict):
                    continue

                event = {
                    "timestamp": timestamp,
                    "cinema": cinema,
                    "show_time": show_time,
                    "previous": change.get(
                        "previous"
                    ),
                    "current": change.get(
                        "current"
                    ),
                    "previous_tickets": change.get(
                        "previous_tickets"
                    ),
                    "current_tickets": change.get(
                        "current_tickets"
                    ),
                    "show_id": change.get(
                        "show_id"
                    ),
                }

                history.append(event)

        self._save(history)

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    def _save(
        self,
        history: List[Dict],
    ) -> None:
        """
        Save history atomically.
        """

        if not isinstance(history, list):
            raise ValueError(
                "History must be a list."
            )

        temporary_file = self.file_path.with_suffix(
            self.file_path.suffix + ".tmp"
        )

        try:

            with temporary_file.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    history,
                    file,
                    indent=2,
                )

                file.flush()

            temporary_file.replace(
                self.file_path
            )

        except Exception:

            if temporary_file.exists():
                temporary_file.unlink()

            raise

    # -----------------------------------------------------
    # Clear
    # -----------------------------------------------------

    def clear(self) -> None:
        """
        Delete the saved history for this watch.
        """

        try:

            self.file_path.unlink()

        except FileNotFoundError:

            pass