from dataclasses import dataclass
from typing import Dict

from app.cinemas import (
    BookMyShowCinemaResolver,
    CinemaVenue,
)
from app.models import Watch
from app.providers.public_page import (
    PublicPageFetcher,
)


@dataclass
class CinemaPage:
    cinema: str
    url: str
    status_code: int
    html: str


class BookMyShowPublicFetcher:
    """
    Fetch public BookMyShow cinema pages.

    Cinema resolution is injected so production uses the
    real BookMyShow resolver while tests can use a fake
    deterministic resolver.

    A cinema name may resolve to:
        - one venue: resolve()
        - multiple venues: resolve_all()

    Multiple matches are useful for chain-level watches
    such as "PVR".
    """

    def __init__(
        self,
        page_fetcher=None,
        cinema_resolver=None,
    ):
        self.page_fetcher = (
            page_fetcher
            if page_fetcher is not None
            else PublicPageFetcher()
        )

        self.cinema_resolver = (
            cinema_resolver
            if cinema_resolver is not None
            else BookMyShowCinemaResolver()
        )

    def resolve_cinema(
        self,
        name: str,
        city: str,
    ) -> CinemaVenue:
        """
        Resolve one specific cinema.

        This remains the compatibility path used by
        existing tests and by requests that identify
        one unambiguous venue.
        """
        return self.cinema_resolver.resolve(
            name=name,
            city=city,
        )

    def resolve_cinemas(
        self,
        name: str,
        city: str,
    ):
        """
        Resolve one or more cinema venues.

        Chain-level searches such as "PVR" use resolve_all().
        If no chain-level/deterministic matches are found,
        fall back to resolve() so that the resolver's fuzzy
        matching can handle small spelling mistakes such as:

            shandhya 70mm
            sudarsham 35 mm
        """

        resolve_all = getattr(
            self.cinema_resolver,
            "resolve_all",
            None,
        )

        if resolve_all is not None:

            venues = resolve_all(
                name=name,
                city=city,
            )

            if venues:
                return venues

        # Important:
        # resolve() contains the final fuzzy matching logic.
        return [
            self.resolve_cinema(
                name=name,
                city=city,
            )
        ]

    def fetch(
        self,
        watch: Watch,
    ) -> Dict[str, CinemaPage]:

        pages: Dict[
            str,
            CinemaPage,
        ] = {}

        for cinema in watch.cinemas:

            venues = self.resolve_cinemas(
                name=cinema,
                city=watch.city,
            )

            for venue in venues:

                url = venue.public_page_url(
                    watch.target_date.isoformat()
                )

                response = (
                    self.page_fetcher.fetch(
                        url
                    )
                )

                # Preserve the old requested cinema key
                # for a single resolved venue.
                #
                # For multiple venues (for example PVR),
                # use the actual BookMyShow venue name so
                # every venue gets its own page.
                if len(venues) == 1:
                    page_key = cinema
                else:
                    page_key = venue.name

                pages[page_key] = CinemaPage(
                    cinema=page_key,
                    url=url,
                    status_code=(
                        response.status_code
                    ),
                    html=response.html,
                )

        return pages