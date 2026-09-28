import pytest

import app.config as config


def test_get_source_name(monkeypatch):
    monkeypatch.setenv(
        "SOURCE",
        "BookMyShow",
    )

    assert (
        config.get_source_name()
        == "bookmyshow"
    )


def test_get_source_name_defaults_to_mock(
    monkeypatch,
):
    monkeypatch.delenv(
        "SOURCE",
        raising=False,
    )

    assert (
        config.get_source_name()
        == "mock"
    )


def test_get_max_cycles(
    monkeypatch,
):
    monkeypatch.setenv(
        "MAX_CYCLES",
        "5",
    )

    assert (
        config.get_max_cycles()
        == 5
    )


def test_get_max_cycles_empty_means_unlimited(
    monkeypatch,
):
    monkeypatch.setenv(
        "MAX_CYCLES",
        "",
    )

    assert (
        config.get_max_cycles()
        is None
    )


def test_get_max_cycles_missing_means_unlimited(
    monkeypatch,
):
    monkeypatch.delenv(
        "MAX_CYCLES",
        raising=False,
    )

    assert (
        config.get_max_cycles()
        is None
    )


def test_get_max_cycles_rejects_invalid_value(
    monkeypatch,
):
    monkeypatch.setenv(
        "MAX_CYCLES",
        "abc",
    )

    with pytest.raises(
        ValueError,
        match="MAX_CYCLES must be an integer",
    ):
        config.get_max_cycles()


def test_get_max_cycles_rejects_zero(
    monkeypatch,
):
    monkeypatch.setenv(
        "MAX_CYCLES",
        "0",
    )

    with pytest.raises(
        ValueError,
        match="MAX_CYCLES must be at least 1",
    ):
        config.get_max_cycles()


def test_normal_interval(
    monkeypatch,
):
    monkeypatch.setenv(
        "NORMAL_INTERVAL",
        "120",
    )

    assert (
        config.get_normal_interval()
        == 120
    )


def test_normal_interval_default(
    monkeypatch,
):
    monkeypatch.delenv(
        "NORMAL_INTERVAL",
        raising=False,
    )

    assert (
        config.get_normal_interval()
        == 60
    )


def test_active_interval(
    monkeypatch,
):
    monkeypatch.setenv(
        "ACTIVE_INTERVAL",
        "15",
    )

    assert (
        config.get_active_interval()
        == 15
    )


def test_active_interval_default(
    monkeypatch,
):
    monkeypatch.delenv(
        "ACTIVE_INTERVAL",
        raising=False,
    )

    assert (
        config.get_active_interval()
        == 10
    )


def test_interval_rejects_invalid_value(
    monkeypatch,
):
    monkeypatch.setenv(
        "ACTIVE_INTERVAL",
        "abc",
    )

    with pytest.raises(
        ValueError,
        match="ACTIVE_INTERVAL must be an integer",
    ):
        config.get_active_interval()


def test_interval_rejects_zero(
    monkeypatch,
):
    monkeypatch.setenv(
        "NORMAL_INTERVAL",
        "0",
    )

    with pytest.raises(
        ValueError,
        match="NORMAL_INTERVAL must be at least 1",
    ):
        config.get_normal_interval()
