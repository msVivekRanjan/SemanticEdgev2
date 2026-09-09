"""
nvr/management/commands/run_openclaw_bot.py
-------------------------------------------
Django management command to run the SemanticEdge OpenClaw Telegram Bot daemon.
Acts as the exclusive Telegram update consumer, passing natural language surveillance
requests to OpenClaw backend NLP engine and executing Django SQLite queries.

Usage:
    python manage.py run_openclaw_bot
"""

import logging
import time
import requests
from django.core.management.base import BaseCommand
from nvr.openclaw import OpenClawAssistant, get_telegram_config, TELEGRAM_API_BASE

logger = logging.getLogger("semanticedge.openclaw")


class Command(BaseCommand):
    help = "Runs the SemanticEdge Telegram Bot long-polling daemon (sole Telegram consumer)."

    def handle(self, *args, **options):
        token, default_chat_id = get_telegram_config()
        if not token:
            self.stdout.write(
                self.style.WARNING(
                    "TELEGRAM_BOT_TOKEN is not configured in .env. Please set TELEGRAM_BOT_TOKEN to start the bot."
                )
            )
            return

        # 1. Verify Bot identity via Telegram getMe
        bot_username = "UnknownBot"
        try:
            me_resp = requests.get(f"{TELEGRAM_API_BASE}/bot{token}/getMe", timeout=10)
            if me_resp.ok:
                bot_data = me_resp.json().get("result", {})
                bot_username = f"@{bot_data.get('username', 'bot')}"
            else:
                self.stdout.write(self.style.WARNING(f"Telegram getMe check failed: {me_resp.text}"))
        except Exception as err:
            self.stdout.write(self.style.WARNING(f"Unable to connect to Telegram getMe: {err}"))

        # 2. Ensure Webhook is cleared so long-polling operates unimpeded
        try:
            wh_resp = requests.get(f"{TELEGRAM_API_BASE}/bot{token}/getWebhookInfo", timeout=10)
            if wh_resp.ok:
                wh_url = wh_resp.json().get("result", {}).get("url", "")
                if wh_url:
                    self.stdout.write(f"Clearing existing webhook: {wh_url}...")
                    requests.post(f"{TELEGRAM_API_BASE}/bot{token}/deleteWebhook", timeout=10)
        except Exception:
            pass

        self.stdout.write(
            self.style.SUCCESS(
                f"===================================================================\n"
                f"  [POLLER] SemanticEdge Telegram Bot Poller Active\n"
                f"  Bot: {bot_username} (Token: ...{token[-8:] if len(token) > 8 else token})\n"
                f"  Default Chat ID: {default_chat_id or 'Auto-detect from incoming'}\n"
                f"  Role: Single Telegram Update Consumer -> OpenClaw Backend NLP\n"
                f"==================================================================="
            )
        )

        assistant = OpenClawAssistant(bot_token=token, chat_id=default_chat_id)
        last_update_id = 0

        while True:
            try:
                url = f"{TELEGRAM_API_BASE}/bot{token}/getUpdates"
                params = {"offset": last_update_id + 1, "timeout": 20}
                resp = requests.get(url, params=params, timeout=25)

                if resp.status_code == 409:
                    self.stdout.write(
                        self.style.ERROR(
                            "[CONFLICT] Conflict detected (HTTP 409): Another process is polling this Telegram bot!\n"
                            "Ensure OpenClaw gateway channel is disabled and no other bot instances are running."
                        )
                    )
                    time.sleep(5)
                    continue

                if not resp.ok:
                    time.sleep(3)
                    continue

                data = resp.json()
                updates = data.get("result", [])
                for update in updates:
                    update_id = update.get("update_id", 0)
                    if update_id > last_update_id:
                        last_update_id = update_id

                    message = update.get("message", {})
                    text = message.get("text", "")
                    sender_chat_id = str(message.get("chat", {}).get("id", ""))
                    if text and sender_chat_id:
                        assistant.handle_incoming_message(text, chat_id=sender_chat_id)

            except KeyboardInterrupt:
                self.stdout.write(self.style.SUCCESS("\n[SemanticEdge] Telegram bot poller gracefully stopped."))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[SemanticEdge] Poller error: {e}"))
                time.sleep(3)
