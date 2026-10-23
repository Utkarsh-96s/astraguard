"""Listen for incoming Telegram messages on @Astrixobot and reply."""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

# Load .env if present
env_file = Path(__file__).resolve().parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BOT_NAME = os.getenv("TELEGRAM_BOT_USERNAME", "AstraGuardBot")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def main() -> None:
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set in .env")
        sys.exit(1)
    print(f"Listening for incoming messages on @{BOT_NAME} (timeout 60s)...")
    start_time = time.time()
    while time.time() - start_time < 60:
        try:
            req = urllib.request.Request(f"{BASE_URL}/getUpdates?timeout=5")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                updates = data.get("result", [])
                if updates:
                    last_update = updates[-1]
                    msg = last_update.get("message") or {}
                    chat = msg.get("chat") or {}
                    chat_id = chat.get("id")
                    first_name = chat.get("first_name") or "Operator"
                    text = msg.get("text") or ""
                    print(f"\n[RECEIVED] Message from {first_name} (Chat ID: {chat_id}): '{text}'")

                    # Send confirmation message
                    reply_text = (
                        "🛰️ <b>ASTRA-GUARD Mission Control Connected!</b>\n\n"
                        f"Operator: <b>{first_name}</b>\n"
                        f"Chat ID: <code>{chat_id}</code>\n\n"
                        "Your Telegram account is now linked to <b>ASTRA-GUARD</b> for mission collision alerts & HITL authorization."
                    )
                    reply_payload = json.dumps({
                        "chat_id": chat_id,
                        "text": reply_text,
                        "parse_mode": "HTML",
                    }).encode("utf-8")
                    reply_req = urllib.request.Request(
                        f"{BASE_URL}/sendMessage",
                        data=reply_payload,
                        headers={"Content-Type": "application/json"},
                    )
                    with urllib.request.urlopen(reply_req, timeout=10) as reply_resp:
                        reply_data = json.loads(reply_resp.read().decode())
                        if reply_data.get("ok"):
                            print(f"[SUCCESS] Reply dispatched to {first_name} (Chat ID: {chat_id})")
                            return
        except Exception as e:  # noqa: BLE001
            print(f"Error: {e}")
        time.sleep(1)

    print("Timeout reached without receiving any new update.")

if __name__ == "__main__":
    main()
