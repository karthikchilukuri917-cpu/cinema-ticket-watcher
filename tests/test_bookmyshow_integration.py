from datetime import date

from app.models import Show, Watch
from app.providers.bookmyshow_public import (
    BookMyShowPublicFetcher,
)
from app.providers.public_page import (
    PublicPageResponse,
)
from app.sources.bookmyshow import (
    BookMyShowSource,
)
from app.sources.result import (
    SourceStatus,
)

from tests.fakes import (
    FakeCinemaResolver,
)


class FakePageFetcher:
    """
    Deterministic page fetcher.

    No real BookMyShow network requests are made by
    integration tests.
    """

    def __init__(
        self,
        html="<html>BookMyShow test page</html>",
    ):
        self.html = html
        self.urls = []

    def fetch(
        self,
        url: str,
    ) -> PublicPageResponse:

        self.urls.append(url)

        return PublicPageResponse(
            url=url,
            status_code=200,
            html=self.html,
        )


class FakeParser:
    """
    Deterministic parser used to test the source adapter
    independently from the real BookMyShow HTML parser.
    """

    def __init__(
        self,
        responses=None,
    ):
        self.responses = (
            responses
            if responses is not None
            else {}
        )

        self.calls = []

    def parse(
        self,
        html,
        movie,
        show_date,
        cinema,
    ):

        self.calls.append(
            {
                "html": html,
                "movie": movie,
                "show_date": show_date,
                "cinema": cinema,
            }
        )

        return list(
            self.responses.get(
                cinema,
                [],
            )
        )


def create_watch(
    cinemas=None,
):
    return Watch(
        movie="Resident Evil",
        target_date=date(
            2026,
            9,
            18,
        ),
        city="Hyderabad",
        cinemas=(
            cinemas
            if cinemas is not None
            else ["PVR"]
        ),
    )


def create_public_fetcher(
    html="<html>BookMyShow test page</html>",
):
    page_fetcher = FakePageFetcher(
        html=html
    )

    cinema_resolver = (
        FakeCinemaResolver()
    )

    public_fetcher = (
        BookMyShowPublicFetcher(
            page_fetcher=page_fetcher,
            cinema_resolver=cinema_resolver,
        )
    )

    return (
        public_fetcher,
        page_fetcher,
        cinema_resolver,
    )


def create_source(
    parser=None,
    html="<html>BookMyShow test page</html>",
):
    if parser is None:
        parser = FakeParser()

    public_fetcher, _, _ = (
        create_public_fetcher(
            html=html
        )
    )

    return BookMyShowSource(
        parser=parser,
        public_fetcher=public_fetcher,
    )


# =========================================================
# PUBLIC FETCHER INTEGRATION
# =========================================================


def test_public_fetcher_does_not_require_real_network():
    public_fetcher, page_fetcher, _ = (
        create_public_fetcher()
    )

    pages = public_fetcher.fetch(
        create_watch()
    )

    assert "PVR" in pages

    assert (
        pages["PVR"].html
        == "<html>BookMyShow test page</html>"
    )

    assert len(
        page_fetcher.urls
    ) == 1


def test_public_fetcher_returns_cinema_page():
    public_fetcher, _, _ = (
        create_public_fetcher()
    )

    pages = public_fetcher.fetch(
        create_watch()
    )

    page = pages["PVR"]

    assert page.cinema == "PVR"

    assert page.status_code == 200

    assert page.html == (
        "<html>BookMyShow test page</html>"
    )


def test_public_fetcher_builds_correct_pvr_url():
    public_fetcher, _, _ = (
        create_public_fetcher()
    )

    pages = public_fetcher.fetch(
        create_watch()
    )

    assert (
        pages["PVR"].url
        == (
            "https://in.bookmyshow.com/"
            "cinemas/HYD/"
            "pvr-nexus-mall-kukatpally"
            "-hyderabad/"
            "buytickets/PVFS/"
            "20260918"
        )
    )


def test_public_fetcher_passes_all_cinemas_to_resolver():
    public_fetcher, _, resolver = (
        create_public_fetcher()
    )

    watch = create_watch(
        cinemas=[
            "PVR",
            "AMB Cinemas",
            "Prasads",
        ]
    )

    pages = public_fetcher.fetch(
        watch
    )

    assert set(
        pages.keys()
    ) == {
        "PVR",
        "AMB Cinemas",
        "Prasads",
    }

    assert resolver.calls == [
        (
            "PVR",
            "Hyderabad",
        ),
        (
            "AMB Cinemas",
            "Hyderabad",
        ),
        (
            "Prasads",
            "Hyderabad",
        ),
    ]


def test_public_fetcher_fetches_one_page_per_cinema():
    public_fetcher, page_fetcher, _ = (
        create_public_fetcher()
    )

    watch = create_watch(
        cinemas=[
            "PVR",
            "AMB Cinemas",
            "Prasads",
        ]
    )

    public_fetcher.fetch(
        watch
    )

    assert len(
        page_fetcher.urls
    ) == 3


# =========================================================
# SOURCE ADAPTER INTEGRATION
# =========================================================


def test_source_uses_public_fetcher():
    parser = FakeParser()

    source = create_source(
        parser=parser
    )

    result = source.get_availability(
        create_watch()
    )

    assert result.status == (
        SourceStatus.NO_SHOWS
    )


def test_source_passes_cinema_page_html_to_parser():
    parser = FakeParser()

    source = create_source(
        parser=parser,
        html="<html>realistic test page</html>",
    )

    watch = create_watch()

    source.get_availability(
        watch
    )

    assert len(
        parser.calls
    ) == 1

    call = parser.calls[0]

    assert (
        call["html"]
        == "<html>realistic test page</html>"
    )

    assert (
        call["movie"]
        == "Resident Evil"
    )

    assert (
        call["show_date"]
        == date(
            2026,
            9,
            18,
        )
    )

    assert (
        call["cinema"]
        == "PVR"
    )


def test_source_converts_parsed_shows_to_result():
    parser = FakeParser(
        responses={
            "PVR": [
                Show(
                    movie="Resident Evil",
                    cinema="PVR",
                    show_date=date(
                        2026,
                        9,
                        18,
                    ),
                    show_time="20:00",
                    status="AVAILABLE",
                    available_tickets=5,
                    source_id="session-123",
                )
            ]
        }
    )

    source = create_source(
        parser=parser
    )

    result = source.get_availability(
        create_watch()
    )

    assert result.status == (
        SourceStatus.SUCCESS
    )

    assert "PVR" in result.data

    assert (
        "20:00"
        in result.data["PVR"]
    )

    show = result.data[
        "PVR"
    ]["20:00"]

    assert (
        show["status"]
        == "AVAILABLE"
    )

    assert (
        show["available_tickets"]
        == 5
    )

    assert (
        show["source_id"]
        == "session-123"
    )


def test_source_supports_multiple_cinemas():
    parser = FakeParser(
        responses={
            "PVR": [
                Show(
                    movie="Resident Evil",
                    cinema="PVR",
                    show_date=date(
                        2026,
                        9,
                        18,
                    ),
                    show_time="20:00",
                    status="AVAILABLE",
                    available_tickets=5,
                    source_id="pvr-session",
                )
            ],
            "AMB Cinemas": [
                Show(
                    movie="Resident Evil",
                    cinema="AMB Cinemas",
                    show_date=date(
                        2026,
                        9,
                        18,
                    ),
                    show_time="21:00",
                    status="AVAILABLE",
                    available_tickets=4,
                    source_id="amb-session",
                )
            ],
        }
    )

    source = create_source(
        parser=parser
    )

    result = source.get_availability(
        create_watch(
            cinemas=[
                "PVR",
                "AMB Cinemas",
            ]
        )
    )

    assert result.status == (
        SourceStatus.SUCCESS
    )

    assert set(
        result.data.keys()
    ) == {
        "PVR",
        "AMB Cinemas",
    }


def test_source_preserves_available_ticket_count():
    parser = FakeParser(
        responses={
            "PVR": [
                Show(
                    movie="Resident Evil",
                    cinema="PVR",
                    show_date=date(
                        2026,
                        9,
                        18,
                    ),
                    show_time="20:00",
                    status="AVAILABLE",
                    available_tickets=7,
                    source_id="session-123",
                )
            ]
        }
    )

    source = create_source(
        parser=parser
    )

    result = source.get_availability(
        create_watch()
    )

    assert (
        result.data["PVR"]["20:00"][
            "available_tickets"
        ]
        == 7
    )


def test_source_preserves_session_id():
    parser = FakeParser(
        responses={
            "PVR": [
                Show(
                    movie="Resident Evil",
                    cinema="PVR",
                    show_date=date(
                        2026,
                        9,
                        18,
                    ),
                    show_time="20:00",
                    status="AVAILABLE",
                    available_tickets=7,
                    source_id="session-123",
                )
            ]
        }
    )

    source = create_source(
        parser=parser
    )

    result = source.get_availability(
        create_watch()
    )

    assert (
        result.data["PVR"]["20:00"][
            "source_id"
        ]
        == "session-123"
    )


def test_source_returns_no_shows_when_parser_returns_empty():
    source = create_source(
        parser=FakeParser()
    )

    result = source.get_availability(
        create_watch()
    )

    assert result.status == (
        SourceStatus.NO_SHOWS
    )


# =========================================================
# SOURCE ERROR HANDLING
# =========================================================


def test_source_handles_public_fetcher_error():
    class FailingPublicFetcher:

        def fetch(self, watch):
            raise RuntimeError(
                "network failure"
            )

    source = BookMyShowSource(
        parser=FakeParser(),
        public_fetcher=(
            FailingPublicFetcher()
        ),
    )

    result = source.get_availability(
        create_watch()
    )

    assert result.status == (
        SourceStatus.ERROR
    )

    assert result.data == {}

    assert (
        "page fetch failed"
        in result.message.lower()
    )


def test_source_handles_parser_error():
    class FailingParser:

        def parse(
            self,
            html,
            movie,
            show_date,
            cinema,
        ):
            raise RuntimeError(
                "parser failure"
            )

    source = create_source(
        parser=FailingParser()
    )

    result = source.get_availability(
        create_watch()
    )

    assert result.status == (
        SourceStatus.ERROR
    )

    assert result.data == {}

    assert (
        "parsing failed"
        in result.message.lower()
    )


# =========================================================
# WATCH PARAMETERS
# =========================================================


def test_source_passes_time_range_watch_unchanged():
    parser = FakeParser()

    source = create_source(
        parser=parser
    )

    watch = create_watch(
    )

    result = source.get_availability(
        watch
    )

    assert result.status == (
        SourceStatus.NO_SHOWS
    )

    assert len(
        parser.calls
    ) == 1


def test_source_handles_multiple_pages_independently():
    parser = FakeParser(
        responses={
            "PVR": [
                Show(
                    movie="Resident Evil",
                    cinema="PVR",
                    show_date=date(
                        2026,
                        9,
                        18,
                    ),
                    show_time="20:00",
                    status="AVAILABLE",
                    available_tickets=5,
                    source_id="pvr-session",
                )
            ],
            "AMB Cinemas": [],
        }
    )

    source = create_source(
        parser=parser
    )

    result = source.get_availability(
        create_watch(
            cinemas=[
                "PVR",
                "AMB Cinemas",
            ]
        )
    )

    assert result.status == (
        SourceStatus.SUCCESS
    )

    assert set(
        result.data.keys()
    ) == {
        "PVR",
    }
