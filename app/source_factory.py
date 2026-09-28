from app.sources import (
    BookMyShowSource,
    CinemaSource,
    MockCinemaSource,
    PublicPageSource,
)


def create_source(
    source_name: str,
) -> CinemaSource:

    normalized_name = (
        source_name.strip().lower()
    )

    if normalized_name == "mock":
        return MockCinemaSource()

    if normalized_name == "bookmyshow":
        return BookMyShowSource()

    if normalized_name == "public":
        return PublicPageSource()

    raise ValueError(
        f"Unknown cinema source: {source_name}"
    )