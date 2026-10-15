"""BDI 2026-10-15 Part C (PLAN.md): two pattern -> rule tests on the two-year open history.
C1 bdi1014-rw2-extension-floor: RW2-FD bar qualifies only if fromOpen >= F or rsi5 >= R (F 2.0/2.5/3.0 x R 85/90/95; 9).
C2 index-up short veto: a short bar does not qualify when SPY fromOpen >= k at that bar (k 0.25/0.50) x 5 setups (10).
Re-uses the nightly1015 first-signal hits (bt1015.py; lab frames through research/history2y, which refuses the locked
block; MCF_HIST_ALLOW_LOCKED never set) and its score()/first() helpers. Production + tod costs as in the scan.
Writes crules_results.csv. Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research" / "bdi" / "nightly1015"), str(ROOT / "research" / "history2y"), str(ROOT)]
import bt1015  # noqa: E402
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

OUT = Path(__file__).resolve().parent
HITS = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/n1015/bt_hits.parquet")
RW2 = "RW2-exhaustion-noon-adv150-short-FD"


def main():
    h = pd.read_parquet(HITS)
    assert not h.date.astype(str).between("2024-11-01", "2025-02-28").any()
    reg = lib.regimes()
    reg.index = pd.to_datetime(reg.index).date
    reg = reg["regime"]
    rows = []
    # ---- C1
    g = h[h.name == RW2].copy()
    months = sorted({str(d)[:7] for d in g.date})
    assert not set(months) & set(lib.LOCKED_MONTHS)
    fr = pd.concat([lib.load_month(m, columns=["symbol", "date", "tod", "fromOpen", "rsi5"]) for m in months])
    fr["symbol"] = fr["symbol"].astype(str)
    fr["date"] = fr["date"].astype(str)
    g["date_s"] = g["date"].astype(str)
    g = g.merge(fr.rename(columns={"date": "date_s"}), on=["symbol", "date_s", "tod"], how="left")
    miss = float(g.fromOpen.isna().mean())
    base = bt1015.first(g)
    b = bt1015.score(base, reg)
    rows.append({"test": "C1", "setup": RW2, "variant": "baseline", **b, "frame_missing_share": round(miss, 4)})
    for F in (2.0, 2.5, 3.0):
        for R in (85, 90, 95):
            keep = g.fromOpen.isna() | (g.fromOpen >= F) | (g.rsi5 >= R)
            s = bt1015.score(bt1015.first(g[keep]), reg)
            rows.append({"test": "C1", "setup": RW2, "variant": f"fo>={F}|rsi5>={R}", **s,
                         **{f"d_{k}": round(s[k] - b[k], 4) for k in ("exp", "train_exp", "late_exp", "up", "down")}})
    # ---- C2
    for nm, g in h.groupby("name"):
        base = bt1015.first(g)
        b = bt1015.score(base, reg)
        rows.append({"test": "C2", "setup": nm, "variant": "baseline", **b,
                     "share_spyfo_ge025": round(float((base.spy_fo >= 0.25).mean()), 3)})
        for k in (0.25, 0.50):
            s = bt1015.score(bt1015.first(g[~(g.spy_fo >= k).fillna(False)]), reg)
            rows.append({"test": "C2", "setup": nm, "variant": f"veto_spyfo>={k}", **s,
                         **{f"d_{x}": round(s[x] - b[x], 4) for x in ("exp", "train_exp", "late_exp", "up", "down")}})
        rem = base[base.spy_fo >= 0.25]
        rows.append({"test": "C2", "setup": nm, "variant": "first_signals_with_spyfo>=0.25 (info)", **bt1015.score(rem, reg)})
    R_ = pd.DataFrame(rows)
    treq = {"C1": gates.t_required(9), "C2": gates.t_required(20)}
    v = R_.variant.str.startswith(("fo>=", "veto"))
    R_["t_req"] = R_.test.map(treq)
    R_["pass"] = None
    R_.loc[v, "pass"] = ((R_.exp > 0) & (R_.d_train_exp > 0) & (R_.d_late_exp > 0) & (R_.d_up > 0) & (R_.d_down > 0)
                         & (R_.t >= R_.t_req))[v]
    R_.to_csv(OUT / "crules_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(R_.to_string())


if __name__ == "__main__":
    main()
