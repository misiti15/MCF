"""Send "your drop is ready" messages.

Providers, cheapest first:
- console: prints. Development.
- email:   any SMTP server. Free tiers exist (Gmail app password for testing, Brevo, Resend).
- sms:     Twilio. Paid per message; needs a registered number before US carriers deliver it.
- push:    web push to the installed app. Phase 2 (needs VAPID keys and a service worker).

Secrets come from environment variables only. Never log them.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import smtplib
from email.message import EmailMessage

import httpx

from . import config

GSM7 = set("@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà")


def sms_segments(text: str) -> int:
    """Carriers bill per segment: 160 plain characters, or only 70 if any emoji/curly quote sneaks in."""
    plain = all(c in GSM7 for c in text)
    single, multi = (160, 153) if plain else (70, 67)
    return 1 if len(text) <= single else -(-len(text) // multi)


def drop_message(user: dict, topic_names: list[str], link: str) -> str:
    topics = " + ".join(topic_names[:2]) or "your topics"
    n = user["drop_size"]
    return f"{config.BRAND}: {n} new questions on {topics}. {link} Reply STOP to opt out."


class Console:
    name = "console"

    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    def send(self, user: dict, text: str) -> str:
        to = user.get("phone") or user.get("email") or user["id"]
        self.sent.append((to, text))
        print(f"[console] to {to}: {text}")
        return "console"


class Email:
    name = "email"

    def __init__(self):
        self.host = os.environ["SMTP_HOST"]
        self.port = int(os.environ.get("SMTP_PORT", "587"))
        self.user = os.environ.get("SMTP_USER")
        self.password = os.environ.get("SMTP_PASSWORD")
        self.sender = os.environ.get("SMTP_FROM", self.user)

    def send(self, user: dict, text: str) -> str:
        if not user.get("email"):
            raise ValueError("user has no email")
        msg = EmailMessage()
        msg["From"], msg["To"] = self.sender, user["email"]
        msg["Subject"] = f"Your {config.BRAND} drop is ready"
        msg.set_content(text.replace(" Reply STOP to opt out.", "\n\nTurn these off any time in Settings."))
        with smtplib.SMTP(self.host, self.port, timeout=20) as s:
            s.starttls()
            if self.user:
                s.login(self.user, self.password)
            s.send_message(msg)
        return "sent"


class TwilioSMS:
    name = "sms"
    API = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"

    def __init__(self, client: httpx.Client | None = None):
        self.sid = os.environ["TWILIO_ACCOUNT_SID"]
        self.token = os.environ["TWILIO_AUTH_TOKEN"]
        # Either a Messaging Service (recommended: handles STOP/HELP) or a single number.
        self.service = os.environ.get("TWILIO_MESSAGING_SERVICE_SID")
        self.sender = os.environ.get("TWILIO_FROM")
        self.client = client or httpx.Client(timeout=20)

    def send(self, user: dict, text: str) -> str:
        if not user.get("phone"):
            raise ValueError("user has no phone number")
        if not user.get("sms_opt_in"):
            raise PermissionError("user has not opted in to texts")
        data = {"To": user["phone"], "Body": text}
        data["MessagingServiceSid" if self.service else "From"] = self.service or self.sender
        r = self.client.post(self.API.format(sid=self.sid), data=data, auth=(self.sid, self.token))
        r.raise_for_status()
        return r.json()["sid"]


def twilio_signature_ok(auth_token: str, url: str, params: dict[str, str], signature: str) -> bool:
    """Check an inbound Twilio webhook really came from Twilio (their documented HMAC-SHA1 scheme)."""
    payload = url + "".join(k + params[k] for k in sorted(params))
    digest = hmac.new(auth_token.encode(), payload.encode(), hashlib.sha1).digest()
    return hmac.compare_digest(base64.b64encode(digest).decode(), signature or "")


def provider_for(user: dict, console: Console | None = None):
    """Pick the provider for a user's channel, falling back to console when it isn't configured."""
    chan = user["channel"]
    try:
        if chan == "sms" and os.environ.get("TWILIO_ACCOUNT_SID"):
            return TwilioSMS()
        if chan == "email" and os.environ.get("SMTP_HOST"):
            return Email()
    except KeyError:
        pass
    return console or Console()
