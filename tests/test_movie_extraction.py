from app.providers.bookmyshow_html import (
    BookMyShowHTMLParser,
)


def make_html():
    return """
    <html>
    <script>
    {
        "Event": [
            {
                "EventTitle": "The Paradise",
                "ChildEvents": [
                    {
                        "EventName": "The Paradise - Telugu",
                        "EventCode": "ET000001",
                        "EventGroup": "EG000001",
                        "EventUrl": "the-paradise",
                        "EventLanguage": "Telugu",
                        "EventDimension": "2D",
                        "ShowTimes": []
                    }
                ]
            },
            {
                "EventTitle": "Avengers: Endgame",
                "ChildEvents": [
                    {
                        "EventName": "Avengers: Endgame - English",
                        "EventCode": "ET000002",
                        "EventGroup": "EG000002",
                        "EventUrl": "avengers-endgame",
                        "EventLanguage": "English",
                        "EventDimension": "2D",
                        "ShowTimes": []
                    }
                ]
            }
        ]
    }
    </script>

    "Event": [
        {
            "EventTitle": "The Paradise",
            "ChildEvents": [
                {
                    "EventName": "The Paradise - Telugu",
                    "EventCode": "ET000001",
                    "EventGroup": "EG000001",
                    "EventUrl": "the-paradise",
                    "EventLanguage": "Telugu",
                    "EventDimension": "2D",
                    "ShowTimes": []
                }
            ]
        }
    ]
    </html>
    """


def test_extract_movie_candidates():
    parser = BookMyShowHTMLParser()

    candidates = parser.extract_movie_candidates(
        make_html()
    )

    assert len(candidates) == 2

    paradise = next(
        movie
        for movie in candidates
        if movie.event_code == "ET000001"
    )

    assert paradise.title == "The Paradise"
    assert (
        paradise.event_name
        == "The Paradise - Telugu"
    )
    assert paradise.event_url == "the-paradise"
    assert paradise.language == "Telugu"
    assert paradise.dimension == "2D"


def test_movie_candidates_use_event_code_as_identity():
    parser = BookMyShowHTMLParser()

    candidates = parser.extract_movie_candidates(
        make_html()
    )

    identities = {
        movie.identity
        for movie in candidates
    }

    assert identities == {
        "ET000001",
        "ET000002",
    }


def test_movie_candidate_title_removes_language_suffix():
    parser = BookMyShowHTMLParser()

    html = """
    <script>
    {
        "Event": [
            {
                "EventTitle": "The Paradise - Telugu",
                "ChildEvents": [
                    {
                        "EventName": "The Paradise - Telugu",
                        "EventCode": "ET000003",
                        "EventLanguage": "Telugu"
                    }
                ]
            }
        ]
    }
    </script>
    """

    candidates = parser.extract_movie_candidates(
        html
    )

    assert candidates[0].title == "The Paradise"


def test_empty_html_returns_no_movies():
    parser = BookMyShowHTMLParser()

    assert (
        parser.extract_movie_candidates("")
        == []
    )