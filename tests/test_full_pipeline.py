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
from app.watcher import run_monitor
from tests.fakes import FakeCinemaResolver


class FakePageFetcher:
    def __init__(
        self,
        html,
    ):
        self.html = html
        self.urls = []

    def fetch(
        self,
        url,
    ):
        self.urls.append(
            url
        )

        return PublicPageResponse(
            url=url,
            status_code=200,
            html=self.html,
        )


class FakeParser:
    def __init__(
        self,
        responses,
    ):
        self.responses = responses
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

        return self.responses.get(
            cinema,
            [],
        )


def create_watch():
    return Watch(
        movie="Resident Evil",
        target_date=date(
            2026,
            9,
            18,
        ),
        city="Hyderabad",
        cinemas=["PVR"],
    )


def create_public_fetcher(
    page_fetcher,
):
    return BookMyShowPublicFetcher(
        page_fetcher=page_fetcher,
        cinema_resolver=FakeCinemaResolver(),
    )


def test_full_bookmyshow_to_notification_pipeline():
    watch = create_watch()

    page_fetcher = FakePageFetcher(
        html="<html>BookMyShow test page</html>"
    )

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
                    status="SOLD_OUT",
                    available_tickets=0,
                    source_id="session-123",
                )
            ]
        }
    )

    public_fetcher = create_public_fetcher(
        page_fetcher
    )

    source = BookMyShowSource(
        parser=parser,
        public_fetcher=public_fetcher,
    )

    first_result = source.get_availability(
        watch
    )

    assert (
        first_result.status
        == SourceStatus.SUCCESS
    )

    assert "PVR" in first_result.data

    assert (
        first_result.data["PVR"]["20:00"][
            "status"
        ]
        == "SOLD_OUT"
    )

    assert (
        first_result.data["PVR"]["20:00"][
            "available_tickets"
        ]
        == 0
    )

    assert (
        first_result.data["PVR"]["20:00"][
            "source_id"
        ]
        == "session-123"
    )

    assert len(
        page_fetcher.urls
    ) == 1

    assert len(
        parser.calls
    ) == 1

    assert (
        parser.calls[0]["movie"]
        == "Resident Evil"
    )

    assert (
        parser.calls[0]["show_date"]
        == date(
            2026,
            9,
            18,
        )
    )

    parser.responses["PVR"] = [
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

    second_result = source.get_availability(
        watch
    )

    assert (
        second_result.status
        == SourceStatus.SUCCESS
    )

    notifications = []
    saved_states = []
    previous_state = {}

    responses = [
        first_result,
        second_result,
    ]

    response_index = 0

    def fetch_availability():
        nonlocal response_index

        result = responses[
            response_index
        ]

        response_index += 1

        return result

    def load_state():
        return previous_state.copy()

    def save_state(state):
        nonlocal previous_state

        previous_state = state.copy()

        saved_states.append(
            state.copy()
        )

    def on_change(changes):
        notifications.append(
            changes
        )

    run_monitor(
        watch=watch,
        fetch_availability=fetch_availability,
        on_change=on_change,
        load_state=load_state,
        save_state=save_state,
        max_cycles=2,
    )

    assert len(
        notifications
    ) == 1

    changes = notifications[0]

    assert "PVR" in changes

    assert "20:00" in (
        changes["PVR"]
    )

    change = (
        changes["PVR"]["20:00"]
    )

    assert (
        change["previous"]
        == "SOLD_OUT"
    )

    assert (
        change["current"]
        == "AVAILABLE"
    )

    assert (
        change["previous_tickets"]
        == 0
    )

    assert (
        change["current_tickets"]
        == 5
    )

    assert len(
        saved_states
    ) == 2

    assert (
        saved_states[-1][
            "session-123"
        ]["status"]
        == "AVAILABLE"
    )


def test_full_pipeline_keeps_all_show_times():
    watch = create_watch()

    page_fetcher = FakePageFetcher(
        html="<html>BookMyShow test page</html>"
    )

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
                    show_time="17:00",
                    status="AVAILABLE",
                    available_tickets=5,
                    source_id="early-show",
                ),
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
                    source_id="evening-show",
                ),
            ]
        }
    )

    public_fetcher = create_public_fetcher(
        page_fetcher
    )

    source = BookMyShowSource(
        parser=parser,
        public_fetcher=public_fetcher,
    )

    result = source.get_availability(
        watch
    )

    assert (
        result.status
        == SourceStatus.SUCCESS
    )

    saved_states = []
    previous_state = {}

    def load_state():
        return previous_state.copy()

    def save_state(state):
        nonlocal previous_state

        previous_state = state.copy()

        saved_states.append(
            state.copy()
        )

    notifications = []

    run_monitor(
        watch=watch,
        fetch_availability=lambda: result,
        on_change=lambda changes: notifications.append(
            changes
        ),
        load_state=load_state,
        save_state=save_state,
        max_cycles=1,
    )

    assert len(
        saved_states
    ) == 1

    # There is no time preference anymore,
    # so every matching show is retained.
    assert "early-show" in (
        saved_states[0]
    )

    assert "evening-show" in (
        saved_states[0]
    )

    assert (
        saved_states[0][
            "early-show"
        ]["show_time"]
        == "17:00"
    )

    assert (
        saved_states[0][
            "evening-show"
        ]["show_time"]
        == "20:00"
    )

    assert (
        saved_states[0][
            "early-show"
        ]["available_tickets"]
        == 5
    )

    assert (
        saved_states[0][
            "evening-show"
        ]["available_tickets"]
        == 5
    )

    # Both shows are new and AVAILABLE,
    # therefore both are reported as changes.
    assert len(
        notifications
    ) == 1

    assert "PVR" in notifications[0]

    assert "17:00" in (
        notifications[0]["PVR"]
    )

    assert "20:00" in (
        notifications[0]["PVR"]
    )

    early_change = (
        notifications[0]["PVR"]["17:00"]
    )

    evening_change = (
        notifications[0]["PVR"]["20:00"]
    )

    assert (
        early_change["previous"]
        is None
    )

    assert (
        early_change["current"]
        == "AVAILABLE"
    )

    assert (
        early_change["previous_tickets"]
        is None
    )

    assert (
        early_change["current_tickets"]
        == 5
    )

    assert (
        evening_change["previous"]
        is None
    )

    assert (
        evening_change["current"]
        == "AVAILABLE"
    )

    assert (
        evening_change["previous_tickets"]
        is None
    )

    assert (
        evening_change["current_tickets"]
        == 5
    )