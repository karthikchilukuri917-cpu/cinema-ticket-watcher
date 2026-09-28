from collections.abc import Callable

from app.models import Watch
from app.sources.base import CinemaSource
from app.sources.result import SourceResult, SourceStatus


class PublicPageSource(CinemaSource):
    """
    Generic source adapter for a permitted public/authorized
    cinema data provider.

    The actual fetching mechanism is injected through `fetcher`.

    Expected fetcher contract:

        fetcher(watch) -> raw availability dictionary
    """

    def __init__(
        self,
        fetcher: Callable[[Watch], dict] | None = None,
    ) -> None:
        self.fetcher = fetcher

    def get_availability(
        self,
        watch: Watch,
    ) -> SourceResult:

        if self.fetcher is None:
            return SourceResult(
                status=SourceStatus.UNAVAILABLE,
                data={},
                message=(
                    "No permitted public cinema "
                    "data provider is configured."
                ),
            )

        try:
            data = self.fetcher(watch)

        except Exception as error:
            return SourceResult(
                status=SourceStatus.ERROR,
                data={},
                message=(
                    "Public cinema source failed: "
                    f"{error}"
                ),
            )

        if not isinstance(data, dict):
            return SourceResult(
                status=SourceStatus.ERROR,
                data={},
                message=(
                    "Public cinema source returned "
                    "invalid data."
                ),
            )

        if not data:
            return SourceResult(
                status=SourceStatus.NO_SHOWS,
                data={},
                message="No shows found.",
            )

        return SourceResult(
            status=SourceStatus.SUCCESS,
            data=data,
        )