from typing import List

from app.models import Show, Watch


def filter_shows(
    shows: List[Show],
    watch: Watch,
) -> List[Show]:
    """
    Return shows that are relevant to the watch.

    Time-slot filtering has been removed from the product.
    A watch now represents interest in any available show
    for the selected movie, date, city, and cinemas.

    The watcher's availability logic is responsible for
    determining whether a show is actually available.
    """

    return shows