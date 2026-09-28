import sys
from pathlib import Path

# Add the project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from dotenv import load_dotenv

from app.notifications import notify


def main():
    load_dotenv(
        PROJECT_ROOT / ".env"
    )

    changes = {
        "PVR": {
            "19:30": {
                "previous": "SOLD_OUT",
                "current": "AVAILABLE",
                "previous_tickets": 0,
                "current_tickets": 5,
            }
        }
    }

    print(
        "Sending Telegram test notification..."
    )

    notify(changes)

    print(
        "Notification attempt completed."
    )


if __name__ == "__main__":
    main()