from datetime import date
from pathlib import Path

from app.models import Watch
from app.sources.result import SourceResult, SourceStatus
from app.watch_runner import WatchRunner


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


class FakeSource:

    def __init__(
        self,
        result=None,
        exception=None,
    ):
        self.result = result
        self.exception = exception

    def get_availability(
        self,
        watch,
    ):

        if self.exception is not None:
            raise self.exception

        return self.result


def make_runner(
    tmp_path: Path,
    source,
):

    def source_factory(
        watch,
    ):
        return source

    return WatchRunner(
        watch_id="watch-1",
        source_factory=source_factory,
        on_change=lambda changes: None,
        state_directory=tmp_path,
    )


def test_health_records_success(
    tmp_path,
):

    source = FakeSource(
        result=SourceResult(
            status=SourceStatus.SUCCESS,
            data={},
        )
    )

    runner = make_runner(
        tmp_path,
        source,
    )

    result = runner._fetch_availability(
        source,
        make_watch(),
    )

    assert result.status == SourceStatus.SUCCESS

    health = runner.get_health()

    assert health["status"] == "SUCCESS"
    assert health["message"] is None
    assert health["last_checked"]


def test_health_records_no_shows(
    tmp_path,
):

    source = FakeSource(
        result=SourceResult(
            status=SourceStatus.NO_SHOWS,
            data={},
            message="No shows found.",
        )
    )

    runner = make_runner(
        tmp_path,
        source,
    )

    result = runner._fetch_availability(
        source,
        make_watch(),
    )

    assert result.status == SourceStatus.NO_SHOWS

    health = runner.get_health()

    assert health["status"] == "NO_SHOWS"
    assert health["message"] == "No shows found."
    assert health["last_checked"]


def test_health_records_unavailable(
    tmp_path,
):

    source = FakeSource(
        result=SourceResult(
            status=SourceStatus.UNAVAILABLE,
            data={},
            message="BookMyShow unavailable.",
        )
    )

    runner = make_runner(
        tmp_path,
        source,
    )

    result = runner._fetch_availability(
        source,
        make_watch(),
    )

    assert result.status == SourceStatus.UNAVAILABLE

    health = runner.get_health()

    assert health["status"] == "UNAVAILABLE"
    assert (
        health["message"]
        == "BookMyShow unavailable."
    )
    assert health["last_checked"]


def test_health_records_error_result(
    tmp_path,
):

    source = FakeSource(
        result=SourceResult(
            status=SourceStatus.ERROR,
            data={},
            message="BookMyShow returned 503.",
        )
    )

    runner = make_runner(
        tmp_path,
        source,
    )

    result = runner._fetch_availability(
        source,
        make_watch(),
    )

    assert result.status == SourceStatus.ERROR

    health = runner.get_health()

    assert health["status"] == "ERROR"
    assert (
        health["message"]
        == "BookMyShow returned 503."
    )
    assert health["last_checked"]


def test_health_records_source_exception(
    tmp_path,
):

    source = FakeSource(
        exception=RuntimeError(
            "Network failure."
        )
    )

    runner = make_runner(
        tmp_path,
        source,
    )

    try:

        runner._fetch_availability(
            source,
            make_watch(),
        )

        assert False, (
            "Expected source exception."
        )

    except RuntimeError as exc:

        assert str(exc) == "Network failure."

    health = runner.get_health()

    assert health["status"] == "ERROR"
    assert (
        health["message"]
        == "Network failure."
    )
    assert health["last_checked"]


def test_health_can_be_cleared(
    tmp_path,
):

    source = FakeSource(
        result=SourceResult(
            status=SourceStatus.SUCCESS,
            data={},
        )
    )

    runner = make_runner(
        tmp_path,
        source,
    )

    runner._fetch_availability(
        source,
        make_watch(),
    )

    assert runner.get_health()

    runner.clear_health()

    assert runner.get_health() == {}


def test_health_survives_new_runner(
    tmp_path,
):

    source = FakeSource(
        result=SourceResult(
            status=SourceStatus.SUCCESS,
            data={},
        )
    )

    runner = make_runner(
        tmp_path,
        source,
    )

    runner._fetch_availability(
        source,
        make_watch(),
    )

    first_health = runner.get_health()

    second_runner = make_runner(
        tmp_path,
        source,
    )

    second_health = second_runner.get_health()

    assert second_health == first_health