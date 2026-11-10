"""FLOW1-2Y (owner queue item; plan = MCF research/bdi/flow1_1104/PLAN.md 'Lab' half, pre-registered 2026-11-04 before any
FLOW1 score). Imports flow1.py's own functions unchanged (signals, state, weights, score, run) and feeds them the 2-year
lab book. Stated deviations from the plan: (1) lists = research/history2y/data/bt_lab1104 (every enabled lab setup,
uncapped signal chains), not the latch_1103 capped reconstruction; (2) the lists now run to 2026-11-09, so 10-08..11-09
is reported as an extra window, NOT part of VALID. TRAIN = open dates <= 2026-02-28, VALID = 2026-03-01..2026-10-07.
One rule chosen on TRAIN (best day-clustered EXCESS t, the guild standard), scored once on VALID. Bars: the plan's own
3.02 (N 96) and the market-state family BAR90 3.57 (N 2,605, Lead 11-10). Locked block never read (asserted).
    python flow1_2y.py          Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT / "research/bdi/flow1_1104"))
import flow1 as F
HERE = Path(__file__).resolve().parent
NY = "America/New_York"; TL0, TL1 = pd.Timestamp("2024-11-01", tz=NY), pd.Timestamp("2025-03-01", tz=NY)
TR_END, VA_END = "2026-02-28", "2026-10-07"

L = pd.concat(pd.read_parquet(p, columns=["setup", "side", "date", "tod", "xtod", "r"])
              for p in sorted((ROOT / "research/history2y/data/bt_lab1104").glob("sig_*.parquet")))
L["date"] = pd.to_datetime(L.date).dt.strftime("%Y-%m-%d")
assert not ((L.date >= "2024-11-01") & (L.date <= "2025-02-28")).any()
hm = lambda x: (x // 100) * 60 + x % 100
T_ = pd.DataFrame({"acct": "lab", "date": L.date, "side": L.side.astype(int), "ent": hm(L.tod.astype(int)),
                   "ext": hm(L.xtod.astype(int)), "r": L.r.astype(float)})
p = ROOT / "data/cache_hist/1Min/SPY.parquet"; ix = "__index_level_0__"
s = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
if ix in s.columns: s = s.set_index(ix)
s.index = pd.DatetimeIndex(s.index).tz_convert(NY); s = s[~s.index.duplicated(keep="last")].sort_index()
m = s.index.hour * 60 + s.index.minute; s = s[(m >= 570) & (m < 960)]
spy = s.rename(columns={"open": "o", "high": "h", "low": "l", "close": "c", "volume": "v"})[["o", "h", "l", "c", "v"]]
ctx = F.spy_ctx(spy)
print(f"lab trades {len(T_)} on {T_.date.nunique()} days ({T_.date.min()}..{T_.date.max()}); SPY ctx rows {len(ctx)}", flush=True)

out = []
for win, tt in (("TRAIN", T_[T_.date <= TR_END]), ("VALID", T_[(T_.date > TR_END) & (T_.date <= VA_END)]),
                ("EXTRA 10-08..11-09", T_[T_.date > VA_END])):
    R, G, Pc = F.run(tt, ctx, win, print)
    R, G, Pc = pd.DataFrame(R), pd.DataFrame(G), pd.DataFrame(Pc)
    R["window"] = win; G["window"] = win; Pc["window"] = win
    out.append((win, R, G, Pc)); print(win, "done", len(tt), flush=True)

R = pd.concat([o[1] for o in out]); G = pd.concat([o[2] for o in out]); Pc = pd.concat([o[3] for o in out])
R.to_csv(HERE / "results_2y.csv", index=False); G.to_csv(HERE / "regress_2y.csv", index=False); Pc.to_csv(HERE / "picture_2y.csv", index=False)
cols = ["window", "T", "k", "m", "rule", "days", "n_later", "base_avg", "delta", "t", "excess", "excess_t", "delta_wo_best",
        "kept_avg", "drop_avg", "n_drop", "on_spy_delta", "on_spy_t", "dt_up", "dt_down", "dt_quiet"]
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
tr = R[(R.window == "TRAIN") & ~R.rule.isin(["SPYrule", "VWAPrule"])]
pick = tr.sort_values("excess_t", ascending=False).iloc[0]
key = (pick["T"], pick["k"], pick["m"], pick["rule"])
print(f"\nTRAIN pick (best excess t of 32): T {key[0]} k {key[1]} m {key[2]} rule {key[3]}  (TRAIN excess t {pick.excess_t})")
sel = R[(R["T"] == key[0]) & (R["k"] == key[1]) & (R["m"] == key[2]) & (R["rule"] == key[3])]
print(sel[cols].to_string(index=False))
print("\nSPY / VWAP controls at the pick's T:")
print(R[(R["T"] == key[0]) & R.rule.isin(["SPYrule", "VWAPrule"])][cols].to_string(index=False))
print("\nall 32 configs on TRAIN (excess t) and VALID (excess t), for the record:")
w = R[~R.rule.isin(["SPYrule", "VWAPrule"])].pivot_table(index=["T", "k", "m", "rule"], columns="window", values="excess_t")
print(w.to_string())
print("\nregressions (book signal beyond SPY), pick's T, k:")
print(G[(G["T"] == key[0]) & (G["k"] == key[1])].to_string(index=False))
print("\nsimple picture (10:30, first k closes green vs red):"); print(Pc.to_string(index=False))
va = sel[sel.window == "VALID"].iloc[0]
print(f"\nVERDICT (fixed): VALID excess t {va.excess_t} vs plan bar 3.02 / family BAR90 3.57; on-top-of-SPY t {va.on_spy_t}. "
      f"Pass = excess t >= 3.57 AND on_spy_t > 0 AND VALID excess > 0: {bool((va.excess_t or 0) >= 3.57 and (va.on_spy_t or 0) > 0 and va.excess > 0)}")
print("Educational only - not financial advice.")
