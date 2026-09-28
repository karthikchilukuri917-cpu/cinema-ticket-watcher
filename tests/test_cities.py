from app.cities import CityCandidate, CityResolver


def make_cities():
    return [
        CityCandidate(
            name="Hyderabad",
            city_code="HYDERABAD",
        ),
        CityCandidate(
            name="Delhi",
            city_code="DELHI",
        ),
        CityCandidate(
            name="Bengaluru",
            city_code="BENGALURU",
        ),
        CityCandidate(
            name="Chennai",
            city_code="CHENNAI",
        ),
    ]


def test_exact_match():
    resolver = CityResolver(make_cities())

    result = resolver.resolve("Hyderabad")

    assert result.status == "MATCH"
    assert result.city.name == "Hyderabad"


def test_case_insensitive_match():
    resolver = CityResolver(make_cities())

    result = resolver.resolve("hyderabad")

    assert result.status == "MATCH"
    assert result.city.city_code == "HYDERABAD"


def test_normalized_match():
    resolver = CityResolver(make_cities())

    result = resolver.resolve("  HYDERABAD  ")

    assert result.status == "MATCH"
    assert result.city.name == "Hyderabad"


def test_partial_match():
    resolver = CityResolver(make_cities())

    result = resolver.resolve("Hyder")

    assert result.status == "MATCH"
    assert result.city.name == "Hyderabad"


def test_fuzzy_match():
    resolver = CityResolver(make_cities())

    result = resolver.resolve("Hyderbad")

    assert result.status == "MATCH"
    assert result.city.name == "Hyderabad"


def test_unknown_city():
    resolver = CityResolver(make_cities())

    result = resolver.resolve("Mumbai")

    assert result.status == "NOT_FOUND"
    assert result.city is None


def test_empty_city():
    resolver = CityResolver(make_cities())

    result = resolver.resolve("")

    assert result.status == "NOT_FOUND"
    assert result.city is None


def test_city_identity_uses_city_code():
    city = CityCandidate(
        name="Hyderabad",
        city_code="HYDERABAD",
    )

    assert city.identity == "HYDERABAD"