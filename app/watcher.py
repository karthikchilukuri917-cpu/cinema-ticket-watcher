import time
import logging
import threading

from datetime import (
    datetime,
    date,
    time as datetime_time,
    timedelta,
)

from typing import Callable, Dict, List

from app.config import (
    get_active_interval,
    get_normal_interval,
)
from app.events import should_notify
from app.models import Show, Watch
from app.normalizer import normalize_availability
from app.sources.result import SourceResult, SourceStatus


logger = logging.getLogger(__name__)


ACTIVE_WINDOW = timedelta(hours=18)


def get_monitoring_mode(
    target_date: date,
    now: datetime | None = None,
) -> str:

    if now is None:
        now = datetime.now()

    target_datetime = datetime.combine(
        target_date,
        datetime_time.min,
    )

    time_until_target = target_datetime - now

    if time_until_target <= ACTIVE_WINDOW:
        return "ACTIVE"

    return "NORMAL"


def get_interval(mode: str) -> int:

    if mode == "ACTIVE":
        return get_active_interval()

    return get_normal_interval()


def shows_to_state(
    shows: List[Show],
) -> Dict:

    state = {}

    for show in shows:

        state[show.identity] = {
            "movie": show.movie,
            "cinema": show.cinema,
            "show_date": show.show_date.isoformat(),
            "show_time": show.show_time,
            "status": show.status,
            "available_tickets": show.available_tickets,
            "source_id": show.source_id,
        }

    return state


def detect_changes(
    previous: Dict,
    current_shows: List[Show],
) -> Dict:

    changes = {}

    for show in current_shows:

        show_id = show.identity

        previous_data = previous.get(
            show_id
        )

        if previous_data is None:

            previous_status = None
            previous_tickets = None

        elif isinstance(previous_data, dict):

            previous_status = previous_data.get(
                "status"
            )

            previous_tickets = previous_data.get(
                "available_tickets"
            )

        else:

            previous_status = previous_data
            previous_tickets = None

        if should_notify(
            previous_status=previous_status,
            current_status=show.status,
        ):

            changes.setdefault(
                show.cinema,
                {}
            )[show.show_time] = {
                "previous": previous_status,
                "current": show.status,
                "previous_tickets": previous_tickets,
                "current_tickets": show.available_tickets,
                "show_id": show_id,
            }

    return changes


def _wait_for_interval(
    interval: int,
    stop_event: threading.Event | None,
    watch: Watch,
) -> bool:
    """
    Wait for the next monitoring interval.

    Returns True when monitoring should stop.

    Using Event.wait() instead of time.sleep() allows the
    scheduler to interrupt the wait immediately when a
    watch is paused, deleted, or the application shuts down.
    """

    if stop_event is None:

        time.sleep(interval)

        return False

    if stop_event.wait(interval):

        logger.info(
            "Monitor stopped by scheduler for %s.",
            watch.movie,
        )

        return True

    return False


def run_monitor(
    watch: Watch,
    fetch_availability: Callable[[], SourceResult],
    on_change: Callable[[Dict], None],
    load_state: Callable[[], Dict],
    save_state: Callable[[Dict], None],
    max_cycles: int | None = None,
    stop_event: threading.Event | None = None,
) -> bool:

    previous_state = load_state()

    cycle = 0

    logger.info(
        "Starting monitor for %s on %s",
        watch.movie,
        watch.target_date,
    )

    try:

        while True:

            if (
                stop_event is not None
                and stop_event.is_set()
            ):
                logger.info(
                    "Monitor stopped by scheduler for %s.",
                    watch.movie,
                )
                break

            cycle += 1

            now = datetime.now()

            mode = get_monitoring_mode(
                watch.target_date,
                now,
            )

            interval = get_interval(mode)

            logger.info(
                "Check #%s | Mode=%s | Interval=%ss",
                cycle,
                mode,
                interval,
            )

            logger.info(
                "Monitoring all available show times."
            )

            # --------------------------------------------------
            # 1. Fetch source data.
            # --------------------------------------------------

            try:

                result = fetch_availability()

            except Exception as error:

                logger.error(
                    "Cinema source failed: %s",
                    error,
                )

                logger.info(
                    "Previous state preserved."
                )

                if (
                    max_cycles is not None
                    and cycle >= max_cycles
                ):
                    break

                if _wait_for_interval(
                    interval,
                    stop_event,
                    watch,
                ):
                    break

                continue

            # --------------------------------------------------
            # 2. Validate source result.
            # --------------------------------------------------

            if not isinstance(
                result,
                SourceResult,
            ):

                logger.error(
                    "Invalid source result received."
                )

                if (
                    max_cycles is not None
                    and cycle >= max_cycles
                ):
                    break

                if _wait_for_interval(
                    interval,
                    stop_event,
                    watch,
                ):
                    break

                continue

            logger.info(
                "Source status: %s",
                result.status.value,
            )

            if result.message:

                logger.info(
                    "Source message: %s",
                    result.message,
                )

            # --------------------------------------------------
            # 3. Handle source failure.
            # --------------------------------------------------

            if result.status in {
                SourceStatus.UNAVAILABLE,
                SourceStatus.ERROR,
            }:

                logger.warning(
                    "Source did not provide reliable data. "
                    "State will not be changed."
                )

                if (
                    max_cycles is not None
                    and cycle >= max_cycles
                ):
                    break

                if _wait_for_interval(
                    interval,
                    stop_event,
                    watch,
                ):
                    break

                continue

            # --------------------------------------------------
            # 4. Handle no shows.
            # --------------------------------------------------

            if result.status == SourceStatus.NO_SHOWS:

                logger.info(
                    "Source successfully checked, "
                    "but no shows were found."
                )

                current_state = {}

                save_state(
                    current_state
                )

                previous_state = current_state

                if (
                    max_cycles is not None
                    and cycle >= max_cycles
                ):
                    break

                if _wait_for_interval(
                    interval,
                    stop_event,
                    watch,
                ):
                    break

                continue

            # --------------------------------------------------
            # 5. Normalize.
            # --------------------------------------------------

            try:

                shows = normalize_availability(
                    data=result.data,
                    movie=watch.movie,
                    show_date=watch.target_date,
                )

            except Exception as error:

                logger.error(
                    "Failed to normalize source data: %s",
                    error,
                )

                if (
                    max_cycles is not None
                    and cycle >= max_cycles
                ):
                    break

                if _wait_for_interval(
                    interval,
                    stop_event,
                    watch,
                ):
                    break

                continue

            logger.info(
                "Normalized %s show(s).",
                len(shows),
            )

            # --------------------------------------------------
            # 6. All normalized shows are relevant.
            # --------------------------------------------------

            matching_shows = shows

            logger.info(
                "Monitoring %s show(s).",
                len(matching_shows),
            )

            # --------------------------------------------------
            # 7. Detect availability changes.
            # --------------------------------------------------

            changes = detect_changes(
                previous=previous_state,
                current_shows=matching_shows,
            )

            if changes:

                logger.info(
                    "Meaningful availability detected."
                )

                try:

                    on_change(changes)

                except Exception as error:

                    logger.error(
                        "Notification failed: %s",
                        error,
                    )

                    # Do NOT stop the watcher when notification
                    # fails. The tickets are available, but the
                    # notification system needs another chance.
                    changes = {}

                else:

                    # --------------------------------------------------
                    # Tickets have been detected and the notification
                    # was successfully handed off.
                    #
                    # This watch is now complete.
                    # --------------------------------------------------

                    logger.info(
                        "Tickets became available for %s. "
                        "Watch completed; stopping monitor.",
                        watch.movie,
                    )

                    current_state = shows_to_state(
                        matching_shows
                    )

                    try:

                        save_state(
                            current_state
                        )

                        previous_state = current_state

                    except Exception as error:

                        logger.error(
                            "Failed to save final state.",
                            exc_info=error,
                        )

                    # --------------------------------------------------
                    # IMPORTANT:
                    #
                    # Tell WatchRunner / WatchScheduler that this
                    # monitor completed because tickets were found.
                    # --------------------------------------------------

                    return True

            else:

                logger.info(
                    "No meaningful availability changes."
                )

            # --------------------------------------------------
            # 8. Save successful state.
            # --------------------------------------------------

            current_state = shows_to_state(
                matching_shows
            )

            logger.info(
                "STATE DEBUG: %s show(s), keys=%s",
                len(current_state),
                list(current_state.keys()),
            )

            try:

                save_state(
                    current_state
                )

                previous_state = current_state

            except Exception as error:

                logger.error(
                    "Failed to save state.",
                    exc_info=True,
                )

            # --------------------------------------------------
            # 9. Stop condition.
            # --------------------------------------------------

            if (
                max_cycles is not None
                and cycle >= max_cycles
            ):

                logger.info(
                    "Test monitoring finished."
                )

                break

            logger.info(
                "Waiting %s seconds...",
                interval,
            )

            if _wait_for_interval(
                interval,
                stop_event,
                watch,
            ):
                break

    except KeyboardInterrupt:

        logger.info(
            "Monitor stopped by user."
        )

    # ----------------------------------------------------------
    # False means the monitor stopped for a reason other than
    # successfully detecting tickets.
    # ----------------------------------------------------------

    return False