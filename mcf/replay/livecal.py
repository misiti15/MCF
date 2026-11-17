"""Calibrated session replay (research/replay_cal): the replay made to see each session the way the live runner of that
account saw it. Opt-in (`python -m mcf.replay run ... --live-cal PARAMS.json`); the default replay is unchanged.

What it adds on top of mcf.replay.harness (each item closes a measured live-vs-replay gap, research/replay_cal/NOTES.md):
  polls      the account's live poll log of that day (data branch polls/<day>/*.jsonl.gz, from 2026-10-22): polls run
             at the live poll times (outages and late polls = no decisions in between), the clock moves on by the
             poll's fetch time before any decision, quote or order, and a bar that had not arrived at that poll
             (poll log `late`: symbol -> its last bar at that poll) is hidden from that poll
  quotes     the quote live actually used for a decision when the account recorded it (data branch
             quotes/<day>/*.jsonl.gz, runner quote_log_dir, from 2026-11-18): same symbol and same poll (decision time to
             the second) -> live's bid / ask / quote time; otherwise the spread per symbol and time of day from the
             model fitted on TRAIN sessions only (median, deterministic), so the spread / spread-vs-stop checks fire
             where live mostly fired. stats.live_cal.quotes_real / quotes_modelled count each source (params
             "recorded_quotes": false turns the recorded quotes off)
  fills      market orders fill inside the minute bar at open + w x (close - open), w fitted on TRAIN live fills
  shortable  shortable / easy-to-borrow flags from that session's universe.csv on the data branch (not today's)
Without a poll log for the day the session runs on the default cadence (and says so in stats.inputs).
Educational only - not financial advice."""

from __future__ import annotations

import gzip
import io
import json
import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from . import store

NY = "America/New_York"


@lru_cache(maxsize=64)
def poll_log(branch: str, day: str) -> tuple:
    """The live poll records of one account and day, sorted by time: (ts ET, fetch seconds, {symbol: last bar HHMM})."""
    r = subprocess.run(["git", "-C", str(store.ROOT), "ls-tree", "-r", "--name-only", branch, f"polls/{day}"],
                       capture_output=True, text=True)
    out = []
    for f in sorted(r.stdout.split()):
        b = subprocess.run(["git", "-C", str(store.ROOT), "show", f"{branch}:{f}"], capture_output=True).stdout
        try:
            txt = gzip.decompress(b).decode()
        except OSError:
            continue
        for line in txt.splitlines():
            try:
                x = json.loads(line)
            except ValueError:
                continue
            late = {}
            for hhmm, syms in (x.get("late") or {}).items():
                for s in syms:
                    late[s] = hhmm
            out.append((pd.Timestamp(f"{day} {x['t']}", tz=NY), float(x.get("ms") or 0) / 1000.0, late))
    out.sort(key=lambda p: p[0])
    return tuple(out)


def _branch_chunks(branch: str, folder: str):
    """Decompressed text of each gzip chunk under `folder` on `branch`, in name order."""
    r = subprocess.run(["git", "-C", str(store.ROOT), "ls-tree", "-r", "--name-only", branch, folder],
                       capture_output=True, text=True)
    for f in sorted(r.stdout.split()):
        b = subprocess.run(["git", "-C", str(store.ROOT), "show", f"{branch}:{f}"], capture_output=True).stdout
        try:
            yield gzip.decompress(b).decode()
        except OSError:
            continue


def parse_quotes(lines) -> dict:
    """(symbol, decision time ET to the second) -> (bid, ask, quote time UTC or None, spread bps) from recorded quote
    lines (runner _record_quote). Decisions taken before any quote fetch (bid null) are left out."""
    out = {}
    for line in lines:
        try:
            x = json.loads(line)
            bid, ask = x.get("bid"), x.get("ask")
            if bid is None or ask is None or not (float(bid) > 0 and float(ask) >= float(bid)):
                continue
            t = pd.Timestamp(x["t"]).tz_convert(NY).floor("s")
            qts = pd.Timestamp(x["qts"]) if x.get("qts") else None
            bps = x.get("bps")
            if bps is None:
                mid = (float(bid) + float(ask)) / 2
                bps = (float(ask) - float(bid)) / mid * 1e4
            out[(str(x["sym"]), t.value)] = (float(bid), float(ask), qts, float(bps))
        except (ValueError, KeyError, TypeError, AttributeError):
            continue
    return out


@lru_cache(maxsize=64)
def quote_log(branch: str, day: str) -> dict:
    """The quotes the live runner of one account recorded at its decisions that day (see parse_quotes)."""
    lines = []
    for txt in _branch_chunks(branch, f"quotes/{day}"):
        lines.extend(txt.splitlines())
    return parse_quotes(lines)


@lru_cache(maxsize=64)
def shortable_on(branch: str, day: str) -> dict | None:
    """symbol -> (shortable, easy_to_borrow) from the universe.csv committed on or before `day` on the data branch."""
    r = subprocess.run(["git", "-C", str(store.ROOT), "log", "-1", f"--until={day} 23:59", "--format=%H", branch, "--",
                        "universe.csv"], capture_output=True, text=True)
    sha = r.stdout.strip()
    if not sha:
        return None
    csv = subprocess.run(["git", "-C", str(store.ROOT), "show", f"{sha}:universe.csv"], capture_output=True).stdout
    try:
        u = pd.read_csv(io.BytesIO(csv), usecols=["symbol", "shortable", "easy_to_borrow"])
    except (ValueError, pd.errors.ParserError):
        return None
    return {str(s): (bool(a), bool(b)) for s, a, b in zip(u.symbol, u.shortable, u.easy_to_borrow)}


def bucket(k: int) -> str:
    """Time-of-day bucket of session minute k (0 = 09:30)."""
    return "open" if k < 15 else ("am" if k < 90 else ("mid" if k < 330 else "close"))


def fit_spreads(journals: list[str | Path], until: str, since: str = "2026-10-06") -> dict:
    """Spread table from live journals, TRAIN sessions only (since <= day <= until): per symbol median bps, a time-of-day
    factor per bucket (median of spread / the symbol's median), and the all-symbol median per bucket."""
    import sqlite3

    rows = []
    for p in journals:
        con = sqlite3.connect(str(p))
        q = con.execute("SELECT symbol, ts, info FROM signals WHERE run_id=1 AND day>=? AND day<=? AND info LIKE "
                        "'%spread_bps%'", (since, until)).fetchall()
        con.close()
        for sym, ts, info in q:
            try:
                v = float(json.loads(info)["spread_bps"])
                t = pd.Timestamp(ts).tz_convert(NY)
            except (ValueError, KeyError, TypeError):
                continue
            k = (t.hour * 60 + t.minute) - 570
            rows.append((sym, bucket(max(0, k)), v))
    df = pd.DataFrame(rows, columns=["symbol", "bucket", "bps"])
    med = df.groupby("symbol")["bps"].median()
    df["rel"] = df["bps"] / df["symbol"].map(med).replace(0, np.nan)
    fac = df.groupby("bucket")["rel"].median().to_dict()
    sym_b = df.groupby(["symbol", "bucket"])["bps"].median()
    n_b = df.groupby(["symbol", "bucket"])["bps"].size()
    per = {}
    for (s, b), v in sym_b.items():
        if n_b[(s, b)] >= 3:
            per.setdefault(s, {})[b] = round(float(v), 2)
    return {"since": since, "until": until, "n": int(len(df)), "symbol": {s: round(float(v), 2) for s, v in med.items()},
            "symbol_bucket": per, "factor": {b: round(float(v), 3) for b, v in fac.items()},
            "all": {b: round(float(v), 2) for b, v in df.groupby("bucket")["bps"].median().items()}}


def spread_features(adv: float, px: float, bar, k: int) -> list[float]:
    """Regressors of log spread (bps): 1, log ADV, log price, log range bps and log dollar volume of the last minute bar,
    first 30 minutes flag (fit_spread_model; the symbol's log median spread is appended when it has a table entry)."""
    o, h, lo, c, v = (float(x) for x in bar[:5])
    rng = (h - lo) / c * 1e4 if c > 0 else 1.0
    return [1.0, float(np.log(max(adv, 1.0))), float(np.log(max(px, 0.01))), float(np.log(max(rng, 1.0))),
            float(np.log(max(v * c, 1e3))), 1.0 if k < 30 else 0.0]


def fit_spread_model(rows: pd.DataFrame) -> dict:
    """OLS of log live spread on spread_features (+ log table median for known symbols). rows: lb, x (list), lmed."""
    out = {}
    for name, sub in (("known", rows[rows["lmed"].notna()]), ("unknown", rows)):
        if len(sub) < 50:
            continue
        X = np.array([list(x) + ([m] if name == "known" else []) for x, m in zip(sub["x"], sub["lmed"])])
        out[name] = [round(float(b), 5) for b in np.linalg.lstsq(X, sub["lb"].to_numpy(float), rcond=None)[0]]
        out[f"{name}_n"] = int(len(sub))
    return out


def fit_fill_weight(pairs: pd.DataFrame) -> float:
    """w minimising sum (live fill - half-spread side cost - (open + w (close - open)))^2 over live market entries.
    pairs: columns fill, open, close, side, half (half-spread in price). Fills more than 1% from the bar open (stale or
    re-priced orders) are left out: a handful of them otherwise decides the fit."""
    pairs = pairs[((pairs["fill"] - pairs["open"]).abs() / pairs["open"]) < 0.01]
    y = pairs["fill"] - pairs["side"] * pairs["half"] - pairs["open"]
    x = pairs["close"] - pairs["open"]
    den = float((x * x).sum())
    return 0.0 if den <= 0 else float(np.clip((x * y).sum() / den, 0.0, 1.0))


class Calibrator:
    """Hooks a harness.run_session (via its `hook`) to one account's live session."""

    def __init__(self, params: dict, branch: str, day):
        self.p, self.branch, self.day = params, branch, str(pd.Timestamp(str(day)).date())
        self.polls = poll_log(branch, self.day) if params.get("polls", True) else ()
        self.recorded = quote_log(branch, self.day) if params.get("recorded_quotes", True) else {}
        self.notes: dict = {}

    def _recorded_at(self, r, sym: str):
        """The quote live recorded for `sym` at the runner's current decision time (same poll, to the second)."""
        now = getattr(r, "_now", None)
        if not self.recorded or now is None:
            return None
        now = pd.Timestamp(now)
        now = (now if now.tzinfo else now.tz_localize(NY)).tz_convert(NY).floor("s")
        return self.recorded.get((sym, now.value))

    def _install_recorded(self, r, quotes):
        """Serve live's recorded quote where one exists for (symbol, decision time); the model otherwise. Fills of
        that minute use the recorded spread too (quotes._bps is what the replay broker reads)."""
        from types import SimpleNamespace as NS

        orig_get, orig_bps = quotes.get_stock_latest_quote, quotes._bps
        n = {"real": 0, "modelled": 0}
        self.notes["quotes_real"] = self.notes["quotes_modelled"] = 0

        def bps(s: str, k: int) -> float:
            rec = self._recorded_at(r, s)
            if rec is not None and quotes.mkt.minute(quotes.clock.now) == k:
                return rec[3]
            return orig_bps(s, k)

        def get_quote(req):
            syms = req.symbol_or_symbols
            syms = [syms] if isinstance(syms, str) else list(syms)
            out, rest = {}, []
            for s in syms:
                rec = self._recorded_at(r, s)
                if rec is None:
                    rest.append(s)
                    continue
                bid, ask, qts, _ = rec
                ts = (qts if qts is not None else quotes.clock.now - pd.Timedelta(seconds=1))
                out[s] = NS(bid_price=bid, ask_price=ask, timestamp=pd.Timestamp(ts).tz_convert("UTC").to_pydatetime())
            if rest:
                out.update(orig_get(NS(symbol_or_symbols=rest if len(rest) > 1 else rest[0])))
            n["real"] += len(syms) - len(rest)
            n["modelled"] += len(rest)
            self.notes["quotes_real"], self.notes["quotes_modelled"] = n["real"], n["modelled"]
            return out

        quotes._bps = bps
        quotes.get_stock_latest_quote = get_quote

    # quotes -----------------------------------------------------------------------------------------------------
    def _bps_fn(self, quotes, priors: dict | None = None):
        tab = self.p.get("spreads") or {}
        per, sym, fac, allb = tab.get("symbol_bucket", {}), tab.get("symbol", {}), tab.get("factor", {}), tab.get("all", {})
        model = self.p.get("spread_model") or {}
        orig = quotes._bps
        mkt = quotes.mkt

        def table(s: str, k: int) -> float | None:
            b = bucket(k)
            if s in per and b in per[s]:
                return per[s][b]
            if s in sym:
                return sym[s] * fac.get(b, 1.0)
            return None

        def bps(s: str, k: int) -> float:
            med = table(s, k)
            beta = model.get("known" if med is not None else "unknown")
            pr = (priors or {}).get(s)
            bar = mkt.bar(s, k - 1) if k > 0 else None
            px = mkt.last_close(s, k)
            if beta and pr is not None and bar is not None and px and getattr(pr, "adv", 0) > 0:
                x = spread_features(float(pr.adv), float(px), bar, k)
                if med is not None:
                    x.append(float(np.log(max(med, 0.5))))
                return float(np.exp(np.dot(beta, x)))
            if med is not None:
                return med
            b = bucket(k)
            if b in allb:
                return allb[b]
            return orig(s, k)
        return bps

    # fills ------------------------------------------------------------------------------------------------------
    def _market_fn(self, client):
        w = float(self.p.get("fill_w", 0.0))

        def market_now(o):
            k = max(client.mkt.minute(client.clock.now), client.done_min + 1)
            o._active = k
            bar = client.mkt.bar(o.symbol, k)
            if bar is not None and k < 390:
                px = float(bar[0]) + (w * (float(bar[3]) - float(bar[0])) if k == client.mkt.minute(client.clock.now)
                                      else 0.0)
                client._fill(o, px, k, "market")
        return market_now

    # polls ------------------------------------------------------------------------------------------------------
    def _install_polls(self, r, feed, clock):
        polls = self.polls
        times = np.array([p[0].value for p in polls], dtype=np.int64)
        flat = pd.Timestamp(f"{self.day} {r.flatten}", tz=NY) if hasattr(r, "flatten") else None
        open_t = pd.Timestamp(f"{self.day} 09:30:00", tz=NY)
        orig_sleep = r._sleep
        state = {"i": None}
        orig_fetch = feed.fetch

        def sleep(s):
            now = clock.now
            tgt = now + pd.Timedelta(seconds=float(s))
            if open_t <= tgt and (flat is None or now < flat):
                j = int(np.searchsorted(times, now.value, side="right"))
                nxt = pd.Timestamp(times[j], tz="UTC").tz_convert(NY) if j < len(times) else None
                if flat is not None and nxt is None:          # no live poll left: the flatten time
                    nxt = flat if flat > now else None
                if nxt is not None and nxt > now:
                    clock.now = nxt
                    state["i"] = j if j < len(times) and times[j] == nxt.value else None
                    return
            orig_sleep(s)
            state["i"] = None

        def fetch(now):
            i = state["i"]
            if i is None:
                return orig_fetch(now)
            ts, sec, late = polls[i]
            cut = now.floor("1min")
            hidden = 0
            out = {}
            for s, b in feed.bars.items():
                c = cut.value
                hh = late.get(s)
                if hh is not None:
                    lc = pd.Timestamp(f"{self.day} {hh[:2]}:{hh[2:]}", tz=NY) + pd.Timedelta(minutes=1)
                    c = min(c, lc.value)
                k = int(np.searchsorted(feed.ns[s], c, side="left"))
                if c < cut.value and k < int(np.searchsorted(feed.ns[s], cut.value, side="left")):
                    hidden += 1
                if k == 0:
                    continue
                old = feed.cache.get(s)
                if old is None or old[0] != k:
                    new = (k, b.iloc[:k])
                    feed.cache[s] = new
                    if feed.on_slice is not None:
                        feed.on_slice(s, k, new[1], None if old is None else old[1])
                    old = new
                out[s] = old[1]
            last_min = cut - pd.Timedelta(minutes=1)
            r.bars = out
            r.health.update(polls=r.health["polls"] + 1, last_poll_s=sec,
                            symbols_last_bar=sum(1 for x in out.values() if x.index[-1] >= last_min),
                            last_bar=str(last_min.time())[:5])
            r.last_fetch = cut
            self.notes["hidden_bars"] = self.notes.get("hidden_bars", 0) + hidden
            clock.now = clock.now + pd.Timedelta(seconds=sec)      # decisions, quotes and orders after the fetch
            return out

        r._sleep = sleep
        r.fetch = fetch

    def __call__(self, r, client, quotes, feed, clock, **_):
        if self.p.get("spreads"):
            quotes._bps = self._bps_fn(quotes, getattr(r, "priors", None))
        self.notes["quote_records"] = len(self.recorded)
        if self.recorded:
            self._install_recorded(r, quotes)
        else:
            self.notes["quotes_real"] = 0
            self.notes["quotes_modelled"] = "all (no recorded quotes)"
        if "fill_w" in self.p:
            client._market_now = self._market_fn(client)
        if self.polls:
            self._install_polls(r, feed, clock)
            self.notes["polls"] = len(self.polls)
        else:
            self.notes["polls"] = "none on record: default cadence"


def shortable_for(params: dict, branch: str, day) -> dict | None:
    return shortable_on(branch, str(pd.Timestamp(str(day)).date())) if params.get("shortable_day", True) else None


def load_params(path: str | Path | None) -> dict | None:
    return json.loads(Path(path).read_text()) if path else None
