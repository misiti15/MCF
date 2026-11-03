"""Recorded live inputs for the replay (research only; the live code and mcf/replay are not changed).

For one session, from the five live journals (signals, run_id 1):
  quotes  symbol -> {poll minute k: (bid, ask, age_s)}  every NBBO the live runner journaled at its quote check
          (submitted entries and realism skips carry bid/ask/spread_bps/quote_age_s in signals.info)
  borrow  account -> symbol -> bool  the live runner's own can_short answer that session (cached per session):
          False after a 'not shortable/ETB' skip, True after a submitted short; other accounts' answers as fallback

RecordedQuotes replaces mcf.replay.broker.SimDataClient inside mcf.replay.harness (monkeypatch, per process):
  mode "exact"   the quote live saw at the same symbol + poll minute (k +- 1), else the nearest same-day recorded
                 quote of the symbol within NEAR_MIN minutes (bid/ask re-centred on the replay's last close, live
                 spread_bps kept), else the old synthetic draw
  mode "near"    leave-one-minute-out: only recorded quotes of the symbol at least 2 minutes away (what a NEW setup
                 would get: it has no live signal at its own minute), else the draw
Counters of the source used per quote are kept in RecordedQuotes.used. Educational only - not financial advice."""
from __future__ import annotations

import json
import sqlite3
from datetime import timedelta
from pathlib import Path

import pandas as pd

from mcf.replay.broker import NS, SimDataClient

BRANCH = {"primary": "mcf-data", "testing": "mcf-data-testing", "testing2": "mcf-data-testing2",
          "graveyard": "mcf-data-graveyard", "gen": "mcf-data-gen"}
NEAR_MIN = 30


def build(day: str, jdir: Path) -> dict:
    """Cached as <jdir>/rec_<day>.pkl (so the journal copies can be deleted once every session is cached)."""
    import pickle

    cp = Path(jdir) / f"rec_{day}.pkl"
    if cp.exists():
        return pickle.loads(cp.read_bytes())
    out = _build(day, Path(jdir))
    tmp = cp.with_suffix(".tmp")
    tmp.write_bytes(pickle.dumps(out))
    tmp.replace(cp)
    return out


def _build(day: str, jdir: Path) -> dict:
    t0 = pd.Timestamp(f"{day} 09:30", tz="America/New_York")
    quotes: dict[str, dict[int, tuple]] = {}
    borrow: dict[str, dict[str, bool]] = {}
    for acct, br in BRANCH.items():
        con = sqlite3.connect(str(jdir / f"{br}.db"))
        rows = con.execute("SELECT ts, symbol, side, status, reason, info FROM signals WHERE run_id=1 AND day=? "
                           "ORDER BY ts", (day,)).fetchall()
        con.close()
        b = borrow.setdefault(acct, {})
        for ts, sym, side, status, reason, info in rows:
            try:
                inf = json.loads(info) if info else {}
            except ValueError:
                inf = {}
            if "bid" in inf and "ask" in inf:
                k = int((pd.Timestamp(ts).tz_convert("America/New_York") - t0) // pd.Timedelta(minutes=1))
                quotes.setdefault(sym, {}).setdefault(k, (float(inf["bid"]), float(inf["ask"]),
                                                           float(inf.get("quote_age_s") or 1.0)))
            if reason == "not shortable/ETB":
                b.setdefault(sym, False)
            elif status == "submitted" and int(side or 0) == -1:
                b.setdefault(sym, True)
    return {"quotes": quotes, "borrow": borrow}


def borrow_flags(rec: dict, account: str, base: dict | None) -> tuple[dict, dict]:
    """(symbol -> (shortable, etb)) = the session universe.csv flags, overridden by the other accounts' recorded
    answers, overridden by this account's own recorded answers. Returns (flags, counts)."""
    out = dict(base or {})
    n = {"own": 0, "other": 0}
    for ac, b in rec["borrow"].items():
        if ac == account:
            continue
        for s, v in b.items():
            out[s] = (v, v)
            n["other"] += 1
    for s, v in rec["borrow"].get(account, {}).items():
        out[s] = (v, v)
        n["own"] += 1
    return out, n


class RecordedQuotes(SimDataClient):
    rec: dict = {}
    mode = "exact"
    used: dict = {}

    def _pick(self, sym: str, k: int):
        q = self.rec.get(sym)
        if not q:
            return None, "draw"
        if self.mode == "exact":
            for dk in (0, -1, 1):
                if k + dk in q:
                    return q[k + dk], "exact"
            cand = [kk for kk in q if abs(kk - k) <= NEAR_MIN]
        else:
            cand = [kk for kk in q if 2 <= abs(kk - k) <= NEAR_MIN]
        if not cand:
            return None, "draw"
        kk = min(cand, key=lambda x: (abs(x - k), x))
        return q[kk], "near"

    def _bps(self, sym: str, k: int) -> float:
        v, _ = self._pick(sym, k)
        if v is None:
            return super()._bps(sym, k)
        bid, ask, _ = v
        return (ask - bid) / ((ask + bid) / 2) * 1e4

    def get_stock_latest_quote(self, req):
        syms = req.symbol_or_symbols
        syms = [syms] if isinstance(syms, str) else list(syms)
        k = self.mkt.minute(self.clock.now)
        out = {}
        for s in syms:
            v, src = self._pick(s, k)
            self.used[src] = self.used.get(src, 0) + 1
            if v is None or src == "near":
                px = self.mkt.last_close(s, k)
                if px is None:
                    raise KeyError(s)
                bps = super()._bps(s, k) if v is None else (v[1] - v[0]) / ((v[1] + v[0]) / 2) * 1e4
                half = max(0.005, px * bps / 2e4)
                bid, ask, age = round(px - half, 4), round(px + half, 4), 1.0
            else:
                bid, ask, age = v
            out[s] = NS(bid_price=bid, ask_price=ask,
                        timestamp=(self.clock.now - timedelta(seconds=age)).tz_convert("UTC").to_pydatetime())
        return out
