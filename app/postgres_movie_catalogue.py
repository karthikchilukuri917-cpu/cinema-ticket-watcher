from datetime import datetime, timezone

from app.database import get_connection


class PostgreSQLMovieCatalogue:
    """
    PostgreSQL repository for the persistent movie catalogue.
    """

    def replace_city(
        self,
        city: str,
        movies: list[dict],
    ) -> None:
        """
        Replace the complete movie catalogue for one city.
        """

        city = city.strip()

        if not city:
            raise ValueError("City cannot be empty.")

        now = datetime.now(timezone.utc)

        with get_connection() as connection:
            with connection.cursor() as cursor:

                # Remove the old catalogue for this city.
                cursor.execute(
                    """
                    DELETE FROM movie_catalogue
                    WHERE LOWER(city) = LOWER(%s)
                    """,
                    (city,),
                )

                # Insert the fresh catalogue.
                for movie in movies:
                    cursor.execute(
                        """
                        INSERT INTO movie_catalogue (
                            city,
                            event_code,
                            title,
                            event_name,
                            event_url,
                            event_group,
                            language,
                            dimension,
                            updated_at
                        )
                        VALUES (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )
                        """,
                        (
                            city,
                            movie["event_code"],
                            movie["title"],
                            movie.get("event_name"),
                            movie.get("event_url"),
                            movie.get("event_group"),
                            movie.get("language"),
                            movie.get("dimension"),
                            now,
                        ),
                    )

            connection.commit()

    def list_by_city(
        self,
        city: str,
    ) -> list[dict]:
        """
        Return all movies stored for a city.
        """

        city = city.strip()

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        event_code,
                        title,
                        event_name,
                        event_url,
                        event_group,
                        language,
                        dimension,
                        city,
                        updated_at
                    FROM movie_catalogue
                    WHERE LOWER(city) = LOWER(%s)
                    ORDER BY title
                    """,
                    (city,),
                )

                rows = cursor.fetchall()

        return [
            {
                "event_code": row[0],
                "title": row[1],
                "event_name": row[2],
                "event_url": row[3],
                "event_group": row[4],
                "language": row[5],
                "dimension": row[6],
                "city": row[7],
                "updated_at": row[8],
            }
            for row in rows
        ]

    def count_by_city(
        self,
        city: str,
    ) -> int:
        """
        Return the number of movies stored for a city.
        """

        city = city.strip()

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM movie_catalogue
                    WHERE LOWER(city) = LOWER(%s)
                    """,
                    (city,),
                )

                row = cursor.fetchone()

        return int(row[0])