from dataclasses import dataclass
from enum import Enum
from typing import Dict


class SourceStatus(Enum):
    """
    Describes the result of a cinema source request.
    """

    SUCCESS = "SUCCESS"
    NO_SHOWS = "NO_SHOWS"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass
class SourceResult:
    """
    Standard result returned by a cinema source.
    """

    status: SourceStatus
    data: Dict
    message: str | None = None

    @property
    def successful(self) -> bool:
        """
        Return True when the source request succeeded.
        """

        return self.status in {
            SourceStatus.SUCCESS,
            SourceStatus.NO_SHOWS,
        }