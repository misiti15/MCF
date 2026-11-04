"""GY-BP replay (research/queue.jsonl, owner 2026-11-03): would a lower Graveyard per-setup cap (25 -> 12 concurrent)
spread its buying power so later setups still get turns? Journal replay only, Graveyard 2026-10-21..2026-11-04.

Per session, events in time order:
  * live entries (run 1). A setup that already holds `cap` replay-open lots has the new lot DROPPED; the dropped lot's
    cost basis (entry x shares) is freed for its live holding interval.
  * buying-power rejects (run 1 status rejected, Alpaca code 40310000). Funded when the setup holds < cap lots and the
    freed pool at that minute covers the rejected order's cost basis; its R = the run-2 what-if r_multiple minus the
    Graveyard median per-trade cost in R (live r_multiple - pnl_adj / $risk).
Kept lots keep their live R (pnl_adj / $risk). Pre-registered pass (before running): net R > 0 over the window, positive
w/o the best session, and >= 5 setups that had no live trade that session get >= 1 funded turn. Configs: cap 12 (1) and,
as a sensitivity only, cap 18.
Usage: python gybp.py <scratch-with-gy/journal.db>      Educational only - not financial advice."""
import json, sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); c = sqlite3.connect(S / "gy" / "journal.db")
L = pd.read_sql("select symbol, strategy, side, date, entry_time, exit_time, entry, stop, shares, r_multiple, pnl_adj from trades where run_id=1", c)
L["risk"] = (L.entry - L.stop).abs() * L.shares; L["R"] = L.pnl_adj / L.risk.replace(0, np.nan)
L["cost"] = L.entry * L.shares; L = L.dropna(subset=["R"])
cost_R = float((L.r_multiple - L.R).median())
for k in ("entry_time", "exit_time"): L[k] = pd.to_datetime(L[k], utc=True, format="mixed")
W = pd.read_sql("select symbol, strategy, date, signal_time, entry_time, exit_time, r_multiple, meta from trades where run_id=2", c)
W = W[W.meta.str.contains("40310000", na=False)].copy()
W["cb"] = W.meta.str.extract(r'cost_basis\\?"\s*:\s*\\?"([0-9.]+)')[0].astype(float)
for k in ("signal_time", "entry_time", "exit_time"): W[k] = pd.to_datetime(W[k], utc=True, format="mixed")
W["R"] = W.r_multiple - cost_R
print(f"Graveyard live lots {len(L)}, buying-power rejects with a what-if {len(W)} (cost basis parsed {W.cb.notna().sum()}), "
      f"median cost {cost_R:.3f}R; reject what-if avg R after cost {W.R.mean():+.3f}")


def replay(cap):
    out = []
    for d in sorted(L.date.unique()):
        lv = L[L.date == d]; rj = W[W.date == d]
        ev = [(r.entry_time, 0, i) for i, r in lv.iterrows()] + [(r.signal_time, 1, i) for i, r in rj.iterrows()]
        ev.sort(key=lambda x: (x[0], x[1]))
        openl = []  # (exit, strategy, kind, cost)
        dropped, funded = [], []
        for t, kind, i in ev:
            openl = [o for o in openl if o[0] > t]
            if kind == 0:
                r = lv.loc[i]; n = sum(1 for o in openl if o[1] == r.strategy and o[2] != "drop")
                if n >= cap:
                    dropped.append(i); openl.append((r.exit_time, r.strategy, "drop", r.cost))
                else:
                    openl.append((r.exit_time, r.strategy, "keep", r.cost))
            else:
                r = rj.loc[i]
                if not np.isfinite(r.cb) or pd.isna(r.exit_time): continue
                n = sum(1 for o in openl if o[1] == r.strategy and o[2] != "drop")
                pool = sum(o[3] for o in openl if o[2] == "drop") - sum(o[3] for o in openl if o[2] == "fund")
                if n < cap and pool >= r.cb:
                    funded.append(i); openl.append((r.exit_time, r.strategy, "fund", r.cb))
        live_setups = set(lv.strategy)
        fs = rj.loc[funded]
        out.append(dict(date=d, live_n=len(lv), live_R=lv.R.sum(), rejects=len(rj), dropped=len(dropped), dropped_R=lv.loc[dropped].R.sum(),
                        funded=len(funded), funded_R=fs.R.sum(), new_setups=len(set(fs.strategy) - live_setups),
                        funded_setups=fs.strategy.nunique(), net=fs.R.sum() - lv.loc[dropped].R.sum(),
                        drop_setups=";".join(sorted(set(lv.loc[dropped].strategy)))[:200]))
    return pd.DataFrame(out)


for cap in (12, 18):
    o = replay(cap); net = o.net
    wob = net.drop(net.idxmax()).sum() if len(net) > 1 else np.nan
    print(f"\n== cap {cap}: sessions {len(o)}; dropped {o.dropped.sum()} lots {o.dropped_R.sum():+.2f}R; funded {o.funded.sum()} rejects "
          f"{o.funded_R.sum():+.2f}R ({o.funded_setups.sum()} setup-days, {o.new_setups.sum()} with no live trade that day); "
          f"NET {net.sum():+.2f}R, w/o best session {wob:+.2f}R, best share {net.max() / net.sum() if net.sum() > 0 else float('nan'):.2f}; "
          f"t {net.mean() / (net.std(ddof=1) / np.sqrt(len(net))) if len(net) > 1 and net.std() > 0 else float('nan'):+.2f}")
    kn = o.live_n.sum() - o.dropped.sum(); kr = o.live_R.sum() - o.dropped_R.sum()
    print(f"   dropped lots avg {o.dropped_R.sum() / max(o.dropped.sum(), 1):+.3f}R vs kept lots avg {kr / kn:+.3f}R (all live {o.live_R.sum() / o.live_n.sum():+.3f}R): "
          f"the cap {'picks worse lots' if o.dropped_R.sum() / max(o.dropped.sum(), 1) < kr / kn - 0.05 else 'does not pick worse lots; the saving is fewer lots of a losing book'}")
    print(o.round(2).to_string(index=False))
    if cap == 12:
        o.to_csv(Path(__file__).with_name("gybp_days.csv"), index=False)
print("\nEducational only - not financial advice.")
