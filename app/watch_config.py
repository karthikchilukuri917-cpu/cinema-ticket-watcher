import os
from datetime import date

from app.models import Watch


def load_watch_from_environment() -> Watch:
    """
    Build a Watch from environment variables.

    This is currently a development configuration source.

    In the production application, this layer can later be
    replaced by a database or API without changing the
    watcher engine.

    Required:
        MOVIE
        TARGET_DATE
        CITY
        CINEMAS
    """

    movie = os.getenv("MOVIE")
    target_date = os.getenv("TARGET_DATE")
    city = os.getenv("CITY")
    cinemas = os.getenv("CINEMAS")

    missing = []

    if not movie:
        missing.append("MOVIE")

    if not target_date:
        missing.append("TARGET_DATE")

    if not city:
        missing.append("CITY")

    if not cinemas:
        missing.append("CINEMAS")

    if missing:
        raise ValueError(
            "Missing required watch configuration: "
            + ", ".join(missing)
        )

    try:
        parsed_date = date.fromisoformat(
            target_date
        )
    except ValueError as error:
        raise ValueError(
            "TARGET_DATE must use YYYY-MM-DD format."
        ) from error

    parsed_cinemas = [
        cinema.strip()
        for cinema in cinemas.split(",")
        if cinema.strip()
    ]

    return Watch(
        movie=movie,
        target_date=parsed_date,
        city=city,
        cinemas=parsed_cinemas,
    )