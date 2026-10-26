"""GEN exposure 2026-10-25: attribute screen-on-the-day signals -> replay -> live, per session (lab universe).

    python research/ops/genexposure1025_attrib.py FR_FIRST.csv REPLAY_RUN_DIR JOURNAL.db ENABLED.csv OUT.json

FR_FIRST.csv: genexposure1025_frames.py output (the screen's first qualifying bar per symbol-day on the day);
REPLAY_RUN_DIR: `python -m mcf.replay run --account gen --as-live --universe live` output (<dir>/gen/<date>/);
JOURNAL.db: the Gen journal (git show origin/mcf-data-gen:journal.db); ENABLED.csv: setups live per day.
For every screen row (live blackout variant, setups enabled that day, symbols in the replay's universe) it checks
  gate   whether the live 5-bar gate can act on that bar at all with a poll every minute: the 1-minute bar count at the
         signal's bar (the first 1-minute bar at or after the bucket's 4th minute) must be a multiple of 5 - the
         runner acts only when that bar is the latest bar and LabStrategy.eligible only when len(bars) % 5 == 0;
         when the first qualifying bar fails this, the symbol-day is lost for the setup (no later bar can fire:
         generate() returns only the first hit)
  replay whether the replay (the live engine, every minute) signalled (setup, symbol) that day
  live   whether the live journal did.
Research only; nothing here trades. Educational only - not financial advice.
"""
from __future__ import annotations

import json
import sqlite3
import sys

import pandas as pd

from mcf.replay import store as RS


def gate_ok(bars: pd.DataFrame | None, tod: int, day: str) -> bool:
    if bars is None or not len(bars):
        return False
    close = pd.Timestamp(f"{day} {tod // 100:02d}:{tod % 100:02d}", tz=RS.TZ)
    end = bars.index.searchsorted(close - pd.Timedelta(minutes=1))
    return end < len(bars) and (end + 1) % 5 == 0


def main(fr, run, jdb, en, out):
    F = pd.read_csv(fr)
    F = F[F.blackout == "live"]
    E = pd.read_csv(en)
    L = pd.read_sql("select day, symbol, strategy, status from signals", sqlite3.connect(jdb))
    res = {}
    rows = []
    for d, grp in E.groupby("day"):
        on = set(grp.k)
        R = pd.read_csv(f"{run}/gen/{d}/signals.csv.gz")
        st = json.load(open(f"{run}/gen/{d}/stats.json"))
        bars = RS.load_day(pd.Timestamp(d).date())
        uni = set(bars)       # the store's symbols; the replay universe is this ∩ live universe - blackout
        f = F[(F.date == d) & F.setup.isin(on)].copy()
        f["gate"] = [gate_ok(bars.get(s), int(t), d) for s, t in zip(f.symbol, f.tod)]
        kr = set(zip(R.strategy, R.symbol))
        kl = set(zip(L[L.day == d].strategy, L[L.day == d].symbol))
        f["replay"] = [(a, b) in kr for a, b in zip(f.setup, f.symbol)]
        f["live"] = [(a, b) in kl for a, b in zip(f.setup, f.symbol)]
        ks = set(zip(f.setup, f.symbol))
        r_extra = len(kr - ks)
        lab = set(open(RS.SYMBOLS_FILE).read().split())
        l_lab = {k for k in kl if k[1] in lab}
        res[d] = {"setups": len(on), "per_day_2y_sum": round(float(grp.pd.sum()), 1), "screen_on_day": len(f),
                  "screen_gate_ok": int(f.gate.sum()), "replay_signals": len(kr),
                  "replay_matched_screen": int(f.replay.sum()), "replay_gate_ok_matched": int((f.gate & f.replay).sum()),
                  "screen_gate_ok_not_replay": int((f.gate & ~f.replay).sum()),
                  "replay_not_in_screen": r_extra,
                  "replay_submitted": int((R.status == "submitted").sum()),
                  "replay_skips": R[R.status != "submitted"].reason.str.replace(r"\d+", "#", regex=True)
                  .value_counts().to_dict(),
                  "live_signals": len(kl), "live_lab_signals": len(l_lab), "live_matched_screen": int(f.live.sum()),
                  "live_matched_replay": len(kl & kr), "live_lab_not_screen": len(l_lab - ks),
                  "live_submitted": int(((L.day == d) & (L.status == "submitted")).sum()),
                  "replay_universe_symbols": st["inputs"].get("symbols"), "polls_replay": st.get("polls")}
        rows.append(f)
        print(d, res[d], flush=True)
    pd.concat(rows).to_csv(out.replace(".json", "_rows.csv"), index=False)
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:6])
