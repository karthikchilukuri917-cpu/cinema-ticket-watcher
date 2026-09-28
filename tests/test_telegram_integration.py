import os

import pytest
import requests

from app.notifications import (
    build_message,
    notify,
    send_telegram_message,
)


def test_build_message_with_ticket_count():
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

    message = build_message(changes)

    assert "TICKETS AVAILABLE!" in message
    assert "PVR" in message
    assert "19:30" in message
    assert "Available tickets: 5" in message


def test_build_message_without_ticket_count():
    changes = {
        "PVR": {
            "19:30": {
                "previous": "SOLD_OUT",
                "current": "AVAILABLE",
                "previous_tickets": None,
                "current_tickets": None,
            }
        }
    }

    message = build_message(changes)

    assert "TICKETS AVAILABLE!" in message
    assert "PVR" in message
    assert "19:30" in message
    assert "Availability confirmed" in message


def test_build_message_supports_multiple_cinemas():
    changes = {
        "PVR": {
            "19:30": {
                "current_tickets": 5,
            }
        },
        "AMB Cinemas": {
            "21:00": {
                "current_tickets": 8,
            }
        },
        "Prasads": {
            "18:30": {
                "current_tickets": 3,
            }
        },
    }

    message = build_message(changes)

    assert "PVR" in message
    assert "19:30" in message
    assert "Available tickets: 5" in message

    assert "AMB Cinemas" in message
    assert "21:00" in message
    assert "Available tickets: 8" in message

    assert "Prasads" in message
    assert "18:30" in message
    assert "Available tickets: 3" in message


def test_send_telegram_message_success(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "ok": True,
                "result": {
                    "message_id": 123
                },
            }

    def fake_post(
        url,
        data,
        timeout,
    ):
        captured["url"] = url
        captured["data"] = data
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        requests,
        "post",
        fake_post,
    )

    send_telegram_message(
        bot_token="test-token",
        chat_id="123456",
        message="Hello Telegram",
    )

    assert (
        captured["url"]
        == "https://api.telegram.org/"
        "bottest-token/sendMessage"
    )

    assert captured["data"] == {
        "chat_id": "123456",
        "text": "Hello Telegram",
    }

    assert captured["timeout"] == 15


def test_send_telegram_message_raises_on_http_failure(
    monkeypatch,
):
    class FakeResponse:
        def raise_for_status(self):
            raise requests.HTTPError(
                "Telegram HTTP failure"
            )

    def fake_post(
        url,
        data,
        timeout,
    ):
        return FakeResponse()

    monkeypatch.setattr(
        requests,
        "post",
        fake_post,
    )

    with pytest.raises(
        requests.HTTPError
    ):
        send_telegram_message(
            bot_token="test-token",
            chat_id="123456",
            message="Hello Telegram",
        )


def test_send_telegram_message_raises_when_telegram_rejects(
    monkeypatch,
):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "ok": False,
                "description": "Bad Request",
            }

    def fake_post(
        url,
        data,
        timeout,
    ):
        return FakeResponse()

    monkeypatch.setattr(
        requests,
        "post",
        fake_post,
    )

    with pytest.raises(
        RuntimeError,
        match="Telegram API rejected",
    ):
        send_telegram_message(
            bot_token="test-token",
            chat_id="123456",
            message="Hello Telegram",
        )


def test_notify_does_nothing_for_empty_changes(
    monkeypatch,
):
    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "Telegram must not be called."
        )

    monkeypatch.setattr(
        "app.notifications.send_telegram_message",
        fail_if_called,
    )

    notify({})


def test_notify_does_not_send_without_bot_token(
    monkeypatch,
    caplog,
):
    monkeypatch.delenv(
        "TELEGRAM_BOT_TOKEN",
        raising=False,
    )

    monkeypatch.setenv(
        "TELEGRAM_CHAT_ID",
        "123456",
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "Telegram must not be called."
        )

    monkeypatch.setattr(
        "app.notifications.send_telegram_message",
        fail_if_called,
    )

    notify(
        {
            "PVR": {
                "19:30": {
                    "current_tickets": 5,
                }
            }
        }
    )

    assert (
        "TELEGRAM_BOT_TOKEN is not configured."
        in caplog.text
    )


def test_notify_does_not_send_without_chat_id(
    monkeypatch,
    caplog,
):
    monkeypatch.setenv(
        "TELEGRAM_BOT_TOKEN",
        "test-token",
    )

    monkeypatch.delenv(
        "TELEGRAM_CHAT_ID",
        raising=False,
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "Telegram must not be called."
        )

    monkeypatch.setattr(
        "app.notifications.send_telegram_message",
        fail_if_called,
    )

    notify(
        {
            "PVR": {
                "19:30": {
                    "current_tickets": 5,
                }
            }
        }
    )

    assert (
        "TELEGRAM_CHAT_ID is not configured."
        in caplog.text
    )


def test_notify_sends_message(
    monkeypatch,
):
    captured = {}

    monkeypatch.setenv(
        "TELEGRAM_BOT_TOKEN",
        "test-token",
    )

    monkeypatch.setenv(
        "TELEGRAM_CHAT_ID",
        "123456",
    )

    def fake_send(
        bot_token,
        chat_id,
        message,
    ):
        captured["bot_token"] = bot_token
        captured["chat_id"] = chat_id
        captured["message"] = message

    monkeypatch.setattr(
        "app.notifications.send_telegram_message",
        fake_send,
    )

    changes = {
        "PVR": {
            "19:30": {
                "current_tickets": 5,
            }
        }
    }

    notify(changes)

    assert (
        captured["bot_token"]
        == "test-token"
    )

    assert (
        captured["chat_id"]
        == "123456"
    )

    assert (
        "PVR"
        in captured["message"]
    )

    assert (
        "19:30"
        in captured["message"]
    )

    assert (
        "Available tickets: 5"
        in captured["message"]
    )


def test_notify_handles_telegram_request_failure(
    monkeypatch,
    caplog,
):
    monkeypatch.setenv(
        "TELEGRAM_BOT_TOKEN",
        "test-token",
    )

    monkeypatch.setenv(
        "TELEGRAM_CHAT_ID",
        "123456",
    )

    def fake_send(
        bot_token,
        chat_id,
        message,
    ):
        raise requests.RequestException(
            "Network failure"
        )

    monkeypatch.setattr(
        "app.notifications.send_telegram_message",
        fake_send,
    )

    notify(
        {
            "PVR": {
                "19:30": {
                    "current_tickets": 5,
                }
            }
        }
    )

    assert (
        "Failed to send Telegram notification"
        in caplog.text
    )
