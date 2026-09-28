from dataclasses import dataclass

import requests


@dataclass
class PublicPageResponse:
    """
    Represents a fetched public webpage.
    """

    url: str
    status_code: int
    html: str


class PublicPageFetcher:
    """
    Fetches publicly accessible webpages using ordinary
    HTTP requests.

    This class does not bypass CAPTCHAs, bot protection,
    authentication, or other access controls.
    """

    def __init__(
        self,
        timeout: int = 15,
    ) -> None:

        self.timeout = timeout

    def fetch(
        self,
        url: str,
    ) -> PublicPageResponse:

        response = requests.get(
            url,
            timeout=self.timeout,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/142.0 Safari/537.36"
                )
            },
        )

        response.raise_for_status()

        return PublicPageResponse(
            url=url,
            status_code=response.status_code,
            html=response.text,
        )