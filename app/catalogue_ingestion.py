from app.cinemas import BookMyShowCinemaResolver
from app.postgres_cinema_catalogue import PostgreSQLCinemaCatalogue
from app.postgres_movie_catalogue import PostgreSQLMovieCatalogue
from app.providers.bookmyshow_movies import BookMyShowMovieProvider


class CatalogueIngestionService:
    """
    Imports BookMyShow catalogue data into PostgreSQL.

    This service is intended to run from a machine that can
    successfully access BookMyShow's public catalogue pages.
    """

    def __init__(self) -> None:
        self.cinema_resolver = BookMyShowCinemaResolver()
        self.movie_provider = BookMyShowMovieProvider()

        self.cinema_catalogue = PostgreSQLCinemaCatalogue()
        self.movie_catalogue = PostgreSQLMovieCatalogue()

    def ingest_cinemas(self, city: str) -> int:
        """
        Discover cinemas from BookMyShow and store them
        in PostgreSQL.
        """

        venues = self.cinema_resolver.discover(city)

        cinemas = [
            {
                "name": venue.name,
                "provider_id": venue.provider_id,
                "slug": venue.slug,
            }
            for venue in venues
        ]

        self.cinema_catalogue.replace_city(
            city=city,
            city_code=venues[0].city_code if venues else "",
            cinemas=cinemas,
        )

        return len(cinemas)

    def ingest_movies(self, city: str) -> int:
        """
        Discover movies from BookMyShow and store them
        in PostgreSQL.
        """

        result = self.movie_provider.get_movies(city)

        movies = [
            {
                "event_code": movie.event_code,
                "title": movie.title,
                "event_name": movie.event_name,
                "event_url": movie.event_url,
                "event_group": movie.event_group,
                "language": movie.language,
                "dimension": movie.dimension,
            }
            for movie in result.movies
        ]

        self.movie_catalogue.replace_city(
            city=city,
            movies=movies,
        )

        return len(movies)

    def ingest_city(self, city: str) -> dict:
        """
        Ingest both cinema and movie catalogues for a city.
        """

        cinema_count = self.ingest_cinemas(city)
        movie_count = self.ingest_movies(city)

        return {
            "city": city,
            "cinemas": cinema_count,
            "movies": movie_count,
        }