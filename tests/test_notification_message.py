from app.notifications import build_message


def test_available_show_message():

    changes = {
        "PVR": {
            "19:30": {
                "previous": "SOLD_OUT",
                "current": "AVAILABLE",
                "previous_tickets": 0,
                "current_tickets": 4,
                "show_id": "session-123",
            }
        }
    }

    message = build_message(changes)

    assert "TICKETS AVAILABLE!" in message
    assert "PVR" in message
    assert "19:30" in message
    assert "Available tickets: 4" in message
