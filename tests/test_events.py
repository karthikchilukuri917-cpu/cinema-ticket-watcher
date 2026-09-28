from app.events import is_available, should_notify


def test_available_status_is_available():
    assert is_available(
        status="AVAILABLE",
    )


def test_sold_out_status_is_not_available():
    assert not is_available(
        status="SOLD_OUT",
    )


def test_unknown_status_is_not_available():
    assert not is_available(
        status="UNKNOWN",
    )


def test_sold_out_to_available_notifies():
    assert should_notify(
        previous_status="SOLD_OUT",
        current_status="AVAILABLE",
    )


def test_available_to_available_does_not_notify():
    assert not should_notify(
        previous_status="AVAILABLE",
        current_status="AVAILABLE",
    )


def test_available_to_sold_out_does_not_notify():
    assert not should_notify(
        previous_status="AVAILABLE",
        current_status="SOLD_OUT",
    )


def test_unknown_to_available_notifies():
    assert should_notify(
        previous_status="UNKNOWN",
        current_status="AVAILABLE",
    )