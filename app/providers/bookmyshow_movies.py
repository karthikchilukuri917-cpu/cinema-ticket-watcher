from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from urllib.parse import urljoin

from app.movies import MovieCandidate
from app.providers.public_page import PublicPageFetcher


BOOKMYSHOW_BASE_URL = "https://in.bookmyshow.com"


@dataclass(frozen=True)
class MovieCatalogueResult:
    city: str
    movies: tuple[MovieCandidate, ...]


class BookMyShowMovieProvider:
    """
    Discovers movie candidates from BookMyShow's
    city-level movie catalogue.

    This provider deliberately does not use cinema pages.
    Cinema discovery remains the responsibility of
    BookMyShowCinemaResolver.
    """

    def __init__(
        self,
        page_fetcher: PublicPageFetcher | None = None,
    ) -> None:
        self.page_fetcher = (
            page_fetcher
            if page_fetcher is not None
            else PublicPageFetcher()
        )

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def catalogue_url(self, city: str) -> str:
        city_slug = self._city_slug(city)

        return (
            f"{BOOKMYSHOW_BASE_URL}/explore/"
            f"movies-{city_slug}?cat=MT"
        )

    def get_movies(
        self,
        city: str,
        target_date: str | None = None,
    ) -> MovieCatalogueResult:

        del target_date

        url = self.catalogue_url(city)

        response = self.page_fetcher.fetch(url)

        if response.status_code != 200:
            raise RuntimeError(
                "BookMyShow movie catalogue returned "
                f"HTTP {response.status_code}."
            )

        movies = self._extract_movies(
            response.html
        )

        return MovieCatalogueResult(
            city=city.strip(),
            movies=tuple(movies),
        )

    # ---------------------------------------------------------
    # URL helpers
    # ---------------------------------------------------------

    @staticmethod
    def _city_slug(city: str) -> str:
        city = city.strip().lower()

        city = re.sub(
            r"[^a-z0-9]+",
            "-",
            city,
        )

        return city.strip("-")

    # ---------------------------------------------------------
    # Movie extraction
    # ---------------------------------------------------------

    def _extract_movies(self, html: str) -> list[MovieCandidate]:
        candidates: list[MovieCandidate] = []
        seen: set[str] = set()

        script_pattern = re.compile(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>'
            r'(.*?)'
            r'</script>',
            re.IGNORECASE | re.DOTALL,
        )

        for match in script_pattern.finditer(html):
            raw_json = unescape(match.group(1).strip())

            try:
                data = json.loads(raw_json)
            except json.JSONDecodeError:
                continue

            if not isinstance(data, dict):
                continue

            if data.get("@type") != "ItemList":
                continue

            items = data.get("itemListElement", [])

            if not isinstance(items, list):
                continue

            for entry in items:
                if not isinstance(entry, dict):
                    continue

                movie_url = entry.get("url")

                if not isinstance(movie_url, str):
                    continue

                absolute_url = urljoin(
                    BOOKMYSHOW_BASE_URL,
                    movie_url,
                )

                movie_slug, event_code = (
                    self._extract_movie_parts(
                        absolute_url
                    )
                )

                if not movie_slug or not event_code:
                    continue

                title = entry.get("name")

                if not isinstance(title, str):
                    title = self._title_from_slug(movie_slug)

                title = title.strip()

                if not title:
                    continue

                if event_code in seen:
                    continue

                seen.add(event_code)

                candidates.append(
                    MovieCandidate(
                        title=title,
                        event_name=title,
                        event_code=event_code,
                        event_url=absolute_url,
                    )
                )

        return candidates

    @staticmethod
    def _extract_movie_parts(
        url: str,
    ) -> tuple[str | None, str | None]:

        match = re.search(
            r"/movies/([^/]+)/"
            r"(ET[A-Z0-9]+)",
            url,
            re.IGNORECASE,
        )

        if not match:
            return None, None

        movie_slug = match.group(1)

        event_code = match.group(2).upper()

        return movie_slug, event_code

    @staticmethod
    def _title_from_slug(
        slug: str,
    ) -> str:

        value = slug.replace(
            "-",
            " ",
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

        return value.title()