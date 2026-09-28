import json
from pathlib import Path
from typing import Dict


STATE_FILE = Path("data/state.json")


def load_state() -> Dict:
    """
    Load the previous availability state.

    If no state exists yet, return an empty dictionary.
    """

    if not STATE_FILE.exists():
        return {}

    try:
        with STATE_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: Dict) -> None:
    """
    Save the current availability state.
    """

    STATE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            state,
            file,
            indent=4,
        )