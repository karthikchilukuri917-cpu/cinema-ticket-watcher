from __future__ import annotations

import argparse
import os

import requests

from app.cinemas import BookMyShowCinemaResolver
from app.providers.bookmyshow_movies import BookMyShowMovieProvider


RENDER_API_URL = os.getenv(
    "CATALOGUE_API_URL",
    "https://cinema-ticket-watcher.onrender.com",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover a city's BookMyShow catalogue and upload it to Render."
    )

    parser.add_argument(
        "--city",
        required=True,
        help="City to ingest, for example: Hyderabad, Mumbai, Bengaluru",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    token = os.getenv("CATALOGUE_INGEST_TOKEN")
    if not token:
        raise RuntimeError(
            "CATALOGUE_INGEST_TOKEN is not configured."
        )

    city = args.city.strip()

    if not city:
        raise ValueError("City cannot be empty.")

    print("=" * 70)
    print("BOOKMYSHOW CATALOGUE UPLOAD")
    print("=" * 70)

    print(f"\nCity: {city}")

    # ---------------------------------------------------------
    # Discover cinemas
    # ---------------------------------------------------------
    print("\nDiscovering cinemas...")

    cinema_resolver = BookMyShowCinemaResolver()
    venues = cinema_resolver.discover(city)

    print(f"Cinemas discovered: {len(venues)}")

    if not venues:
        raise RuntimeError(
            f"No cinemas discovered for city: {city}"
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
    # Discover movies
    # ---------------------------------------------------------
    print("\nDiscovering movies...")

    movie_provider = BookMyShowMovieProvider()
    movie_result = movie_provider.get_movies(city)

    print(f"Movies discovered: {len(movie_result.movies)}")

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
    # Build upload payload
    # ---------------------------------------------------------
    payload = {
        "city": city,
        "city_code": city_code,
        "cinemas": cinemas,
        "movies": movies,
    }

    # ---------------------------------------------------------
    # Upload to Render
    # ---------------------------------------------------------
    url = f"{RENDER_API_URL}/internal/catalogue/ingest"

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