from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re


@dataclass(frozen=True)
class CityCandidate:
    name: str
    city_code: str | None = None

    @property
    def identity(self) -> str:
        return self.city_code or self.name


@dataclass(frozen=True)
class CityResolveResult:
    status: str
    city: CityCandidate | None = None
    candidates: tuple[CityCandidate, ...] = ()


class CityResolver:
    """
    Resolves a user's city input against known city candidates.

    The resolver only identifies a city.
    Cinema discovery remains the responsibility of CinemaResolver.
    """

    def __init__(
        self,
        cities: list[CityCandidate],
    ) -> None:
        self.cities = list(cities)

    @staticmethod
    def _normalize(value: str) -> str:
        value = value.lower().strip()
        value = re.sub(r"[^a-z0-9]+", " ", value)
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _unique(
        cities: list[CityCandidate],
    ) -> list[CityCandidate]:
        seen: set[str] = set()
        result: list[CityCandidate] = []

        for city in cities:
            if city.identity in seen:
                continue

            seen.add(city.identity)
            result.append(city)

        return result

    def resolve(
        self,
        query: str,
    ) -> CityResolveResult:
        if not query or not query.strip():
            return CityResolveResult(
                status="NOT_FOUND",
            )

        normalized_query = self._normalize(query)

        # Exact match
        exact = self._unique(
            [
                city
                for city in self.cities
                if self._normalize(city.name)
                == normalized_query
            ]
        )

        if len(exact) == 1:
            return CityResolveResult(
                status="MATCH",
                city=exact[0],
            )

        if len(exact) > 1:
            return CityResolveResult(
                status="AMBIGUOUS",
                candidates=tuple(exact),
            )

        # Token / partial match
        partial = self._unique(
            [
                city
                for city in self.cities
                if normalized_query
                in self._normalize(city.name)
            ]
        )

        if len(partial) == 1:
            return CityResolveResult(
                status="MATCH",
                city=partial[0],
            )

        if len(partial) > 1:
            return CityResolveResult(
                status="AMBIGUOUS",
                candidates=tuple(partial),
            )

        # Fuzzy match
        scored: list[tuple[float, CityCandidate]] = []

        for city in self.cities:
            score = SequenceMatcher(
                None,
                normalized_query,
                self._normalize(city.name),
            ).ratio()

            if score >= 0.70:
                scored.append((score, city))

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        if scored:
            highest = scored[0][0]

            fuzzy = self._unique(
                [
                    city
                    for score, city in scored
                    if score >= highest - 0.08
                ]
            )

            if len(fuzzy) == 1:
                return CityResolveResult(
                    status="MATCH",
                    city=fuzzy[0],
                )

            if len(fuzzy) > 1:
                return CityResolveResult(
                    status="AMBIGUOUS",
                    candidates=tuple(fuzzy),
                )

        return CityResolveResult(
            status="NOT_FOUND",
        )