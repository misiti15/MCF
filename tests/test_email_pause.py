"""Owner 2026-10-27: all MCF notification emails on hold (report.email_enabled: false)."""

from mcf.report import brief


def test_emails_paused_by_default_config(monkeypatch):
    assert brief.emails_paused() is True
    sent = []
    monkeypatch.setattr(brief.smtplib, "SMTP_SSL", lambda *a, **k: sent.append(1))
    monkeypatch.setenv("MCF_SMTP_USER", "x"); monkeypatch.setenv("MCF_SMTP_PASSWORD", "y")
    brief.send_email("s", "t", None, "to@example.com")
    assert sent == []


def test_eod_email_paused(monkeypatch):
    from mcf.report import eod
    monkeypatch.setenv("MCF_SMTP_USER", "x"); monkeypatch.setenv("MCF_SMTP_PASSWORD", "y")
    monkeypatch.setattr(eod.smtplib, "SMTP_SSL", lambda *a, **k: (_ for _ in ()).throw(AssertionError("sent")))
    assert eod.send({}, "to@example.com", "2026-10-27") is False
