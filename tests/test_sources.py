from datetime import date

from app.models import Watch
from app.sources.bookmyshow import BookMyShowSource
from app.sources.public_page import PublicPageSource
from app.sources.result import SourceStatus


def make_watch() -> Watch:
    return Watch(
        movie="The Paradise",
        target_date=date(2026, 9, 24),
        city="Hyderabad",
        cinemas=["PVR"],
    )


def test_bookmyshow_source_without_custom_fetcher():

    class FakePublicFetcher:
        def fetch(self, watch):
            return {}

    source = BookMyShowSource(
        public_fetcher=FakePublicFetcher()
    )

    result = source.get_availability(
        make_watch()
    )

    assert result.status == SourceStatus.NO_SHOWS
    assert result.data == {}


def test_bookmyshow_source_uses_fetcher():

    def fake_fetcher(watch):

        assert watch.movie == "The Paradise"
        assert watch.city == "Hyderabad"

        return {
            "PVR": {
                "19:30": {
                    "status": "AVAILABLE",
                    "available_tickets": 4,
                    "source_id": "test-123",
                }
            }
        }

    source = BookMyShowSource(
        fetcher=fake_fetcher
    )

    result = source.get_availability(
        make_watch()
    )

    assert result.status == SourceStatus.SUCCESS

    assert (
        result.data["PVR"]["19:30"]["status"]
        == "AVAILABLE"
    )


def test_bookmyshow_source_handles_empty_data():

    def fake_fetcher(watch):
        return {}

    source = BookMyShowSource(
        fetcher=fake_fetcher
    )

    result = source.get_availability(
        make_watch()
    )

    assert result.status == SourceStatus.NO_SHOWS
    assert result.data == {}


def test_bookmyshow_source_handles_invalid_data():

    def fake_fetcher(watch):
        return "invalid"

    source = BookMyShowSource(
        fetcher=fake_fetcher
    )

    result = source.get_availability(
        make_watch()
    )

    assert result.status == SourceStatus.ERROR


def test_bookmyshow_source_handles_fetcher_error():

    def fake_fetcher(watch):
        raise RuntimeError("connection failed")

    source = BookMyShowSource(
        fetcher=fake_fetcher
    )

    result = source.get_availability(
        make_watch()
    )

    assert result.status == SourceStatus.ERROR
    assert (
        "connection failed"
        in result.message
    )


def test_public_page_source_without_fetcher():

    source = PublicPageSource()

    result = source.get_availability(
        make_watch()
    )

    assert result.status == SourceStatus.UNAVAILABLE
    assert result.data == {}
    assert result.message is not None


def test_public_page_source_uses_fetcher():

    def fake_fetcher(watch):

        return {
            "PVR": {
                "19:30": {
                    "status": "AVAILABLE",
                    "available_tickets": None,
                    "source_id": "public-123",
                }
            }
        }

    source = PublicPageSource(
        fetcher=fake_fetcher
    )

    result = source.get_availability(
        make_watch()
    )

    assert result.status == SourceStatus.SUCCESS

    assert (
        result.data["PVR"]["19:30"]["status"]
        == "AVAILABLE"
    )

    assert (
        result.data["PVR"]["19:30"]
        ["available_tickets"]
        is None
    )


def test_public_page_source_handles_empty_data():

    source = PublicPageSource(
        fetcher=lambda watch: {}
    )

    result = source.get_availability(
        make_watch()
    )

    assert result.status == SourceStatus.NO_SHOWS
    assert result.data == {}


def test_public_page_source_handles_invalid_data():

    source = PublicPageSource(
        fetcher=lambda watch: "invalid"
    )

    result = source.get_availability(
        make_watch()
    )

    assert result.status == SourceStatus.ERROR


def test_public_page_source_handles_fetcher_error():

    def failing_fetcher(watch):
        raise RuntimeError("provider unavailable")

    source = PublicPageSource(
        fetcher=failing_fetcher
    )

    result = source.get_availability(
        make_watch()
    )

    assert result.status == SourceStatus.ERROR
    assert (
        "provider unavailable"
        in result.message
    )

