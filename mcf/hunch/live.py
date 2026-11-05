"""Hunch live shadow: real guesses on live 3-min bars, scored and learned from, no orders (owner 2026-11-04).

Each trading day (.github/workflows/hunch.yml, one light job, concurrency group `hunch`):
  * start-of-day model = state/model.npz on branch mcf-data-hunch (the end of the previous day), or the seed from
    the replay (research/hunch/u200/state/M1_model.npz) on the first day
  * every 3 minutes (35 s after each 3-min bar closes) it reads 1-min bars for the universe from Alpaca market data
    (read-only GETs with the existing data keys; this module imports no order / trading code), rebuilds the
    point-in-time features (mcf.hunch.data), and walks today's bars from the start-of-day model in the same order as
    the replay: guess bar b, then - once bar b+1 has closed - score it and update every Hunch (one logistic learner
    per ticker, each on its own guesses) and the pooled model (all tickers), then guess bar b+1
  * a guess is written to guesses/<day>.csv the first time it is made and never revised (`guessed_at`); outcomes
    and hits are filled in when the next bar closes. scoreboard.csv / scoreboard.md keep the running record.
  * after 16:00 ET the end-of-day model is saved as state/model.npz (+ state/model_<day>.npz) for the next day.
Restart-safe: each tick recomputes today from the start-of-day model, so a crash or the 6-hour job hand-over costs
nothing but the minutes it was down. Live shadow results are labelled as such and kept apart from replay results
(RESEARCH_RULES 7). Educational only - not financial advice.
"""
from __future__ import annotations

import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from . import data as D
from . import learners as Lr
from . import metrics as M

ET = D.TZ
LAG_S = 35          # seconds after a bar's close before it counts as closed
GUESS_COLS = ["date", "b", "bar_close", "symbol", "guessed_at", "p_pooled", "guess_pooled", "p_own", "guess_own",
              "same_last", "mom20", "base_rate"]
DISCLAIMER = "Educational only — not financial advice."


# ------------------------------------------------------------------------------------------------ model state


def load_model(path: Path) -> dict:
    z = np.load(path, allow_pickle=False)
    feats = [str(f) for f in z["feats"]]
    syms = [str(s) for s in z["symbols"]]
    tod = feats.index("tod")
    pooled = Lr.LogReg(len(feats), tod, n_groups=len(syms))
    pooled.w, pooled.wg = z["p_w"].copy(), z["p_wg"].copy()
    pooled.sc.mu, pooled.sc.m2, pooled.sc.n = z["p_mu"].copy(), z["p_m2"].copy(), z["p_n"].copy()
    pooled.rows = int(z["p_rows"])
    tick = Lr.PerTicker(len(syms), len(feats), tod)
    tick.W, tick.mu, tick.m2, tick.n, tick.rows = (z["t_W"].copy(), z["t_mu"].copy(), z["t_m2"].copy(),
                                                   z["t_n"].copy(), z["t_rows"].copy())
    return {"metric": str(z["metric"]), "last_date": str(z["last_date"]), "symbols": syms, "feats": feats,
            "pooled": pooled, "ticker": tick, "yes_n": float(z["yes_n"]), "tot_n": float(z["tot_n"])}


def save_model(m: dict, path: Path, last_date: str) -> None:
    p, t = m["pooled"], m["ticker"]
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp.npz")
    np.savez_compressed(tmp, metric=m["metric"], last_date=last_date, symbols=np.array(m["symbols"]),
                        feats=np.array(m["feats"]), yes_n=m["yes_n"], tot_n=m["tot_n"],
                        p_w=p.w, p_wg=p.wg, p_mu=p.sc.mu, p_m2=p.sc.m2, p_n=p.sc.n, p_rows=p.rows,
                        t_W=t.W, t_mu=t.mu, t_m2=t.m2, t_n=t.n, t_rows=t.rows)
    tmp.replace(path)


def _copy_model(m: dict) -> dict:
    import copy

    return {**m, "pooled": copy.deepcopy(m["pooled"]), "ticker": copy.deepcopy(m["ticker"])}


# ------------------------------------------------------------------------------------------------ one day


def bar_close(day: str, b: int) -> pd.Timestamp:
    return pd.Timestamp(f"{day} 09:30", tz=ET) + pd.Timedelta(minutes=3 * (b + 1))


def walk_day(model: dict, panel: pd.DataFrame, day: str, now: pd.Timestamp) -> tuple[pd.DataFrame, dict, bool]:
    """Walk today's closed bars from the start-of-day `model` (copied; the input is not changed).
    Returns (guesses with outcomes so far, the model after the last scored bar, whether the day is complete)."""
    m = _copy_model(model)
    met, feats, syms = m["metric"], m["feats"], m["symbols"]
    sidx = {s: i for i, s in enumerate(syms)}
    p = panel[panel["symbol"].isin(sidx)].sort_values(["symbol", "date", "b"], kind="mergesort").reset_index(drop=True)
    p["y"] = M.label(p, met)
    p["same_last"] = M.same_last(p, met)
    p["mom20"] = M.mom20(p, met)
    p["next_filled"] = p.groupby(["symbol", "date"], sort=False)["filled"].shift(-1).fillna(1).to_numpy()
    t = p[p["date"].astype(str) == day]
    closed_b = [b for b in range(D.GUESS_FIRST, D.GUESS_LAST + 1) if bar_close(day, b) + pd.Timedelta(seconds=LAG_S) <= now]
    out = []
    pending = None  # (rows, X, idx) guessed at the previous bar, waiting for their answer
    for b in closed_b:
        r = t[(t["b"] == b) & (t["filled"] == 0) & (t["warmup"] == 0) & np.isfinite(t["atr"].to_numpy())]
        if pending is not None:
            pr, pX, pidx = pending
            known = bar_close(day, b) + pd.Timedelta(seconds=LAG_S) <= now  # bar b (= previous b + 1) has closed
            if known:
                y = pr["y"].to_numpy(dtype=float)
                ok = np.isfinite(y) & (pr["next_filled"].to_numpy() == 0)
                if ok.any():
                    m["pooled"].update(pX[ok], y[ok], pidx[ok])
                    m["ticker"].update(pX[ok], y[ok], pidx[ok])
                    m["yes_n"] += float(y[ok].sum())
                    m["tot_n"] += float(ok.sum())
        if not len(r):
            pending = None
            continue
        X = r[feats].to_numpy(dtype=float)
        idx = r["symbol"].map(sidx).to_numpy()
        pp = m["pooled"].proba(X, idx)
        po = m["ticker"].proba(X, idx)
        g = pd.DataFrame({"date": day, "b": b, "bar_close": bar_close(day, b).strftime("%H:%M"),
                          "symbol": r["symbol"].to_numpy(), "p_pooled": pp.round(4), "guess_pooled": (pp > 0.5).astype(int),
                          "p_own": po.round(4), "guess_own": (po > 0.5).astype(int),
                          "same_last": r["same_last"].to_numpy(), "mom20": r["mom20"].to_numpy(),
                          "base_rate": int(m["tot_n"] > 0 and m["yes_n"] / m["tot_n"] > 0.5),
                          "_y": r["y"].to_numpy(), "_nf": r["next_filled"].to_numpy()})
        out.append(g)
        pending = (r, X, idx)
    # the last guessed bar's answer arrives when the bar after it closes
    if pending is not None and closed_b:
        nb = closed_b[-1] + 1
        if bar_close(day, nb) + pd.Timedelta(seconds=LAG_S) <= now:
            pr, pX, pidx = pending
            y = pr["y"].to_numpy(dtype=float)
            ok = np.isfinite(y) & (pr["next_filled"].to_numpy() == 0)
            if ok.any():
                m["pooled"].update(pX[ok], y[ok], pidx[ok])
                m["ticker"].update(pX[ok], y[ok], pidx[ok])
                m["yes_n"] += float(y[ok].sum())
                m["tot_n"] += float(ok.sum())
    g = pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=GUESS_COLS + ["_y", "_nf"])
    known_until = now - pd.Timedelta(seconds=LAG_S)
    if len(g):
        ans = np.array([bar_close(day, int(b) + 1) <= known_until for b in g["b"]], bool)
        yk = np.where(ans & (g["_nf"].to_numpy() == 0), g["_y"].to_numpy(dtype=float), np.nan)
    else:
        yk = np.zeros(0)
    g["outcome"] = yk
    for c in ("guess_pooled", "guess_own", "same_last", "mom20", "base_rate"):
        g[f"hit_{c.replace('guess_', '')}"] = np.where(np.isfinite(yk), (g[c].to_numpy(dtype=float) == yk).astype(float), np.nan)
    g = g.drop(columns=["_y", "_nf"])
    complete = bar_close(day, D.GUESS_LAST + 1) + pd.Timedelta(seconds=LAG_S) <= now
    return g, m, complete


def merge_frozen(old: pd.DataFrame | None, new: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    """Keep every guess exactly as first written; take outcomes / hits from the newest computation."""
    new = new.copy()
    new["guessed_at"] = now.strftime("%H:%M:%S")
    # a guess first written more than one bar after its bar closed (a restart catching up) is a backfill: kept in
    # the file for the record but left out of the live scoreboard
    if len(new):
        close = pd.to_datetime(new["date"].astype(str) + " " + new["bar_close"]).dt.tz_localize(ET)
        new["backfill"] = ((now - close).dt.total_seconds() > 180 + LAG_S).astype(int).to_numpy()
    else:
        new["backfill"] = []
    if old is None or not len(old):
        return new
    key = ["b", "symbol"]
    frozen = ["guessed_at", "backfill", "p_pooled", "guess_pooled", "p_own", "guess_own", "same_last", "mom20", "base_rate"]
    o = old.set_index(key)
    n = new.set_index(key)
    both = n.index.intersection(o.index)
    n.loc[both, frozen] = o.loc[both, frozen]
    # re-score the frozen guesses against the newest outcome
    yk = n["outcome"].to_numpy(dtype=float)
    for c in ("guess_pooled", "guess_own", "same_last", "mom20", "base_rate"):
        n[f"hit_{c.replace('guess_', '')}"] = np.where(np.isfinite(yk), (n[c].to_numpy(dtype=float) == yk).astype(float), np.nan)
    gone = o.index.difference(n.index)  # a guess already written stays in the record even if a recompute drops it
    out = pd.concat([n, o.loc[gone]]).reset_index()
    return out.sort_values(["b", "symbol"]).reset_index(drop=True)


def scoreboard(state: Path) -> pd.DataFrame:
    rows = []
    for f in sorted((state / "guesses").glob("*.csv")):
        g = pd.read_csv(f)
        bf = int(g["backfill"].sum()) if "backfill" in g else 0
        s = g[np.isfinite(g["outcome"]) & (g.get("backfill", 0) == 0)] if len(g) else g
        r = {"date": f.stem, "guesses": len(g), "scored": len(s), "backfill": bf,
             "tickers": g["symbol"].nunique() if len(g) else 0}
        for c in ("pooled", "own", "same_last", "mom20", "base_rate"):
            r[f"hit_{c}"] = round(float(s[f"hit_{c}"].mean()), 4) if len(s) else np.nan
        rows.append(r)
    sb = pd.DataFrame(rows)
    if len(sb):
        sb.to_csv(state / "scoreboard.csv", index=False)
        tot = {c: np.average(sb[f"hit_{c}"].fillna(0), weights=sb["scored"]) if sb["scored"].sum() else np.nan
               for c in ("pooled", "own", "same_last", "mom20", "base_rate")}
        lines = ["# Hunch live shadow scoreboard", "",
                 f"*{DISCLAIMER} Live shadow guesses only — no orders. Metric M1: {M.DESCRIBE['M1']}. Hit rates "
                 "count live guesses only (a guess first written > 1 bar after its bar closed, after a restart, is a "
                 "backfill and is left out). Replay results are in research/hunch/ and are not mixed in.*", "",
                 "| day | tickers | scored | pooled | own (per ticker) | same_last | mom20 | base_rate |",
                 "|---|---|---|---|---|---|---|---|"]
        for _, r in sb.iterrows():
            lines.append(f"| {r['date']} | {r['tickers']} | {r['scored']:,} | " + " | ".join(
                "—" if not np.isfinite(r[f'hit_{c}']) else f"{r[f'hit_{c}'] * 100:.2f}%"
                for c in ("pooled", "own", "same_last", "mom20", "base_rate")) + " |")
        lines.append(f"| **all** | | {int(sb['scored'].sum()):,} | " + " | ".join(
            f"**{tot[c] * 100:.2f}%**" if np.isfinite(tot[c]) else "—"
            for c in ("pooled", "own", "same_last", "mom20", "base_rate")) + " |")
        (state / "scoreboard.md").write_text("\n".join(lines) + "\n")
    return sb


# ------------------------------------------------------------------------------------------------ data + loop


class Bars:
    """1-min bars for the universe from Alpaca market data (read-only), fetched incrementally."""

    def __init__(self, symbols, feed: str | None = None, fetch=None):
        self.symbols = list(dict.fromkeys(list(symbols) + D.CONTEXT))
        self.feed = feed or os.environ.get("ALPACA_DATA_FEED", "sip")
        self.data: dict[str, pd.DataFrame] = {}
        self.since: pd.Timestamp | None = None
        self._fetch = fetch

    def _get(self, syms, start, end):
        if self._fetch:
            return self._fetch(syms, start, end)
        from mcf.data.alpaca_data import fetch_bars  # StockHistoricalDataClient: market data only

        return fetch_bars(syms, start.to_pydatetime(), end.to_pydatetime(), feed=self.feed)

    def refresh(self, now: pd.Timestamp, days_back: int = 7):
        start = self.since - pd.Timedelta(minutes=5) if self.since is not None else now.normalize() - pd.Timedelta(days=days_back)
        end = now
        for i in range(0, len(self.symbols), 100):
            chunk = self.symbols[i:i + 100]
            for attempt in range(3):
                try:
                    got = self._get(chunk, start, end)
                    break
                except Exception as e:  # network hiccup: retry, then carry on with what we have
                    print(f"  fetch failed ({type(e).__name__}): retry {attempt + 1}", flush=True)
                    time.sleep(5)
            else:
                got = {}
            for s, df in got.items():
                old = self.data.get(s)
                df = pd.concat([old, df]) if old is not None else df
                self.data[s] = df[~df.index.duplicated(keep="last")].sort_index()
        self.since = now

    def loader(self, s):
        return self.data.get(s)


def _git(state: Path, *args) -> bool:
    return subprocess.run(["git", "-C", str(state), *args], capture_output=True, text=True).returncode == 0


def push(state: Path, msg: str, branch: str = "mcf-data-hunch") -> None:
    ident = ["-c", "user.name=mcf-bot", "-c", "user.email=mcf-bot@users.noreply.github.com"]
    _git(state, "add", "-A")
    if subprocess.run(["git", "-C", str(state), "diff", "--cached", "--quiet"]).returncode == 0:
        return
    _git(state, *ident, "commit", "-q", "-m", msg)
    for _ in range(3):
        if _git(state, "push", "-q", "origin", f"HEAD:{branch}"):
            return
        _git(state, *ident, "pull", "-q", "--rebase", "--depth", "1", "origin", branch) or _git(state, "rebase", "--abort")
    print("  push failed (will retry next save)", flush=True)


def run_live(state: Path, seed: Path | None, do_push: bool = False, max_minutes: float = 340, bars: Bars | None = None,
             clock=None, sleep=time.sleep) -> str:
    """The shadow loop for one trading day. Returns why it stopped."""
    clock = clock or (lambda: pd.Timestamp.now(tz=ET))
    t0 = clock()
    day = t0.strftime("%Y-%m-%d")
    if t0.dayofweek >= 5:
        return "weekend"
    mp = state / "state" / "model.npz"
    if mp.exists():
        model = load_model(mp)
    elif seed and Path(seed).exists():
        model = load_model(Path(seed))
    else:
        return "no model state (state/model.npz or --seed)"
    if model["last_date"] >= day:
        return f"day {day} already finalized"
    bars = bars or Bars(model["symbols"])
    gpath = state / "guesses" / f"{day}.csv"
    gpath.parent.mkdir(parents=True, exist_ok=True)
    tick = 0
    while True:
        now = clock()
        if (now - t0).total_seconds() / 60 > max_minutes:
            push(state, f"hunch {day} hand-over") if do_push else None
            return "max minutes (hand-over to the next queued run)"
        first_close = bar_close(day, D.GUESS_FIRST) + pd.Timedelta(seconds=LAG_S)
        if now < first_close:
            sleep(min(60.0, (first_close - now).total_seconds()))
            continue
        bars.refresh(now)
        spy = bars.data.get("SPY")
        if (spy is None or not (spy.index.strftime("%Y-%m-%d") == day).any()) and now.hour * 60 + now.minute > 10 * 60 + 15:
            return "no SPY bars today after 10:15 ET (market holiday?)"
        syms = [s for s in model["symbols"] if s in bars.data]
        panel = D.build_panel(syms, loader=bars.loader)
        g, m_after, complete = walk_day(model, panel, day, now)
        old = pd.read_csv(gpath) if gpath.exists() else None
        g = merge_frozen(old, g, now)
        g.to_csv(gpath, index=False)
        scoreboard(state)
        tick += 1
        sc = g[np.isfinite(g["outcome"])]
        print(f"  {now:%H:%M:%S} guesses {len(g)} scored {len(sc)} hit pooled "
              f"{sc['hit_pooled'].mean() if len(sc) else float('nan'):.4f} own "
              f"{sc['hit_own'].mean() if len(sc) else float('nan'):.4f}", flush=True)
        if complete:
            save_model(m_after, mp, day)
            save_model(m_after, state / "state" / f"model_{day}.npz", day)
            push(state, f"hunch {day} final") if do_push else None
            return "day complete"
        if do_push and tick % 5 == 0:
            push(state, f"hunch {day} {now:%H:%M}")
        nxt = now.floor("3min") + pd.Timedelta(minutes=3)
        sleep(max(1.0, (nxt + pd.Timedelta(seconds=LAG_S) - clock()).total_seconds()))
