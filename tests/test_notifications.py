from unittest.mock import Mock, patch

from app.notifications import (
    build_message,
    notify,
)


def test_build_message():

    changes = {
        "PVR": {
            "19:30": {
                "current_tickets": 4,
            }
        },
        "Prasads": {
            "21:00": {
                "current_tickets": 3,
            }
        },
    }

    message = build_message(
        changes
    )

    assert "🎬 TICKETS AVAILABLE!" in message
    assert "🏢 PVR" in message
    assert "🕐 19:30" in message
    assert "Available tickets: 4" in message
    assert "🏢 Prasads" in message
    assert "🕐 21:00" in message
    assert "Available tickets: 3" in message


def test_notify_does_nothing_for_empty_changes():

    with patch(
        "app.notifications.send_telegram_message"
    ) as mock_send:

        notify({})

        mock_send.assert_not_called()


def test_notify_does_nothing_without_configuration():

    with patch.dict(
        "os.environ",
        {},
        clear=True,
    ):

        with patch(
            "app.notifications.send_telegram_message"
        ) as mock_send:

            notify(
                {
                    "PVR": {
                        "19:30": {
                            "current_tickets": 4,
                        }
                    }
                }
            )

            mock_send.assert_not_called()


def test_notify_sends_telegram_message():

    changes = {
        "PVR": {
            "19:30": {
                "current_tickets": 4,
            }
        }
    }

    with patch.dict(
        "os.environ",
        {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "TELEGRAM_CHAT_ID": "123456",
        },
        clear=True,
    ):

        with patch(
            "app.notifications.send_telegram_message"
        ) as mock_send:

            notify(changes)

            mock_send.assert_called_once()

            arguments = (
                mock_send.call_args.kwargs
            )

            assert (
                arguments["bot_token"]
                == "test-token"
            )

            assert (
                arguments["chat_id"]
                == "123456"
            )

            assert (
                "PVR"
                in arguments["message"]
            )
