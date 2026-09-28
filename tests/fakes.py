from typing import Dict, List

from app.cinemas import CinemaVenue


class FakeCinemaResolver:
    """
    Deterministic cinema resolver for tests.

    This prevents tests from making real BookMyShow
    network requests.
    """

    def __init__(
        self,
        venues: Dict[
            str,
            CinemaVenue,
        ] | None = None,
    ):

        self.venues = (
            venues
            if venues is not None
            else self.default_venues()
        )

        self.calls: List[
            tuple[str, str]
        ] = []

    @staticmethod
    def default_venues():

        return {
            "pvr": CinemaVenue(
                name=(
                    "PVR: Nexus Mall Kukatpally"
                ),
                city="Hyderabad",
                provider_id="PVFS",
                slug=(
                    "pvr-nexus-mall-kukatpally"
                    "-hyderabad"
                ),
                city_code="HYD",
            ),

            "amb cinemas": CinemaVenue(
                name=(
                    "AMB Cinemas: Gachibowli"
                ),
                city="Hyderabad",
                provider_id="AMBH",
                slug=(
                    "amb-cinemas-gachibowli"
                    "-hyderabad"
                ),
                city_code="HYD",
            ),

            "prasads": CinemaVenue(
                name="Prasads Multiplex",
                city="Hyderabad",
                provider_id="PRHN",
                slug=(
                    "prasads-multiplex"
                    "-hyderabad"
                ),
                city_code="HYD",
            ),

            "art": CinemaVenue(
                name="ART Cinemas",
                city="Hyderabad",
                provider_id="TEST_ART",
                slug=(
                    "art-cinemas-hyderabad"
                ),
                city_code="HYD",
            ),

            "shiva ganga": CinemaVenue(
                name="Shiva Ganga",
                city="Hyderabad",
                provider_id=(
                    "TEST_SHIVA_GANGA"
                ),
                slug=(
                    "shiva-ganga-hyderabad"
                ),
                city_code="HYD",
            ),
        }

    @staticmethod
    def normalize(
        value: str,
    ) -> str:

        return " ".join(
            value
            .strip()
            .lower()
            .split()
        )

    def resolve(
        self,
        name: str,
        city: str,
    ) -> CinemaVenue:

        self.calls.append(
            (
                name,
                city,
            )
        )

        key = self.normalize(
            name
        )

        venue = self.venues.get(
            key
        )

        if venue is None:

            raise ValueError(
                "Fake cinema not configured: "
                f"{name} ({city})"
            )

        return venue
