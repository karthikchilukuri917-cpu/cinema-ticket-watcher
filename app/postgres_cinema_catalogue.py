from datetime import datetime, timezone

from app.database import get_connection


class PostgreSQLCinemaCatalogue:
    """
    PostgreSQL repository for the persistent cinema catalogue.
    """

    def replace_city(
        self,
        city: str,
        city_code: str,
        cinemas: list[dict],
    ) -> None:
        """
        Replace the complete cinema catalogue for one city.
        """

        city = city.strip()
        city_code = city_code.strip().upper()

        if not city:
            raise ValueError("City cannot be empty.")

        if not city_code:
            raise ValueError("City code cannot be empty.")

        now = datetime.now(timezone.utc)

        with get_connection() as connection:
            with connection.cursor() as cursor:

                # Remove the old catalogue for this city.
                cursor.execute(
                    """
                    DELETE FROM cinema_catalogue
                    WHERE city_code = %s
                    """,
                    (city_code,),
                )

                # Insert the fresh catalogue.
                for cinema in cinemas:
                    cursor.execute(
                        """
                        INSERT INTO cinema_catalogue (
                            city,
                            city_code,
                            name,
                            provider_id,
                            slug,
                            updated_at
                        )
                        VALUES (
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
                            city_code,
                            cinema["name"],
                            cinema["provider_id"],
                            cinema["slug"],
                            now,
                        ),
                    )

            connection.commit()

    def list_by_city(
        self,
        city: str,
    ) -> list[dict]:
        """
        Return all cinemas stored for a city.
        """

        city = city.strip()

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        name,
                        provider_id,
                        slug,
                        city,
                        city_code,
                        updated_at
                    FROM cinema_catalogue
                    WHERE LOWER(city) = LOWER(%s)
                    ORDER BY name
                    """,
                    (city,),
                )

                rows = cursor.fetchall()

        return [
            {
                "name": row[0],
                "provider_id": row[1],
                "slug": row[2],
                "city": row[3],
                "city_code": row[4],
                "updated_at": row[5],
            }
            for row in rows
        ]

    def count_by_city(
        self,
        city: str,
    ) -> int:
        """
        Return the number of cinemas stored for a city.
        """

        city = city.strip()

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM cinema_catalogue
                    WHERE LOWER(city) = LOWER(%s)
                    """,
                    (city,),
                )

                row = cursor.fetchone()

        return int(row[0])