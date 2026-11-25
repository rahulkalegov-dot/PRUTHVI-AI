
"""PRUTHVI AI Telegram command handler.

Supports /start, /status, /report and /help.
Paper-trading monitoring only. No order execution.
"""

import os
import time
import requests

from .telegram_reporter import send_telegram_report


TELEGRAM_API = "https://api.telegram.org"


def _get_config():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise RuntimeError("Telegram configuration missing")

    return token, str(chat_id)


def _send_reply(message):
    return send_telegram_report(message)


def _get_system_status():
    from .main import run_system_check

    return run_system_check()


def handle_update(update, status_provider=None, report_provider=None):
    """Process one Telegram update."""

    _, allowed_chat_id = _get_config()

    message = update.get("message", {})
    chat = message.get("chat", {})
    incoming_chat_id = str(chat.get("id", ""))

    # Accept commands only from the configured Telegram chat.
    if incoming_chat_id != allowed_chat_id:
        return False

    text = message.get("text", "").strip()

    if not text:
        return False

    command = text.split()[0].split("@")[0].lower()

    if command == "/start":
        reply = (
            "Welcome to PRUTHVI AI!\n\n"
            "NSE NIFTY 50 monitoring system.\n"
            "Mode: PAPER ONLY\n\n"
            "Available commands:\n"
            "/start - Start the bot\n"
            "/status - Check system status\n"
            "/report - Get daily report\n"
            "/help - Show commands"
        )

    elif command == "/help":
        reply = (
            "PRUTHVI AI COMMANDS\n\n"
            "/start - Start the bot\n"
            "/status - Check system status\n"
            "/report - Get daily report\n"
            "/help - Show commands"
        )

    elif command == "/status":
        try:
            provider = status_provider or _get_system_status
            status = provider()

            if isinstance(status, dict):
                reply = "PRUTHVI AI SYSTEM STATUS\n"
                reply += "\n".join(
                    f"{key}: {value}"
                    for key, value in status.items()
                )
            else:
                reply = f"PRUTHVI AI SYSTEM STATUS\n{status}"

            reply += "\n\nMode: PAPER ONLY"

        except Exception:
            reply = "Unable to retrieve system status."

    elif command == "/report":
        if report_provider is None:
            reply = (
                "Daily report provider is not connected yet.\n"
                "Please check the scheduled daily report."
            )
        else:
            try:
                reply = report_provider()

                if not isinstance(reply, str) or not reply.strip():
                    reply = "No daily report is currently available."

            except Exception:
                reply = "Unable to retrieve the daily report."

    else:
        reply = "Unknown command. Send /help to see available commands."

    success, _ = _send_reply(reply)
    return success


def run_telegram_bot():
    """Continuously receive and process Telegram commands."""

    token, _ = _get_config()

    url = f"{TELEGRAM_API}/bot{token}/getUpdates"
    offset = None

    while True:
        try:
            params = {
                "timeout": 25,
                "allowed_updates": '["message"]',
            }

            if offset is not None:
                params["offset"] = offset

            response = requests.get(
                url,
                params=params,
                timeout=35,
            )

            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                raise RuntimeError("Telegram update request failed")

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                try:
                    handle_update(update)
                except Exception:
                    # Continue processing subsequent updates.
                    continue

        except requests.HTTPError as error:
            if error.response is not None and error.response.status_code == 409:
                raise RuntimeError(
                    "Telegram webhook is active. "
                    "Polling cannot run until the webhook is removed."
                ) from None

            time.sleep(5)

        except (requests.RequestException, ValueError):
            time.sleep(5)


if __name__ == "__main__":
    run_telegram_bot()
