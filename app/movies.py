from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re


@dataclass(frozen=True)
class MovieCandidate:
    """
    A BookMyShow movie/event candidate.

    event_code is the stable BookMyShow event identifier.
    """

    title: str
    event_name: str
    event_code: str
    event_url: str | None = None
    event_group: str | None = None
    language: str | None = None
    dimension: str | None = None

    @property
    def identity(self) -> str:
        return self.event_code


@dataclass(frozen=True)
class MovieResolveResult:
    """
    Result of resolving a user's movie search.
    """

    status: str
    movie: MovieCandidate | None = None
    candidates: tuple[MovieCandidate, ...] = ()


class MovieResolver:
    """
    Resolves a user's movie input against BookMyShow movie candidates.

    Resolution order:
        1. Exact normalized title
        2. Exact normalized event name
        3. Token/partial match
        4. Fuzzy match

    Ambiguous matches are returned as candidates instead of
    silently selecting one.
    """

    def __init__(
        self,
        candidates: list[MovieCandidate],
    ) -> None:
        self.candidates = list(candidates)

    @staticmethod
    def _normalize(value: str) -> str:
        value = value.lower().strip()
        value = re.sub(r"[^a-z0-9]+", " ", value)
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def _tokens(cls, value: str) -> set[str]:
        normalized = cls._normalize(value)
        return set(normalized.split()) if normalized else set()

    def _exact_matches(
        self,
        query: str,
    ) -> list[MovieCandidate]:
        normalized_query = self._normalize(query)

        return [
            movie
            for movie in self.candidates
            if normalized_query
            in {
                self._normalize(movie.title),
                self._normalize(movie.event_name),
            }
        ]

    def _partial_matches(
        self,
        query: str,
    ) -> list[MovieCandidate]:
        normalized_query = self._normalize(query)

        if not normalized_query:
            return []

        query_tokens = self._tokens(query)

        matches = []

        for movie in self.candidates:
            title = self._normalize(movie.title)
            event_name = self._normalize(movie.event_name)

            if (
                normalized_query in title
                or normalized_query in event_name
            ):
                matches.append(movie)
                continue

            title_tokens = self._tokens(movie.title)
            event_tokens = self._tokens(movie.event_name)

            if query_tokens and (
                query_tokens <= title_tokens
                or query_tokens <= event_tokens
            ):
                matches.append(movie)

        return matches

    def _fuzzy_matches(
        self,
        query: str,
    ) -> list[MovieCandidate]:
        normalized_query = self._normalize(query)

        if not normalized_query:
            return []

        scored: list[tuple[float, MovieCandidate]] = []

        for movie in self.candidates:
            title = self._normalize(movie.title)
            event_name = self._normalize(movie.event_name)

            title_score = SequenceMatcher(
                None,
                normalized_query,
                title,
            ).ratio()

            event_score = SequenceMatcher(
                None,
                normalized_query,
                event_name,
            ).ratio()

            score = max(title_score, event_score)

            if score >= 0.70:
                scored.append((score, movie))

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        if not scored:
            return []

        highest = scored[0][0]

        # Keep candidates close to the best fuzzy result.
        return [
            movie
            for score, movie in scored
            if score >= highest - 0.08
        ]

    @staticmethod
    def _unique(
        movies: list[MovieCandidate],
    ) -> list[MovieCandidate]:
        seen: set[str] = set()
        result: list[MovieCandidate] = []

        for movie in movies:
            if movie.identity in seen:
                continue

            seen.add(movie.identity)
            result.append(movie)

        return result

    def resolve(
        self,
        query: str,
    ) -> MovieResolveResult:
        if not query or not query.strip():
            return MovieResolveResult(
                status="NOT_FOUND",
            )

        # 1. Exact match
        matches = self._unique(
            self._exact_matches(query)
        )

        if len(matches) == 1:
            return MovieResolveResult(
                status="MATCH",
                movie=matches[0],
            )

        if len(matches) > 1:
            return MovieResolveResult(
                status="AMBIGUOUS",
                candidates=tuple(matches),
            )

        # 2. Partial/token match
        matches = self._unique(
            self._partial_matches(query)
        )

        if len(matches) == 1:
            return MovieResolveResult(
                status="MATCH",
                movie=matches[0],
            )

        if len(matches) > 1:
            return MovieResolveResult(
                status="AMBIGUOUS",
                candidates=tuple(matches),
            )

        # 3. Fuzzy match
        matches = self._unique(
            self._fuzzy_matches(query)
        )

        if len(matches) == 1:
            return MovieResolveResult(
                status="MATCH",
                movie=matches[0],
            )

        if len(matches) > 1:
            return MovieResolveResult(
                status="AMBIGUOUS",
                candidates=tuple(matches),
            )

        return MovieResolveResult(
            status="NOT_FOUND",
        )