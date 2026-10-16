import base64
import hashlib
import hmac
from datetime import datetime, timezone

import httpx

from trivia import db, notify, scheduler


def test_drop_text_fits_one_sms_segment(user):
    text = notify.drop_message(user, ["Cincinnati Reds", "Marshall University"], "https://example.app/d/" + "x" * 32)
    assert notify.sms_segments(text) == 1
    assert "STOP" in text


def test_emoji_costs_more_segments():
    assert notify.sms_segments("a" * 100) == 1
    assert notify.sms_segments("a" * 100 + "🔥") == 2


def test_twilio_send(monkeypatch, user):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC123")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "secret")
    monkeypatch.setenv("TWILIO_FROM", "+15550001111")
    seen = {}

    def handler(req):
        seen["url"], seen["body"] = str(req.url), req.content.decode()
        return httpx.Response(201, json={"sid": "SM1"})

    sms = notify.TwilioSMS(httpx.Client(transport=httpx.MockTransport(handler)))
    u = user | {"phone": "+13045551234", "sms_opt_in": 1}
    assert sms.send(u, "hi") == "SM1"
    assert "Accounts/AC123/Messages.json" in seen["url"] and "To=%2B13045551234" in seen["body"]


def test_twilio_refuses_without_opt_in(monkeypatch, user):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC123")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "secret")
    sms = notify.TwilioSMS(httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500))))
    try:
        sms.send(user | {"phone": "+13045551234", "sms_opt_in": 0}, "hi")
        raise AssertionError("should refuse")
    except PermissionError:
        pass


def test_twilio_signature():
    params = {"Body": "STOP", "From": "+13045551234"}
    url = "https://example.app/api/sms/inbound"
    sig = base64.b64encode(hmac.new(b"tok", (url + "BodySTOPFrom+13045551234").encode(), hashlib.sha1).digest()).decode()
    assert notify.twilio_signature_ok("tok", url, params, sig)
    assert not notify.twilio_signature_ok("tok", url, params, "nope")


def test_scheduler_sends_once_when_due(con):
    u = db.create_user(con, ["reds"], send_days=["Fri"], send_time="12:15", tz="America/New_York", channel="push")
    early = datetime(2026, 10, 16, 15, 0, tzinfo=timezone.utc)    # 11:00 ET Friday
    late = datetime(2026, 10, 16, 16, 30, tzinfo=timezone.utc)    # 12:30 ET Friday
    console = notify.Console()
    assert scheduler.run(con, early, console=console) == []
    assert len(scheduler.run(con, late, console=console)) == 1
    assert scheduler.run(con, late, console=console) == []         # not twice
    assert u["token"] in console.sent[0][1]
