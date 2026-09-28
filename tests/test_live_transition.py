from datetime import date

from app.models import Watch, Show
from app.watcher import detect_changes


def make_watch() -> Watch:
    return Watch(
        movie="The Paradise",
        target_date=date(
            2026,
            9,
            24,
        ),
        city="Hyderabad",
        cinemas=["PVR"],
    )


def test_sold_out_to_available_triggers_notification():

    watch = make_watch()

    previous_show = Show(
        movie=watch.movie,
        cinema="PVR",
        show_date=watch.target_date,
        show_time="19:30",
        status="SOLD_OUT",
        available_tickets=0,
        source_id="session-123",
    )

    current_show = Show(
        movie=watch.movie,
        cinema="PVR",
        show_date=watch.target_date,
        show_time="19:30",
        status="AVAILABLE",
        available_tickets=4,
        source_id="session-123",
    )

    previous_state = {
        previous_show.identity: {
            "movie": previous_show.movie,
            "cinema": previous_show.cinema,
            "show_date": (
                previous_show.show_date.isoformat()
            ),
            "show_time": previous_show.show_time,
            "status": previous_show.status,
            "available_tickets": (
                previous_show.available_tickets
            ),
            "source_id": previous_show.source_id,
        }
    }

    changes = detect_changes(
        previous=previous_state,
        current_shows=[current_show],
    )

    assert changes

    assert "PVR" in changes

    assert "19:30" in changes["PVR"]

    change = changes["PVR"]["19:30"]

    assert change["previous"] == "SOLD_OUT"
    assert change["current"] == "AVAILABLE"

    assert change["previous_tickets"] == 0
    assert change["current_tickets"] == 4

    assert change["show_id"] == "session-123"