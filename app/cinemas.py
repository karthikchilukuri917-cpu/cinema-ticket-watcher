from __future__ import annotations

from dataclasses import dataclass
import difflib
import json
import re
from typing import Any, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BOOKMYSHOW_BASE_URL = "https://in.bookmyshow.com"
DEFAULT_TIMEOUT = 15

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/142.0 Safari/537.36"
)


@dataclass(frozen=True)
class CinemaVenue:
    """
    One concrete BookMyShow cinema venue.
    """

    name: str
    city: str
    provider_id: str
    slug: str
    city_code: str

    @property
    def identity(self) -> str:
        return (
            f"{self.city}|"
            f"{self.name}|"
            f"{self.provider_id}"
        )

    def public_page_url(
        self,
        target_date: str,
    ) -> str:
        compact_date = target_date.replace("-", "")

        return (
            f"{BOOKMYSHOW_BASE_URL}/cinemas/"
            f"{self.city_code}/"
            f"{self.slug}/"
            f"buytickets/"
            f"{self.provider_id}/"
            f"{compact_date}"
        )


@dataclass(frozen=True)
class CinemaDiscovery:
    """
    One cinema discovered from BookMyShow.
    """

    name: str
    city: str
    provider_id: str
    slug: str
    city_code: str

    # BookMyShow may expose the dates for which the venue
    # currently accepts bookings.
    open_dates: tuple[str, ...] = ()


class BookMyShowCinemaResolver:
    """
    Dynamically discovers BookMyShow cinemas for a city.

    Primary source:
        BookMyShow's embedded __INITIAL_STATE__ data.

    Fallback:
        Public cinema links.

    No hardcoded cinema registry is used.
    """

    GENERIC_WORDS = {
        "theatre",
        "theater",
        "cinema",
        "cinemas",
        "multiplex",
        "movie",
        "movies",
    }

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout = timeout

        self.session = (
            session
            if session is not None
            else requests.Session()
        )

        self._discovery_cache: dict[
            str,
            List[CinemaDiscovery],
        ] = {}

    # =========================================================
    # NORMALIZATION
    # =========================================================

    @staticmethod
    def normalize(value: str) -> str:
        value = value.strip().lower()

        value = re.sub(
            r"(\d+)\s+(mm|imax|d|k)\b",
            r"\1\2",
            value,
        )

        value = re.sub(
            r"[^a-z0-9]+",
            " ",
            value,
        )

        return " ".join(
            value.split()
        )

    @classmethod
    def normalize_search(cls, value: str) -> str:
        """
        Normalize a user search while removing generic
        cinema words such as:

            theatre
            theater
            cinema
            cinemas
            multiplex
        """

        value = cls.normalize(value)

        tokens = [
            token
            for token in value.split()
            if token not in cls.GENERIC_WORDS
        ]

        return " ".join(tokens)

    @staticmethod
    def city_slug(city: str) -> str:
        value = city.strip().lower()

        value = re.sub(
            r"[^a-z0-9]+",
            "-",
            value,
        )

        return value.strip("-")

    @staticmethod
    def _slugify_cinema_name(
        name: str,
    ) -> str:
        value = name.strip().lower()

        value = re.sub(
            r"[^a-z0-9]+",
            "-",
            value,
        )

        value = re.sub(
            r"-+",
            "-",
            value,
        )

        return value.strip("-")

    # =========================================================
    # HTTP
    # =========================================================

    def _get(
        self,
        url: str,
    ) -> requests.Response:
        response = self.session.get(
            url,
            timeout=self.timeout,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
        )

        response.raise_for_status()

        return response

    # =========================================================
    # __INITIAL_STATE__ EXTRACTION
    # =========================================================

    @staticmethod
    def _extract_initial_state(
        html: str,
    ) -> Any | None:
        """
        Extract BookMyShow's window.__INITIAL_STATE__.

        Supports the common forms:

            window.__INITIAL_STATE__ = {...};

        and:

            window.__INITIAL_STATE__={...}

        We use a balanced-brace scanner rather than a regex
        for the JSON body because the state object contains
        nested objects and arrays.
        """

        patterns = [
            r"window\.__INITIAL_STATE__\s*=",
            r"__INITIAL_STATE__\s*=",
        ]

        start = None

        for pattern in patterns:
            match = re.search(
                pattern,
                html,
                flags=re.IGNORECASE,
            )

            if match:
                start = match.end()
                break

        if start is None:
            return None

        while (
            start < len(html)
            and html[start].isspace()
        ):
            start += 1

        # Some pages wrap the JSON in JSON.parse("...").
        if html.startswith(
            "JSON.parse",
            start,
        ):
            open_paren = html.find(
                "(",
                start,
            )

            if open_paren == -1:
                return None

            quote_start = open_paren + 1

            while (
                quote_start < len(html)
                and html[quote_start].isspace()
            ):
                quote_start += 1

            if (
                quote_start >= len(html)
                or html[quote_start] not in {
                    '"',
                    "'",
                }
            ):
                return None

            quote = html[quote_start]

            value_start = quote_start + 1
            escaped = False
            chars: list[str] = []

            for index in range(
                value_start,
                len(html),
            ):
                char = html[index]

                if escaped:
                    chars.append(char)
                    escaped = False
                    continue

                if char == "\\":
                    escaped = True
                    chars.append(char)
                    continue

                if char == quote:
                    encoded = "".join(chars)

                    try:
                        decoded = json.loads(
                            f'"{encoded}"'
                        )
                        return json.loads(decoded)
                    except (
                        json.JSONDecodeError,
                        TypeError,
                    ):
                        return None

                chars.append(char)

            return None

        if start >= len(html):
            return None

        opening = html[start]

        if opening not in "{[":
            # Occasionally whitespace or another JS token
            # can appear between "=" and the JSON.
            next_object = html.find(
                "{",
                start,
            )
            next_array = html.find(
                "[",
                start,
            )

            candidates = [
                position
                for position in (
                    next_object,
                    next_array,
                )
                if position != -1
            ]

            if not candidates:
                return None

            start = min(candidates)
            opening = html[start]

        closing = (
            "}"
            if opening == "{"
            else "]"
        )

        depth = 0
        in_string = False
        escaped = False

        for index in range(
            start,
            len(html),
        ):
            char = html[index]

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False

                continue

            if char == '"':
                in_string = True
                continue

            if char == opening:
                depth += 1

            elif char == closing:
                depth -= 1

                if depth == 0:
                    raw_json = html[
                        start:index + 1
                    ]

                    try:
                        return json.loads(
                            raw_json
                        )
                    except json.JSONDecodeError:
                        return None

        return None

    # =========================================================
    # GENERIC STATE WALKER
    # =========================================================

    @staticmethod
    def _walk_objects(
        value: Any,
    ):
        """
        Recursively yield dictionaries from an arbitrary
        JSON-like structure.
        """

        if isinstance(value, dict):
            yield value

            for child in value.values():
                yield from (
                    BookMyShowCinemaResolver
                    ._walk_objects(child)
                )

        elif isinstance(value, list):
            for child in value:
                yield from (
                    BookMyShowCinemaResolver
                    ._walk_objects(child)
                )

    # =========================================================
    # VALUE HELPERS
    # =========================================================

    @staticmethod
    def _first_string(
        record: dict[str, Any],
        keys: tuple[str, ...],
    ) -> str | None:
        for key in keys:
            value = record.get(key)

            if isinstance(value, str):
                value = value.strip()

                if value:
                    return value

        return None

    @staticmethod
    def _extract_open_dates(
        record: dict[str, Any],
    ) -> tuple[str, ...]:
        """
        Extract DateCode values from venue-level date
        structures when BookMyShow exposes them.
        """

        dates: list[str] = []

        possible_keys = (
            "ShowDatesArray",
            "ShowDates",
            "Dates",
            "dates",
            "showDates",
        )

        def collect(
            value: Any,
        ) -> None:
            if isinstance(value, list):
                for item in value:
                    collect(item)
                return

            if not isinstance(value, dict):
                return

            date_code = (
                value.get("DateCode")
                or value.get("dateCode")
                or value.get("Date")
                or value.get("date")
            )

            disabled = (
                value.get("isDisabled")
                if "isDisabled" in value
                else value.get("IsDisabled")
            )

            if (
                date_code is not None
                and disabled is not True
            ):
                text = str(
                    date_code
                ).strip()

                if re.fullmatch(
                    r"\d{8}",
                    text,
                ):
                    dates.append(text)

            for key in possible_keys:
                if key in value:
                    collect(
                        value[key]
                    )

        for key in possible_keys:
            if key in record:
                collect(
                    record[key]
                )

        return tuple(
            dict.fromkeys(dates)
        )

    @staticmethod
    def _extract_slug(
        record: dict[str, Any],
        name: str,
    ) -> str:
        """
        Prefer a real BookMyShow slug if the embedded
        record exposes one.

        Otherwise derive a slug from the venue name.
        """

        for key in (
            "Slug",
            "slug",
            "VenueSlug",
            "venueSlug",
            "SeoUrl",
            "seoUrl",
            "URLSlug",
            "urlSlug",
        ):
            value = record.get(key)

            if isinstance(value, str):
                value = value.strip().strip("/")

                if value:
                    # If BookMyShow gives a complete path,
                    # retain only the useful cinema slug.
                    parts = [
                        part
                        for part in value.split("/")
                        if part
                    ]

                    if parts:
                        return parts[-1]

                    return value

        return (
            BookMyShowCinemaResolver
            ._slugify_cinema_name(name)
        )

    @staticmethod
    def _extract_city_code(
        record: dict[str, Any],
        fallback: str,
    ) -> str:
        value = (
            record.get("RegionCode")
            or record.get("regionCode")
            or record.get("CityCode")
            or record.get("cityCode")
        )

        if isinstance(value, str):
            value = value.strip()

            if value:
                return value.upper()

        return fallback.upper()

    # =========================================================
    # INITIAL STATE VENUES
    # =========================================================

    @classmethod
    def _extract_venue_records_from_state(
        cls,
        state: Any,
        city: str,
    ) -> List[CinemaDiscovery]:
        discoveries: list[CinemaDiscovery] = []

        seen: set[
            tuple[str, str]
        ] = set()

        requested_city = cls.normalize(
            city
        )

        fallback_city_code = cls.city_slug(
            city
        ).upper()

        for record in cls._walk_objects(
            state
        ):
            name = cls._first_string(
                record,
                (
                    "VenueName",
                    "venueName",
                    "VenueDisplayName",
                    "venueDisplayName",
                ),
            )

            provider_id = cls._first_string(
                record,
                (
                    "VenueCode",
                    "venueCode",
                    "ProviderId",
                    "providerId",
                ),
            )

            if not name or not provider_id:
                continue

            discovered_city = cls._first_string(
                record,
                (
                    "City",
                    "city",
                    "CityName",
                    "cityName",
                ),
            )

            if discovered_city:
                if cls.normalize(
                    discovered_city
                ) != requested_city:
                    continue
            else:
                discovered_city = city

            city_code = cls._extract_city_code(
                record,
                fallback_city_code,
            )

            slug = cls._extract_slug(
                record,
                name,
            )

            open_dates = cls._extract_open_dates(
                record
            )

            identity = (
                cls.normalize(name),
                provider_id.lower(),
            )

            if identity in seen:
                continue

            seen.add(identity)

            discoveries.append(
                CinemaDiscovery(
                    name=name,
                    city=discovered_city,
                    provider_id=provider_id,
                    slug=slug,
                    city_code=city_code,
                    open_dates=open_dates,
                )
            )

        return discoveries

    # =========================================================
    # PUBLIC LINK FALLBACK
    # =========================================================

    @staticmethod
    def _extract_provider_details(
        href: str,
    ) -> tuple[str, str] | None:
        booking_match = re.search(
            r"/cinemas/"
            r"[^/]+/"
            r"([^/]+)/"
            r"buytickets/"
            r"([^/?#]+)",
            href,
            flags=re.IGNORECASE,
        )

        if booking_match:
            return (
                booking_match.group(1),
                booking_match.group(2),
            )

        return None

    def _extract_link_venues(
        self,
        html: str,
        city: str,
    ) -> List[CinemaDiscovery]:
        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        discoveries: list[CinemaDiscovery] = []

        seen: set[
            tuple[str, str]
        ] = set()

        city_code = self.city_slug(
            city
        ).upper()

        for link in soup.find_all("a"):
            href = link.get("href")

            if not href:
                continue

            absolute_url = urljoin(
                BOOKMYSHOW_BASE_URL,
                href,
            )

            details = (
                self._extract_provider_details(
                    absolute_url
                )
            )

            if details is None:
                continue

            slug, provider_id = details

            text = link.get_text(
                " ",
                strip=True,
            )

            if not text:
                continue

            identity = (
                self.normalize(text),
                provider_id.lower(),
            )

            if identity in seen:
                continue

            seen.add(identity)

            discoveries.append(
                CinemaDiscovery(
                    name=text,
                    city=city,
                    provider_id=provider_id,
                    slug=slug,
                    city_code=city_code,
                )
            )

        return discoveries

    # =========================================================
    # DISCOVERY
    # =========================================================

    def discover(
        self,
        city: str,
    ) -> List[CinemaDiscovery]:
        if not city or not city.strip():
            raise ValueError(
                "City cannot be empty."
            )

        normalized_city = self.normalize(
            city
        )

        cached = self._discovery_cache.get(
            normalized_city
        )

        if cached is not None:
            return list(cached)

        city_slug = self.city_slug(
            city
        )

        url = (
            f"{BOOKMYSHOW_BASE_URL}/"
            f"{city_slug}/venue-list"
        )

        try:
            response = self._get(
                url
            )
        except requests.RequestException as error:
            raise RuntimeError(
                "Failed to discover BookMyShow "
                f"cinemas for {city}: {error}"
            ) from error

        html = response.text

        # -----------------------------------------------------
        # PRIMARY: embedded __INITIAL_STATE__
        # -----------------------------------------------------

        state = (
            self._extract_initial_state(
                html
            )
        )

        discoveries: list[
            CinemaDiscovery
        ] = []

        if state is not None:
            discoveries = (
                self._extract_venue_records_from_state(
                    state=state,
                    city=city,
                )
            )

        # -----------------------------------------------------
        # FALLBACK: actual public cinema links
        # -----------------------------------------------------

        link_discoveries = (
            self._extract_link_venues(
                html=html,
                city=city,
            )
        )

        seen = {
            (
                self.normalize(item.name),
                item.provider_id.lower(),
            )
            for item in discoveries
        }

        for item in link_discoveries:
            identity = (
                self.normalize(item.name),
                item.provider_id.lower(),
            )

            if identity in seen:
                continue

            discoveries.append(
                item
            )

            seen.add(
                identity
            )

        if not discoveries:
            raise ValueError(
                "No BookMyShow cinema venues were "
                "discovered for city: "
                f"{city}"
            )

        self._discovery_cache[
            normalized_city
        ] = list(discoveries)

        return list(
            discoveries
        )

    # =========================================================
    # DATE CHECK
    # =========================================================

    def is_date_open(
        self,
        name: str,
        city: str,
        target_date: str,
    ) -> bool | None:
        """
        Check whether BookMyShow's currently captured
        directory data says a date is open.

        Returns:

            True  -> date explicitly listed as open
            False -> venue has date information and date
                     is not listed
            None  -> no usable date information
        """

        venue = self.resolve(
            name=name,
            city=city,
        )

        discoveries = self.discover(
            city
        )

        target = target_date.replace(
            "-",
            "",
        )

        for item in discoveries:
            if (
                item.provider_id
                == venue.provider_id
                and item.name
                == venue.name
            ):
                if not item.open_dates:
                    return None

                return target in item.open_dates

        return None

    # =========================================================
    # RESOLUTION
    # =========================================================

    @staticmethod
    def _to_venue(
        cinema: CinemaDiscovery,
    ) -> CinemaVenue:
        return CinemaVenue(
            name=cinema.name,
            city=cinema.city,
            provider_id=cinema.provider_id,
            slug=cinema.slug,
            city_code=cinema.city_code,
        )

    def resolve_all(
        self,
        name: str,
        city: str,
    ) -> List[CinemaVenue]:
        """
        Return all reasonable cinema matches.

        Useful for chain-level searches such as:

            PVR
            INOX
            Cinepolis
        """

        if not name or not name.strip():
            raise ValueError(
                "Cinema name cannot be empty."
            )

        if not city or not city.strip():
            raise ValueError(
                "City cannot be empty."
            )

        requested = self.normalize_search(
            name
        )

        if not requested:
            raise ValueError(
                "Cinema search contains only generic "
                "cinema words."
            )

        discoveries = self.discover(
            city
        )

        requested_tokens = set(
            requested.split()
        )

        matches: list[
            CinemaDiscovery
        ] = []

        for cinema in discoveries:
            cinema_normalized = (
                self.normalize_search(
                    cinema.name
                )
            )

            cinema_tokens = set(
                cinema_normalized.split()
            )

            if requested == cinema_normalized:
                matches.append(
                    cinema
                )
                continue

            if (
                requested_tokens
                and requested_tokens.issubset(
                    cinema_tokens
                )
            ):
                matches.append(
                    cinema
                )
                continue

            if (
                requested
                in cinema_normalized
            ):
                matches.append(
                    cinema
                )

        # Deduplicate.
        unique: list[
            CinemaDiscovery
        ] = []

        seen: set[
            tuple[str, str]
        ] = set()

        for cinema in matches:
            identity = (
                self.normalize(cinema.name),
                cinema.provider_id.lower(),
            )

            if identity in seen:
                continue

            seen.add(identity)
            unique.append(cinema)

        return [
            self._to_venue(cinema)
            for cinema in unique
        ]

    @staticmethod
    def _similarity(
        left: str,
        right: str,
    ) -> float:
        return difflib.SequenceMatcher(
            None,
            left,
            right,
        ).ratio()

    @classmethod
    def _fuzzy_match_score(
        cls,
        requested: str,
        candidate: str,
    ) -> float:
        """Score a user search against a cinema name.

        The comparison is token-aware so a typo in the main
        cinema name can still match even when the BookMyShow
        venue has additional descriptive words.

        It also compares adjacent candidate tokens joined
        together, which handles forms such as:

            "35 mm" <-> "35mm"
        """

        requested_tokens = requested.split()
        candidate_tokens = candidate.split()

        if not requested_tokens or not candidate_tokens:
            return 0.0

        candidate_forms = list(candidate_tokens)

        for index in range(len(candidate_tokens) - 1):
            candidate_forms.append(
                candidate_tokens[index]
                + candidate_tokens[index + 1]
            )

        # Also compare numeric/unit forms such as:
        # "35 mm" <-> "35mm"
        for token in candidate_tokens:
            match = re.fullmatch(
                r"(\d+)(mm|k|d|imax)",
                token,
            )

            if match:
                candidate_forms.append(
                    match.group(1)
                )

        token_scores = []

        for requested_token in requested_tokens:
            best = max(
                (
                    cls._similarity(
                        requested_token,
                        candidate_form,
                    )
                    for candidate_form in candidate_forms
                ),
                default=0.0,
            )
            token_scores.append(best)

        # Require every requested token to have a credible
        # counterpart. A short token can be matched exactly
        # against a joined form such as "35mm".
        if any(score < 0.80 for score in token_scores):
            return 0.0

        return sum(token_scores) / len(token_scores)

    def resolve(
        self,
        name: str,
        city: str,
    ) -> CinemaVenue:
        """
        Resolve a user-entered cinema name.

        Matching order:

        1. Exact normalized match.
        2. Exact match after removing generic words.
        3. Token containment.
        4. Unique substring.

        Ambiguous searches raise a useful error instead
        of silently selecting an arbitrary cinema.
        """

        if not name or not name.strip():
            raise ValueError(
                "Cinema name cannot be empty."
            )

        if not city or not city.strip():
            raise ValueError(
                "City cannot be empty."
            )

        requested_full = self.normalize(
            name
        )

        requested = self.normalize_search(
            name
        )

        discoveries = self.discover(
            city
        )

        # -----------------------------------------------------
        # 1. Exact full-name match
        # -----------------------------------------------------

        exact_full = [
            cinema
            for cinema in discoveries
            if self.normalize(
                cinema.name
            ) == requested_full
        ]

        if len(exact_full) == 1:
            return self._to_venue(
                exact_full[0]
            )

        if len(exact_full) > 1:
            names = ", ".join(
                cinema.name
                for cinema in exact_full
            )

            raise ValueError(
                "Cinema name is ambiguous. "
                f"Matches: {names}"
            )

        # -----------------------------------------------------
        # 2. Exact match after removing generic words
        #
        # Example:
        #
        # "Sushma Theatre"
        # ->
        # "sushma"
        #
        # "Sushma 2K Dolby Digital Cinema: Vanasthalipuram"
        # ->
        # "sushma 2k dolby digital vanasthalipuram"
        # -----------------------------------------------------

        exact_search = [
            cinema
            for cinema in discoveries
            if self.normalize_search(
                cinema.name
            ) == requested
        ]

        if len(exact_search) == 1:
            return self._to_venue(
                exact_search[0]
            )

        if len(exact_search) > 1:
            names = ", ".join(
                cinema.name
                for cinema in exact_search
            )

            raise ValueError(
                "Cinema name is ambiguous. "
                f"Matches: {names}"
            )

        # -----------------------------------------------------
        # 3. Token-based matching
        # -----------------------------------------------------

        requested_tokens = set(
            requested.split()
        )

        token_matches: list[
            CinemaDiscovery
        ] = []

        for cinema in discoveries:
            cinema_normalized = (
                self.normalize_search(
                    cinema.name
                )
            )

            cinema_tokens = set(
                cinema_normalized.split()
            )

            if (
                requested_tokens
                and requested_tokens.issubset(
                    cinema_tokens
                )
            ):
                token_matches.append(
                    cinema
                )

        if len(token_matches) == 1:
            return self._to_venue(
                token_matches[0]
            )

        if len(token_matches) > 1:
            names = ", ".join(
                cinema.name
                for cinema in token_matches
            )

            raise ValueError(
                "Cinema name is ambiguous. "
                f"Matches: {names}"
            )

        # -----------------------------------------------------
        # 4. Unique substring matching
        # -----------------------------------------------------

        partial_matches = [
            cinema
            for cinema in discoveries
            if requested
            and requested
            in self.normalize_search(
                cinema.name
            )
        ]

        if len(partial_matches) == 1:
            return self._to_venue(
                partial_matches[0]
            )

        if len(partial_matches) > 1:
            names = ", ".join(
                cinema.name
                for cinema in partial_matches
            )

            raise ValueError(
                "Cinema name is ambiguous. "
                f"Matches: {names}"
            )

        # -----------------------------------------------------
        # 5. Fuzzy matching
        #
        # Only reached after deterministic matching fails.
        # Handles small spelling mistakes such as:
        #
        #   shandhya 70mm -> sandhya 70mm
        #   sudarsham 35 mm -> sudarshan 35mm
        #
        # Weak matches are rejected, and tied strong matches
        # remain ambiguous instead of guessing.
        # -----------------------------------------------------

        fuzzy_candidates: list[
            tuple[float, CinemaDiscovery]
        ] = []

        for cinema in discoveries:
            candidate = self.normalize_search(
                cinema.name
            )

            score = self._fuzzy_match_score(
                requested,
                candidate,
            )

            if score >= 0.84:
                fuzzy_candidates.append(
                    (score, cinema)
                )

        fuzzy_candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        if fuzzy_candidates:
            best_score = fuzzy_candidates[0][0]

            tied = [
                cinema
                for score, cinema in fuzzy_candidates
                if best_score - score <= 0.03
            ]

            if len(tied) == 1:
                return self._to_venue(
                    tied[0]
                )

            names = ", ".join(
                cinema.name
                for cinema in tied
            )

            raise ValueError(
                "Cinema name is ambiguous. "
                f"Matches: {names}"
            )

        # -----------------------------------------------------
        # 6. Not found
        # -----------------------------------------------------

        raise ValueError(
            "Cinema venue not found on "
            "BookMyShow: "
            f"{name} ({city})"
        )


def get_cinema_venue(
    name: str,
    city: str,
) -> CinemaVenue:
    """
    Application-level cinema resolver.
    """

    resolver = BookMyShowCinemaResolver()

    return resolver.resolve(
        name=name,
        city=city,
    )