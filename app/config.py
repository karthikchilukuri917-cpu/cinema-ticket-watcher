import os

from dotenv import load_dotenv


# Load project-level environment variables whenever
# the application configuration module is imported.
load_dotenv()


def get_source_name() -> str:
    source = (
        os.getenv(
            "SOURCE",
            "mock",
        )
        .strip()
        .lower()
    )

    allowed_sources = {
        "mock",
        "bookmyshow",
        "public",
    }

    if source not in allowed_sources:
        raise ValueError(
            "SOURCE must be one of: "
            "mock, bookmyshow, public."
        )

    return source


def get_max_cycles() -> int | None:
    value = os.getenv(
        "MAX_CYCLES"
    )

    if value is None or not value.strip():
        return None

    try:
        cycles = int(value)
    except ValueError as error:
        raise ValueError(
            "MAX_CYCLES must be an integer."
        ) from error

    if cycles < 1:
        raise ValueError(
            "MAX_CYCLES must be at least 1."
        )

    return cycles


def _get_positive_integer(
    environment_name: str,
    default: int,
) -> int:
    value = os.getenv(
        environment_name
    )

    if value is None or not value.strip():
        return default

    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(
            f"{environment_name} must be an integer."
        ) from error

    if parsed < 1:
        raise ValueError(
            f"{environment_name} must be at least 1."
        )

    return parsed


def get_normal_interval() -> int:
    return _get_positive_integer(
        "NORMAL_INTERVAL",
        60,
    )


def get_active_interval() -> int:
    return _get_positive_integer(
        "ACTIVE_INTERVAL",
        10,
    )