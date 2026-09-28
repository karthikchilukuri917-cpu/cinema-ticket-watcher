from datetime import date

from app.filters import filter_shows
from app.models import Show, Watch


def make_watch():
    return Watch(
        movie="The Paradise",
        target_date=date(2026, 9, 24),
        city="Hyderabad",
        cinemas=["PVR"],
    )


def make_show(show_time):
    return Show(
        movie="The Paradise",
        cinema="PVR",
        show_date=date(2026, 9, 24),
        show_time=show_time,
        status="AVAILABLE",
    )


def test_filter_shows_keeps_all_show_times():
    watch = make_watch()

    shows = [
        make_show("17:00"),
        make_show("18:00"),
        make_show("20:00"),
        make_show("21:30"),
        make_show("23:00"),
    ]

    result = filter_shows(
        shows,
        watch,
    )

    assert len(result) == 5


def test_filter_shows_does_not_remove_early_shows():
    watch = make_watch()

    shows = [
        make_show("17:00"),
        make_show("20:00"),
    ]

    result = filter_shows(
        shows,
        watch,
    )

    assert len(result) == 2
    assert result[0].show_time == "17:00"


def test_filter_shows_does_not_remove_late_shows():
    watch = make_watch()

    shows = [
        make_show("20:00"),
        make_show("23:00"),
    ]

    result = filter_shows(
        shows,
        watch,
    )

    assert len(result) == 2
    assert result[1].show_time == "23:00"