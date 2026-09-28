from app.models import Watch
from app.mock_data import FIRST_CHECK, SECOND_CHECK
from app.sources.base import CinemaSource
from app.sources.result import SourceResult, SourceStatus


class MockCinemaSource(CinemaSource):
    """
    Fake cinema source used for development and testing.

    It simulates availability changing over time.
    """

    def __init__(self) -> None:
        self.check_number = 0

    def get_availability(
        self,
        watch: Watch,
    ) -> SourceResult:

        self.check_number += 1

        print(
            f"Mock source checking: "
            f"{watch.movie} | "
            f"{watch.target_date} | "
            f"{watch.city}"
        )

        if self.check_number == 1:
            raw_data = FIRST_CHECK
        else:
            raw_data = SECOND_CHECK

        filtered_data = self._filter_requested_cinemas(
            raw_data,
            watch,
        )

        if not filtered_data:
            return SourceResult(
                status=SourceStatus.NO_SHOWS,
                data={},
                message="No shows found.",
            )

        return SourceResult(
            status=SourceStatus.SUCCESS,
            data=filtered_data,
        )

    def _filter_requested_cinemas(
        self,
        data: dict,
        watch: Watch,
    ) -> dict:
        """
        Return only cinemas requested by the Watch.
        """

        requested_cinemas = {
            cinema.lower()
            for cinema in watch.cinemas
        }

        return {
            cinema: shows
            for cinema, shows in data.items()
            if cinema.lower() in requested_cinemas
        }