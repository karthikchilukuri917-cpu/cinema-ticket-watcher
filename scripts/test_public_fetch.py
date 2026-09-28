import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


HTML_FILE = (
    PROJECT_ROOT
    / "data"
    / "bookmyshow_pvr.html"
)


def extract_event_array(
    html: str,
):
    """
    Extract the Event array from the embedded
    BookMyShow page data.

    This uses balanced-bracket detection rather
    than assuming the data is inside a JSON script tag.
    """

    match = re.search(
        r'"Event"\s*:\s*\[',
        html,
    )

    if match is None:
        raise ValueError(
            "Event array not found."
        )

    array_start = (
        html.find(
            "[",
            match.start(),
        )
    )

    depth = 0
    in_string = False
    escaped = False

    for position in range(
        array_start,
        len(html),
    ):

        character = html[position]

        if in_string:

            if escaped:
                escaped = False

            elif character == "\\":
                escaped = True

            elif character == '"':
                in_string = False

            continue

        if character == '"':
            in_string = True

        elif character == "[":
            depth += 1

        elif character == "]":

            depth -= 1

            if depth == 0:

                return html[
                    array_start:
                    position + 1
                ]

    raise ValueError(
        "Could not find the end of Event array."
    )


def main():

    if not HTML_FILE.exists():

        print(
            f"File not found:\n{HTML_FILE}"
        )

        return

    html = HTML_FILE.read_text(
        encoding="utf-8"
    )

    print(
        f"Loaded HTML: {len(html)} characters"
    )

    try:

        event_array_text = (
            extract_event_array(html)
        )

    except ValueError as error:

        print(
            f"\nERROR: {error}"
        )

        return

    print(
        f"\nExtracted Event array:"
    )

    print(
        f"Characters: "
        f"{len(event_array_text)}"
    )

    # --------------------------------------------------
    # Try parsing the extracted array as JSON
    # --------------------------------------------------

    try:

        events = json.loads(
            event_array_text
        )

    except json.JSONDecodeError as error:

        print(
            "\nJSON parsing FAILED."
        )

        print(
            f"Error: {error}"
        )

        print(
            "\nFirst 2000 characters:"
        )

        print(
            event_array_text[:2000]
        )

        return

    print(
        "\nJSON parsing SUCCESS!"
    )

    print(
        f"Events found: {len(events)}"
    )

    # --------------------------------------------------
    # Inspect the first event
    # --------------------------------------------------

    if not events:
        print(
            "Event array is empty."
        )
        return

    first_event = events[0]

    print(
        "\nFirst Event:"
    )

    print(
        json.dumps(
            first_event,
            indent=2,
        )[:5000]
    )

    # --------------------------------------------------
    # Count ShowTimes
    # --------------------------------------------------

    showtime_count = 0

    for event in events:

        child_events = event.get(
            "ChildEvents",
            [],
        )

        for child_event in child_events:

            showtimes = child_event.get(
                "ShowTimes",
                [],
            )

            showtime_count += len(
                showtimes
            )

    print(
        "\nTotal ShowTimes:"
    )

    print(
        showtime_count
    )


if __name__ == "__main__":
    main()