from __future__ import annotations

import os

import requests

from app.cinemas import BookMyShowCinemaResolver
from app.providers.bookmyshow_movies import BookMyShowMovieProvider


RENDER_API_URL = os.getenv(
    "CATALOGUE_API_URL",
    "https://cinema-ticket-watcher.onrender.com",
)


def main() -> None:
    token = os.getenv("CATALOGUE_INGEST_TOKEN")

    if not token:
        raise RuntimeError(
            "CATALOGUE_INGEST_TOKEN is not configured."
        )

    city = "Hyderabad"

    print("=" * 70)
    print("BOOKMYSHOW CATALOGUE UPLOAD")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Discover cinemas locally
    # ---------------------------------------------------------

    print("\nDiscovering cinemas...")

    cinema_resolver = BookMyShowCinemaResolver()

    venues = cinema_resolver.discover(city)

    print(f"Cinemas discovered: {len(venues)}")

    if not venues:
        raise RuntimeError(
            "No cinemas discovered."
        )

    city_code = venues[0].city_code

    cinemas = [
        {
            "name": venue.name,
            "provider_id": venue.provider_id,
            "slug": venue.slug,
        }
        for venue in venues
    ]

    # ---------------------------------------------------------
    # 2. Discover movies locally
    # ---------------------------------------------------------

    print("\nDiscovering movies...")

    movie_provider = BookMyShowMovieProvider()

    movie_result = movie_provider.get_movies(city)

    print(
        f"Movies discovered: {len(movie_result.movies)}"
    )

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
        for movie in movie_result.movies
    ]

    # ---------------------------------------------------------
    # 3. Build payload
    # ---------------------------------------------------------

    payload = {
        "city": city,
        "city_code": city_code,
        "cinemas": cinemas,
        "movies": movies,
    }

    # ---------------------------------------------------------
    # 4. Upload to Render
    # ---------------------------------------------------------

    url = (
        f"{RENDER_API_URL}"
        "/internal/catalogue/ingest"
    )

    print("\nUploading catalogue...")
    print(f"URL: {url}")

    response = requests.post(
        url,
        json=payload,
        headers={
            "X-Catalogue-Token": token,
        },
        timeout=60,
    )

    print("HTTP status:", response.status_code)

    if not response.ok:
        print("Response:")
        print(response.text)
        response.raise_for_status()

    print("\nUpload successful.")
    print(response.json())


if __name__ == "__main__":
    main()