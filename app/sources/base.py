from abc import ABC, abstractmethod

from app.models import Watch
from app.sources.result import SourceResult


class CinemaSource(ABC):
    """
    Base interface for every cinema availability source.

    Every source must return a SourceResult.
    """

    @abstractmethod
    def get_availability(
        self,
        watch: Watch,
    ) -> SourceResult:
        """
        Fetch availability for a Watch.

        The source must never return raw data directly.

        It must return:

            SourceResult(
                status=...,
                data=...,
                message=...
            )
        """

        raise NotImplementedError