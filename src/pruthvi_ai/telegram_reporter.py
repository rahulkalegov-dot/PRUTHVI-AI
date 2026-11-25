import os
import requests


def send_telegram_report(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return False, "Telegram configuration missing"

    if not message:
        return False, "Report message is empty"

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": message
            },
            timeout=15
        )

        response.raise_for_status()
        result = response.json()

        if not result.get("ok"):
            return False, "Telegram rejected the message"

        return True, "Report sent"

    except requests.RequestException:
        return False, "Telegram connection failed"
    except ValueError:
        return False, "Invalid Telegram response"