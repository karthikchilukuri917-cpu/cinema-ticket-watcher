import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from app.models import Watch


DEFAULT_WATCHES_FILE = Path(
    "data/watches.json"
)


@dataclass(frozen=True)
class WatchRecord:
    """
    Represents a persisted watch together with its ID.
    """

    watch_id: str
    watch: Watch


class WatchRepository:
    """
    Persistent repository for Watch objects.

    The repository currently uses a JSON file for storage.

    Storage can later be replaced with a database without
    changing the WatchManager or Watcher layers.
    """

    def __init__(
        self,
        file_path: Path = DEFAULT_WATCHES_FILE,
    ) -> None:

        self.file_path = Path(file_path)

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    # -----------------------------------------------------
    # Serialization
    # -----------------------------------------------------

    @staticmethod
    def _watch_to_dict(
        watch_id: str,
        watch: Watch,
    ) -> Dict:

        return {
            "id": watch_id,
            "movie": watch.movie,
            "movie_event_code": (
                watch.movie_event_code
            ),
            "target_date": (
                watch.target_date.isoformat()
            ),
            "city": watch.city,
            "cinemas": watch.cinemas,
            "active": watch.active,
            "completed": watch.completed,
        }

    @staticmethod
    def _dict_to_watch(
        data: Dict,
    ) -> Watch:

        from datetime import date

        return Watch(
            movie=data["movie"],
            movie_event_code=data.get(
                "movie_event_code"
            ),
            target_date=date.fromisoformat(
                data["target_date"]
            ),
            city=data["city"],
            cinemas=data["cinemas"],
            active=data.get(
                "active",
                True,
            ),
            completed=data.get(
                "completed",
                False,
            ),
        )

    # -----------------------------------------------------
    # File handling
    # -----------------------------------------------------

    def _load(self) -> Dict:
        """
        Load raw repository data.

        This method remains private intentionally.
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

    def _save(
        self,
        data: Dict,
    ) -> None:

        temporary_file = self.file_path.with_suffix(
            self.file_path.suffix + ".tmp"
        )

        try:

            with temporary_file.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    data,
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
    # Create
    # -----------------------------------------------------

    def create(
        self,
        watch_id: str,
        watch: Watch,
    ) -> Watch:

        data = self._load()

        if watch_id in data:
            raise ValueError(
                f"Watch already exists: {watch_id}"
            )

        data[watch_id] = (
            self._watch_to_dict(
                watch_id,
                watch,
            )
        )

        self._save(data)

        return watch

    # -----------------------------------------------------
    # Get
    # -----------------------------------------------------

    def get(
        self,
        watch_id: str,
    ) -> Watch | None:

        data = self._load()

        watch_data = data.get(
            watch_id
        )

        if watch_data is None:
            return None

        return self._dict_to_watch(
            watch_data
        )

    # -----------------------------------------------------
    # Get record
    # -----------------------------------------------------

    def get_record(
        self,
        watch_id: str,
    ) -> WatchRecord | None:
        """
        Return a watch together with its repository ID.
        """

        watch = self.get(
            watch_id
        )

        if watch is None:
            return None

        return WatchRecord(
            watch_id=watch_id,
            watch=watch,
        )

    # -----------------------------------------------------
    # List
    # -----------------------------------------------------

    def list(
        self,
    ) -> List[Watch]:

        return [
            record.watch
            for record in self.list_records()
        ]

    def list_records(
        self,
    ) -> List[WatchRecord]:
        """
        Return all watches together with their IDs.
        """

        data = self._load()

        records = []

        for watch_id, watch_data in data.items():

            records.append(
                WatchRecord(
                    watch_id=watch_id,
                    watch=self._dict_to_watch(
                        watch_data
                    ),
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

        data = self._load()

        if watch_id not in data:
            raise ValueError(
                f"Watch not found: {watch_id}"
            )

        data[watch_id] = (
            self._watch_to_dict(
                watch_id,
                watch,
            )
        )

        self._save(data)

        return watch

    # -----------------------------------------------------
    # Delete
    # -----------------------------------------------------

    def delete(
        self,
        watch_id: str,
    ) -> bool:

        data = self._load()

        if watch_id not in data:
            return False

        del data[watch_id]

        self._save(data)

        return True