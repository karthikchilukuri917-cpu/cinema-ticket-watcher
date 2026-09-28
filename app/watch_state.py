import json
from pathlib import Path
from typing import Dict


DEFAULT_WATCH_STATE_DIRECTORY = Path(
    "data/watches"
)


class WatchStateStore:
    """
    Persistent state store for one specific watch.

    Each watch gets its own JSON state file so that
    multiple watches cannot overwrite each other's
    availability state.

    Example:

        data/watches/
            watch-001.json
            watch-002.json
            watch-003.json
    """

    def __init__(
        self,
        watch_id: str,
        directory: Path = DEFAULT_WATCH_STATE_DIRECTORY,
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
            / f"{self.watch_id}.json"
        )

    # -----------------------------------------------------
    # Load
    # -----------------------------------------------------

    def load(self) -> Dict:
        """
        Load the saved state for this watch.

        If no state exists yet, return an empty
        dictionary.
        """

        if not self.file_path.exists():
            return {}

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

            return {}

        if not isinstance(data, dict):
            return {}

        return data

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    def save(
        self,
        state: Dict,
    ) -> None:
        """
        Save the state for this watch atomically.
        """

        if not isinstance(state, dict):
            raise ValueError(
                "Watch state must be a dictionary."
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
                    state,
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
        Delete the saved state for this watch.

        If no state exists, do nothing.
        """

        try:

            self.file_path.unlink()

        except FileNotFoundError:

            pass