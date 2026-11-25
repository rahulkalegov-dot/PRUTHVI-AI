import pytest

from pruthvi_ai import telegram_bot


@pytest.fixture
def telegram_config(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")


def make_update(text, chat_id=12345):
    return {
        "message": {
            "text": text,
            "chat": {"id": chat_id}
        }
    }


def test_start_command(telegram_config, monkeypatch):
    sent = []
    monkeypatch.setattr(
        telegram_bot,
        "_send_reply",
        lambda message: (sent.append(message) or True, "OK")
    )

    result = telegram_bot.handle_update(make_update("/start"))

    assert result is True
    assert "PAPER ONLY" in sent[0]


def test_help_command(telegram_config, monkeypatch):
    sent = []
    monkeypatch.setattr(
        telegram_bot,
        "_send_reply",
        lambda message: (sent.append(message) or True, "OK")
    )

    assert telegram_bot.handle_update(make_update("/help")) is True
    assert "/status" in sent[0]


def test_status_command(telegram_config, monkeypatch):
    sent = []
    monkeypatch.setattr(
        telegram_bot,
        "_send_reply",
        lambda message: (sent.append(message) or True, "OK")
    )

    result = telegram_bot.handle_update(
        make_update("/status"),
        status_provider=lambda: {"status": "OK"}
    )

    assert result is True
    assert "status: OK" in sent[0]
    assert "PAPER ONLY" in sent[0]


def test_report_command(telegram_config, monkeypatch):
    sent = []
    monkeypatch.setattr(
        telegram_bot,
        "_send_reply",
        lambda message: (sent.append(message) or True, "OK")
    )

    result = telegram_bot.handle_update(
        make_update("/report"),
        report_provider=lambda: "Daily report test"
    )

    assert result is True
    assert sent[0] == "Daily report test"


def test_report_without_provider(telegram_config, monkeypatch):
    sent = []
    monkeypatch.setattr(
        telegram_bot,
        "_send_reply",
        lambda message: (sent.append(message) or True, "OK")
    )

    assert telegram_bot.handle_update(make_update("/report")) is True
    assert "not connected yet" in sent[0]


def test_unknown_command(telegram_config, monkeypatch):
    sent = []
    monkeypatch.setattr(
        telegram_bot,
        "_send_reply",
        lambda message: (sent.append(message) or True, "OK")
    )

    assert telegram_bot.handle_update(make_update("/unknown")) is True
    assert "Unknown command" in sent[0]


def test_unauthorized_chat_is_rejected(telegram_config, monkeypatch):
    monkeypatch.setattr(
        telegram_bot,
        "_send_reply",
        lambda message: (True, "OK")
    )

    assert telegram_bot.handle_update(
        make_update("/start", chat_id=99999)
    ) is False


def test_empty_message_is_rejected(telegram_config, monkeypatch):
    assert telegram_bot.handle_update(make_update("")) is False


def test_missing_configuration(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    with pytest.raises(RuntimeError):
        telegram_bot.handle_update(make_update("/start"))