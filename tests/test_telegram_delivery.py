from app.notifications import notify


def test_telegram_delivery():
    changes = {
        "PVR: Nexus Mall Kukatpally": {
            "18:30": {
                "previous": "SOLD_OUT",
                "current": "AVAILABLE",
                "previous_tickets": 0,
                "current_tickets": 5,
                "show_id": "telegram-test",
            }
        }
    }

    notify(changes)
