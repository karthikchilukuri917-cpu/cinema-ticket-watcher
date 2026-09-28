import logging
import os
from typing import Dict

import requests


logger = logging.getLogger(__name__)


TELEGRAM_API_URL = (
    "https://api.telegram.org/bot{}/sendMessage"
)


def build_message(
    changes: Dict,
) -> str:
    """
    Convert availability changes into a Telegram message.
    """

    lines = [
        "🎬 TICKETS AVAILABLE!",
        "",
    ]

    for cinema, shows in changes.items():

        lines.append(
            f"🏢 {cinema}"
        )

        for show_time, change in shows.items():

            current_tickets = change.get(
                "current_tickets"
            )

            if current_tickets is None:

                ticket_text = (
                    "Availability confirmed"
                )

            else:

                ticket_text = (
                    f"Available tickets: "
                    f"{current_tickets}"
                )

            lines.append(
                f"🕐 {show_time}"
            )

            lines.append(
                f"🎟 {ticket_text}"
            )

            lines.append("")

    return "\n".join(lines).strip()


def send_telegram_message(
    bot_token: str,
    chat_id: str,
    message: str,
) -> None:
    """
    Send one message through the Telegram Bot API.
    """

    url = TELEGRAM_API_URL.format(
        bot_token
    )

    response = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": message,
        },
        timeout=15,
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):

        raise RuntimeError(
            f"Telegram API rejected the message: "
            f"{result}"
        )


def notify(
    changes: Dict,
) -> None:
    """
    Send availability changes to Telegram.
    """

    if not changes:
        return

    bot_token = os.getenv(
        "TELEGRAM_BOT_TOKEN"
    )

    chat_id = os.getenv(
        "TELEGRAM_CHAT_ID"
    )

    if not bot_token:

        logger.error(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

        return

    if not chat_id:

        logger.error(
            "TELEGRAM_CHAT_ID is not configured."
        )

        return

    message = build_message(
        changes
    )

    try:

        send_telegram_message(
            bot_token=bot_token,
            chat_id=chat_id,
            message=message,
        )

        logger.info(
            "Telegram notification sent successfully."
        )

    except (
        requests.RequestException,
        RuntimeError,
    ) as error:

        logger.error(
            "Failed to send Telegram notification: %s",
            error,
        )