"""Rank every scored CWT configuration for the Testing 2 batch (owner 2026-10-12). Educational only - not financial
advice. NONE of these passed the gates; this ranking only orders failures for an owner-directed forward test.

Rule (fixed before choosing): all scored intraday configurations of packages A (566), B (368) and the intraday rows of
C (8) are ranked by open-history expectancy after costs (R = 0.25 x daily ATR). A configuration is eligible when
  1. n >= 150 on the open two-year history,
  2. the live LabStrategy can run it faithfully: decision bars 09:50-15:00 at a 5-minute close, the fixed
     t1s1 / t05s1 / t1s05 exit flat at 15:55, and only data the live frame carries (today's 5-minute bars from 09:35,
     prior-day high/low/close, daily ATR, the gap, the prior 60 5-minute bars),
  3. it is the best eligible exit/window of its signal (one configuration per signal: two configurations with the
     same entry rule would fire on the same symbol-day and starve each other under one-position-per-symbol),
  4. at most 4 per family (diversity).
Output: ranking.csv (every configuration, its eligibility reason and whether it was chosen).

    python research/bdi/cwt/live/rank.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
CWT = HERE.parent
sys.path.insert(0, str(HERE))
from selection import S  # noqa: E402

GEOMS = {"t1s1", "t05s1", "t1s05"}


def b_rows():
    b = pd.read_csv(CWT / "test_b" / "results.csv")
    out = pd.DataFrame({"pkg": "B", "family": b["fam"], "config": b["name"], "cid": b["id"], "side": b["side"],
                        "exit": b["exit"], "window": b["win"], "n": b["n"], "per_day": b["per_day"], "exp": b["exp"],
                        "t": b["t"], "up_exp": b["up_exp"], "down_exp": b["down_exp"], "verdict": b["verdict"]})
    out["signal"] = b["name"].str.replace(r"-(S|t1s1|t05s1|t1s05)-(full|guest)$", "", regex=True)
    why = np.where(b["fam"] == "B6", "needs rvol at 12:00 vs 20 prior sessions (live frame lacks)",
          np.where((b["fam"] == "B7") & b["name"].str.contains("parta"), "needs 252-day high / 20-day return (daily data)",
          np.where(b["fam"] == "B7", "needs 60-day beta and SPY's intraday path (live frame is one symbol)",
          np.where(b["name"].str.contains("Dret5"), "needs 5-day return (daily data)",
          np.where(b["exit"] == "S", "structural exit (LabStrategy has fixed R geometries only)", "")))))
    out["why_not"] = why
    return out


def a_rows():
    a = pd.read_csv(CWT / "test_a" / "results.csv")
    pcols = ["univ", "trig", "gap", "hset", "q", "cat", "side", "var", "k", "rvol", "g", "ref", "E", "c", "H", "hedge"]
    sig = a["family"] + "|" + a[pcols].apply(lambda r: "|".join(str(v) for v in r.tolist() if str(v) != "nan"), axis=1)
    side = np.where(a["side_n"].str.startswith("0L"), "short", np.where(a["side_n"].str.endswith("/0S"), "long", "both"))
    out = pd.DataFrame({"pkg": "A", "family": a["family"], "config": "A" + a["cid"].astype(str) + "|" + sig + "|" +
                        a["exit"] + "|" + a["win"], "cid": a["cid"], "side": side, "exit": a["exit"], "window": a["win"],
                        "n": a["n"], "per_day": np.nan, "exp": a["exp"], "t": a["t"], "up_exp": a["up_exp"],
                        "down_exp": a["down_exp"], "verdict": np.where(a["probation_pass"], "pass", "fail")})
    out["signal"] = sig
    fam_why = {
        "A1": "needs prior 3-5 day run / up-streak (daily data); entries mostly before 09:50",
        "A2": "needs rvol at the signal vs 20 prior sessions (live frame lacks)",
        "A3": "stop-order entry at the prior-day level from 09:35 (LabStrategy enters at a 5-minute close from 09:50)",
        "A4": "stop-order entries at the opening range from 09:35; rvol_15 vs prior sessions",
        "A5": "opening auction print and 60-day beta (not available live)",
        "A6": "about half the entries are before 09:50; 5-day high reference needs daily data",
        "A8": "needs rvol at 10:15 vs 20 prior sessions",
        "A9": "needs rvol vs 20 prior sessions",
    }
    why = a["family"].map(fam_why).fillna("")
    a7 = a["family"] == "A7"
    why = np.where(a7 & (a["E"] == "earn"), "earnings-day version (live earnings blackout blocks these days)", why)
    why = np.where(a7 & (a["E"] == "out") & (a["exit"] == "S"),
                   "structural exit (stop at the first-hour high, hold to 15:55): needs a LabStrategy exit extension",
                   why)
    why = np.where(a7 & (a["E"] == "out") & (a["exit"] != "S") & (a["share_pre950"] > 0),
                   "entries before 09:50 (full-day T2)", why)
    why = np.where(a7 & (a["E"] == "out") & (a["exit"] != "S") & (a["share_pre950"] == 0),
                   "package A engine (1-minute next-bar fills, adv >= $1M universe): port not done in drop 1", why)
    out["why_not"] = why
    return out


def c_rows():
    g = pd.read_csv(CWT / "test_c" / "gates.csv")
    g = g[g["intraday"] == True]  # noqa: E712
    return pd.DataFrame({"pkg": "C", "family": g["family"], "config": g["id"], "cid": -1, "side": g["side"],
                         "exit": "", "window": "", "n": g["all_open_n"], "per_day": np.nan,
                         "exp": np.nan, "t": g["all_open_t"], "up_exp": np.nan, "down_exp": np.nan,
                         "verdict": g["verdict"], "signal": g["id"],
                         "why_not": "multi-day hold or daily-bar signal (and n < 150 for C5/C7)"})


def main():
    r = pd.concat([b_rows(), a_rows(), c_rows()], ignore_index=True)
    r["eligible"] = (r["n"] >= 150) & (r["why_not"] == "")
    r.loc[(r["n"] < 150) & (r["why_not"] == ""), "why_not"] = "n < 150"
    chosen = {(s["pkg"], s["cid"]): s["name"] for s in S}
    r["chosen_as"] = [chosen.get((p, c), "") for p, c in zip(r["pkg"], r["cid"])]
    r = r.sort_values("exp", ascending=False, na_position="last")
    r.to_csv(HERE / "ranking.csv", index=False)
    e = r[r["eligible"]].drop_duplicates("signal")
    print("configurations ranked:", len(r), "| eligible:", int(r["eligible"].sum()), "| eligible signals:", len(e))
    print(e.groupby("family").size().to_dict())


if __name__ == "__main__":
    main()
