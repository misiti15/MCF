"""FWDCAL - mirror-live calibration of the forward replay (guild Builder, Lead lead-20261111-1100-3; owner P1 'quality
live reps faster', item 2). Research only: no config / setup / assignment / ledger change; nothing can reach a broker.

fwdrep (main session, vendor/run.py + vendor/report.py, copied unchanged from claude/charming-mccarthy-i3rhhr d3901f7e)
replays setups ISOLATED (no caps, no twin block, no account -R halt, no Testing A top-500 pool, 0-minute order delay).
Its rule-21 audit failed (Skeptic 11-11: 56% of live trades matched, replay +0.081R optimistic). This mode MIRRORS
each account as it actually ran that session:
  * every setup ENABLED in that account's own setups/<day>.json snapshot, with that day's block (the rules in force),
    plus that session's live / shorts / exits sections - caps, twin block, account -R halt, trade caps all ON;
  * Testing A (testing2) keeps universe.top_n (UNI1 top-500 pool) from 2026-11-04 on, as live did; off before;
  * --delay D: market ENTRY orders fill at the open of the bar D minutes after the replay's own fill bar (live sends
    the order ~1.3 min after the decision bar closes: journal bar_age_min ~1.3; D=1 approximates it). Exits unchanged.
Then rule 21's audit per account: share of live trades matched (setup, symbol, side, entry within 5 min; also exact
minute), avg R gap on matched trades and overall, never optimistic by > 0.03R. Every unmatched trade gets a cause:
  live-only : replay had no signal for it (setup/data/universe difference) | replay signal skipped (reason bucket) |
              replay entered at a different time (> 5 min)
  replay-only: live signal skipped (live reason bucket: buying power, borrow, spread, caps ...) | live no signal.
    python mirror.py --dates 2026-11-06..2026-11-10 [--accounts testing,gen] [--delay 1] [--fetch] [--jobs 3]
    python mirror.py --audit [--delay 1]          (rebuild the audit from the cached books)
Inputs: data/team caches (bars/priors fetched read-only by the fwdrep code, --fetch only after 16:05 ET).
Educational only - not financial advice."""
from __future__ import annotations

import argparse, json, os, sqlite3, sys, tempfile, time
from pathlib import Path

import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(HERE / "vendor")); sys.path.insert(0, str(ROOT))
import run as RUN  # noqa: E402  (fwdrep, unchanged)
import report as REP  # noqa: E402

NY = "America/New_York"
OUT = HERE / "out"
UNI1_FROM = "2026-11-04"


MASK_ERR = {"n": 0}


def patch_mask_errors() -> None:
    """fast.py's whole-session pre-mask runs a module on the whole day's frame; a module that fails on a frame shape
    (LD1-ns1-breadthup: _shift(k=2) on a 1-row frame, a symbol with one 5-min bar) would crash the book. Fall back to
    None = 'unknown here, let the real generate() decide', which is exactly the live code path. Counted, reported."""
    from mcf.replay import fast as F
    if getattr(F.FastSession.full_mask, "_fwdcal", False):
        return
    orig = F.FastSession.full_mask

    def full_mask(self, name, sym):
        try:
            return orig(self, name, sym)
        except (ValueError, IndexError):
            MASK_ERR["n"] += 1
            self.masks[(name, sym)] = None
            return None
    full_mask._fwdcal = True
    F.FastSession.full_mask = full_mask


def patch_delay(D: int) -> None:
    from mcf.replay import broker as B
    if D <= 0 or getattr(B.SimTradingClient, "_fwdcal_delay", None) == D:
        return
    orig = getattr(B.SimTradingClient, "_fwdcal_orig", B.SimTradingClient._market_now)

    def mn(self, o):
        if o._role == "entry":                      # entries only; exits / flattens keep the replay's timing
            o._active = max(self.mkt.minute(self.clock.now), self.done_min + 1) + D   # advance() fills it at that open
            return
        return orig(self, o)

    B.SimTradingClient._fwdcal_orig = orig
    B.SimTradingClient._market_now = mn
    B.SimTradingClient._fwdcal_delay = D


CFG_BRANCH = "origin/claude/intraday-trading-system-witis4"


def cfg_dir(day: str) -> Path:
    """config/ as it stood at day 09:30 ET (default branch tip then; Skeptic 11-11: TEAM-6, caps, CF, lots changed)."""
    t = pd.Timestamp(f"{day} 09:30", tz=NY).isoformat()
    c = (RUN.git("rev-list", "-1", "--first-parent", f"--before={t}", CFG_BRANCH) or "").strip()
    assert c, f"no config commit before {t} (deepen: git fetch --shallow-since=2026-10-20 origin <default branch>)"
    d = OUT / "cfg" / c[:10]
    if not (d / "config" / "default.yaml").exists():
        import subprocess, io, tarfile
        raw = subprocess.run(["git", "-C", str(ROOT), "archive", c, "config"], capture_output=True, check=True).stdout
        d.mkdir(parents=True, exist_ok=True); tarfile.open(fileobj=io.BytesIO(raw)).extractall(d)
    return d / "config"


def live_equity(acc: str, day: str) -> float | None:
    """The account's equity going into `day` (status.json on its data branch, last commit before 09:30 ET)."""
    t = pd.Timestamp(f"{day} 09:30", tz=NY).isoformat()
    c = (RUN.git("rev-list", "-1", f"--before={t}", f"origin/{RUN.BRANCH[acc]}", "--", "status.json") or "").strip()
    if not c:
        return None
    try:
        return float(json.loads(RUN.git("show", f"{c}:status.json"))["account"]["equity"])
    except Exception:
        return None


def mirror_cfg(acc: str, day: str) -> dict | None:
    import mcf.config as MC
    from mcf.config import load_config
    snap = RUN.bjson(RUN.BRANCH[acc], f"setups/{day}.json")
    if not snap:
        return None
    old = os.environ.get("MCF_ACCOUNT"); os.environ["MCF_ACCOUNT"] = acc
    old_dir = MC.CONFIG_DIR; MC.CONFIG_DIR = cfg_dir(day)
    try:
        cfg = load_config()
    finally:
        MC.CONFIG_DIR = old_dir
        os.environ.pop("MCF_ACCOUNT", None) if old is None else os.environ.__setitem__("MCF_ACCOUNT", old)
    eq = live_equity(acc, day)
    cfg["_fwdcal"] = {"config_dir": str(cfg_dir(day)), "equity_live": eq,
                      "equity_config": cfg["account"].get("starting_equity")}
    if eq:
        cfg["account"]["starting_equity"] = eq      # live equity going into the session (buying power, Skeptic 3)
    for k in ("live", "shorts", "exits"):
        if isinstance(snap.get(k), dict):
            cfg[k] = {**(cfg.get(k) or {}), **snap[k]}
    on = {s: dict(b) for s, b in (snap.get("strategies") or {}).items() if b.get("enabled", True)}
    if not on:
        return None
    cfg["strategies"] = on
    uni = cfg.setdefault("universe", {})
    # universe.top_n now comes from that day's config (UNI1 wired 11-03, live from 11-04); belt and braces:
    if not (acc == "testing2" and day >= UNI1_FROM):
        uni.pop("top_n", None); uni.pop("top_n_min_adv", None)
    cfg["account_name"] = f"fwdcal-{acc}"
    return cfg


QUOTES = {"on": False, "table": None, "exact": 0, "near": 0, "pool": 0}


def book_path(day, acc, D):
    return OUT / "books" / f"{'q' if QUOTES['on'] else 'd'}{D}" / day / f"{acc}.json"


def quote_table(days) -> dict:
    """(day, symbol) -> [(minute epoch ns, bid, ask)] from the quotes the live runners journaled (signals.info) in ALL
    seven accounts (a quote is market data, shared). Built once in the parent; forked workers inherit it."""
    import json as _j
    Q = {}
    for acc in RUN.ACC_ORDER:
        raw = RUN.git("show", f"origin/{RUN.BRANCH[acc]}:journal.db", text=False)
        if not raw:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as fh:
            fh.write(raw)
        try:
            c = sqlite3.connect(fh.name); q = ",".join("?" * len(days))
            rows = c.execute(f"select day, ts, symbol, info from signals where day in ({q}) and info like '%\"bid\"%'", list(days)).fetchall()
            c.close()
        finally:
            os.unlink(fh.name)
        for day, ts, sym, info in rows:
            try:
                d = _j.loads(info[: info.rindex("}") + 1])
                b, a = float(d["bid"]), float(d["ask"])
            except Exception:
                continue
            if b > 0 and a >= b:
                m = pd.Timestamp(ts).tz_convert(NY).floor("min").value
                Q.setdefault((day, sym), []).append((m, b, a))
    for k in Q:
        Q[k].sort()
    return Q


def patch_quotes() -> None:
    """Replay quote = the quote live logged for this symbol in this same minute (bid/ask as logged: the spread and
    the quote-vs-bar cross-check both mirror live); else the nearest logged quote within 2 minutes gives the spread in
    bps around the replay price; else the existing deterministic pool draw. Counted."""
    from mcf.replay import broker as BR
    if getattr(BR.SimDataClient.get_stock_latest_quote, "_fwdcal", False):
        return
    orig = BR.SimDataClient.get_stock_latest_quote

    def gq(self, req):
        out = orig(self, req)
        now = self.clock.now; m0 = now.floor("min").value; day = str(now.date())
        for s, q in out.items():
            L = QUOTES["table"].get((day, s)) if QUOTES["table"] else None
            best = None
            if L:
                best = min(L, key=lambda x: abs(x[0] - m0))
                dm = abs(best[0] - m0) / 6e10
            if best is not None and dm < 0.5:
                out[s] = type(q)(bid_price=best[1], ask_price=best[2], timestamp=q.timestamp); QUOTES["exact"] += 1
            elif best is not None and dm <= 2:
                px = (q.bid_price + q.ask_price) / 2; bps = (best[2] - best[1]) / ((best[1] + best[2]) / 2) * 1e4
                half = max(0.005, px * bps / 2e4)
                out[s] = type(q)(bid_price=round(px - half, 4), ask_price=round(px + half, 4), timestamp=q.timestamp); QUOTES["near"] += 1
            else:
                QUOTES["pool"] += 1
        return out
    gq._fwdcal = True
    BR.SimDataClient.get_stock_latest_quote = gq


def run_book(job):
    day, acc, D = job
    f = book_path(day, acc, D)
    if f.exists():
        return json.loads(f.read_text())
    from mcf.report import team as T
    from mcf.backtest.engine import pinned_symbols
    patch_delay(D); patch_mask_errors()
    if QUOTES["on"]:
        patch_quotes()
    cfg = mirror_cfg(acc, day)
    if cfg is None:
        rep = {"day": day, "acc": acc, "delay": D, "trades": [], "signals": [], "skipped": "no snapshot / nothing enabled"}
    else:
        RUN.load_day(day, False, log=lambda *a: None)
        C = RUN._CTX; t0 = time.time(); MASK_ERR["n"] = 0
        QUOTES.update(exact=0, near=0, pool=0)
        ss = set(C["syms"]) | pinned_symbols(cfg)
        sim = T.simulate(cfg, day, {s: b for s, b in C["bars"].items() if s in ss},
                         {s: p for s, p in C["priors"].items() if s in ss}, None, C["shortable"], C["spreads"], log=lambda *a: None)
        sg = sim["signals"]
        sig = [] if not hasattr(sg, "to_dict") or not len(sg) else sg[[c for c in ("ts", "symbol", "strategy", "side", "status", "reason")
                                                                        if c in sg]].astype(str).to_dict("records")
        rep = {"day": day, "acc": acc, "delay": D, "setups": sorted(cfg["strategies"]), "fwdcal": cfg.get("_fwdcal"), "trades": sim["trades"],
               "signals": sig, "seconds": round(time.time() - t0, 1), "mask_errors": MASK_ERR["n"], "quotes": {k: QUOTES[k] for k in ("exact", "near", "pool")} if QUOTES["on"] else None, "notes": {k: str(v) for k, v in (C.get("notes") or {}).items()}}
    f.parent.mkdir(parents=True, exist_ok=True)
    f.with_suffix(".tmp").write_text(json.dumps(rep, default=str)); f.with_suffix(".tmp").replace(f)
    print(f"fwdcal d{D} {day} {acc}: {len(rep['trades'])} trades, {rep.get('seconds')} s", flush=True)
    return rep


# ------------------------------------------------------------------------------------------------------------ audit
def live_signals(accs, days) -> pd.DataFrame:
    rows = []
    for acc in accs:
        raw = RUN.git("show", f"origin/{RUN.BRANCH[acc]}:journal.db", text=False)
        if not raw:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as fh:
            fh.write(raw)
        try:
            c = sqlite3.connect(fh.name)
            q = ",".join("?" * len(days))
            s = pd.read_sql(f"select day as date, ts, symbol, strategy as setup, side, status, reason from signals "
                            f"where run_id=1 and day in ({q})", c, params=list(days))
            c.close()
        finally:
            os.unlink(fh.name)
        s["acct"] = acc; rows.append(s)
    S = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if len(S):
        S["et"] = pd.to_datetime(S.ts, utc=True, format="mixed")
    return S


def _wilson(k, n, z=1.96):
    if not n:
        return (np.nan, np.nan)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def _gap_ci(a, b, z=1.96):
    """95% CI of mean(a) - mean(b), independent samples (Welch SE); trades within a day are correlated, so it is a
    lower bound on the width (Lead: the setup-day is the unit)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return (np.nan, np.nan)
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)); g = a.mean() - b.mean()
    return (g - z * se, g + z * se)


def bucket(status, reason):
    from mcf.report.playing_time import classify
    b = classify(status, reason)
    r = str(reason or "").lower()
    if b not in ("taken",) and ("buying power" in r or "notional" in r):
        return "buying_power"
    if "spread" in r or "quote" in r:
        return "spread_quote"
    return b


def near(df, setup, sym, side, et, win=5.0):
    c = df[(df.setup == setup) & (df.symbol == sym) & (df.side == side)]
    if not len(c):
        return None
    d = (c.et - et).abs().dt.total_seconds() / 60
    return c.loc[d.idxmin()] if d.min() <= win else None


def xkind(r) -> str:
    r = str(r or "").lower()
    return "stop" if "stop" in r else "target" if ("target" in r or "limit" in r) else "time/flat" if r else "?"


def live_trades_x() -> pd.DataFrame:
    """report.live_trades() plus exit_reason (same filters, same R)."""
    L = REP.live_trades()
    rows = []
    for acc, br in RUN.BRANCH.items():
        raw = RUN.git("show", f"origin/{br}:journal.db", text=False)
        if not raw:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as fh:
            fh.write(raw)
        try:
            c = sqlite3.connect(fh.name)
            t = pd.read_sql("select date, strategy as setup, symbol, side, entry_time, exit_reason from trades "
                            "where run_id=1 and exit is not null", c); c.close()
        finally:
            os.unlink(fh.name)
        t["acct"] = acc; rows.append(t)
    E = pd.concat(rows, ignore_index=True); E["date"] = E.date.astype(str)
    L = L.merge(E.drop_duplicates(["acct", "date", "setup", "symbol", "side", "entry_time"]),
                on=["acct", "date", "setup", "symbol", "side", "entry_time"], how="left")
    L["xk"] = L.exit_reason.map(xkind)
    return L


def audit(D: int, dates: list[str] | None = None, tag: str = "") -> pd.DataFrame:
    fs = sorted((OUT / "books" / f"{'q' if QUOTES['on'] else 'd'}{D}").glob("*/*.json"))
    if dates:
        fs = [f for f in fs if f.parent.name in dates]
    reps = [json.loads(f.read_text()) for f in fs]
    reps = [r for r in reps if not r.get("skipped")]
    if not reps:
        sys.exit("no books")
    X = pd.DataFrame([{"date": r["day"], "acct": r["acc"], "setup": t["strategy"], "symbol": t["symbol"], "side": int(t["side"]),
                       "entry_time": t["entry_time"], "R": t["r"], "xk": xkind(t.get("exit_reason"))} for r in reps for t in r["trades"]])
    X["et"] = pd.to_datetime(X.entry_time, utc=True, format="mixed")
    XS = pd.DataFrame([{"date": r["day"], "acct": r["acc"], **s} for r in reps for s in r["signals"]])
    if len(XS):
        XS["side"] = XS.side.astype(float).astype(int); XS = XS.rename(columns={"strategy": "setup"})
        XS["et"] = pd.to_datetime(XS.ts, utc=True, format="mixed")
    keys = {(r["day"], r["acc"]) for r in reps}
    L = live_trades_x()
    L = L[[(d, a) in keys for d, a in zip(L.date, L.acct)]].copy()
    LS = live_signals(sorted({a for _, a in keys}), sorted({d for d, _ in keys}))
    out, causes = [], []
    for (d, a), _ in sorted(dict.fromkeys(keys).items()):
        x = X[(X.date == d) & (X.acct == a)]; l = L[(L.date == d) & (L.acct == a)]
        pairs = REP.match(x, l, 5.0)
        pi, li = {p for p, _ in pairs}, {q for _, q in pairs}
        for i, j in pairs:
            causes.append(dict(date=d, acct=a, kind="matched", cause="exact_minute" if X.loc[i, "et"].floor("min") == L.loc[j, "et"].floor("min") else "within_5min",
                               rdiff=X.loc[i, "R"] - L.loc[j, "R"], xk_live=L.loc[j, "xk"], xk_rep=X.loc[i, "xk"],
                               R=X.loc[i, "R"]))
        xs = XS[(XS.date == d) & (XS.acct == a)] if len(XS) else XS
        ls = LS[(LS.date == d) & (LS.acct == a)] if len(LS) else LS
        for j in l.index.difference(list(li)):
            r = L.loc[j]
            s = near(xs, r.setup, r.symbol, int(r.side), r.et, 5.0) if len(xs) else None
            if s is None:
                s2 = near(xs, r.setup, r.symbol, int(r.side), r.et, 400.0) if len(xs) else None
                cause = "replay_no_signal" if s2 is None else "replay_signal_other_time"
            else:
                cause = "replay_skip:" + bucket(s.status, s.reason)
            causes.append(dict(date=d, acct=a, kind="live_only", cause=cause, R=r.R, xk_live=r.xk))
        for i in x.index.difference(list(pi)):
            r = X.loc[i]
            s = near(ls, r.setup, r.symbol, int(r.side), r.et, 5.0) if len(ls) else None
            cause = "live_no_signal" if s is None else "live_skip:" + bucket(s.status, s.reason)
            causes.append(dict(date=d, acct=a, kind="replay_only", cause=cause, R=r.R, xk_rep=r.xk))
    C = pd.DataFrame(causes)
    for a, g in list(C.groupby("acct")) + [("ALL", C)]:
        xl = X if a == "ALL" else X[X.acct == a]; ll = L if a == "ALL" else L[L.acct == a]
        m = g[g.kind == "matched"]
        out.append(dict(acct=RUN.TAG.get(a, a), sessions=g.date.nunique(), live_trades=len(ll), replay_trades=len(xl),
                        matched=len(m), match_rate=round(len(m) / max(len(ll), 1), 3),
                        exact_min_share=round((m.cause == "exact_minute").mean(), 3) if len(m) else np.nan,
                        replay_only_share=round((g.kind == "replay_only").sum() / max(len(xl), 1), 3),
                        rdiff_matched=round(m.rdiff.mean(), 4) if len(m) else np.nan,
                        replay_avgR=round(xl.R.mean(), 4), live_avgR=round(ll.R.mean(), 4),
                        gap_avgR=round(xl.R.mean() - ll.R.mean(), 4),
                        gap_ci95=f"[{_gap_ci(xl.R, ll.R)[0]:+.3f},{_gap_ci(xl.R, ll.R)[1]:+.3f}]",
                        exact_match_rate=round((m.cause == "exact_minute").sum() / max(len(ll), 1), 3),
                        exact_ci95=f"[{_wilson((m.cause == 'exact_minute').sum(), len(ll))[0]:.2f},{_wilson((m.cause == 'exact_minute').sum(), len(ll))[1]:.2f}]",
                        rule21=bool((m.cause == "exact_minute").sum() / max(len(ll), 1) >= 0.95 and abs(xl.R.mean() - ll.R.mean()) <= 0.03)))
    A = pd.DataFrame(out)
    cz = C[C.kind != "matched"].groupby(["acct", "kind", "cause"]).agg(n=("R", "size"), avgR=("R", "mean")).round(3).reset_index()
    m = C[C.kind == "matched"]
    xg = m.groupby(["xk_live", "xk_rep"]).agg(n=("rdiff", "size"), rdiff_mean=("rdiff", "mean"),
                                              rdiff_sum=("rdiff", "sum")).round(4).reset_index()
    bp = C[C.cause.astype(str).str.contains("buying_power")]
    OUT.mkdir(exist_ok=True)
    sfx = f"_d{D}{tag}"
    A.to_csv(OUT / f"audit{sfx}.csv", index=False); cz.to_csv(OUT / f"causes{sfx}.csv", index=False)
    xg.to_csv(OUT / f"exitkind{sfx}.csv", index=False)
    pd.set_option("display.width", 250)
    print(f"FWDCAL mirror-live audit, delay {D} (rule 21 since Lead 11-11 21:00: EXACT-minute match >= 95% AND |avg R gap| <= 0.03; 5-min match diagnostic):")
    print(A.to_string(index=False)); print("\nunmatched trades by cause:"); print(cz.to_string(index=False))
    print("\nmatched trades: replay - live R by exit kind (live kind x replay kind; Skeptic 4):"); print(xg.to_string(index=False))
    print(f"\nbuying-power causes (config/live equity, Skeptic 3): {len(bp)} trades; matched rate if they are set aside: "
          f"{len(m) / max(len(L) - (bp.kind == 'live_only').sum(), 1):.3f}")
    print("FORWARD REPLAY = simulated; never mixed with live records. Educational only - not financial advice.")
    return A


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dates"); ap.add_argument("--accounts", default=",".join(RUN.ACC_ORDER))
    ap.add_argument("--delay", type=int, default=1); ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--fetch", action="store_true"); ap.add_argument("--audit", action="store_true")
    ap.add_argument("--tag", default="")
    ap.add_argument("--quotes", action="store_true", help="replay the quotes live journaled (books under out/books/q<D>)")
    a = ap.parse_args()
    QUOTES["on"] = a.quotes
    if a.audit:
        audit(a.delay, RUN.trading_days(*a.dates.split("..")) if a.dates else None, a.tag); return
    now = pd.Timestamp.now(tz=NY)
    if a.fetch and now.dayofweek < 5 and "09:25" <= now.strftime("%H:%M") < "16:05":
        sys.exit("fwdcal: --fetch refused during market hours")
    RUN.git("fetch", "-q", "origin", *RUN.BRANCH.values())
    days = RUN.trading_days(*a.dates.split(".."))
    ok = []
    for d in days:
        try:
            if a.fetch:
                RUN.throttle(); RUN.load_day(d, True)
            elif not ((RUN.TEAM_CACHE / "priors" / f"{d}.pkl.gz").exists() and (RUN.TEAM_CACHE / "1Min" / f"{d}.parquet").exists()):
                raise FileNotFoundError("no cached bars/priors")
            ok.append(d)
        except FileNotFoundError as e:
            print(f"fwdcal {d}: SKIPPED - {e}", flush=True)
    if a.quotes:
        QUOTES["table"] = quote_table(ok)
        print(f"fwdcal quotes: {sum(len(v) for v in QUOTES['table'].values())} logged quotes, {len(QUOTES['table'])} symbol-days", flush=True)
    jobs = [(d, acc, a.delay) for d in ok for acc in a.accounts.split(",") if not book_path(d, acc, a.delay).exists()]
    print(f"fwdcal: {len(ok)} sessions, {len(jobs)} books to run, delay {a.delay}", flush=True)
    if a.jobs > 1 and len(jobs) > 1:
        import multiprocessing as mp
        with mp.get_context("fork").Pool(min(a.jobs, len(jobs)), maxtasksperchild=4) as pool:
            list(pool.imap_unordered(run_book, jobs, chunksize=1))
    else:
        for j in jobs:
            run_book(j)
    audit(a.delay, ok, a.tag)


if __name__ == "__main__":
    main()
