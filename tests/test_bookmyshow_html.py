from datetime import date

from app.providers.bookmyshow_html import (
    BookMyShowHTMLParser,
)


def test_parser_extracts_real_bookmyshow_structure():

    html = """
    <script type="application/json">
    {
        "Event": [
            {
                "EventTitle": "The Paradise",
                "ChildEvents": [
                    {
                        "EventName": "The Paradise - Telugu",
                        "ShowTimes": [
                            {
                                "ShowDateTime": "202609241000",
                                "ShowTime": "10:00 AM",
                                "AvailStatus": "3",
                                "BestAvailableSeats": 5,
                                "SessionId": "12345"
                            },
                            {
                                "ShowDateTime": "202609241300",
                                "ShowTime": "1:00 PM",
                                "AvailStatus": "0",
                                "BestAvailableSeats": 0,
                                "SessionId": "12346"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    </script>
    """

    parser = BookMyShowHTMLParser()

    shows = parser.parse(
        html=html,
        movie="The Paradise",
        show_date=date(
            2026,
            9,
            24,
        ),
        cinema="PVR",
    )

    assert len(shows) == 2

    assert shows[0].show_time == "10:00"
    assert shows[0].status == "AVAILABLE"
    assert shows[0].available_tickets == 5
    assert shows[0].source_id == "12345"

    assert shows[1].show_time == "13:00"
    assert shows[1].status == "SOLD_OUT"
    assert shows[1].available_tickets == 0
    assert shows[1].source_id == "12346"


def test_parser_ignores_other_dates():

    html = """
    <script type="application/json">
    {
        "Event": [
            {
                "EventTitle": "The Paradise",
                "ChildEvents": [
                    {
                        "EventName": "The Paradise - Telugu",
                        "ShowTimes": [
                            {
                                "ShowDateTime": "202609231000",
                                "ShowTime": "10:00 AM",
                                "AvailStatus": "3",
                                "BestAvailableSeats": 5,
                                "SessionId": "111"
                            },
                            {
                                "ShowDateTime": "202609241000",
                                "ShowTime": "10:00 AM",
                                "AvailStatus": "3",
                                "BestAvailableSeats": 4,
                                "SessionId": "222"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    </script>
    """

    parser = BookMyShowHTMLParser()

    shows = parser.parse(
        html=html,
        movie="The Paradise",
        show_date=date(
            2026,
            9,
            24,
        ),
        cinema="PVR",
    )

    assert len(shows) == 1

    assert shows[0].source_id == "222"


def test_parser_ignores_different_movie():

    html = """
    <script type="application/json">
    {
        "Event": [
            {
                "EventTitle": "Resident Evil",
                "ChildEvents": [
                    {
                        "EventName": "Resident Evil - English",
                        "ShowTimes": [
                            {
                                "ShowDateTime": "202609241000",
                                "ShowTime": "10:00 AM",
                                "AvailStatus": "3",
                                "BestAvailableSeats": 5,
                                "SessionId": "999"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    </script>
    """

    parser = BookMyShowHTMLParser()

    shows = parser.parse(
        html=html,
        movie="The Paradise",
        show_date=date(
            2026,
            9,
            24,
        ),
        cinema="PVR",
    )

    assert shows == []


def test_parser_matches_requested_movie_event_code():

    html = """
    <script type="application/json">
    {
        "Event": [
            {
                "EventTitle": "The Paradise",
                "ChildEvents": [
                    {
                        "EventName": "The Paradise - Telugu",
                        "EventCode": "ET111",
                        "ShowTimes": [
                            {
                                "ShowDateTime": "202609241000",
                                "ShowTime": "10:00 AM",
                                "AvailStatus": "3",
                                "BestAvailableSeats": 5,
                                "SessionId": "111"
                            }
                        ]
                    },
                    {
                        "EventName": "The Paradise - Telugu",
                        "EventCode": "ET222",
                        "ShowTimes": [
                            {
                                "ShowDateTime": "202609241400",
                                "ShowTime": "2:00 PM",
                                "AvailStatus": "3",
                                "BestAvailableSeats": 4,
                                "SessionId": "222"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    </script>
    """

    parser = BookMyShowHTMLParser()

    shows = parser.parse(
        html=html,
        movie="The Paradise",
        show_date=date(
            2026,
            9,
            24,
        ),
        cinema="PVR",
        movie_event_code="ET222",
    )

    assert len(shows) == 1
    assert shows[0].show_time == "14:00"
    assert shows[0].source_id == "222"


def test_parser_detects_disabled_bookmyshow_date():

    html = """
    <script>
    {
        "ShowDatesArray": [
            {
                "DispDate": "Today, 21 Sep",
                "DateCode": "20260921",
                "isDisabled": false
            },
            {
                "DispDate": "Thursday, 24 Sep",
                "DateCode": "20260924",
                "isDisabled": true
            }
        ]
    }
    </script>
    """

    parser = BookMyShowHTMLParser()

    status = parser.get_date_status(
        html=html,
        show_date=date(2026, 9, 24),
    )

    assert status == "DISABLED"


def test_parser_detects_available_bookmyshow_date():

    html = """
    <script>
    {
        "ShowDatesArray": [
            {
                "DateCode": "20260924",
                "isDisabled": false
            }
        ]
    }
    </script>
    """

    parser = BookMyShowHTMLParser()

    status = parser.get_date_status(
        html=html,
        show_date=date(2026, 9, 24),
    )

    assert status == "AVAILABLE"


def test_parser_returns_none_when_date_information_missing():

    html = """
    <script>
    {
        "Event": []
    }
    </script>
    """

    parser = BookMyShowHTMLParser()

    status = parser.get_date_status(
        html=html,
        show_date=date(2026, 9, 24),
    )

    assert status is None