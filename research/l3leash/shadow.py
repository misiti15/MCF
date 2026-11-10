"""LEASH shadow (owner 2026-11-10 ~13:30 ET "LEASH shadow yes"): forward, paper-only tracking of two leashes on the live
Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` trades. Nothing here touches config, orders or the live path.

For one session it reads the setup's live trades from Primary (origin/mcf-data journal.db, run_id 1, plus the run_id 2
what-ifs that the -2R setup latch blocked) and Testing 1 (origin/mcf-data-testing journal.db, run_id 1) and scores:
  base   actual R of the run-1 trades (pnl_adj / (|entry - stop| x shares), costs in as booked)
  base_sim  the same candidates re-simulated in entry order with the -2R per-setup realised-R latch (like-for-like
         reference for the two leashes; equals base when the live latch acted as modelled)
  K11    0.5x size for an entry when SPY >= +0.40% from its open (1-min SIP bar closed by the entry minute), -2R latch kept
  K12    per-setup daily stop -1R (instead of -2R) once the production Market Compass (W60) has read UP-confirmed at any
         15-min mark <= the entry (origin/mcf-data-compass compass/<day>.csv; days before 11-06 recomputed with
         mcf.report.compass_live, production code, or read from --compass-parquet)
  dK11 / dK12 = leash - base_sim.

Writes / replaces one row per (date, account) in research/l3leash/shadow_scoreboard.csv (idempotent) and recomputes the
running totals (cum_*) per account and kind. kind = "forward" for dates >= 2026-11-10, else "backfill (in-sample)".
11-10 is flagged seen_at_design=1: K11 / K12 were declared (research/l3leash) after its morning was seen.
Re-score target: 20 forward sessions after 11-10 (research/l3leash2/NOTES.md).

Usage (nightly, after 16:05 ET):  python research/l3leash/shadow.py --date YYYY-MM-DD
  options: --no-fetch (skip `git fetch` of the data branches), --compass-parquet P / --spy-parquet P (backfill caches
  written by research/l3leash/live_compass.py). Market data: read-only 1-min bar GET (the same one compass_live uses).
Educational only - not financial advice."""
from __future__ import annotations

import argparse
import io
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BOARD = Path(__file__).resolve().parent / "shadow_scoreboard.csv"
SETUP = "L3-gap-slope-fromopen-FD"
NY = "America/New_York"
FORWARD_FROM = "2026-11-10"
SEEN_AT_DESIGN = {"2026-11-10"}
ACCOUNTS = (("Primary", "mcf-data", True), ("Testing1", "mcf-data-testing", False))   # (name, branch, use latch what-ifs)
W60 = {"UP-confirmed": 2, "leaning up": 1, "neutral": 0, "leaning down": -1, "DOWN-confirmed": -2}
COLS = ["date", "account", "kind", "seen_at_design", "n_trades", "n_whatif", "base_R", "base_sim_R", "K11_R", "K12_R", "dK11",
        "dK12", "n_half_K11", "n_cut_K12", "first_up_conf", "spy_fo_max_at_entry", "compass_src", "spy_src", "cum_base_R",
        "cum_K11_R", "cum_K12_R", "cum_dK11", "cum_dK12", "sessions", "updated_at"]


# ------------------------------------------------------------------------------------------------ pure scoring
def simulate(r: np.ndarray, e: np.ndarray, x: np.ndarray, w: np.ndarray, upso: np.ndarray | None = None,
             latch: float = -2.0, latch_up: float | None = None) -> np.ndarray:
    """Per-trade weight taken (0 = blocked) for one setup-day, candidates sorted by entry. The realised-R latch blocks new
    entries once closed R <= latch (or <= latch_up once upso[i] is true). Weights scale R (0.5 = half size)."""
    took = np.zeros(len(r)); open_: list[tuple[float, float]] = []; real = 0.0
    for i in range(len(r)):
        still = []
        for xx, rc in open_:
            if xx <= e[i]:
                real += rc
            else:
                still.append((xx, rc))
        open_ = still
        lim = latch_up if (latch_up is not None and upso is not None and upso[i]) else latch
        if real <= lim + 1e-12 or w[i] <= 0:
            continue
        took[i] = w[i]; open_.append((x[i], w[i] * r[i]))
    return took


def score(t: pd.DataFrame) -> dict:
    """t: one account-day with columns r, e, x (minutes since midnight ET), run_id (1 live, 2 latch what-if), spy_fo (%),
    upso (compass UP-confirmed at a mark <= entry). Returns the scoreboard numbers."""
    t = t.sort_values(["e", "x"]).reset_index(drop=True)
    r, e, x = t.r.values.astype(float), t.e.values.astype(float), t.x.values.astype(float)
    one = np.ones(len(t)); upso = t.upso.values.astype(bool)
    half = np.where(t.spy_fo.values >= 0.40, 0.5, 1.0)
    b = simulate(r, e, x, one); k11 = simulate(r, e, x, half); k12 = simulate(r, e, x, one, upso, -2.0, -1.0)
    live = t.run_id.values == 1
    R = lambda w: float((w * r).sum())
    return dict(n_trades=int(live.sum()), n_whatif=int((~live).sum()), base_R=float(r[live].sum()), base_sim_R=R(b),
                K11_R=R(k11), K12_R=R(k12), dK11=R(k11) - R(b), dK12=R(k12) - R(b),
                n_half_K11=int(((k11 > 0) & (k11 < 1)).sum()), n_cut_K12=int(((b > 0) & (k12 == 0)).sum()),
                spy_fo_max_at_entry=float(np.nanmax(t.spy_fo.values)) if len(t) and np.isfinite(t.spy_fo.values).any() else np.nan)


def upsert(board: Path, rows: list[dict]) -> pd.DataFrame:
    """Replace rows with the same (date, account), then recompute running totals per (account, kind)."""
    old = pd.read_csv(board, dtype={"date": str}) if board.exists() else pd.DataFrame(columns=COLS)
    new = pd.DataFrame(rows)
    keys = set(zip(new.date, new.account))
    old = old[[k not in keys for k in zip(old.date, old.account)]]
    df = pd.concat([old, new], ignore_index=True) if len(old) else new
    df = df.sort_values(["kind", "account", "date"]).reset_index(drop=True)
    for c, s in (("cum_base_R", "base_R"), ("cum_K11_R", "K11_R"), ("cum_K12_R", "K12_R"), ("cum_dK11", "dK11"), ("cum_dK12", "dK12")):
        df[c] = df.groupby(["kind", "account"])[s].cumsum()
    df["sessions"] = df.groupby(["kind", "account"]).cumcount() + 1
    df = df.sort_values(["date", "account"]).reset_index(drop=True)
    df[COLS].to_csv(board, index=False, float_format="%.4f")
    return df


# ------------------------------------------------------------------------------------------------ data access (read-only)
def _git(*a: str, binary: bool = False):
    p = subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, check=True)
    return p.stdout if binary else p.stdout.decode()


def _minutes(col: pd.Series) -> pd.Series:
    ts = pd.to_datetime(col, utc=True, format="mixed").dt.tz_convert(NY)
    return ts.dt.hour * 60 + ts.dt.minute + ts.dt.second / 60


def trades(branch: str, day: str, whatifs: bool) -> pd.DataFrame:
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        f.write(_git("show", f"origin/{branch}:journal.db", binary=True)); f.flush()
        c = sqlite3.connect(f.name)
        t = pd.read_sql("select run_id, symbol, entry_time, exit_time, entry, stop, shares, pnl_adj, r_multiple, meta from trades "
                        "where strategy=? and date=? and run_id in (1, 2)", c, params=(SETUP, day))
        c.close()
    why = t.meta.fillna("").str.extract(r"why=(.*)$")[0]
    t = t[(t.run_id == 1) | (whatifs & (why == "setup daily loss limit"))].copy()
    t["r"] = np.where(t.run_id == 1, t.pnl_adj / ((t.entry - t.stop).abs() * t.shares), t.r_multiple)
    t["e"] = _minutes(t.entry_time); t["x"] = _minutes(t.exit_time)
    return t.dropna(subset=["r", "x", "e"])


def compass_marks(day: str, parquet: str | None) -> tuple[np.ndarray, np.ndarray, str]:
    """(mark minutes, W60 code) for the day: production compass rows, else research parquet, else recompute."""
    try:
        df = pd.read_csv(io.StringIO(_git("show", f"origin/mcf-data-compass:compass/{day}.csv"))); src = "compass_live rows"
    except subprocess.CalledProcessError:
        df = None
    if df is None and parquet and Path(parquet).exists():
        df = pd.read_parquet(parquet); df = df[df.date == day]; src = "live_compass.py parquet"
        df = df if len(df) else None
    if df is None:
        sys.path.insert(0, str(ROOT))
        from mcf.report import compass_live as CL
        names = CL.universe(); syms = list(dict.fromkeys(["SPY", "QQQ", "IWM"] + names))
        now = pd.Timestamp(f"{day} 16:00", tz=NY)
        df = pd.DataFrame(CL.compute(CL.fetch(day, syms, now, log=lambda *a: None), day, now, names)); src = "recomputed (compass_live)"
    T = df["T"].astype(str)
    m = (T.str[:2].astype(int) * 60 + T.str[3:5].astype(int)).values
    return m, df.w60.map(W60).fillna(0).astype(int).values, src


def spy_bars(day: str, parquet: str | None) -> tuple[pd.DataFrame, str]:
    if parquet and Path(parquet).exists():
        b = pd.read_parquet(parquet); b = b[b.date == day]
        if len(b):
            return b, "live_compass.py parquet"
    sys.path.insert(0, str(ROOT))
    from mcf.report import compass_live as CL
    return CL.fetch(day, ["SPY"], pd.Timestamp(f"{day} 16:00", tz=NY), log=lambda *a: None)["SPY"], "1-min SIP GET"


def spy_fo_at(b: pd.DataFrame, e_min: np.ndarray) -> np.ndarray:
    """SPY % from its open using the last 1-min bar that closed by the entry minute (bar start <= entry - 1)."""
    idx = pd.to_datetime(b.index)
    idx = idx.tz_localize(NY) if idx.tz is None else idx.tz_convert(NY)
    m = (idx.hour * 60 + idx.minute).values
    o = float(b.open.values[0]); c = b.close.values
    out = []
    for e in e_min:
        k = np.where(m <= int(e) - 1)[0]
        out.append((c[k[-1]] / o - 1) * 100 if len(k) else 0.0)
    return np.array(out)


def run_day(day: str, compass_parquet: str | None = None, spy_parquet: str | None = None) -> list[dict]:
    mk, w, csrc = compass_marks(day, compass_parquet)
    up = mk[w == 2]
    first_up = f"{up.min() // 60:02d}:{up.min() % 60:02d}" if len(up) else ""
    bars = None; ssrc = ""
    rows = []
    for acct, br, wi in ACCOUNTS:
        t = trades(br, day, wi)
        if len(t):
            if bars is None:
                bars, ssrc = spy_bars(day, spy_parquet)
            t["spy_fo"] = spy_fo_at(bars, t.e.values)
            t["upso"] = [bool(((mk <= e) & (w == 2)).any()) for e in t.e.values]
            s = score(t)
        else:
            s = dict(n_trades=0, n_whatif=0, base_R=0.0, base_sim_R=0.0, K11_R=0.0, K12_R=0.0, dK11=0.0, dK12=0.0, n_half_K11=0,
                     n_cut_K12=0, spy_fo_max_at_entry=np.nan)
        rows.append(dict(date=day, account=acct, kind="forward" if day >= FORWARD_FROM else "backfill (in-sample)",
                         seen_at_design=int(day in SEEN_AT_DESIGN), **s, first_up_conf=first_up, compass_src=csrc,
                         spy_src=ssrc, updated_at=pd.Timestamp.now(tz=NY).strftime("%Y-%m-%d %H:%M ET")))
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True, nargs="+", help="session date(s) YYYY-MM-DD")
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--compass-parquet"); ap.add_argument("--spy-parquet")
    a = ap.parse_args(argv)
    now = pd.Timestamp.now(tz=NY)
    if not a.no_fetch:
        for br in ("mcf-data", "mcf-data-testing", "mcf-data-compass"):
            subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "origin", br], check=False)
    rows = []
    for d in a.date:
        if d == now.strftime("%Y-%m-%d") and now.hour * 60 + now.minute < 16 * 60 + 5:
            print(f"{d}: session not closed yet (before 16:05 ET) - skipped"); continue
        rows += run_day(d, a.compass_parquet, a.spy_parquet)
    if not rows:
        return 0
    df = upsert(BOARD, rows)
    for r in rows:
        print(f"{r['date']} {r['account']:8s} {r['kind']}: n {r['n_trades']} base {r['base_R']:+.2f}R (sim {r['base_sim_R']:+.2f}) "
              f"K11 {r['K11_R']:+.2f} ({r['dK11']:+.2f}) K12 {r['K12_R']:+.2f} ({r['dK12']:+.2f}) up-conf {r['first_up_conf'] or '-'}")
    f = df[(df.kind == "forward") & (df.seen_at_design == 0)]
    print(f"forward sessions after 11-10: {f.date.nunique()} of 20 (re-score target); "
          + "; ".join(f"{a_} dK11 {g.dK11.sum():+.2f} dK12 {g.dK12.sum():+.2f}" for a_, g in f.groupby("account")))
    print("Educational only - not financial advice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
