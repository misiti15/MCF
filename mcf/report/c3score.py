"""C3-SCORE (owner yes 2026-11-18; research/consultant_p3/RESULTS.md #10 and "Weekly check-in scorecard"): the Primary
scorecard line for the nightly brief and the Friday review, plus the reporting fixes that go with it. Reporting only:
nothing here changes which trades are taken or how they exit.

  scorecard line   median day R (last 10 sessions), green-day % (last 20), worst day and days <= -10R (last 20), the
                   week's R without its best day and that day's share ("1 day" tag at >= 50%), Primary account R
                   ($ / 0.25% of equity) next to dashboard R, open owner decisions older than 3 nights
  account R        dashboard R = sum of per-trade R after costs; account R = $ P/L after costs / (risk_pct x equity).
                   They differ because the ~$4k position cap, not 0.25% risk, sets most position sizes (P6/P8: +92.2R
                   dashboard = +21.8R account)
  day-type tag     point-in-time SPY tag known at 09:50 (owner anchor 2026-11-14): open gap vs prior close
                   (gap-up / gap-down / flat at +-0.30%) and the 09:30-09:50 drift (up / down / flat at +-0.20%).
                   A label for reading results, never a switch (P2: no classifier kept its sign)
  what-if fix      corrected what-if sums: unfillable skips dropped (spread, borrow, halt, price through stop/target,
                   broker rejects, no quote), first signal per name-day only, then each trade's R less the quoted
                   spread in R and a 0.05R haircut. Raw what-if sums ("this rule cost us R") are never quoted alone
  capture buckets  Move Hunt capture in three buckets: headline (all top moves), tradable (not in the earnings
                   blackout) and earnings blackout (no setup may trade them except EARN-GO)
  epoch pairs      C3-EPOCH: per session, Primary's of_live shadow R (current book) vs the BASE1 shadow R (frozen book),
                   same polls and fill model; mean paired difference, its SD and standard error

    python -m mcf.report.c3score --journal <primary journal.db> [--day YYYY-MM-DD] [--moves research/bdi/moves/moves.csv]

Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DISCLAIMER = "Educational only — not financial advice."
ONE_DAY_SHARE = 0.50
HAIRCUT_R = 0.05
UNFILLABLE = re.compile(r"spread|borrow|ETB|shortable|halt|through (?:stop|target)|reject|no quote|price below minimum|"
                        r"buying_power|code\"?:\s*4\d{7}|missed", re.I)


# --------------------------------------------------------------------------------------------------- per-day table
def trade_r(df: pd.DataFrame) -> pd.Series:
    """R after costs per trade: pnl_adj (else pnl) / (|entry - stop| x shares)."""
    pnl = df["pnl_adj"].fillna(df["pnl"]) if "pnl_adj" in df else df["pnl"]
    risk = (df["entry"] - df["stop"]).abs() * df["shares"].abs()
    return (pnl / risk.where(risk > 0)).astype(float)


def day_table(trades: pd.DataFrame, equity: float = 100_000.0, risk_pct: float = 0.25) -> pd.DataFrame:
    """date -> trades, dash_r (sum of trade R after costs), usd (P/L after costs), acct_r ($ / risk_pct% of equity)."""
    if trades is None or trades.empty:
        return pd.DataFrame(columns=["trades", "dash_r", "usd", "acct_r"])
    t = trades.copy()
    t["R"] = trade_r(t)
    t["usd"] = t["pnl_adj"].fillna(t["pnl"]) if "pnl_adj" in t else t["pnl"]
    g = t.groupby(t["date"].astype(str))
    out = pd.DataFrame({"trades": g.size(), "dash_r": g["R"].sum(), "usd": g["usd"].sum()})
    out["acct_r"] = out["usd"] / (equity * risk_pct / 100.0)
    return out.sort_index()


def week_wo_best(days: pd.Series) -> dict:
    """The window's R, its R without the best day, and the best day's share of the total (1 day tag at >= 50%)."""
    if days.empty:
        return {"total": 0.0, "wo_best": 0.0, "best_day": None, "best_share": None, "one_day": False}
    tot, best = float(days.sum()), float(days.max())
    share = best / tot if tot > 0 else None
    return {"total": round(tot, 2), "wo_best": round(tot - best, 2), "best_day": str(days.idxmax()),
            "best_share": None if share is None else round(share, 2), "one_day": bool(share is not None and share >= ONE_DAY_SHARE)}


def scorecard(days: pd.DataFrame, day: str | None = None, stale: int | None = None) -> dict:
    """The seven check-in numbers (RESULTS.md 'Weekly check-in scorecard') from a Primary day table."""
    d = days[days.index <= day] if day else days
    r = d["dash_r"]
    last10, last20, week = r.tail(10), r.tail(20), r.tail(5)
    return {
        "day": day or (str(d.index.max()) if len(d) else None), "sessions": int(len(d)),
        "median_day_r_10": None if last10.empty else round(float(last10.median()), 2),
        "green_pct_20": None if last20.empty else round(float((last20 > 0).mean()) * 100, 1),
        "worst_day_20": None if last20.empty else round(float(last20.min()), 2),
        "days_le_m10_20": int((last20 <= -10).sum()),
        "week": week_wo_best(week),
        "dash_r_week": round(float(week.sum()), 2) if len(week) else 0.0,
        "acct_r_week": round(float(d["acct_r"].tail(5).sum()), 2) if len(d) else 0.0,
        # UNIT1 (owner yes 2026-11-18, display only: setups and days are still judged by trade R): the day's trade R
        # with account R beside it, and a flag when the two disagree in sign
        "dash_r_day": round(float(r.iloc[-1]), 2) if len(d) else None,
        "acct_r_day": round(float(d["acct_r"].iloc[-1]), 2) if len(d) else None,
        "stale_decisions": stale,
    }


def line(sc: dict, tag: str | None = None) -> str:
    """One scorecard line for the brief (<= ~60 words)."""
    w = sc["week"]
    share = "–" if w["best_share"] is None else f"{w['best_share'] * 100:.0f}%" + (" 1 day" if w["one_day"] else "")
    head = f"Scorecard {sc['day']}" + (f" [{tag}]" if tag else "") + ": "
    parts = [f"median day {sc['median_day_r_10']:+.2f}R (10)" if sc["median_day_r_10"] is not None else "median day –",
             f"green {sc['green_pct_20']:.0f}% (20)" if sc["green_pct_20"] is not None else "green –",
             f"worst {sc['worst_day_20']:+.1f}R, {sc['days_le_m10_20']} days <= -10R (20)" if sc["worst_day_20"] is not None else "worst –",
             f"week {w['total']:+.1f}R, w/o best day {w['wo_best']:+.1f}R (best {share})",
             f"dashboard {sc['dash_r_week']:+.1f}R vs account {sc['acct_r_week']:+.1f}R (week)"]
    if sc.get("dash_r_day") is not None and sc.get("acct_r_day") is not None:   # UNIT1: display only
        flip = (sc["dash_r_day"] > 0) != (sc["acct_r_day"] > 0) and sc["dash_r_day"] != 0 and sc["acct_r_day"] != 0
        parts.insert(0, f"day {sc['dash_r_day']:+.2f} trade R / {sc['acct_r_day']:+.2f} account R" + (" (signs differ)" if flip else ""))
    if sc.get("stale_decisions") is not None:
        parts.append(f"{sc['stale_decisions']} owner decisions > 3 nights")
    return head + " · ".join(parts) + ". " + DISCLAIMER


# ------------------------------------------------------------------------------------------------------ day type
def day_type(spy: pd.DataFrame, prev_close: float, gap_band: float = 0.30, drift_band: float = 0.20) -> str:
    """Point-in-time SPY tag at 09:50 from 1-minute bars of the session (index ET timestamps, open/close columns):
    'gap-up|gap-down|flat-open' + '/ 0950 up|down|flat' (drift from the open to the close of the 09:49 bar)."""
    if spy is None or spy.empty or not prev_close:
        return "n/a"
    idx = spy.index.tz_convert("America/New_York") if spy.index.tz is not None else spy.index
    s = spy.set_axis(idx)
    o = float(s["open"].iloc[0])
    gap = (o / prev_close - 1) * 100
    g = "gap-up" if gap >= gap_band else "gap-down" if gap <= -gap_band else "flat-open"
    pre = s[[(t.hour, t.minute) < (9, 50) for t in s.index]]
    if pre.empty:
        return g
    drift = (float(pre["close"].iloc[-1]) / o - 1) * 100
    dr = "up" if drift >= drift_band else "down" if drift <= -drift_band else "flat"
    return f"{g} / 0950 {dr}"


# ------------------------------------------------------------------------------------------------------- what-if
def whatif_corrected(w: pd.DataFrame, key=("symbol", "date"), haircut: float = HAIRCUT_R) -> dict:
    """Corrected what-if sum. `w`: what-if trades (symbol, date, entry, stop, shares, pnl_adj|pnl, optional reason,
    spread_bps, entry_time). Unfillable rows are dropped, then the first signal per name-day is kept, then each R
    loses its spread (spread_bps x entry / |entry-stop|) and `haircut`. Returns raw vs corrected totals."""
    if w is None or w.empty:
        return {"raw_n": 0, "raw_r": 0.0, "n": 0, "r": 0.0, "dropped_unfillable": 0, "dropped_dupes": 0}
    t = w.copy()
    t["R"] = trade_r(t)
    if "r_multiple" in t:   # W8-DQ: journal what-if rows carry shares 0 / pnl 0 - their R is r_multiple (engine costs)
        t["R"] = t["R"].fillna(pd.to_numeric(t["r_multiple"], errors="coerce"))
    t = t[t["R"].notna()]
    raw_n, raw_r = len(t), float(t["R"].sum())
    if "reason" in t:
        reason = t["reason"].fillna("").astype(str)
    elif "meta" in t:       # W8-DQ: the journal keeps the skip reason in meta ("status=..;why=..")
        reason = t["meta"].fillna("").astype(str).str.extract(r"why=(.*)$")[0].fillna("")
    else:
        reason = pd.Series("", index=t.index)
    keep = ~reason.str.contains(UNFILLABLE)
    unf = int((~keep).sum())
    t = t[keep]
    order = [c for c in ("entry_time", "signal_time") if c in t]
    if order:
        t = t.sort_values(order)
    before = len(t)
    t = t.drop_duplicates(list(key), keep="first")
    dupes = before - len(t)
    sp = t["spread_bps"].fillna(0.0) if "spread_bps" in t else pd.Series(0.0, index=t.index)
    spread_r = sp / 1e4 * t["entry"] / (t["entry"] - t["stop"]).abs()
    t["R_adj"] = t["R"] - spread_r - haircut
    return {"raw_n": raw_n, "raw_r": round(raw_r, 2), "n": int(len(t)), "r": round(float(t["R_adj"].sum()), 2),
            "dropped_unfillable": unf, "dropped_dupes": int(dupes), "haircut_r": haircut}


# ----------------------------------------------------------------------------------------------- capture buckets
def capture_buckets(moves: pd.DataFrame) -> dict:
    """Move Hunt capture (share of top moves caught by >= 1 right-side trade) in three buckets."""
    m = moves[moves["set"] == "all"] if "set" in moves else moves
    bo = m["blackout"].astype(str).str.lower().isin(("true", "1"))
    caught = m["n_right"].fillna(0) > 0

    def b(mask):
        n = int(mask.sum())
        return {"moves": n, "caught": int((caught & mask).sum()),
                "pct": None if n == 0 else round(float((caught & mask).sum()) / n * 100, 1)}
    return {"headline": b(pd.Series(True, index=m.index)), "tradable": b(~bo), "earnings_blackout": b(bo)}


# --------------------------------------------------------------------------------------------------- epoch pairs
def epoch_pairs(shadow: pd.DataFrame, baseline_id: str = "BASE1", start: str | None = None) -> dict:
    """Per session: current-book shadow R (of_live lots) vs baseline shadow R ("<id>:" lots) and the difference."""
    if shadow is None or shadow.empty:
        return {"days": [], "n": 0, "mean_diff": None, "sd": None, "se": None}
    t = shadow.copy()
    t["date"] = t["date"].astype(str)
    if start:
        t = t[t["date"] >= start]
    t["R"] = trade_r(t)
    pre = f"{baseline_id}:"
    is_b = t["strategy"].astype(str).str.startswith(pre)
    cur_t = t[~is_b]
    if "meta" in cur_t.columns:     # current book = of_live lots only (a future shadow-only setup is not the book)
        mode = cur_t["meta"].astype(str).str.extract(r"mode=(\w+)")[0].fillna("of_live")
        cur_t = cur_t[mode == "of_live"]
    cur = cur_t.groupby("date")["R"].sum()
    base = t[is_b].groupby("date")["R"].sum()
    days = sorted(set(base.index))           # sessions the baseline ran
    rows = [{"date": d, "current": round(float(cur.get(d, 0.0)), 2), "baseline": round(float(base.get(d, 0.0)), 2),
             "diff": round(float(cur.get(d, 0.0) - base.get(d, 0.0)), 2)} for d in days]
    diffs = [r["diff"] for r in rows]
    n = len(diffs)
    mean = sum(diffs) / n if n else None
    sd = (math.sqrt(sum((x - mean) ** 2 for x in diffs) / (n - 1)) if n > 1 else None)
    return {"days": rows, "n": n, "mean_diff": None if mean is None else round(mean, 2),
            "sd": None if sd is None else round(sd, 2), "se": None if sd is None else round(sd / math.sqrt(n), 2),
            "note": "paired SD target < 8R (C3-EPOCH); a verdict needs the difference beyond ~2 SE"}


# ---------------------------------------------------------------------------------------------- stale decisions
def stale_decisions(decisions: list[dict], inbox_dir: Path, today: str, nights: int = 3) -> int:
    """Open owner decisions first raised more than `nights` nights ago (first owner_inbox file naming the code)."""
    files = sorted(Path(inbox_dir).glob("20??-??-??.md"))
    first: dict[str, str] = {}
    open_codes = [str(d.get("code")) for d in decisions if d.get("status") == "open" and d.get("code")]
    for f in files:
        txt = f.read_text(errors="ignore")
        for c in open_codes:
            if c not in first and re.search(r"\b" + re.escape(c) + r"\b", txt):
                first[c] = f.stem
    lim = (pd.Timestamp(today) - pd.Timedelta(days=nights)).strftime("%Y-%m-%d")
    return sum(1 for c in open_codes if first.get(c, today) < lim)


# ------------------------------------------------------------------------------------------------------- journal
def from_journal(journal, day: str | None = None, cfg: dict | None = None, baseline_id: str = "BASE1") -> dict:
    """Scorecard + epoch pairs from a Primary journal (live run kind 'paper'/'live' = run 1; shadow = kind 'shadow')."""
    acct = (cfg or {}).get("account") or {}
    eq, rp = float(acct.get("starting_equity", 100_000)), float(acct.get("risk_per_trade_pct", 0.25))
    live = journal.trades(run_id=1)
    days = day_table(live, eq, rp)
    stale = None
    try:
        dec = json.loads((ROOT / "docs" / "live" / "decisions.json").read_text())
        stale = stale_decisions(dec, ROOT / "research" / "owner_inbox", day or (str(days.index.max()) if len(days) else "2100-01-01"))
    except Exception:
        pass
    sc = scorecard(days, day, stale)
    try:
        sh = journal.trades(kind="shadow")
    except Exception:
        sh = pd.DataFrame()
    b = (cfg or {}).get("baseline") or {}
    sc["epoch"] = {"epoch": b.get("epoch"), "since": b.get("epoch_start"),
                   **epoch_pairs(sh, b.get("id", baseline_id), b.get("epoch_start"))}
    sc["days_table"] = days.round(2).reset_index(names="date").to_dict("records")
    return sc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--journal", required=True)
    ap.add_argument("--day")
    ap.add_argument("--moves", help="research/bdi/moves/moves.csv for the capture buckets")
    ap.add_argument("--json", help="write the full scorecard here")
    a = ap.parse_args(argv)
    from ..config import load_config
    from ..journal import Journal

    cfg = load_config()
    sc = from_journal(Journal(a.journal), a.day, cfg)
    if a.moves:
        sc["capture"] = capture_buckets(pd.read_csv(a.moves))
    print(line(sc))
    e = sc["epoch"]
    print(f"Epoch {e.get('epoch')} since {e.get('since')}: {e['n']} paired sessions, mean current - BASE1 "
          f"{e['mean_diff']}R/day, SD {e['sd']}, SE {e['se']}")
    if a.json:
        Path(a.json).write_text(json.dumps(sc, indent=1, default=str))


if __name__ == "__main__":
    main()
