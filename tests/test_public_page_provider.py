from unittest.mock import Mock, patch

import pytest

from app.providers.public_page import (
    PublicPageFetcher,
)


def test_fetcher_returns_page_response():

    response = Mock()

    response.status_code = 200
    response.text = "<html>Hello</html>"

    with patch(
        "app.providers.public_page.requests.get",
        return_value=response,
    ) as mock_get:

        fetcher = PublicPageFetcher()

        result = fetcher.fetch(
            "https://example.com"
        )

        assert result.url == "https://example.com"
        assert result.status_code == 200
        assert result.html == "<html>Hello</html>"

        mock_get.assert_called_once()


def test_fetcher_raises_for_http_error():

    response = Mock()

    response.raise_for_status.side_effect = (
        RuntimeError("HTTP error")
    )

    response.status_code = 403
    response.text = "Forbidden"

    with patch(
        "app.providers.public_page.requests.get",
        return_value=response,
    ):

        fetcher = PublicPageFetcher()

        with pytest.raises(RuntimeError):

            fetcher.fetch(
                "https://example.com"
            )


def test_fetcher_uses_timeout():

    response = Mock()

    response.status_code = 200
    response.text = "OK"

    with patch(
        "app.providers.public_page.requests.get",
        return_value=response,
    ) as mock_get:

        fetcher = PublicPageFetcher(
            timeout=20
        )

        fetcher.fetch(
            "https://example.com"
        )

        arguments = mock_get.call_args.kwargs

        assert arguments["timeout"] == 20
