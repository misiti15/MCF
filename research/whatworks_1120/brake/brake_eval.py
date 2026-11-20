"""OUT-BRAKE study (research only, no config change). Replays candidate cost-in brakes on the live closed-trade record
(LR8 R after costs, all accounts, entries/exits in time order) and reports, per brake and per account scope:
blocked trades, R saved (blocked losers), R forgone (blocked winners), net, days triggered, per-setup better/worse,
the one-big-day check (net without the best day, best day's share). Mechanics: a brake looks only at R REALIZED (closed,
cost-in) before the entry's timestamp by trades that were themselves not blocked; open trades at the trigger are kept to
their real exit (journals hold no mark path); blocked trades are removed whole. Limits: trades the live brakes already
blocked (Primary -2R latch from 10-29, Primary -20R halt, Graveyard -2R latch / 120R halt) are not in the record, so only
TIGHTER/extra brakes are testable there. Educational only - not financial advice.
usage: python brake_eval.py trades.parquet out.csv"""
import re, sys
import numpy as np
import pandas as pd

t = pd.read_parquet(sys.argv[1])
t["et"] = pd.to_datetime(t["entry_time"], utc=True, format="mixed")
t["xt"] = pd.to_datetime(t["exit_time"], utc=True, format="mixed")
t["family"] = [s.split("-", 1)[0] if "-" in s else re.sub(r"_[a-z]$", "", s) for s in t["strategy"]]
t["unit"] = t["account"] + "|" + t["strategy"]
t = t.sort_values("et").reset_index(drop=True)
ET, XT, R = t["et"].values, t["xt"].values, t["r"].values


def loss_brake(keys, X, need_accts=1):
    """Latched stop: entries of a key are blocked once the key's realized (non-blocked) cost-in R path has touched <= -X
    before the entry time. need_accts>1: also require >= need_accts accounts with negative realized R in that key."""
    blocked = np.zeros(len(t), bool)
    for _, idx in t.groupby(keys, sort=False).indices.items():
        idx = np.sort(idx)
        if len(idx) < 2:
            continue
        kept, latched = [], False
        for i in idx:
            if not latched and kept:
                k = np.array(kept)
                done = k[XT[k] < ET[i]]
                if len(done):
                    o = done[np.argsort(XT[done])]
                    cum = np.cumsum(R[o])
                    if cum.min() <= -X:
                        if need_accts > 1:
                            a = t.loc[o, ["account"]].assign(r=R[o]).groupby("account").r.sum()
                            latched = (a < 0).sum() >= need_accts
                        else:
                            latched = True
            if latched:
                blocked[i] = True
            else:
                kept.append(i)
    return blocked


def burst_brake(keys, N, M, mode="cool", need_loss=False):
    """>= N kept entries of the key in the previous M minutes -> block (mode cool: until the window clears;
    latch: rest of day). need_loss: only while the key's realized R today is < 0."""
    blocked = np.zeros(len(t), bool)
    win = np.timedelta64(int(M * 60), "s")
    for _, idx in t.groupby(keys, sort=False).indices.items():
        idx = np.sort(idx)
        if len(idx) < N:
            continue
        kept, latched = [], False
        for i in idx:
            hit = latched
            if not hit and len(kept) >= N:
                k = np.array(kept)
                if (ET[k] > ET[i] - win).sum() >= N:
                    if need_loss:
                        done = k[XT[k] < ET[i]]
                        hit = len(done) > 0 and R[done].sum() < 0
                    else:
                        hit = True
                    if hit and mode == "latch":
                        latched = True
            if hit:
                blocked[i] = True
            else:
                kept.append(i)
    return blocked


def cap_brake(keys, N):
    return (t.groupby(keys).cumcount() >= N).values


def open_cap(keys, K):
    """Concurrent-lot cap: an entry is blocked while >= K kept lots of the key are open (entered, not yet exited)."""
    blocked = np.zeros(len(t), bool)
    for _, idx in t.groupby(keys, sort=False).indices.items():
        idx = np.sort(idx)
        if len(idx) <= K:
            continue
        kept = []
        for i in idx:
            if kept:
                k = np.array(kept)
                if (XT[k] > ET[i]).sum() >= K:
                    blocked[i] = True
                    continue
            kept.append(i)
    return blocked


SD = ["account", "strategy", "date"]
configs = {}
for X in (2, 3, 4, 5, 6, 8):
    configs[f"setup_stop_{X}R"] = lambda X=X: loss_brake(SD, X)
for X in (10, 15, 20, 30, 40, 60):
    configs[f"acct_halt_{X}R"] = lambda X=X: loss_brake(["account", "date"], X)
for X in (4, 6, 10):
    configs[f"xacct_family_{X}R_2acct"] = lambda X=X: loss_brake(["family", "date"], X, need_accts=2)
for X in (100, 200):
    configs[f"system_halt_{X}R"] = lambda X=X: loss_brake(["date"], X)
for N, M in ((10, 5), (10, 10), (15, 15), (20, 15), (20, 30), (30, 30)):
    configs[f"burst_{N}in{M}m_cool"] = lambda N=N, M=M: burst_brake(SD, N, M)
    configs[f"burst_{N}in{M}m_cool_losing"] = lambda N=N, M=M: burst_brake(SD, N, M, need_loss=True)
for N, M in ((25, 5), (30, 10), (40, 10), (50, 15)):
    configs[f"burst_{N}in{M}m_cool"] = lambda N=N, M=M: burst_brake(SD, N, M)
for N, M in ((10, 10), (20, 30)):
    configs[f"burst_{N}in{M}m_latch"] = lambda N=N, M=M: burst_brake(SD, N, M, mode="latch")
for N in (20, 30, 50, 75):
    configs[f"setup_cap_{N}"] = lambda N=N: cap_brake(SD, N)
for K in (10, 15, 20, 30):
    configs[f"open_cap_{K}"] = lambda K=K: open_cap(SD, K)
configs["combo_stop4R+burst20in30_losing"] = lambda: loss_brake(SD, 4) | burst_brake(SD, 20, 30, need_loss=True)

# targeted: stop at -X only after the setup has taken >= K entries today (a runaway, not a normal 2-3 loss day)
def runaway_stop(X, K):
    b = loss_brake(SD, X)
    n = t.groupby(SD).cumcount().values
    # keep entries before the K-th; brake counts only once K entries exist
    return b & (n >= K)
for X, K in ((4, 10), (5, 10), (5, 15), (8, 15)):
    configs[f"runaway_stop_{X}R_after{K}"] = lambda X=X, K=K: runaway_stop(X, K)

SCOPES = {"primary": t.account == "primary", "gen": t.account == "gen", "graveyard": t.account == "graveyard",
          "testing_all": t.account.isin(["testing", "testing2", "testingd", "testinge", "testingf"]),
          "lowrep": t.account.isin(["explore1", "livelab"]), "all": t.account.notna()}
rows, blocks = [], {}
for name, fn in configs.items():
    b = fn()
    blocks[name] = b
    for sc, m in SCOPES.items():
        m = m.values
        bb = b & m
        r = R[bb]
        delta_day = pd.Series(-r).groupby(t.loc[bb, "date"].values).sum() if bb.any() else pd.Series(dtype=float)
        per_unit = pd.Series(-r).groupby(t.loc[bb, "unit"].values).sum() if bb.any() else pd.Series(dtype=float)
        base = R[m].sum()
        net = -r.sum()
        best = delta_day.max() if len(delta_day) else 0.0
        units = t.loc[m, "unit"].nunique()
        rows.append(dict(brake=name, scope=sc, trades=int(m.sum()), base_R=round(base, 1), blocked=int(bb.sum()),
                         R_saved=round(-r[r < 0].sum(), 1), R_forgone=round(r[r > 0].sum(), 1), net_R=round(net, 1),
                         new_total_R=round(base + net, 1), days_triggered=int(t.loc[bb, "date"].nunique()),
                         days_better=int((delta_day > 0).sum()), days_worse=int((delta_day < 0).sum()),
                         best_day=(delta_day.idxmax() if len(delta_day) else ""), best_day_R=round(best, 1),
                         net_wo_best_day=round(net - best, 1),
                         best_day_share=round(best / net, 2) if net > 0 else np.nan,
                         net_wo_1117=round(-R[bb & (t.date.values != "2026-11-17")].sum(), 1),
                         setups=units, setups_touched=len(per_unit), setups_better=int((per_unit > 0.05).sum()),
                         setups_worse=int((per_unit < -0.05).sum()),
                         R_better=round(per_unit[per_unit > 0].sum(), 1), R_worse=round(per_unit[per_unit < 0].sum(), 1),
                         worst_setup_harm=round(per_unit.min(), 1) if len(per_unit) else 0.0))
out = pd.DataFrame(rows)
out.to_csv(sys.argv[2], index=False)
np.savez_compressed(sys.argv[2].replace(".csv", "_blocks.npz"), **blocks)
print(len(configs), "configs")
