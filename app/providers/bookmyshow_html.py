import json
import re
from datetime import date, datetime
from typing import Any, Dict, List

from app.models import Show
from app.movies import MovieCandidate

class BookMyShowHTMLParser:
    """
    Parse BookMyShow showtime data embedded inside public HTML.

    BookMyShow may report an available show with an unknown seat count.
    Such counts are represented as None by this parser.
    """

    def parse(
        self,
        html: str,
        movie: str,
        show_date: date,
        cinema: str,
        movie_event_code: str | None = None,
    ) -> List[Show]:

        if not html or not html.strip():
            return []

        event_data = self._extract_event_array(
            html
        )

        if event_data is None:
            return []

        shows: List[Show] = []

        self._extract_events(
            data=event_data,
            movie=movie,
            movie_event_code=movie_event_code,
            show_date=show_date,
            cinema=cinema,
            output=shows,
            parent_event_title="",
        )

        return self._remove_duplicates(
            shows
        )

    # ==================================================
    # DATE STATUS
    # ==================================================

    def get_date_status(
        self,
        html: str,
        show_date: date,
    ) -> str | None:
        """
        Return the BookMyShow state for a requested date.

        Returns:

            "AVAILABLE"
                Date exists and is not disabled.

            "DISABLED"
                Date exists and is explicitly disabled.

            None
                Date information is unavailable.
        """

        if not html or not html.strip():
            return None

        show_dates = (
            self._extract_show_dates_array(
                html
            )
        )

        if show_dates is None:
            return None

        expected_date = (
            show_date.strftime("%Y%m%d")
        )

        for item in show_dates:

            if not isinstance(
                item,
                dict,
            ):
                continue

            if str(
                item.get(
                    "DateCode",
                    "",
                )
            ) != expected_date:
                continue

            if bool(
                item.get(
                    "isDisabled"
                )
            ):
                return "DISABLED"

            return "AVAILABLE"

        return None

    # ==================================================
    # EVENT ARRAY EXTRACTION
    # ==================================================

    def _extract_event_array(
        self,
        html: str,
    ) -> List[Dict[str, Any]] | None:

        event_match = re.search(
            r'"Event"\s*:\s*\[',
            html,
        )

        if event_match is None:
            return None

        array_start = (
            event_match.end() - 1
        )

        array_end = (
            self._find_matching_bracket(
                text=html,
                start=array_start,
            )
        )

        if array_end is None:
            return None

        event_json = html[
            array_start : array_end + 1
        ]

        try:

            data = json.loads(
                event_json
            )

        except json.JSONDecodeError:

            try:

                unescaped = (
                    event_json
                    .replace(
                        '\\"',
                        '"',
                    )
                    .replace(
                        "\\/",
                        "/",
                    )
                )

                data = json.loads(
                    unescaped
                )

            except (
                json.JSONDecodeError,
                ValueError,
            ):
                return None

        if not isinstance(
            data,
            list,
        ):
            return None

        return data

    # ==================================================
    # SHOW DATE ARRAY EXTRACTION
    # ==================================================

    def _extract_show_dates_array(
        self,
        html: str,
    ) -> List[Dict[str, Any]] | None:

        match = re.search(
            r'"ShowDatesArray"\s*:\s*\[',
            html,
        )

        if match is None:
            return None

        array_start = (
            match.end() - 1
        )

        array_end = (
            self._find_matching_bracket(
                text=html,
                start=array_start,
            )
        )

        if array_end is None:
            return None

        dates_json = html[
            array_start : array_end + 1
        ]

        try:

            data = json.loads(
                dates_json
            )

        except json.JSONDecodeError:

            try:

                unescaped = (
                    dates_json
                    .replace(
                        '\\"',
                        '"',
                    )
                    .replace(
                        "\\/",
                        "/",
                    )
                )

                data = json.loads(
                    unescaped
                )

            except (
                json.JSONDecodeError,
                ValueError,
            ):
                return None

        if not isinstance(
            data,
            list,
        ):
            return None

        return data

    @staticmethod
    def _find_matching_bracket(
        text: str,
        start: int,
    ) -> int | None:

        depth = 0
        in_string = False
        escaped = False

        for index in range(
            start,
            len(text),
        ):

            character = text[index]

            if in_string:

                if escaped:
                    escaped = False
                    continue

                if character == "\\":
                    escaped = True
                    continue

                if character == '"':
                    in_string = False

                continue

            if character == '"':
                in_string = True
                continue

            if character == "[":
                depth += 1

            elif character == "]":

                depth -= 1

                if depth == 0:
                    return index

        return None

    # ==================================================
    # EVENT EXTRACTION
    # ==================================================

    def _extract_events(
        self,
        data: Any,
        movie: str,
        show_date: date,
        cinema: str,
        output: List[Show],
        parent_event_title: str = "",
        movie_event_code: str | None = None,
    ) -> None:

        if isinstance(
            data,
            list,
        ):

            for item in data:

                self._extract_events(
                    data=item,
                    movie=movie,
                    movie_event_code=movie_event_code,
                    show_date=show_date,
                    cinema=cinema,
                    output=output,
                    parent_event_title=(
                        parent_event_title
                    ),
                )

            return

        if not isinstance(
            data,
            dict,
        ):
            return

        current_event_title = str(
            data.get(
                "EventTitle",
                parent_event_title,
            )
            or parent_event_title
        )

        # ----------------------------------------------
        # Event containing ShowTimes directly
        # ----------------------------------------------

        if "ShowTimes" in data:

            event_name = str(
                data.get(
                    "EventName",
                    "",
                )
                or ""
            )

            if self._movie_matches(
                requested_movie=movie,
                requested_event_code=movie_event_code,
                event_name=event_name,
                event_title=current_event_title,
                event_code=data.get(
                    "EventCode"
                ),
            ):

                showtimes = data.get(
                    "ShowTimes",
                    [],
                )

                if isinstance(
                    showtimes,
                    list,
                ):

                    for show_data in showtimes:

                        self._add_show(
                            show_data=show_data,
                            movie=movie,
                            show_date=show_date,
                            cinema=cinema,
                            output=output,
                        )

            return

        # ----------------------------------------------
        # ChildEvents
        # ----------------------------------------------

        child_events = data.get(
            "ChildEvents",
            [],
        )

        if isinstance(
            child_events,
            list,
        ):

            for child_event in child_events:

                self._extract_events(
                    data=child_event,
                    movie=movie,
                    movie_event_code=movie_event_code,
                    show_date=show_date,
                    cinema=cinema,
                    output=output,
                    parent_event_title=(
                        current_event_title
                    ),
                )

        # ----------------------------------------------
        # Search nested structures
        # ----------------------------------------------

        for key, value in data.items():

            if key in (
                "ChildEvents",
                "ShowTimes",
            ):
                continue

            if isinstance(
                value,
                (dict, list),
            ):

                self._extract_events(
                    data=value,
                    movie=movie,
                    movie_event_code=movie_event_code,
                    show_date=show_date,
                    cinema=cinema,
                    output=output,
                    parent_event_title=(
                        current_event_title
                    ),
                )

    # ==================================================
    # SHOW CREATION
    # ==================================================

    def _add_show(
        self,
        show_data: Any,
        movie: str,
        show_date: date,
        cinema: str,
        output: List[Show],
    ) -> None:

        if not isinstance(
            show_data,
            dict,
        ):
            return

        show_date_time = str(
            show_data.get(
                "ShowDateTime",
                "",
            )
            or ""
        )

        show_time = show_data.get(
            "ShowTime"
        )

        if (
            not show_date_time
            or not show_time
        ):
            return

        expected_date = (
            show_date.strftime(
                "%Y%m%d"
            )
        )

        if not show_date_time.startswith(
            expected_date
        ):
            return

        raw_availability = (
            show_data.get(
                "AvailStatus"
            )
        )

        availability = (
            self._map_availability(
                raw_availability
            )
        )

        available_tickets = (
            self._extract_available_tickets(
                show_data=show_data,
                availability=availability,
            )
        )

        session_id = (
            show_data.get(
                "SessionId"
            )
        )

        output.append(
            Show(
                movie=movie,
                cinema=cinema,
                show_date=show_date,
                show_time=(
                    self._normalize_time(
                        str(show_time)
                    )
                ),
                status=availability,
                available_tickets=(
                    available_tickets
                ),
                source_id=(
                    str(session_id)
                    if session_id is not None
                    else None
                ),
            )
        )

    # ==================================================
    # TICKET COUNT
    # ==================================================

    @classmethod
    def _extract_available_tickets(
        cls,
        show_data: Dict[str, Any],
        availability: str,
    ) -> int | None:
        """
        Extract a trustworthy available-ticket count.

        BookMyShow may report:

            AvailStatus = "1"
            BestAvailableSeats = 0

        while the show is still available.

        Therefore:

            AVAILABLE + 0
                -> None

        means "available, but count unknown."

        For an explicitly SOLD_OUT show, preserving 0 is
        useful because it represents the known sold-out
        state.
        """

        value = cls._to_int(
            show_data.get(
                "BestAvailableSeats"
            )
        )

        if value is None:
            return None

        if (
            availability != "SOLD_OUT"
            and value <= 0
        ):
            return None

        return value

    # ==================================================
    # AVAILABILITY
    # ==================================================

    @staticmethod
    def _map_availability(
        value: Any,
    ) -> str:
        """
        Map BookMyShow's AvailStatus to the internal
        availability state.

        Confirmed from the live BookMyShow response:

            AvailStatus = "1"
                -> AVAILABLE

        Existing parser behavior also supports:

            AvailStatus = "3"
                -> AVAILABLE

            AvailStatus = "0"
                -> SOLD_OUT

        Any other value remains UNKNOWN.
        """

        value = str(
            value
        )

        # BookMyShow live response:
        # AvailStatus="1" means the show is available.
        if value == "1":
            return "AVAILABLE"

        # Preserve the existing supported AVAILABLE state.
        if value == "3":
            return "AVAILABLE"

        if value == "0":
            return "SOLD_OUT"

        return "UNKNOWN"

    # ==================================================
    # MOVIE MATCHING
    # ==================================================

    @staticmethod
    def _movie_matches(
        requested_movie: str,
        requested_event_code: str | None,
        event_name: Any,
        event_title: Any,
        event_code: Any,
    ) -> bool:

        if requested_event_code:
            actual_code = str(
                event_code or ""
            ).strip().upper()

            if actual_code:
                return (
                    actual_code
                    == requested_event_code.strip().upper()
                )

        requested = requested_movie.strip().lower()

        candidates = [
            str(event_name).strip().lower(),
            str(event_title).strip().lower(),
        ]

        return any(
            requested in candidate
            for candidate in candidates
            if candidate
        )

    # ==================================================
    # HELPERS
    # ==================================================

    @staticmethod
    def _to_int(
        value: Any,
    ) -> int | None:

        if value is None:
            return None

        try:

            return int(value)

        except (
            TypeError,
            ValueError,
        ):

            return None

    @staticmethod
    def _normalize_time(
        value: str,
    ) -> str:

        value = value.strip()

        for fmt in (
            "%I:%M %p",
            "%I:%M%p",
        ):

            try:

                parsed = datetime.strptime(
                    value.upper(),
                    fmt,
                )

                return parsed.strftime(
                    "%H:%M"
                )

            except ValueError:
                continue

        return value

    # ==================================================
    # DEDUPLICATION
    # ==================================================

    @staticmethod
    def _remove_duplicates(
        shows: List[Show],
    ) -> List[Show]:

        unique: Dict[str, Show] = {}

        for show in shows:

            unique[
                show.identity
            ] = show

        return list(
            unique.values()
        )
        # ==================================================
    # MOVIE / EVENT EXTRACTION
    # ==================================================

    def extract_movie_candidates(
        self,
        html: str,
    ) -> list[MovieCandidate]:
        """
        Extract unique BookMyShow movie/event candidates
        from the Event structure embedded in the HTML.

        This does not perform user-input matching.

        It only extracts BookMyShow's canonical movie data.
        """

        if not html or not html.strip():
            return []

        event_data = self._extract_event_array(
            html
        )

        if event_data is None:
            return []

        candidates: list[MovieCandidate] = []
        seen: set[str] = set()

        self._extract_movie_events(
            data=event_data,
            output=candidates,
            seen=seen,
        )

        return candidates

    def _extract_movie_events(
        self,
        data: Any,
        output: list[MovieCandidate],
        seen: set[str],
    ) -> None:
        """
        Recursively walk BookMyShow Event/ChildEvents
        structures and extract canonical movie events.
        """

        if isinstance(data, list):
            for item in data:
                self._extract_movie_events(
                    data=item,
                    output=output,
                    seen=seen,
                )

            return

        if not isinstance(data, dict):
            return

        event_title = str(
            data.get(
                "EventTitle",
                "",
            )
            or ""
        ).strip()

        event_name = str(
            data.get(
                "EventName",
                "",
            )
            or ""
        ).strip()

        event_code = str(
            data.get(
                "EventCode",
                "",
            )
            or ""
        ).strip()

        event_url = str(
            data.get(
                "EventUrl",
                "",
            )
            or ""
        ).strip()

        event_group = str(
            data.get(
                "EventGroup",
                "",
            )
            or ""
        ).strip()

        language = str(
            data.get(
                "EventLanguage",
                "",
            )
            or ""
        ).strip()

        dimension = str(
            data.get(
                "EventDimension",
                "",
            )
            or ""
        ).strip()

        # A ChildEvent containing EventCode represents
        # a concrete BookMyShow movie/event variant.
        if event_code and (
            event_name or event_title
        ):
            identity = event_code

            if identity not in seen:
                seen.add(identity)

                candidates_title = (
                    event_title
                    or event_name
                )

                if language:
                    candidates_title = re.sub(
                        rf"\s*-\s*{re.escape(language)}$",
                        "",
                        candidates_title,
                        flags=re.IGNORECASE,
                    ).strip()

                output.append(
                    MovieCandidate(
                        title=candidates_title,
                        event_name=event_name,
                        event_code=event_code,
                        event_url=(
                            event_url
                            or None
                        ),
                        event_group=(
                            event_group
                            or None
                        ),
                        language=(
                            language
                            or None
                        ),
                        dimension=(
                            dimension
                            or None
                        ),
                    )
                )

        # Continue through nested ChildEvents and
        # any other nested structures.
        for key, value in data.items():

            if key == "ShowTimes":
                continue

            if isinstance(
                value,
                (dict, list),
            ):
                self._extract_movie_events(
                    data=value,
                    output=output,
                    seen=seen,
                )