AVAILABLE_STATUSES = {
    "AVAILABLE",
    "FILLING_FAST",
    "ALMOST_FULL",
}


def is_available(
    status: str | None,
) -> bool:
    """
    Return True if the show appears to have tickets available.

    Availability is determined by the source status.
    The number of available tickets is intentionally not
    used as a requirement for a watch.
    """

    return status in AVAILABLE_STATUSES


def should_notify(
    previous_status: str | None,
    current_status: str | None,
) -> bool:
    """
    Return True when a show transitions from unavailable
    to available.
    """

    was_available = is_available(previous_status)

    is_available_now = is_available(current_status)

    if not was_available and is_available_now:
        return True

    return False