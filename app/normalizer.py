from datetime import date
from typing import Dict, List

from app.models import Show


def normalize_availability(
    data: Dict,
    movie: str,
    show_date: date,
) -> List[Show]:
    """
    Convert raw availability data into Show objects.

    Supported raw format:

    {
        "PVR": {
            "19:30": {
                "status": "AVAILABLE",
                "available_tickets": 4,
                "source_id": "987654"
            }
        }
    }

    For backwards compatibility, this is also accepted:

    {
        "PVR": {
            "19:30": "AVAILABLE"
        }
    }
    """

    shows: List[Show] = []

    for cinema, cinema_shows in data.items():

        for show_time, show_data in cinema_shows.items():

            if isinstance(show_data, dict):

                status = show_data.get("status")

                available_tickets = show_data.get(
                    "available_tickets"
                )

                source_id = show_data.get(
                    "source_id"
                )

            else:

                status = show_data

                available_tickets = None

                source_id = None

            show = Show(
                movie=movie,
                cinema=cinema,
                show_date=show_date,
                show_time=show_time,
                status=status,
                available_tickets=available_tickets,
                source_id=source_id,
            )

            shows.append(show)

    return shows