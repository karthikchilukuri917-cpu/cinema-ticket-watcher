from dataclasses import dataclass
from datetime import date
from typing import List


@dataclass
class Cinema:
    """
    Represents one specific cinema venue.
    """

    name: str
    city: str
    venue_id: str | None = None

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.city = self.city.strip()

        if not self.name:
            raise ValueError(
                "Cinema name cannot be empty."
            )

        if not self.city:
            raise ValueError(
                "Cinema city cannot be empty."
            )

        if self.venue_id is not None:
            self.venue_id = self.venue_id.strip()

    @property
    def identity(self) -> str:
        """
        Return the most stable identity available.
        """

        if self.venue_id:
            return self.venue_id

        return f"{self.city}|{self.name}"


@dataclass
class Watch:
    """
    Represents one cinema ticket availability watch.

    A watch monitors whether tickets become available for
    a movie on a specific date, city, and set of cinemas.
    """

    movie: str
    target_date: date
    city: str
    cinemas: List[str]
    movie_event_code: str | None = None
    active: bool = True
    completed: bool = False

    def __post_init__(self) -> None:
        if not self.movie.strip():
            raise ValueError(
                "Movie name cannot be empty."
            )

        if not self.city.strip():
            raise ValueError(
                "City cannot be empty."
            )

        if not self.cinemas:
            raise ValueError(
                "At least one cinema is required."
            )

        self.movie = self.movie.strip()
        self.city = self.city.strip()

        if self.movie_event_code is not None:
            self.movie_event_code = (
                self.movie_event_code.strip()
            ) or None

        self.cinemas = [
            cinema.strip()
            for cinema in self.cinemas
            if cinema.strip()
        ]

        if not self.cinemas:
            raise ValueError(
                "At least one valid cinema is required."
            )


@dataclass
class Show:
    """
    Represents one movie screening.
    """

    movie: str
    cinema: str
    show_date: date
    show_time: str
    status: str
    available_tickets: int | None = None
    source_id: str | None = None

    @property
    def identity(self) -> str:
        """
        Return a stable identity for this show.

        Prefer the source-provided ID when available.
        """

        if self.source_id:
            return self.source_id

        return (
            f"{self.movie}|"
            f"{self.cinema}|"
            f"{self.show_date.isoformat()}|"
            f"{self.show_time}"
        )