class SourceError(Exception):
    """Base error for cinema source failures."""


class SourceNotConfiguredError(SourceError):
    """Raised when a source has not been configured."""


class SourceUnavailableError(SourceError):
    """Raised when a source cannot currently be reached."""


class SourceDataError(SourceError):
    """Raised when a source returns unusable data."""