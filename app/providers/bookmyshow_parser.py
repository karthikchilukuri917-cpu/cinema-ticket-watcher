import json
import re
from datetime import date, datetime
from typing import Any, Dict, List

from app.models import Show


class BookMyShowHTMLParser:
    """
    Parse BookMyShow showtime data embedded inside public HTML.

    BookMyShow does not necessarily expose the Event data as a
    standalone JSON <script>. The Event array can be embedded
    inside a larger JavaScript/data structure.

    Relevant structure:

        "Event": [
            {
                "EventTitle": "...",
                "ChildEvents": [
                    {
                        "EventName": "...",
                        "ShowTimes": [
                            {
                                "ShowDateTime": "...",
                                "ShowTime": "...",
                                "AvailStatus": "...",
                                "BestAvailableSeats": ...,
                                "SessionId": "..."
                            }
                        ]
                    }
                ]
            }
        ]
    """

    def parse(
        self,
        html: str,
        movie: str,
        show_date: date,
        cinema: str,
    ) -> List[Show]:

        if not html or not html.strip():
            return []

        event_arrays = self._extract_event_arrays(
            html
        )

        shows: List[Show] = []

        for event_array in event_arrays:
            self._extract_events(
                data=event_array,
                movie=movie,
                show_date=show_date,
                cinema=cinema,
                output=shows,
            )

        return self._remove_duplicates(
            shows
        )

    # ==================================================
    # EVENT ARRAY EXTRACTION
    # ==================================================

    def _extract_event_arrays(
        self,
        html: str,
    ) -> List[Any]:
        """
        Find embedded `"Event": [...]` arrays.

        We deliberately do not try to parse the entire
        <script> as JSON because BookMyShow frequently
        embeds the Event data inside a larger JavaScript
        object or state payload.
        """

        results: List[Any] = []

        pattern = re.compile(
            r'"Event"\s*:\s*\[',
            re.IGNORECASE,
        )

        for match in pattern.finditer(html):

            opening_bracket = html.find(
                "[",
                match.start(),
                match.end(),
            )

            if opening_bracket == -1:
                continue

            array_text = self._extract_balanced_json(
                html,
                opening_bracket,
            )

            if array_text is None:
                continue

            try:
                data = json.loads(
                    array_text
                )
            except (
                json.JSONDecodeError,
                ValueError,
            ):
                continue

            if isinstance(data, list):
                results.append(data)

        return results

    @staticmethod
    def _extract_balanced_json(
        text: str,
        start: int,
    ) -> str | None:
        """
        Extract a balanced JSON array/object.

        Handles nested structures, strings and escaped
        quotes.
        """

        if start >= len(text):
            return None

        opening = text[start]

        if opening not in "[{":
            return None

        closing = (
            "]"
            if opening == "["
            else "}"
        )

        depth = 0
        in_string = False
        escaped = False

        for index in range(
            start,
            len(text),
        ):

            char = text[index]

            if in_string:

                if escaped:
                    escaped = False
                    continue

                if char == "\\":
                    escaped = True
                    continue

                if char == '"':
                    in_string = False

                continue

            if char == '"':
                in_string = True
                continue

            if char == opening:
                depth += 1
                continue

            if char == closing:
                depth -= 1

                if depth == 0:
                    return text[
                        start:index + 1
                    ]

        return None

    # ==================================================
    # EVENT WALKING
    # ==================================================

    def _extract_events(
        self,
        data: Any,
        movie: str,
        show_date: date,
        cinema: str,
        output: List[Show],
    ) -> None:

        if isinstance(data, list):

            for item in data:

                self._extract_events(
                    data=item,
                    movie=movie,
                    show_date=show_date,
                    cinema=cinema,
                    output=output,
                )

            return

        if not isinstance(data, dict):
            return

        # Direct ShowTimes object.
        if "ShowTimes" in data:

            event_name = data.get(
                "EventName",
                "",
            )

            event_title = data.get(
                "EventTitle",
                "",
            )

            if self._movie_matches(
                requested_movie=movie,
                event_name=event_name,
                event_title=event_title,
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

        # Parent Event object.
        event_title = data.get(
            "EventTitle"
        )

        child_events = data.get(
            "ChildEvents"
        )

        if isinstance(
            child_events,
            list,
        ):

            for child_event in child_events:

                self._extract_child_event(
                    child_event=child_event,
                    event_title=event_title,
                    movie=movie,
                    show_date=show_date,
                    cinema=cinema,
                    output=output,
                )

            return

        # Generic recursive fallback.
        for value in data.values():

            if isinstance(
                value,
                (dict, list),
            ):

                self._extract_events(
                    data=value,
                    movie=movie,
                    show_date=show_date,
                    cinema=cinema,
                    output=output,
                )

    def _extract_child_event(
        self,
        child_event: Any,
        event_title: Any,
        movie: str,
        show_date: date,
        cinema: str,
        output: List[Show],
    ) -> None:

        if not isinstance(
            child_event,
            dict,
        ):
            return

        event_name = child_event.get(
            "EventName",
            "",
        )

        if not self._movie_matches(
            requested_movie=movie,
            event_name=event_name,
            event_title=event_title,
        ):
            return

        showtimes = child_event.get(
            "ShowTimes",
            [],
        )

        if not isinstance(
            showtimes,
            list,
        ):
            return

        for show_data in showtimes:

            self._add_show(
                show_data=show_data,
                movie=movie,
                show_date=show_date,
                cinema=cinema,
                output=output,
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
        )

        expected_date = (
            show_date.strftime(
                "%Y%m%d"
            )
        )

        if (
            show_date_time
            and not show_date_time.startswith(
                expected_date
            )
        ):
            return

        show_time = show_data.get(
            "ShowTime"
        )

        if not show_time:
            return

        status = self._map_availability(
            show_data.get(
                "AvailStatus"
            )
        )

        available_tickets = (
            self._to_int(
                show_data.get(
                    "BestAvailableSeats"
                )
            )
        )

        session_id = show_data.get(
            "SessionId"
        )

        output.append(
            Show(
                movie=movie,
                cinema=cinema,
                show_date=show_date,
                show_time=self._normalize_time(
                    str(show_time)
                ),
                status=status,
                available_tickets=available_tickets,
                source_id=(
                    str(session_id)
                    if session_id is not None
                    else None
                ),
            )
        )

    # ==================================================
    # MOVIE MATCHING
    # ==================================================

    @staticmethod
    def _movie_matches(
        requested_movie: str,
        event_name: Any,
        event_title: Any,
    ) -> bool:

        requested = (
            requested_movie
            .strip()
            .lower()
        )

        candidates = [
            str(event_name)
            .strip()
            .lower(),
            str(event_title)
            .strip()
            .lower(),
        ]

        for candidate in candidates:

            if not candidate:
                continue

            if requested in candidate:
                return True

        return False

    # ==================================================
    # AVAILABILITY
    # ==================================================

    @staticmethod
    def _map_availability(
        value: Any,
    ) -> str:

        value = str(value)

        if value == "3":
            return "AVAILABLE"

        if value == "0":
            return "SOLD_OUT"

        return "UNKNOWN"

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

    @staticmethod
    def _remove_duplicates(
        shows: List[Show],
    ) -> List[Show]:

        unique: Dict[
            str,
            Show,
        ] = {}

        for show in shows:

            unique[
                show.identity
            ] = show

        return list(
            unique.values()
        )