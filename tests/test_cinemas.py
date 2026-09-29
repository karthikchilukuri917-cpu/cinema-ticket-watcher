from dataclasses import dataclass

import pytest

from app.cinemas import (
    BookMyShowCinemaResolver,
    CinemaVenue,
)


@dataclass
class FakeResponse:
    text: str

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self, html: str):
        self.html = html
        self.requested_urls = []

    def get(
        self,
        url,
        timeout,
        headers,
    ):
        self.requested_urls.append(url)

        return FakeResponse(
            text=self.html
        )


BOOKMYSHOW_HTML = """
<html>
<body>

<a href="/cinemas/hyderabad/
art-cinemas-vanasthalipuram/
buytickets/ACEV/20260924">
    ART CINEMAS: Vanasthalipuram
</a>

<a href="/cinemas/hyderabad/
pvr-nexus-mall-kukatpally-hyderabad/
buytickets/PVFS/20260924">
    PVR: Nexus Mall Kukatpally, Hyderabad
</a>

<a href="/cinemas/hyderabad/
amb-cinemas-gachibowli-hyderabad/
buytickets/AMBH/20260924">
    AMB Cinemas: Gachibowli
</a>

<a href="/cinemas/hyderabad/
prasads-multiplex-hyderabad/
buytickets/PRHN/20260924">
    Prasads Multiplex
</a>

</body>
</html>
"""


def create_resolver():
    session = FakeSession(
        BOOKMYSHOW_HTML
    )

    resolver = BookMyShowCinemaResolver(
        session=session,
    )

    return resolver, session


def test_discover_hyderabad_cinemas():
    resolver, session = create_resolver()

    cinemas = resolver.discover(
        "Hyderabad"
    )

    names = [
        cinema.name
        for cinema in cinemas
    ]

    assert (
        "ART CINEMAS: Vanasthalipuram"
        in names
    )

    assert (
        "PVR: Nexus Mall Kukatpally, Hyderabad"
        in names
    )

    assert (
        "AMB Cinemas: Gachibowli"
        in names
    )

    assert (
        "Prasads Multiplex"
        in names
    )

    assert session.requested_urls == [
        "https://in.bookmyshow.com/"
        "hyderabad/venue-list"
    ]


def test_resolve_art_dynamically():
    resolver, _ = create_resolver()

    venue = resolver.resolve(
        "ART",
        "Hyderabad",
    )

    assert venue.name == (
        "ART CINEMAS: Vanasthalipuram"
    )

    assert venue.provider_id == "ACEV"

    assert venue.slug == (
        "art-cinemas-vanasthalipuram"
    )

    assert venue.city_code == "HYDERABAD"


def test_resolve_pvr_dynamically():
    resolver, _ = create_resolver()

    venue = resolver.resolve(
        "PVR",
        "Hyderabad",
    )

    assert venue.name == (
        "PVR: Nexus Mall Kukatpally, Hyderabad"
    )

    assert venue.provider_id == "PVFS"


def test_resolve_amb_dynamically():
    resolver, _ = create_resolver()

    venue = resolver.resolve(
        "AMB Cinemas",
        "Hyderabad",
    )

    assert venue.name == (
        "AMB Cinemas: Gachibowli"
    )

    assert venue.provider_id == "AMBH"


def test_resolve_prasads_dynamically():
    resolver, _ = create_resolver()

    venue = resolver.resolve(
        "Prasads",
        "Hyderabad",
    )

    assert venue.name == "Prasads Multiplex"

    assert venue.provider_id == "PRHN"


def test_public_page_url():
    resolver, _ = create_resolver()

    venue = resolver.resolve(
        "ART",
        "Hyderabad",
    )

    url = venue.public_page_url(
        "2026-09-24"
    )

    assert url == (
        "https://in.bookmyshow.com/cinemas/"
        "HYDERABAD/"
        "art-cinemas-vanasthalipuram/"
        "buytickets/"
        "ACEV/"
        "20260924"
    )


def test_unknown_cinema_raises_error():
    resolver, _ = create_resolver()

    with pytest.raises(ValueError):
        resolver.resolve(
            "Unknown Cinema",
            "Hyderabad",
        )


def test_empty_cinema_raises_error():
    resolver, _ = create_resolver()

    with pytest.raises(ValueError):
        resolver.resolve(
            "",
            "Hyderabad",
        )
