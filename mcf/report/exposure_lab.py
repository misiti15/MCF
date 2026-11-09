"""Exposure Lab (shadow, research only, no orders) - owner 2026-11-09.

For the setups in Primary's PV decision (research/preval_1107/NOTES.md: PV0 = Primary as is, PV1 = Option 1 (opt1b),
PV2 = Option 2 (opt2b)) plus the top 20 by total R over the last 15 sessions, run on one session with the Team's as-live
engine (mcf.report.team -> mcf.replay.harness.run_session, fills=costs, limit_fill=through) under Primary's rules
(config/default.yaml) on Primary's universe:

  (a) ALONE   - each setup on its own, with a whole Primary account (slots / buying power / -2R latch / -20R halt) to itself;
  (b) TOGETHER - all of them in one Primary-rules book (one position per symbol, shared slots / halt);
  (c) PV books - PV0 / PV1 / PV2.

Reports per setup trades and R alone vs together (difference = crowding / conflict, with the together-book skip reasons),
pairwise conflicts from the alone runs (same-symbol overlapping trades, opposite-side clashes, correlation of 5-minute
changes in open + closed P/L in R), and each book's R, green day and worst intraday drawdown (peak-to-trough of the
5-minute marked R path). Simulated fills, not broker fills.

    python -m mcf.report.exposure_lab --date 2026-11-09 [--jobs 4] [--only alone,together,pv]

Writes research/exposure_lab/<date>.json (per-run partials cached in data/exposure_lab/<date>/, git-ignored).
Educational only - not financial advice."""
from __future__ import annotations

import argparse
import itertools
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
NY = "America/New_York"
OUT = ROOT / "research" / "exposure_lab"
PART = ROOT / "data" / "exposure_lab"
DISCLAIMER = "Educational only — not financial advice."
LABEL = "Shadow — simulated, no orders (research only)"

# setup -> home account for the 11-09 / 11-10 window (owner 2026-11-09 exposure set; GEN flagged by prefix; 5 GEN setups are
# temporarily in Testing 1 / 2, ledger 2026-11-09-expo1109-gen-temp-moves - the block is the same Gen block either way)
SETUPS = {
    # PV decision setups
    "RW3-gapdn-rsi5pop-flowsell-short-FD": "primary", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "primary",
    "L3-gap-slope-fromopen-FD": "primary", "ST7-rsi50dn-long-pm-t1s1-FD": "primary",
    "NS5-sma50-flush-oversold-long": "primary", "MF2-open-rsimidhi-flowsell-FD": "primary",
    "MF4-h40-open-flowsell-FD": "primary", "MF4-h40-open-flowsell": "primary", "NS1-rsidip-rsi5pop-long": "primary",
    "L3-gap-slope-rsi5hi-FD": "primary", "NM-ETF-late-dip-di-long": "livelab",
    # top 20 by total R (10-19..11-06, 7 accounts, run_id=1) not already above
    "RW7-gapdn-bounce-early-short-FD": "testing", "L3-gap-slope-lowdist-FD": "testing",
    "RW1-gapdn-bounce-flowsell-short-FD": "testing2", "NM-MF3-qqqdn-gapdn-FD": "testing2",
    "CWT09-gapdn-bounce-g5-lowerhalf-short": "graveyard", "CWT09-gapdn-vwaploss-g5-short": "graveyard",
    "CWT09-gapdn-vwaploss-g10-short": "livelab",
    "GEN-261020-10-BBpctge0p81-ORBfailDn-AM-BRvwlt0p3-hold-short": "gen",
    "GEN-261021-02-BarRngATRge0p14-PDLdistlem0p045-OPEN-SPYgt0p5-t1s1-long": "testing",
    "GEN-261028-06-RSI5le13-VWAPatrlem0p15-DayRngVsPrevle0p34-MID-BRoplt0p35-hold-short": "gen",
    "GEN-261022-07-Z12lem1p9-FlowShiftlem0p96-ATRdge3p6-AM-BRopgt0p5-t1s1-short": "testing2",
    "GEN-261026-02-VolRatioge2-SMA20dlem0p58-BarsSinceLODle1-LATE-BRoplt0p35-t1s1-long": "testing",
    "GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short": "testing2",
    "GEN-261027-08-ORBfailDn-FromPCATRlem0p96-LUNCH-QQQltm0p6-hold-short": "gen",
    "GEN-261019-03-Ret15mATRlem0p12-FromOpenATRlem0p34-SMA20slopege0p29-PM-BRoplt0p5-t05s1-long": "testing",
}
PV0 = ["L3-gap-slope-fromopen-FD", "L3-gap-slope-rsi5hi-FD", "MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell",
       "MF4-h40-open-flowsell-FD", "NS1-rsidip-rsi5pop-long", "NS5-sma50-flush-oversold-long",
       "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "ST7-rsi50dn-long-pm-t1s1-FD"]
PV_BOOKS = {
    "PV0": PV0,                                                                     # Primary as is
    "PV1": [s for s in PV0 if s not in ("MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD",
                                         "MF4-h40-open-flowsell")],                 # Option 1 (opt1b)
    "PV2": ["RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
            "L3-gap-slope-fromopen-FD", "ST7-rsi50dn-long-pm-t1s1-FD", "NS5-sma50-flush-oversold-long",
            "NM-ETF-late-dip-di-long"],                                             # Option 2 (opt2b)
}


def picks(ids) -> dict:
    return {"setups": [{"id": s, "account": SETUPS[s]} for s in ids]}


def runs() -> dict[str, list[str]]:
    """run name -> setup ids."""
    r = {f"alone:{s}": [s] for s in SETUPS}
    r["together"] = list(SETUPS)
    r.update({f"book:{k}": v for k, v in PV_BOOKS.items()})
    return r


# ------------------------------------------------------------------------------------------------------------- metrics
def _ts(x) -> pd.Timestamp | None:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    t = pd.Timestamp(x)
    return t.tz_localize(NY) if t.tzinfo is None else t.tz_convert(NY)


def grid(day) -> pd.DatetimeIndex:
    d = pd.Timestamp(str(day)).date()
    return pd.date_range(pd.Timestamp(f"{d} 09:35", tz=NY), pd.Timestamp(f"{d} 16:00", tz=NY), freq="5min")


def r_path(trades: list[dict], closes: dict[str, pd.Series], g: pd.DatetimeIndex) -> pd.Series:
    """Cumulative R (closed + open marked at the last 1-minute close) at each 5-minute mark."""
    out = np.zeros(len(g))
    for t in trades:
        en, ex = _ts(t.get("entry_time")), _ts(t.get("exit_time"))
        if en is None:
            continue
        risk = abs(float(t["entry"]) - float(t["stop"])) * abs(float(t["shares"]))
        r = float(t["r"]) if t.get("r") == t.get("r") and t.get("r") is not None else 0.0
        done = g >= ex if ex is not None else np.zeros(len(g), bool)
        out[done] += r
        live = (g > en) & ~done
        if live.any() and risk > 0:
            c = closes.get(t["symbol"])
            if c is not None and len(c):
                px = c.reindex(g[live] - pd.Timedelta(minutes=1), method="ffill").to_numpy(dtype=float)
                px = np.where(np.isnan(px), float(t["entry"]), px)
                out[live] += t["side"] * (px - float(t["entry"])) * abs(float(t["shares"])) / risk
    return pd.Series(out, index=g)


def book_stats(trades: list[dict], path: pd.Series) -> dict:
    rr = [t["r"] for t in trades if t.get("r") == t.get("r") and t.get("r") is not None]
    tot = float(sum(rr))
    p = np.concatenate([[0.0], path.to_numpy(dtype=float)]) if len(path) else np.zeros(1)
    dd = float((p - np.maximum.accumulate(p)).min())
    return {"trades": len(trades), "r": round(tot, 2), "green": tot > 0, "wins": sum(1 for v in rr if v > 0),
            "long_r": round(sum(t["r"] for t in trades if t["side"] > 0 and t["r"] == t["r"]), 2),
            "short_r": round(sum(t["r"] for t in trades if t["side"] < 0 and t["r"] == t["r"]), 2),
            "worst_intraday_dd_r": round(dd, 2), "low_r": round(float(p.min()), 2), "high_r": round(float(p.max()), 2)}


def overlaps(a: list[dict], b: list[dict]) -> tuple[int, int]:
    """(same-symbol trades whose holding times overlap, of which opposite side)."""
    same = opp = 0
    for x in a:
        xe, xx = _ts(x.get("entry_time")), _ts(x.get("exit_time"))
        if xe is None:
            continue
        for y in b:
            if y["symbol"] != x["symbol"]:
                continue
            ye, yx = _ts(y.get("entry_time")), _ts(y.get("exit_time"))
            if ye is None:
                continue
            if xe < (yx or pd.Timestamp.max.tz_localize(NY)) and ye < (xx or pd.Timestamp.max.tz_localize(NY)):
                same += 1
                opp += int(x["side"] != y["side"])
    return same, opp


def pairwise(alone: dict[str, list[dict]], paths: dict[str, pd.Series]) -> list[dict]:
    rows = []
    inc = {s: p.diff().fillna(p.iloc[0] if len(p) else 0.0) for s, p in paths.items()}
    for a, b in itertools.combinations(sorted(alone), 2):
        same, opp = overlaps(alone[a], alone[b])
        x, y = inc.get(a), inc.get(b)
        corr = None
        if x is not None and y is not None and x.std() > 0 and y.std() > 0:
            corr = round(float(np.corrcoef(x.to_numpy(), y.to_numpy())[0, 1]), 3)
        if same or corr is not None:
            rows.append({"a": a, "b": b, "same_symbol_overlaps": same, "opposite_side": opp, "corr_5min": corr})
    return sorted(rows, key=lambda r: (-r["same_symbol_overlaps"], -(r["corr_5min"] or 0)))


def crowding(alone: dict[str, dict], together: dict, skips: dict[str, dict]) -> list[dict]:
    rows = []
    for s in SETUPS:
        a = alone.get(s) or {}
        t = (together.get("per_setup") or {}).get(s) or {}
        rows.append({"id": s, "home": SETUPS[s], "gen": s.startswith("GEN-"),
                     "alone_trades": a.get("trades"), "alone_r": a.get("r"),
                     "together_trades": t.get("trades"), "together_r": t.get("r"),
                     "diff_trades": None if a.get("trades") is None or t.get("trades") is None else t["trades"] - a["trades"],
                     "diff_r": None if a.get("r") is None or t.get("r") is None else round(t["r"] - a["r"], 2),
                     "together_skips": skips.get(s, {})})
    return rows


def per_setup(trades: list[dict], ids) -> dict:
    out = {}
    for s in ids:
        x = [t for t in trades if t["strategy"] == s]
        rr = [t["r"] for t in x if t["r"] == t["r"]]
        out[s] = {"trades": len(x), "r": round(sum(rr), 2), "wins": sum(1 for v in rr if v > 0)}
    return out


# ------------------------------------------------------------------------------------------------------------- engine
_CTX: dict = {}


def _prepare(day, log=print) -> None:
    from . import team as T

    T.fetch_branches(sorted({T.ACCOUNT_BRANCH.get(a, "mcf-data") for a in SETUPS.values()} | {"mcf-data"}))
    cfg = T.team_config(picks(SETUPS), day)
    uni, unote = T.primary_universe(day)
    syms, notes = T.team_symbols(cfg, uni, day)
    exact = sorted({s for st in cfg["strategies"].values() for s in (st.get("symbols") or [])
                    if isinstance(st.get("symbols"), list)})
    pri = T.get_priors(syms, day, exact, log=log)
    bars = T.get_bars(syms, day, None, log=log)
    _CTX.update(day=str(day), uni=uni, unote=unote, notes=notes, priors=pri, bars=bars,
                shortable={str(s): (bool(a), bool(b)) for s, a, b in zip(uni.symbol, uni.shortable, uni.easy_to_borrow)},
                spreads=T.get_spreads())


def _run(name_ids):
    from . import team as T
    from .playing_time import classify

    name, ids = name_ids
    day = _CTX["day"]
    f = PART / day / (name.replace(":", "__") + ".json")
    if f.exists():
        return json.loads(f.read_text())
    cfg = T.team_config(picks(ids), day)
    syms, _ = T.team_symbols(cfg, _CTX["uni"], day)
    ss = set(syms)
    sim = T.simulate(cfg, day, {s: b for s, b in _CTX["bars"].items() if s in ss},
                     {s: p for s, p in _CTX["priors"].items() if s in ss}, None, _CTX["shortable"], _CTX["spreads"],
                     log=lambda *a: None)
    sig = sim["signals"]
    skips: dict = {}
    if hasattr(sig, "groupby") and len(sig) and "status" in sig:
        for st, status, reason in zip(sig.strategy, sig.status, sig.get("reason", [None] * len(sig))):
            b = classify(status, reason)
            if b != "taken":
                skips.setdefault(str(st), {}).setdefault(b, 0)
                skips[str(st)][b] += 1
    rep = {"name": name, "setups": ids, "trades": sim["trades"], "skips": skips,
           "seconds": (sim["stats"] or {}).get("seconds")}
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(rep, default=str))
    return rep


def build(day, jobs: int = 1, only=("alone", "together", "pv"), log=print) -> dict:
    day = str(pd.Timestamp(str(day)).date())
    _prepare(day, log=log)
    want = {k: v for k, v in runs().items()
            if ("alone" in only and k.startswith("alone:")) or ("together" in only and k == "together")
            or ("pv" in only and k.startswith("book:"))}
    items = list(want.items())
    log(f"exposure_lab {day}: {len(items)} runs, {len(_CTX['bars'])} symbols with bars, jobs={jobs}")
    if jobs > 1:
        import multiprocessing as mp

        with mp.get_context("fork").Pool(jobs) as pool:
            res = pool.map(_run, items, chunksize=1)
    else:
        res = [_run(i) for i in items]
    R = {r["name"]: r for r in res}
    closes = {s: b["close"] for s, b in _CTX["bars"].items()}
    g = grid(day)
    alone_tr = {k.split(":", 1)[1]: v["trades"] for k, v in R.items() if k.startswith("alone:")}
    alone_paths = {s: r_path(t, closes, g) for s, t in alone_tr.items()}
    alone = {s: book_stats(t, alone_paths[s]) for s, t in alone_tr.items()}
    together = {}
    if "together" in R:
        tt = R["together"]["trades"]
        together = {**book_stats(tt, r_path(tt, closes, g)), "per_setup": per_setup(tt, SETUPS)}
    books = {}
    for k, v in R.items():
        if k.startswith("book:"):
            books[k[5:]] = {**book_stats(v["trades"], r_path(v["trades"], closes, g)),
                            "setups": v["setups"], "per_setup": per_setup(v["trades"], v["setups"]),
                            "skips": v["skips"]}
    rep = {"date": day, "label": LABEL, "disclaimer": DISCLAIMER,
           "set": [{"id": s, "home": a, "gen": s.startswith("GEN-"), "pv": s in set(PV0) | set(PV_BOOKS["PV2"])}
                   for s, a in SETUPS.items()],
           "pv_map": {"PV0": "Primary as is", "PV1": "Option 1 (opt1b)", "PV2": "Option 2 (opt2b)"},
           "crowding": crowding(alone, together, (R.get("together") or {}).get("skips", {})),
           "alone": alone, "together": {k: v for k, v in together.items() if k != "per_setup"},
           "pairwise": pairwise(alone_tr, alone_paths) if alone_tr else [],
           "books": books,
           "sum_alone_r": round(sum(v["r"] for v in alone.values()), 2) if alone else None,
           "method": {"engine": "mcf.report.team -> mcf.replay.harness.run_session (as-live PaperRunner), fills=costs, "
                                "limit_fill=through", "rules": "Primary (config/default.yaml) for every run",
                      "universe": _CTX["unote"], "symbols": _CTX["notes"].get("symbols"),
                      "r": "simulated P/L after costs / (|entry - stop| x shares)",
                      "path": "5-minute marks, open lots at the last 1-minute close (no exit cost)",
                      "fills": "SIMULATED from 1-minute bars (not broker fills)"},
           "trades": {k: v["trades"] for k, v in R.items()}}
    return rep


def write(rep: dict, out_dir: Path = OUT) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{rep['date']}.json"
    p.write_text(json.dumps(rep, indent=1, default=str))
    return p


def text(rep: dict) -> str:
    L = [f"Exposure Lab {rep['date']} - {rep['label']}. {rep['disclaimer']}"]
    for k, b in rep.get("books", {}).items():
        L.append(f"  {k}: {b['r']:+.2f}R in {b['trades']} trades, green {b['green']}, worst intraday DD {b['worst_intraday_dd_r']:+.2f}R")
    t = rep.get("together") or {}
    if t:
        L.append(f"  together: {t['r']:+.2f}R / {t['trades']} (sum alone {rep.get('sum_alone_r')}R), worst DD {t['worst_intraday_dd_r']:+.2f}R")
    for c in sorted(rep.get("crowding", []), key=lambda c: c["diff_r"] if c["diff_r"] is not None else 0)[:8]:
        if c["diff_r"]:
            L.append(f"  crowded: {c['id'][:48]} alone {c['alone_r']}R/{c['alone_trades']} -> together {c['together_r']}R/{c['together_trades']}")
    for p in rep.get("pairwise", [])[:5]:
        L.append(f"  pair: {p['a'][:30]} x {p['b'][:30]} overlaps {p['same_symbol_overlaps']} (opp {p['opposite_side']}) corr {p['corr_5min']}")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Exposure Lab (shadow): alone vs together vs PV books for one session")
    ap.add_argument("--date", default=None, help="session date (default: today ET)")
    ap.add_argument("--jobs", type=int, default=int(os.environ.get("MCF_EXPO_JOBS", "1")))
    ap.add_argument("--only", default="alone,together,pv")
    a = ap.parse_args(argv)
    day = a.date or str(pd.Timestamp.now(tz=NY).date())
    rep = build(day, jobs=a.jobs, only=tuple(a.only.split(",")))
    p = write(rep)
    print(text(rep))
    print(f"wrote {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
