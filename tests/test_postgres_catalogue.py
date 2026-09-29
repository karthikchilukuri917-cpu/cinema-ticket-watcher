from app.postgres_cinema_catalogue import PostgreSQLCinemaCatalogue
from app.postgres_movie_catalogue import PostgreSQLMovieCatalogue


def test_cinema_catalogue_round_trip():
    repository = PostgreSQLCinemaCatalogue()

    city = "TEST_CITY"
    city_code = "TEST"

    cinemas = [
        {
            "name": "Test PVR",
            "provider_id": "TEST_PVR",
            "slug": "test-pvr",
        },
        {
            "name": "Test INOX",
            "provider_id": "TEST_INOX",
            "slug": "test-inox",
        },
    ]

    repository.replace_city(
        city=city,
        city_code=city_code,
        cinemas=cinemas,
    )

    result = repository.list_by_city(city)

    assert len(result) == 2
    assert result[0]["name"] == "Test INOX"
    assert result[1]["name"] == "Test PVR"

    assert repository.count_by_city(city) == 2

    # Cleanup
    repository.replace_city(
        city=city,
        city_code=city_code,
        cinemas=[],
    )

    assert repository.count_by_city(city) == 0


def test_movie_catalogue_round_trip():
    repository = PostgreSQLMovieCatalogue()

    city = "TEST_CITY"

    movies = [
        {
            "event_code": "ETTEST001",
            "title": "Test Movie One",
            "event_name": "Test Movie One",
            "event_url": "https://example.com/movie-one",
            "event_group": "Movie",
            "language": "Telugu",
            "dimension": "2D",
        },
        {
            "event_code": "ETTEST002",
            "title": "Test Movie Two",
            "event_name": "Test Movie Two",
            "event_url": "https://example.com/movie-two",
            "event_group": "Movie",
            "language": "English",
            "dimension": "3D",
        },
    ]

    repository.replace_city(
        city=city,
        movies=movies,
    )

    result = repository.list_by_city(city)

    assert len(result) == 2
    assert result[0]["title"] == "Test Movie One"
    assert result[1]["title"] == "Test Movie Two"

    assert repository.count_by_city(city) == 2

    # Cleanup
    repository.replace_city(
        city=city,
        movies=[],
    )

    assert repository.count_by_city(city) == 0