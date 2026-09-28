from datetime import date

import pytest

from app.models import Cinema, Show, Watch
from app.normalizer import normalize_availability
from app.sources.mock import MockCinemaSource
from app.sources.result import SourceStatus


def test_watch_can_be_created_without_time_or_ticket_preferences():
    watch = Watch(
        movie="The Paradise",
        target_date=date(2026, 9, 24),
        city="Hyderabad",
        cinemas=["PVR", "AMB Cinemas"],
    )

    assert watch.movie == "The Paradise"
    assert watch.target_date == date(2026, 9, 24)
    assert watch.city == "Hyderabad"
    assert watch.cinemas == ["PVR", "AMB Cinemas"]


def test_watch_rejects_empty_cinemas():
    with pytest.raises(ValueError):
        Watch(
            movie="The Paradise",
            target_date=date(2026, 9, 24),
            city="Hyderabad",
            cinemas=[],
        )


def test_show_can_be_created():
    show = Show(
        movie="The Paradise",
        cinema="PVR",
        show_date=date(2026, 9, 24),
        show_time="19:30",
        status="AVAILABLE",
    )

    assert show.movie == "The Paradise"
    assert show.cinema == "PVR"
    assert show.show_time == "19:30"
    assert show.status == "AVAILABLE"


def test_normalizer_creates_show_objects():
    raw_data = {
        "PVR": {
            "19:30": "AVAILABLE",
            "21:00": "SOLD_OUT",
        },
        "Prasads": {
            "21:00": "AVAILABLE",
        },
    }

    shows = normalize_availability(
        data=raw_data,
        movie="The Paradise",
        show_date=date(2026, 9, 24),
    )

    assert len(shows) == 3

    assert shows[0].movie == "The Paradise"
    assert shows[0].cinema == "PVR"
    assert shows[0].show_time == "19:30"
    assert shows[0].status == "AVAILABLE"


def test_normalizer_handles_empty_data():
    shows = normalize_availability(
        data={},
        movie="The Paradise",
        show_date=date(2026, 9, 24),
    )

    assert shows == []


def test_mock_source_respects_requested_cinemas():
    watch = Watch(
        movie="The Paradise",
        target_date=date(2026, 9, 24),
        city="Hyderabad",
        cinemas=["PVR"],
    )

    source = MockCinemaSource()

    result = source.get_availability(watch)

    assert result.status == SourceStatus.SUCCESS
    assert "PVR" in result.data
    assert "AMB Cinemas" not in result.data
    assert "Prasads" not in result.data


def test_cinema_identity_uses_venue_id():
    cinema = Cinema(
        name="PVR",
        city="Hyderabad",
        venue_id="pvr-hyderabad-123",
    )

    assert cinema.identity == "pvr-hyderabad-123"


def test_cinema_identity_falls_back_to_city_and_name():
    cinema = Cinema(
        name="PVR",
        city="Hyderabad",
    )

    assert cinema.identity == "Hyderabad|PVR"