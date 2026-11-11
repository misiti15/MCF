"""REGSW forward shadow: journal-only tracking of the three closest REGSW switch candidates on live run-1 trades of the
REGSW target setups in every account. Nothing here touches config, orders or the live path.

Candidates (frozen 2026-11-11, research/regime_switch/NOTES.md; decision times 09:50 10:00 10:30 11:00 12:00 13:00, a
trade gets the state read at the last decision time <= its entry; trades before 09:50 are untouched):
  GAP-U   universal: shorts switched when SPY opened > +0.25% above the prior close, longs when < -0.25%
  IDX3-P  per-setup fingerprint (fits_P.csv, TRAIN only): switch the setup's worst IDX3 state
          (SPY, QQQ and IWM all > +0.10% from open = +1, all < -0.10% = -1, else 0)
  SPYO-P  per-setup fingerprint (fits_P.csv): switch the setup's worst SPY-from-open state (+-0.10%)
Each row: dR_off = -(R of switched trades), dR_half = dR_off / 2, plus avg R of switched vs kept trades.
R = pnl_adj / (|entry - stop| x shares), costs in as booked. Live trades are not re-simulated.

Writes / replaces rows per (date, cfg, account) in research/regime_switch/shadow_scoreboard.csv (idempotent) and the
running totals. kind = "forward" for dates >= 2026-11-11, else "backfill (in-sample)" (those sessions were in the
REGSW live check). Re-score after 20 forward sessions.

Usage (nightly, after 16:05 ET):  python research/regime_switch/shadow.py --date YYYY-MM-DD [YYYY-MM-DD ...] [--no-fetch]
Market data: read-only 1-min bar GET (the one compass_live uses). Educational only - not financial advice."""
from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]; HERE = Path(__file__).resolve().parent
BOARD = HERE / "shadow_scoreboard.csv"
NY = "America/New_York"; FORWARD_FROM = "2026-11-11"
DT = [590, 600, 630, 660, 720, 780]
ACCTS = {"mcf-data": "Primary", "mcf-data-testing": "Testing1", "mcf-data-testing2": "Testing2", "mcf-data-graveyard": "Graveyard",
         "mcf-data-livelab": "LiveLab", "mcf-data-explore1": "Explore1", "mcf-data-gen": "Gen"}
CFGS = ("GAP-U", "IDX3-P", "SPYO-P")
COLS = ["date", "cfg", "account", "kind", "n_trades", "base_R", "n_switched", "R_switched", "dR_off", "dR_half", "avgR_switched",
        "avgR_kept", "gap_pct", "states", "cum_base_R", "cum_dR_off", "cum_dR_half", "sessions", "updated_at"]


def _git(*a, binary=False):
    p = subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, check=True)
    return p.stdout if binary else p.stdout.decode()


def _min(col):
    ts = pd.to_datetime(col, utc=True, format="mixed").dt.tz_convert(NY)
    return ts.dt.hour * 60 + ts.dt.minute + ts.dt.second / 60


def fetch(day, syms):
    sys.path.insert(0, str(ROOT))
    from mcf.report import compass_live as CL
    return CL.fetch(day, syms, pd.Timestamp(f"{day} 16:00", tz=NY), log=lambda *a: None)


def states(day):
    """state per decision time for GAP / SPYO / IDX3 (+ the gap %)."""
    b = fetch(day, ["SPY", "QQQ", "IWM"])
    prev = None
    for k in range(1, 7):
        d0 = str((pd.Timestamp(day) - pd.tseries.offsets.BDay(k)).date())
        p = fetch(d0, ["SPY"]).get("SPY")
        if p is not None and len(p):
            prev = float(p.close.values[-1]); break
    fo = {}
    for s in ("SPY", "QQQ", "IWM"):
        x = b[s]; m = (x.index.hour * 60 + x.index.minute).values; o = float(x.open.values[0])
        fo[s] = [float(x.close.values[np.where(m <= T - 1)[0][-1]] / o - 1) if (m <= T - 1).any() else 0.0 for T in DT]
    gap = float(b["SPY"].open.values[0]) / prev - 1 if prev else np.nan
    th = lambda v, t: 1 if v > t else (-1 if v < -t else 0)
    out = {}
    for i, T in enumerate(DT):
        a, q, w = th(fo["SPY"][i], 0.001), th(fo["QQQ"][i], 0.001), th(fo["IWM"][i], 0.001)
        out[T] = dict(GAP=th(gap, 0.0025) if np.isfinite(gap) else 0, SPYO=a, IDX3=a if a == q == w else 0)
    return out, gap


def trades(branch, day, keep):
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        try:
            f.write(_git("show", f"origin/{branch}:journal.db", binary=True)); f.flush()
        except subprocess.CalledProcessError:
            return pd.DataFrame()
        c = sqlite3.connect(f.name)
        t = pd.read_sql("select strategy setup, side, entry_time, exit_time, entry, stop, shares, pnl_adj from trades "
                        "where run_id=1 and date=?", c, params=(day,))
        c.close()
    t = t[t.setup.isin(keep)].copy()
    den = (t.entry - t.stop).abs() * t.shares
    t["r"] = np.where(den > 0, t.pnl_adj / den, np.nan)
    t["e"] = _min(t.entry_time)
    return t.dropna(subset=["r", "e"])


def switched(cfg, t, st, fitP):
    b = np.searchsorted(np.array(DT), t.e.values, side="right") - 1
    out = np.zeros(len(t), bool)
    for i, (bk, side, su) in enumerate(zip(b, t.side.values, t.setup.values)):
        if bk < 0:
            continue
        s = st[DT[bk]]
        if cfg == "GAP-U":
            out[i] = (side < 0 and s["GAP"] == 1) or (side > 0 and s["GAP"] == -1)
        else:
            sig = cfg.split("-")[0]; tgt = fitP.get((sig, su))
            out[i] = tgt is not None and s[sig] == tgt
    return out


def upsert(rows):
    old = pd.read_csv(BOARD, dtype={"date": str}) if BOARD.exists() else pd.DataFrame(columns=COLS)
    new = pd.DataFrame(rows); keys = set(zip(new.date, new.cfg, new.account))
    old = old[[k not in keys for k in zip(old.date, old.cfg, old.account)]]
    df = (pd.concat([old, new], ignore_index=True) if len(old) else new).sort_values(["kind", "cfg", "account", "date"]).reset_index(drop=True)
    for c, s in (("cum_base_R", "base_R"), ("cum_dR_off", "dR_off"), ("cum_dR_half", "dR_half")):
        df[c] = df.groupby(["kind", "cfg", "account"])[s].cumsum()
    df["sessions"] = df.groupby(["kind", "cfg", "account"]).cumcount() + 1
    df.sort_values(["date", "cfg", "account"])[COLS].to_csv(BOARD, index=False, float_format="%.4f")
    return df


def run_day(day):
    keep = set(pd.read_csv(HERE / "targets.csv").query("in_lab").setup)
    fp = pd.read_csv(HERE / "fits_P.csv").dropna()
    fitP = {(r.signal, r.setup): int(r.state_switched) for r in fp.itertuples()}
    st, gap = states(day)
    sline = " ".join(f"{T // 60:02d}:{T % 60:02d}:G{v['GAP']:+d}S{v['SPYO']:+d}I{v['IDX3']:+d}" for T, v in st.items())
    rows = []
    for br, acct in ACCTS.items():
        t = trades(br, day, keep)
        for cfg in CFGS:
            sw = switched(cfg, t, st, fitP) if len(t) else np.zeros(0, bool)
            r = t.r.values if len(t) else np.zeros(0)
            rs = float(r[sw].sum())
            rows.append(dict(date=day, cfg=cfg, account=acct, kind="forward" if day >= FORWARD_FROM else "backfill (in-sample)",
                             n_trades=len(r), base_R=float(r.sum()), n_switched=int(sw.sum()), R_switched=rs, dR_off=-rs, dR_half=-rs / 2,
                             avgR_switched=rs / sw.sum() if sw.sum() else np.nan,
                             avgR_kept=float(r[~sw].sum() / (~sw).sum()) if (~sw).sum() else np.nan,
                             gap_pct=gap * 100, states=sline, updated_at=pd.Timestamp.now(tz=NY).strftime("%Y-%m-%d %H:%M ET")))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True, nargs="+"); ap.add_argument("--no-fetch", action="store_true")
    a = ap.parse_args(argv)
    if not a.no_fetch:
        subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "origin", *ACCTS], check=False)
    rows = []
    for d in a.date:
        rows += run_day(d); print(d, "done", flush=True)
    df = upsert(rows)
    tot = df.groupby(["kind", "cfg"]).agg(sessions=("date", "nunique"), base_R=("base_R", "sum"), dR_off=("dR_off", "sum"),
                                          dR_half=("dR_half", "sum"), n_switched=("n_switched", "sum"))
    print(tot.round(2).to_string()); print("Educational only - not financial advice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
