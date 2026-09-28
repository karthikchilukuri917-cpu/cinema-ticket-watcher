from datetime import date

from app.models import Watch
from app.providers.bookmyshow_public import (
    BookMyShowPublicFetcher,
)
from app.providers.public_page import (
    PublicPageResponse,
)

from tests.fakes import (
    FakeCinemaResolver,
)


class FakePageFetcher:

    def __init__(
        self,
        html="<html>test</html>",
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


def make_watch():

    return Watch(
        movie="Resident Evil",
        target_date=date(
            2026,
            9,
            18,
        ),
        city="Hyderabad",
        cinemas=[
            "PVR",
            "AMB Cinemas",
            "Prasads",
        ],
    )


def make_fetcher():

    page_fetcher = FakePageFetcher()

    cinema_resolver = (
        FakeCinemaResolver()
    )

    fetcher = (
        BookMyShowPublicFetcher(
            page_fetcher=page_fetcher,
            cinema_resolver=cinema_resolver,
        )
    )

    return (
        fetcher,
        page_fetcher,
        cinema_resolver,
    )


def test_fetches_all_requested_cinemas():

    fetcher, page_fetcher, resolver = (
        make_fetcher()
    )

    pages = fetcher.fetch(
        make_watch()
    )

    assert set(
        pages.keys()
    ) == {
        "PVR",
        "AMB Cinemas",
        "Prasads",
    }

    assert len(
        page_fetcher.urls
    ) == 3

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


def test_builds_correct_pvr_url():

    fetcher, _, _ = (
        make_fetcher()
    )

    pages = fetcher.fetch(
        make_watch()
    )

    pvr_page = pages[
        "PVR"
    ]

    assert (
        pvr_page.url
        == (
            "https://in.bookmyshow.com/"
            "cinemas/HYD/"
            "pvr-nexus-mall-kukatpally"
            "-hyderabad/"
            "buytickets/PVFS/"
            "20260918"
        )
    )


def test_page_contains_html():

    fetcher, _, _ = (
        make_fetcher()
    )

    pages = fetcher.fetch(
        make_watch()
    )

    assert (
        pages["PVR"].html
        == "<html>test</html>"
    )


def test_injected_resolver_is_used():

    fetcher, _, resolver = (
        make_fetcher()
    )

    fetcher.fetch(
        make_watch()
    )

    assert len(
        resolver.calls
    ) == 3
