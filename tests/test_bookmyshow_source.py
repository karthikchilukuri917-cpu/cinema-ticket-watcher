from datetime import date

from app.models import Watch
from app.sources.bookmyshow import (
    BookMyShowSource,
)
from app.sources.result import SourceStatus


def make_watch() -> Watch:
    return Watch(
        movie="The Paradise",
        target_date=date(
            2026,
            9,
            24,
        ),
        city="Hyderabad",
        cinemas=[
            "PVR",
        ],
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

    assert (
        result.status
        == SourceStatus.NO_SHOWS
    )
    assert result.data == {}


def test_bookmyshow_source_parses_html():

    html = """
    <script type="application/json">
    {
        "Event": [
            {
                "EventTitle": "The Paradise",
                "ChildEvents": [
                    {
                        "EventName":
                            "The Paradise - Telugu",
                        "ShowTimes": [
                            {
                                "ShowDateTime":
                                    "202609241930",
                                "ShowTime":
                                    "07:30 PM",
                                "AvailStatus":
                                    "3",
                                "BestAvailableSeats":
                                    4,
                                "SessionId":
                                    "test-123"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    </script>
    """

    def fake_fetcher(watch):
        return html

    source = BookMyShowSource(
        fetcher=fake_fetcher
    )

    result = source.get_availability(
        make_watch()
    )

    assert (
        result.status
        == SourceStatus.SUCCESS
    )

    assert "PVR" in result.data

    assert (
        result.data["PVR"]["19:30"]["status"]
        == "AVAILABLE"
    )

    assert (
        result.data["PVR"]["19:30"][
            "available_tickets"
        ]
        == 4
    )

    assert (
        result.data["PVR"]["19:30"][
            "source_id"
        ]
        == "test-123"
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

    assert (
        result.status
        == SourceStatus.NO_SHOWS
    )


def test_bookmyshow_source_handles_invalid_data():

    def fake_fetcher(watch):
        return "invalid"

    source = BookMyShowSource(
        fetcher=fake_fetcher
    )

    result = source.get_availability(
        make_watch()
    )

    assert (
        result.status
        == SourceStatus.ERROR
    )

def test_bookmyshow_source_reports_disabled_date_as_unavailable():

    html = """
    <script>
    {
        "ShowDatesArray": [
            {
                "DateCode": "20260921",
                "isDisabled": false
            },
            {
                "DateCode": "20260924",
                "isDisabled": true
            }
        ],
        "Event": [
            {
                "EventTitle": "The Paradise",
                "ChildEvents": [
                    {
                        "EventName": "The Paradise - Telugu",
                        "ShowTimes": [
                            {
                                "ShowDateTime": "202609211930",
                                "ShowTime": "07:30 PM",
                                "AvailStatus": "3",
                                "BestAvailableSeats": 4,
                                "SessionId": "old-date-show"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    </script>
    """

    source = BookMyShowSource(
        fetcher=lambda watch: html
    )

    result = source.get_availability(
        make_watch()
    )

    assert result.status == SourceStatus.UNAVAILABLE
    assert result.data == {}
    assert "2026-09-24" in result.message


def test_bookmyshow_source_passes_movie_event_code_to_parser():
    received_event_code = None

    class FakeParser:
        def parse(
            self,
            html,
            movie,
            show_date,
            cinema,
            movie_event_code=None,
        ):
            nonlocal received_event_code
            received_event_code = movie_event_code
            return []

    watch = Watch(
        movie="The Paradise",
        movie_event_code="KNOWN_EVENT_CODE",
        target_date=date(
            2026,
            9,
            24,
        ),
        city="Hyderabad",
        cinemas=["PVR"],
    )

    source = BookMyShowSource(
        fetcher=lambda watch: "<html>test</html>",
        parser=FakeParser(),
    )

    result = source.get_availability(watch)

    assert result.status == SourceStatus.NO_SHOWS
    assert received_event_code == "KNOWN_EVENT_CODE"