"""L3REFIRE-1127 live replay (descriptive, PREREG.md; engine label: Live replay, primshorts_1126 booksim rules).
Primary journal (run 1, closed lots; a scratch copy of origin/mcf-data:journal.db), R after costs LR8
(mcf.costs.cost_r_lr8). All Primary lots on the sessions L3 traded in Primary. Current rules on every day (-2R latch,
-20R halt; LO on/off) + the config's L3 rule in time order; the replay only drops lots. Open marks: 1-min close grids
(primshorts grid_primary.npz + extra grids fetched by GET for missing days); missing marks count 0.
Usage (cwd repo): python research/l3refire_1127/l3live.py JOURNAL GRIDS(comma-sep npz) OUTDIR.
Educational only - not financial advice."""
import json
import sqlite3
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from mcf.config import load_config  # noqa: E402
from mcf.costs import cost_r_lr8  # noqa: E402

JDB, GRIDS, OUT = sys.argv[1], sys.argv[2].split(","), Path(sys.argv[3])
TZ = "America/New_York"; L3 = "L3-gap-slope-fromopen-FD"; BIG = 10 ** 6
CFG = {"keep": (0, 0), "OPEN1": (1, 1), "OPEN2": (1, 2), "GAP30": (2, 30), "GAP60": (2, 60), "GAP120": (2, 120),
       "NOSTOP": (3, 0), "FIRST1": (2, BIG)}
con = sqlite3.connect(JDB)
t = pd.read_sql("SELECT strategy, symbol, side, date, entry_time, exit_time, entry, stop, target, exit, exit_reason, meta, "
                "shares, pnl, pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
con.close()
t["date"] = t.date.astype(str).str[:10]
assert not t.date.between("2024-11-01", "2025-02-28").any()
t["r"] = cost_r_lr8(t, load_config()).astype(float)
t = t[t.r.notna()].copy()
days = sorted(t[t.strategy == L3].date.unique())
t = t[t.date.isin(days)].copy()
t["side_n"] = np.where(t.side.astype(float) > 0, 1, -1)
t["risk"] = (t.entry - t.stop).abs(); t = t[t.risk > 0].copy()
t["cost"] = t.side_n * (t.exit - t.entry) / t.risk - t.r
for c, s in (("em", "entry_time"), ("xm", "exit_time")):
    tt = pd.to_datetime(t[s].astype(str), utc=True, format="mixed").dt.tz_convert(TZ)
    t[c] = (tt.dt.hour * 60 + tt.dt.minute).to_numpy()
t["e_ns"] = pd.to_datetime(t.entry_time.astype(str), utc=True, format="mixed").dt.as_unit("ns").astype("int64")
t["x_ns"] = pd.to_datetime(t.exit_time.astype(str), utc=True, format="mixed").dt.as_unit("ns").astype("int64")
t["xm"] = np.maximum(t.xm, t.em).clip(upper=959)
t = t[(t.em >= 570) & (t.em < 960)].sort_values(["date", "e_ns"]).reset_index(drop=True)
t["stopx"] = t.exit_reason.astype(str).eq("stop")
setups = [L3] + sorted(s for s in t.strategy.unique() if s != L3)
t["si"] = t.strategy.map({s: i for i, s in enumerate(setups)})
NS = len(setups)
G = {}
for f in GRIDS:
    z = np.load(f, allow_pickle=True); G.update(dict(zip(z["keys"], z["arr"])))
DAYG = {}
D0 = {d: int(pd.Timestamp(d + " 00:00", tz=TZ).value) for d in days}
miss = 0
for d, g in t.groupby("date"):
    g = g.reset_index(drop=True)
    grids = []
    for q, s in enumerate(g.symbol):
        a = G.get(f"{s}|{d}")
        if a is not None:
            a = np.asarray(a, float).copy(); g0 = a[min(389, max(0, g.em[q] - 570))]
            if g0 > 0 and abs(g0 / g.entry[q] - 1) > 0.05:
                a = a * (g.entry[q] / g0)
        else:
            miss += 1
        grids.append(a if a is not None else np.full(390, np.nan))
    DAYG[d] = (g, np.stack(grids), pd.factorize(g.symbol)[0])


def sim_day(d, keep, lo, mode, par):
    """booksim.sim_day (primshorts_1126) rules + the L3 rule; live timestamps order entries and exits."""
    g, gm, sym = DAYG[d]
    si, em, xm, rr = g.si.to_numpy(), g.em.to_numpy(), g.xm.to_numpy(), g.r.to_numpy(float)
    side, ent, risk, cost = (g[c].to_numpy(float) for c in ("side_n", "entry", "risk", "cost"))
    ens, xns, stopx = g.e_ns.to_numpy(), g.x_ns.to_numpy(), g.stopx.to_numpy()
    realized = np.zeros(NS); latched = np.zeros(NS, bool); olat = np.zeros(NS, bool)
    taken = np.zeros(len(g), bool); open_ = []; cnt = np.zeros(NS, int); symcnt = {}; recent = [[] for _ in range(NS)]
    lastent, stopped = {}, set(); halted = False
    by_m = {}
    for k in np.flatnonzero(keep):
        by_m.setdefault(int(em[k]), []).append(k)
    if not by_m:
        return np.zeros(NS), taken
    m0, last = min(by_m), max(by_m)

    def realize(now_ns):
        nonlocal open_
        kp = []
        for k in open_:
            if xns[k] <= now_ns:
                realized[si[k]] += rr[k]; cnt[si[k]] -= 1; symcnt[(si[k], sym[k])] -= 1
                if si[k] == 0 and stopx[k]:
                    stopped.add(sym[k])
            else:
                kp.append(k)
        open_ = kp
    for m in range(m0, 960):
        if m > last and not open_:
            break
        for k in by_m.get(m, ()):
            realize(ens[k])              # exits strictly by live timestamp before this entry
            latched[realized <= -2.0 + 1e-12] = True
            s = si[k]
            if halted or latched[s] or olat[s]:
                continue
            if len(open_) >= 77 or cnt[s] >= 30 or symcnt.get((s, sym[k]), 0) >= 3:
                continue
            if s == 0 and mode:
                if mode == 1 and symcnt.get((0, sym[k]), 0) >= par:
                    continue
                if mode == 2 and m - lastent.get(sym[k], -BIG) < par:
                    continue
                if mode == 3 and sym[k] in stopped:
                    continue
            recent[s] = [x for x in recent[s] if x > m - 10]
            if len(recent[s]) >= 30:
                continue
            recent[s].append(m); open_.append(k); cnt[s] += 1; taken[k] = True
            symcnt[(s, sym[k])] = symcnt.get((s, sym[k]), 0) + 1
            if s == 0:
                lastent[sym[k]] = m
        realize(D0[d] + (m + 1) * 60 * 10 ** 9 - 1)   # exits up to the end of minute m
        latched[realized <= -2.0 + 1e-12] = True
        ps = realized.copy()
        if open_:
            o = np.asarray(open_)
            v = np.nan_to_num(side[o] * (gm[o, min(389, max(0, m - 570))] - ent[o]) / risk[o] - cost[o])
            ps += np.bincount(si[o], weights=v, minlength=NS)
        if lo:
            olat |= ps <= -2.0 + 1e-12
        if ps.sum() <= -20.0 + 1e-12:
            halted = True
    for k in open_:
        realized[si[k]] += rr[k]
    return realized, taken


def wob(x):
    i = int(np.argmax(x)); return (x.sum() - x[i]) / max(len(x) - 1, 1), (x[i] / x.sum() if x.sum() > 0 else np.nan)


res = {"days": days, "n_days": len(days), "lots": int(len(t)), "missing_mark_lots": miss,
       "R_journal_LR8": round(float(t.r.sum()), 2), "by_setup": t.groupby("strategy").r.agg(["size", "sum"]).round(2).to_dict("index")}
# consultant split: first L3 lot per name per day vs repeats (as traded)
l3 = t[t.strategy == L3].sort_values(["date", "e_ns"]).copy()
l3["rep"] = l3.groupby(["date", "symbol"]).cumcount() > 0
sp = {}
for nm, g in (("first", l3[~l3.rep]), ("repeat", l3[l3.rep])):
    dd = g.groupby("date").r.sum()
    sp[nm] = dict(n=int(len(g)), avg=float(g.r.mean()), total=float(g.r.sum()),
                  total_wo_best_day=float(dd.sum() - dd.max()),
                  since_1119=float(g[g.date >= "2026-11-19"].r.sum()), since_1119_n=int((g.date >= "2026-11-19").sum()))
res["consultant_split"] = sp
rows = []
for lo in (False, True):
    base = {d: sim_day(d, np.ones(len(DAYG[d][0]), bool), lo, 0, 0) for d in days}
    a = np.array([base[d][0].sum() for d in days])
    pool = [(d, k) for d in days for k in np.flatnonzero(base[d][1] & (DAYG[d][0].si.to_numpy() == 0))]
    for cfg, (mode, par) in CFG.items():
        rr_ = {d: sim_day(d, np.ones(len(DAYG[d][0]), bool), lo, mode, par) for d in days}
        x = np.array([rr_[d][0].sum() for d in days]); dd = x - a
        rmv = [(d, k) for d in days for k in np.flatnonzero(base[d][1] & ~rr_[d][1] & (DAYG[d][0].si.to_numpy() == 0))]
        rmR = float(sum(DAYG[d][0].r[k] for d, k in rmv))
        sd = dd.std(ddof=1)
        bi = int(np.argmax(dd))
        l3c = np.array([rr_[d][0][0] for d in days])
        nl3 = np.array([int((rr_[d][1] & (DAYG[d][0].si.to_numpy() == 0)).sum()) for d in days])
        bl = int(np.argmax(l3c))
        row = dict(lo=lo, cfg=cfg, book_R=float(x.sum()), dR_total=float(dd.sum()), dR=float(dd.mean()),
                   t=float(dd.mean() / (sd / np.sqrt(len(dd)))) if sd > 0 else 0.0,
                   dR_wo_best=float(np.delete(dd, bi).mean()), best_share=float(dd[bi] / dd.sum()) if dd.sum() > 0 else np.nan,
                   days_better=int((dd > 1e-9).sum()), days_worse=int((dd < -1e-9).sum()),
                   l3_lots=int(nl3.sum()), l3_removed=len(rmv), removed_R=rmR,
                   l3_R=float(l3c.sum()), l3_avg=float(l3c.sum() / max(nl3.sum(), 1)),
                   l3_avg_wo_best=float((l3c.sum() - l3c[bl]) / max(nl3.sum() - nl3[bl], 1)),
                   l3_best_share=float(l3c[bl] / l3c.sum()) if l3c.sum() > 0 else np.nan,
                   worst5=float(np.sort(x)[:5].sum()), red=int((x < 0).sum()),
                   since1119_dR=float(sum(dd[i] for i, d in enumerate(days) if d >= "2026-11-19")),
                   d1127=float(dd[days.index("2026-11-27")]) if "2026-11-27" in days else np.nan,
                   per_setup={setups[s]: float(sum(rr_[d][0][s] - base[d][0][s] for d in days)) for s in range(NS)
                              if abs(sum(rr_[d][0][s] - base[d][0][s] for d in days)) > 1e-9})
        if mode:
            g = np.random.default_rng(1127); rd = []
            n = len(rmv)
            for _ in range(500):
                pick = g.choice(len(pool), min(n, len(pool)), replace=False)
                drop = {}
                for i in pick:
                    drop.setdefault(pool[i][0], []).append(pool[i][1])
                tot = 0.0
                for d in days:
                    if d in drop:
                        kp = np.ones(len(DAYG[d][0]), bool); kp[drop[d]] = False
                        tot += sim_day(d, kp, lo, 0, 0)[0].sum()
                    else:
                        tot += base[d][0].sum()
                rd.append(tot / len(days) - a.mean())
            rd = np.array(rd)
            row.update(rnd_mean=float(rd.mean()), rnd_p95=float(np.percentile(rd, 95)),
                       pctile=float((rd < row["dR"]).mean() * 100))
        rows.append(row)
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items() if k != "per_setup"}, flush=True)
        print("   per setup", {k[:22]: round(v, 2) for k, v in row["per_setup"].items()}, flush=True)
res["rows"] = rows
OUT.mkdir(parents=True, exist_ok=True)
pd.DataFrame([{k: v for k, v in r.items() if k != "per_setup"} for r in rows]).to_csv(OUT / "live_replay.csv", index=False)
json.dump(res, open(OUT / "live_replay.json", "w"), indent=1, default=float)
print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1, default=float))
