"""OUT-NULL: matched random-entry null for every setup with >= 10 live trades (research only; no config change).

For each live closed trade (run 1, deduped like mcf/report/footrace.live_trades, LR8 cost basis):
  * candidate entries = EVERY 1-min bar open on the same symbol + session, same side, entry minute within +-30 min of the
    real entry minute, clamped to [09:50, setup window end] (window from config/*.yaml; the real minute is always kept);
  * each candidate keeps the trade's own stop and target distance (as % of entry), exits on 1-min SIP bars: stop
    (stop order; gap-through fills at the bar open), target (limit, needs 1 tick through), both in one bar -> stop,
    otherwise flat at the 15:55 bar open; LR8 costs (mcf.costs.lot_costs formula, qty 100).
  * null of a setup's average = 4000 resamples, each trade taking one random candidate (so >= 200 random entries per
    trade are evaluated: every candidate minute is simulated exactly, and 4000 draws are taken over them).
  * 'sim' = the same simulator at the trade's REAL entry minute (bar-open entry, same geometry) -> clean edge sim-null
    (no live-fill slippage on either side); 'live' = booked LR8 R -> edge live-null (as asked).
  * the +-30 null mixes minutes BEFORE the signal (price still moving against the setup: a soft bar) with minutes
    AFTER it; so pre-only (-30..-1) and post-only (+1..+30, 'enter later at random') nulls are reported too.
  * replay check: the simulator run with the trade's actual entry/stop/target prices vs the journal (exit kind, R).
Usage: python null.py <repo> <work dir with trades_full.pkl, bars/, win.json> <out dir>
"""
import json, sys
import numpy as np, pandas as pd
from numba import njit

R, W, O = sys.argv[1:4]
NRES, SEED = 4000, 1120
rng = np.random.default_rng(SEED)

t = pd.read_pickle(f"{W}/trades_full.pkl")
g = t.groupby("strategy").size()
t = t[t.strategy.isin(g[g >= 10].index)].reset_index(drop=True)
win = json.load(open(f"{W}/win.json"))
prim = ["L3-gap-slope-fromopen-FD", "NM-ETF-late-dip-di-long", "RW3-gapdn-rsi5pop-flowsell-short-FD",
        "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "ST7-rsi50dn-long-pm-t1s1-FD"]


def hm2i(hm):  # HHMM -> minute index from 09:30
    return (int(hm) // 100) * 60 + int(hm) % 100 - 570


wend = {k: max(hm2i(w[1]) for _, w in v) for k, v in win.items()}
et = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
t["mi"] = (et.dt.hour * 60 + et.dt.minute - 570).astype(int)
t["side"] = t.side.astype(int)

SEC, TAF, CAT = 20.60 / 1e6, 0.000195, 0.00005


@njit(cache=True)
def sim(O_, H, L, C, k, e, s, tg, side):
    """One trade from bar k (entry at price e). Returns (exit px, kind 1 stop / 2 target / 0 flat, exit bar)."""
    for j in range(k, 385):
        if np.isnan(O_[j]):
            continue
        if side == 1:
            if L[j] <= s:
                return min(O_[j], s) if j > k else s, 1, j
            if tg > 0 and H[j] >= tg + 0.01:
                return tg, 2, j
        else:
            if H[j] >= s:
                return max(O_[j], s) if j > k else s, 1, j
            if tg > 0 and L[j] <= tg - 0.01:
                return tg, 2, j
    for j in range(385, 390):
        if not np.isnan(O_[j]):
            return O_[j], 0, j
    for j in range(384, k - 1, -1):
        if not np.isnan(C[j]):
            return C[j], 0, j
    return np.nan, -1, -1


def r_after(side, e, s, px, kind):
    """R after LR8 costs per share (lot_costs with one exit part; fees at 2026 rates)."""
    risk = np.abs(e - s)
    c = 1e-4 * e
    c = c + np.where(kind == 1, np.maximum(0.02, 4e-4 * px), np.where(kind == 0, np.maximum(0.01, 1e-4 * px), 0.0))
    sellpx = np.where(side == -1, e, px)
    c = c + SEC * sellpx + TAF + 2 * CAT
    return (side * (px - e) - c) / risk


days = {}
rows, cand = [], {}  # per trade: dict; cand: {trade index: (offsets, candidate R)}
for d, gg in t.groupby("date"):
    z = np.load(f"{W}/bars/{d}.npz")
    for i, r in gg.iterrows():
        if r.symbol not in z.files:
            rows.append(dict(i=i, ok=False)); cand[i] = None; continue
        a = z[r.symbol]; O_, H, L, C = (np.ascontiguousarray(a[:, q].astype(np.float64)) for q in range(4))
        side, m = int(r.side), int(r.mi)
        e0, s0 = float(r.entry), float(r.stop)
        tg0 = float(r.target) if pd.notna(r.target) else 0.0
        if not (0 <= m < 385) or not np.abs(e0 - s0) > 0:
            rows.append(dict(i=i, ok=False)); cand[i] = None; continue
        dp = abs(e0 - s0) / e0
        tp = abs(tg0 - e0) / e0 if tg0 > 0 else 0.0
        # replay check: actual prices from the actual entry minute
        px, kd, xb = sim(O_, H, L, C, m, e0, s0, tg0, side)
        r_rep = float(r_after(side, e0, s0, px, kd)) if kd >= 0 else np.nan
        hi = min(m + 30, wend.get(r.strategy, hm2i(1500)), 384)
        lo = max(m - 30, 20)
        lo, hi = min(lo, m), max(hi, m)
        ks = np.arange(lo, hi + 1)
        rr = np.full(len(ks), np.nan)
        for q, k in enumerate(ks):
            e = O_[k]
            if np.isnan(e):
                continue
            s = e * (1 - side * dp); tg = e * (1 + side * tp) if tp > 0 else 0.0
            p2, k2, _ = sim(O_, H, L, C, k, e, s, tg, side)
            if k2 >= 0:
                rr[q] = r_after(side, e, s, p2, k2)
        r_sim = rr[ks == m][0]
        okm = ~np.isnan(rr); good = rr[okm]; offs = (ks - m)[okm]
        rows.append(dict(i=i, ok=len(good) > 0 and not np.isnan(r_sim), r_rep=r_rep, kind_rep=int(kd), r_sim=r_sim,
                         ncand=len(good), cand_mean=good.mean() if len(good) else np.nan,
                         cand_post=good[offs > 0].mean() if (offs > 0).any() else np.nan))
        cand[i] = (offs, good)
    print(d, flush=True)

P = pd.DataFrame(rows).set_index("i")
t = t.join(P)
t["kind_live"] = t.exit_reason.map(lambda x: 1 if x in ("stop", "scaled+breakeven") else 2 if x in ("target", "scaled+target") else 0)
t.drop(columns=["meta"]).to_pickle(f"{W}/trades_null.pkl")

# ---- replay agreement on taken trades
v = t[t.ok == True]
agree = dict(trades=len(t), replayed=len(v), kind_match=float((v.kind_rep == v.kind_live).mean()),
             corr=float(np.corrcoef(v.r_rep, v.r)[0, 1]), mean_live=float(v.r.mean()), mean_rep=float(v.r_rep.mean()),
             mean_sim=float(v.r_sim.mean()), mae=float((v.r_rep - v.r).abs().median()))
json.dump(agree, open(f"{O}/replay_agreement.json", "w"), indent=1)
print(agree)


# ---- per-setup null
def null_dist(idx, mode="sym"):
    """Resampled null of the average R: each trade takes one random candidate minute. sym = -30..+30 (the approved
    spec), pre = -30..-1 only (entering before the signal), post = +1..+30 only (entering later than the signal)."""
    tot = np.zeros(NRES); n = 0
    for j in idx:
        o, c = cand[j]
        if mode == "pre": c = c[o < 0]
        elif mode == "post": c = c[o > 0]
        if not len(c): continue
        tot += c[rng.integers(0, len(c), NRES)]; n += 1
    return tot / max(n, 1)


def clustered_p(gg, col, base):
    """One-sided p of mean(col - base) > 0 with a day-clustered standard error (trades on one day are not independent)."""
    from scipy.stats import t as tdist
    d = (gg[col] - gg[base]).dropna(); dd = gg.loc[d.index, "date"]
    n, mu = len(d), d.mean(); k = dd.nunique()
    if k < 3: return np.nan
    s2 = ((d - mu).groupby(dd).sum() ** 2).sum() * k / (k - 1)
    se = np.sqrt(s2) / n
    return float(tdist.sf(mu / se, k - 1)) if se > 0 else np.nan


out = []
for k, gg in v.groupby("strategy"):
    if len(gg) < 10:
        continue
    idx = gg.index.to_numpy()
    nd = null_dist(idx)
    day = gg.groupby("date").r.sum(); best = day.idxmax()
    share = day.max() / gg.r.sum() if gg.r.sum() > 0 else np.nan
    g2 = gg[gg.date != best]; nd2 = null_dist(g2.index.to_numpy()) if len(g2) >= 5 else None
    rec = dict(setup=k, primary=k in prim, accounts="/".join(sorted(gg.account.unique())), n=len(gg),
               days=gg.date.nunique(), live_avg=gg.r.mean(), sim_avg=gg.r_sim.mean(), rep_avg=gg.r_rep.mean(),
               null_mean=nd.mean(), null_p05=np.quantile(nd, .05), null_p95=np.quantile(nd, .95),
               edge_live=gg.r.mean() - nd.mean(), edge_sim=gg.r_sim.mean() - nd.mean(),
               pct_live=(nd < gg.r.mean()).mean() * 100, pct_sim=(nd < gg.r_sim.mean()).mean() * 100,
               p_live=((nd >= gg.r.mean()).sum() + 1) / (NRES + 1), p_sim=((nd >= gg.r_sim.mean()).sum() + 1) / (NRES + 1),
               best_day=best, best_share=share, live_avg_wo=g2.r.mean(), sim_avg_wo=g2.r_sim.mean(),
               null_mean_wo=nd2.mean() if nd2 is not None else np.nan,
               edge_sim_wo=g2.r_sim.mean() - nd2.mean() if nd2 is not None else np.nan,
               p_sim_wo=((nd2 >= g2.r_sim.mean()).sum() + 1) / (NRES + 1) if nd2 is not None else np.nan,
               edge_live_wo=g2.r.mean() - nd2.mean() if nd2 is not None else np.nan,
               p_live_wo=((nd2 >= g2.r.mean()).sum() + 1) / (NRES + 1) if nd2 is not None else np.nan,
               **{f"{md}_{q}": v for md in ("pre", "post") for q, v in zip(("null", "p_sim", "p_live"), (lambda nd_: (nd_.mean(), ((nd_ >= gg.r_sim.mean()).sum() + 1) / (NRES + 1), ((nd_ >= gg.r.mean()).sum() + 1) / (NRES + 1)))(null_dist(idx, md)))},
               first=gg.date.min(), last=gg.date.max(), cand_per_trade=gg.ncand.mean())
    # Primary-only slice for the 5 Primary setups
    if k in prim:
        gp = gg[gg.account == "primary"]
        if len(gp) >= 5:
            ndp = null_dist(gp.index.to_numpy())
            rec.update(prim_n=len(gp), prim_live=gp.r.mean(), prim_sim=gp.r_sim.mean(), prim_null=ndp.mean(),
                       prim_p_sim=((ndp >= gp.r_sim.mean()).sum() + 1) / (NRES + 1),
                       prim_p_live=((ndp >= gp.r.mean()).sum() + 1) / (NRES + 1))
    out.append(rec)
for rec in out:
    gg = v[v.strategy == rec["setup"]]
    rec["pc_sim"] = clustered_p(gg, "r_sim", "cand_mean"); rec["pc_live"] = clustered_p(gg, "r", "cand_mean")
    rec["pc_post_sim"] = clustered_p(gg, "r_sim", "cand_post"); rec["pc_post_live"] = clustered_p(gg, "r", "cand_post")
    g2 = gg[gg.date != rec["best_day"]]
    rec["pc_sim_wo"] = clustered_p(g2, "r_sim", "cand_mean"); rec["pc_live_wo"] = clustered_p(g2, "r", "cand_mean")
res = pd.DataFrame(out).sort_values("edge_sim", ascending=False)


def bh(p):
    p = np.asarray(p); n = len(p); o = np.argsort(p); q = p[o] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]; z = np.empty(n); z[o] = np.minimum(q, 1); return z


res["q_sim"] = bh(res.p_sim); res["q_live"] = bh(res.p_live); res["q_post_sim"] = bh(res.post_p_sim); res["qc_sim"] = bh(res.pc_sim.fillna(1)); res["qc_live"] = bh(res.pc_live.fillna(1))
res.round(4).to_csv(f"{O}/null_results.csv", index=False)
print(res[["setup", "n", "live_avg", "sim_avg", "null_mean", "edge_sim", "p_sim", "p_live"]].round(3).head(30).to_string())

# ---- the one owner image: sorted edge per setup vs its random-entry null (live R after LR8 costs)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
SHORT = {"L3-gap-slope-fromopen-FD": "L3 gap slope", "NM-ETF-late-dip-di-long": "ETF late dip",
         "RW3-gapdn-rsi5pop-flowsell-short-FD": "RW3 gap-dn pop", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "RW5 heat30",
         "ST7-rsi50dn-long-pm-t1s1-FD": "ST7 RSI dip"}
BLUE, GRAY, ORANGE, INK, INK2, SURF = "#2a78d6", "#c9c8c3", "#eb6834", "#0b0b0b", "#52514e", "#fcfcfb"
fig, axes = plt.subplots(2, 1, figsize=(7.2, 9.6), facecolor=SURF)
panels = [("null_mean", "null_p05", "null_p95", "pc_live", "vs random entry minute within ±30 min of the real one"),
          ("post_null", None, None, "pc_post_live", "vs random LATER entry (1-30 min after the real one)")]
for ax, (nm, lo, hi, pc, sub) in zip(axes, panels):
    d = res.assign(edge=res.live_avg - res[nm]).sort_values("edge").reset_index(drop=True)
    x = np.arange(len(d)); win_ = d[pc] < 0.05
    if lo:
        ax.vlines(x, d[lo] - d[nm], d[hi] - d[nm], color="#e4e3de", lw=2.2, label="luck range of random entries (5-95%)")
    ax.axhline(0, color=INK2, lw=1)
    ax.scatter(x[~win_], d.edge[~win_], s=14, color=GRAY, lw=0, label=f"not better than random ({(~win_).sum()})")
    ax.scatter(x[win_], d.edge[win_], s=16, color=BLUE, lw=0, label=f"beats random, p<0.05 ({win_.sum()})")
    pm = d.setup.isin(prim)
    ax.scatter(x[pm], d.edge[pm], s=70, color=ORANGE, edgecolor=SURF, lw=1.5, zorder=5, label="Primary setup")
    for rk, j in enumerate(np.flatnonzero(pm)):
        tag = "beats random" if win_[j] else "not better"
        ax.annotate(f"{SHORT.get(d.setup[j], d.setup[j])} {d.edge[j]:+.2f} ({tag})", (x[j], d.edge[j]),
                    xytext=(len(d) * 0.50, -0.40 - 0.12 * rk), textcoords="data", ha="right", va="center", fontsize=9.5,
                    color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6, shrinkA=3, shrinkB=5, relpos=(1, 0.5)))
    ax.set_ylim(-1.0, 1.0); ax.set_xlim(-2, len(d) + 1); ax.set_xticks([])
    ax.set_ylabel("avg R per trade vs random", fontsize=10, color=INK2)
    ax.set_title(f"{sub}\n{win_.sum()} of {len(d)} setups beat it (luck alone: ~{0.05 * len(d):.0f})", fontsize=11,
                 color=INK, loc="left")
    ax.set_xlabel("each dot = one setup (≥10 live trades), sorted", fontsize=9, color=INK2)
    for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
    ax.set_facecolor(SURF); ax.grid(axis="y", color="#e9e8e4", lw=0.6); ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=8.5, frameon=False)
fig.suptitle("How many setups beat random entries?", fontsize=15, fontweight="bold", color=INK, x=0.02, ha="left")
fig.text(0.02, 0.006, f"Live R after LR8 costs, {res.first.min()} to {res.last.max()}, {int(res.n.sum())} trades. Random entries keep the same stock, day,\n"
         "side, stop & target; p<0.05 day-clustered. Educational only — not financial advice.", fontsize=7.5, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 0.97))
fig.savefig(f"{O}/null_vs_live.png", dpi=150, facecolor=SURF)
