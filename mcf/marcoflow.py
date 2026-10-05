"""Read-only client for MarcoFlow's public API (see MARCOFLOW_CONTEXT.md).

SAFETY: only the allow-listed GET endpoints below can be called. The tick, heartbeat, daily-brief
and other secret-protected endpoints make MarcoFlow scan/trade/email and must never be called
from MCF — this client has no way to send a POST, auth header, or secret.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

BASE = "https://marcoflow.abacusai.app"
ALLOWED = [
    r"/api/health", r"/api/observations", r"/api/performance", r"/api/scorecard",
    r"/api/paper/status", r"/api/review", r"/api/simulations", r"/api/insights", r"/api/screener",
    r"/api/heat-tracker/[A-Za-z.\-]{1,12}", r"/api/stocks/[A-Za-z.\-]{1,12}",
]
FORBIDDEN_PARAMS = {"key", "secret", "token", "send"}


def get(path: str, **params) -> dict:
    if not any(re.fullmatch(p, path) for p in ALLOWED):
        raise PermissionError(f"{path} is not an allow-listed read-only MarcoFlow endpoint")
    if FORBIDDEN_PARAMS & {k.lower() for k in params}:
        raise PermissionError("secret/action parameters are not allowed")
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json", "User-Agent": "MCF-readonly/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())
