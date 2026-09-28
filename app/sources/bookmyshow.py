from collections.abc import Callable
from typing import Dict

from app.models import Watch
from app.providers.bookmyshow_html import (
    BookMyShowHTMLParser,
)
from app.providers.bookmyshow_public import (
    BookMyShowPublicFetcher,
    CinemaPage,
)
from app.sources.base import CinemaSource
from app.sources.result import (
    SourceResult,
    SourceStatus,
)


class BookMyShowSource(CinemaSource):
    """
    BookMyShow source adapter.

    Supported fetcher contracts:

        fetcher(watch) -> dict

        fetcher(watch) -> HTML string

        fetcher(watch) -> dict[str, CinemaPage]

    Production behavior:

        No custom fetcher
            ↓
        BookMyShowPublicFetcher
            ↓
        CinemaPage objects
            ↓
        BookMyShowHTMLParser
            ↓
        normalized availability

    Tests can inject a fake fetcher, parser, or
    BookMyShowPublicFetcher without making live requests.
    """

    def __init__(
        self,
        fetcher: Callable[[Watch], object] | None = None,
        parser: BookMyShowHTMLParser | None = None,
        public_fetcher: BookMyShowPublicFetcher | None = None,
    ) -> None:

        self.fetcher = fetcher

        self.parser = (
            parser
            if parser is not None
            else BookMyShowHTMLParser()
        )

        self.public_fetcher = (
            public_fetcher
            if public_fetcher is not None
            else BookMyShowPublicFetcher()
        )

    def get_availability(self, watch: Watch) -> SourceResult:
        try:
            if self.fetcher is not None:
                raw_data = self.fetcher(watch)
            else:
                raw_data = self.public_fetcher.fetch(watch)

        except Exception as error:
            return SourceResult(
                status=SourceStatus.ERROR,
                data={},
                message=(
                    "BookMyShow page fetch failed: "
                    f"{error}"
                ),
            )

        # ---------------------------------------------------------
        # Dictionary result
        # ---------------------------------------------------------
        if isinstance(raw_data, dict):

            if not raw_data:
                return SourceResult(
                    status=SourceStatus.NO_SHOWS,
                    data={},
                    message="No shows found.",
                )

            if all(
                isinstance(value, CinemaPage)
                for value in raw_data.values()
            ):
                return self._parse_cinema_pages(
                    pages=raw_data,
                    watch=watch,
                )

            return SourceResult(
                status=SourceStatus.SUCCESS,
                data=raw_data,
            )

        # ---------------------------------------------------------
        # Raw HTML result
        # ---------------------------------------------------------
        if isinstance(raw_data, str):

            html = raw_data.strip()

            if not html:
                return SourceResult(
                    status=SourceStatus.NO_SHOWS,
                    data={},
                    message=(
                        "BookMyShow page contained no HTML."
                    ),
                )

            lowered = html.lower()

            if (
                "<html" not in lowered
                and "<script" not in lowered
            ):
                return SourceResult(
                    status=SourceStatus.ERROR,
                    data={},
                    message=(
                        "BookMyShow fetcher returned "
                        "invalid HTML."
                    ),
                )

            # -----------------------------------------------------
            # The raw-HTML contract is the one place where we can
            # inspect the page-level date state before deciding
            # that an empty parsed result means NO_SHOWS.
            #
            # This fixes:
            #
            #   disabled target date -> UNAVAILABLE
            #
            # without changing the CinemaPage/test-parser contract.
            # -----------------------------------------------------
            get_date_status = getattr(
                self.parser,
                "get_date_status",
                None,
            )

            if callable(get_date_status):
                try:
                    date_status = get_date_status(
                        html=html,
                        show_date=watch.target_date,
                    )
                except Exception:
                    # Date-status detection is supplementary.
                    # Normal parsing remains authoritative.
                    date_status = None

                if date_status == "DISABLED":
                    return SourceResult(
                        status=SourceStatus.UNAVAILABLE,
                        data={},
                        message=(
                            "BookMyShow date is disabled: "
                            f"{watch.target_date}"
                        ),
                    )

            try:
                data = self._parse_html(
                    html=html,
                    watch=watch,
                )

            except Exception as error:
                return SourceResult(
                    status=SourceStatus.ERROR,
                    data={},
                    message=(
                        "BookMyShow HTML parsing failed: "
                        f"{error}"
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

        # ---------------------------------------------------------
        # Unsupported result
        # ---------------------------------------------------------
        return SourceResult(
            status=SourceStatus.ERROR,
            data={},
            message=(
                "BookMyShow fetcher returned "
                "unsupported data."
            ),
        )

    def _parse_cinema_pages(
        self,
        pages: Dict[str, CinemaPage],
        watch: Watch,
    ) -> SourceResult:

        result: Dict = {}

        for cinema, page in pages.items():

            if page is None:
                continue

            html = (
                page.html
                if isinstance(page.html, str)
                else ""
            )

            if not html.strip():
                continue

            try:
                try:
                    shows = self.parser.parse(
                        html=html,
                        movie=watch.movie,
                        show_date=watch.target_date,
                        cinema=cinema,
                        movie_event_code=watch.movie_event_code,
                    )

                except TypeError as error:
                    if "movie_event_code" not in str(error):
                        raise

                    # Backward compatibility with older/fake parsers
                    # that don't accept movie_event_code.
                    shows = self.parser.parse(
                        html=html,
                        movie=watch.movie,
                        show_date=watch.target_date,
                        cinema=cinema,
                    )

            except Exception as error:
                return SourceResult(
                    status=SourceStatus.ERROR,
                    data={},
                    message=(
                        "BookMyShow parsing failed "
                        f"for {cinema}: {error}"
                    ),
                )

            if not shows:
                continue

            cinema_data: Dict = {}

            for show in shows:
                cinema_data[show.show_time] = {
                    "status": show.status,
                    "available_tickets": (
                        show.available_tickets
                    ),
                    "source_id": show.source_id,
                }

            if cinema_data:
                result[cinema] = cinema_data

        if not result:
            return SourceResult(
                status=SourceStatus.NO_SHOWS,
                data={},
                message="No shows found.",
            )

        return SourceResult(
            status=SourceStatus.SUCCESS,
            data=result,
        )

    def _parse_html(
        self,
        html: str,
        watch: Watch,
    ) -> Dict:

        result: Dict = {}

        for cinema in watch.cinemas:

            try:
                try:
                    shows = self.parser.parse(
                        html=html,
                        movie=watch.movie,
                        show_date=watch.target_date,
                        cinema=cinema,
                        movie_event_code=watch.movie_event_code,
                    )

                except TypeError as error:
                    if "movie_event_code" not in str(error):
                        raise

                    shows = self.parser.parse(
                        html=html,
                        movie=watch.movie,
                        show_date=watch.target_date,
                        cinema=cinema,
                    )

            except Exception as error:
                return SourceResult(
                    status=SourceStatus.ERROR,
                    data={},
                    message=(
                        "BookMyShow parsing failed "
                        f"for {cinema}: {error}"
                    ),
                )

            if not shows:
                continue

            cinema_data: Dict = {}

            for show in shows:
                cinema_data[show.show_time] = {
                    "status": show.status,
                    "available_tickets": (
                        show.available_tickets
                    ),
                    "source_id": show.source_id,
                }

            if cinema_data:
                result[cinema] = cinema_data

        return result