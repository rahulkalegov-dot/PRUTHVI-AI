from pruthvi_ai.telegram_reporter import send_telegram_report


def test_missing_telegram_configuration(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    success, message = send_telegram_report("Test report")

    assert success is False
    assert message == "Telegram configuration missing"


def test_empty_message(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")

    success, message = send_telegram_report("")

    assert success is False
    assert message == "Report message is empty"