from app.movies import MovieCandidate, MovieResolver


def make_movies():
    return [
        MovieCandidate(
            title="The Paradise",
            event_name="The Paradise - Telugu",
            event_code="ET000001",
            event_url=None,
            event_group=None,
            language="Telugu",
            dimension=None,
        ),
        MovieCandidate(
            title="Avengers Endgame",
            event_name="Avengers Endgame: Encore",
            event_code="ET000002",
            event_url=None,
            event_group=None,
            language="English",
            dimension="4DX 3D",
        ),
        MovieCandidate(
            title="The Paradise 2",
            event_name="The Paradise 2 - Telugu",
            event_code="ET000003",
            event_url=None,
            event_group=None,
            language="Telugu",
            dimension=None,
        ),
    ]


def test_exact_match():
    resolver = MovieResolver(make_movies())

    result = resolver.resolve("The Paradise")

    assert result.status == "MATCH"
    assert result.movie.event_code == "ET000001"


def test_normalized_match():
    resolver = MovieResolver(make_movies())

    result = resolver.resolve("the-paradise")

    assert result.status == "MATCH"
    assert result.movie.event_code == "ET000001"


def test_partial_match():
    resolver = MovieResolver(make_movies())

    result = resolver.resolve("Avengers")

    assert result.status == "MATCH"
    assert result.movie.event_code == "ET000002"


def test_fuzzy_match():
    resolver = MovieResolver(make_movies())

    result = resolver.resolve("Avenger Endgam")

    assert result.status == "MATCH"
    assert result.movie.event_code == "ET000002"


def test_no_match():
    resolver = MovieResolver(make_movies())

    result = resolver.resolve("Spider-Man")

    assert result.status == "NOT_FOUND"
    assert result.movie is None


def test_ambiguous_match_returns_candidates():
    resolver = MovieResolver(make_movies())

    result = resolver.resolve("Paradise")

    assert result.status == "AMBIGUOUS"
    assert result.movie is None

    codes = {movie.event_code for movie in result.candidates}

    assert codes == {"ET000001", "ET000003"}


def test_event_code_is_canonical_identity():
    resolver = MovieResolver(make_movies())

    result = resolver.resolve("The Paradise")

    assert result.movie.identity == "ET000001"