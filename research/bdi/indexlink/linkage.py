"""Task 1 (NOTES 1.2 / 1.3): per-product linkage map -> linkage.csv, plus the ix-leadlag tradable test summary
-> leadlag_results.csv and linkage_summary.json. Educational only - not financial advice."""
import json

import numpy as np
import pandas as pd

from common import DATA, HERE, ROOT, SECTOR, W2ETFS, bars, etf1m, ffill_rows, lib, pit_betas

meta, C5, V5, O0, CL = bars()
syms, dates = meta["syms"], meta["dates"]
ND, NS = len(dates), len(syms)
si = {s: i for i, s in enumerate(syms)}
valid = np.array([str(d) > "2025-12-31" for d in dates])
quarter = np.array([f"{d.year}Q{(d.month - 1) // 3 + 1}" for d in dates])
pb, R, adv = pit_betas(syms, dates)
np.savez(DATA / "pit_betas.npz", **pb)

# daily open-to-close (%), incl. UUP
uup = pd.read_parquet(DATA / "uup_daily.parquet")
uup["date"] = uup["ts"].dt.date
u = uup.set_index("date").reindex(dates)
uup_o2c = ((u["close"] / u["open"] - 1) * 100).to_numpy(float)


def bc(y, x):
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 30:
        return np.nan, np.nan
    x, y = x[ok], y[ok]
    cx = x - x.mean()
    cy = y - y.mean()
    vx = (cx * cx).sum()
    return float((cx * cy).sum() / vx), float((cx * cy).sum() / np.sqrt(vx * (cy * cy).sum()))


def r5(j):
    c = C5[j].astype(np.float64)
    r = np.full(c.shape, np.nan)
    r[:, 1:] = np.log(c[:, 1:] / c[:, :-1])
    return r[:, 1:77]          # bars ending 09:40 .. 15:55


idx5 = {s: r5(si[s]) for s in ["SPY", "QQQ", "IWM", "DIA"] + SECTOR}
b1030, b1555 = 11, 76
spy = si["SPY"]
spy_fo1030 = (C5[spy, :, b1030] / O0[spy] - 1) * 100
spy_rod = (C5[spy, :, b1555] / C5[spy, :, b1030] - 1) * 100
LL = np.load(DATA / "leadlag.npz")["LL"]          # [sym, index, lag, split, (n sx sy sxx syy sxy)]


def llcorr(a):
    n, sx, sy, sxx, syy, sxy = [a[..., k] for k in range(6)]
    with np.errstate(invalid="ignore", divide="ignore"):
        return (sxy - sx * sy / n) / np.sqrt((sxx - sx ** 2 / n) * (syy - sy ** 2 / n))


ll_all = llcorr(LL.sum(3))                          # [sym, index, lag]
ll_split = llcorr(LL)                               # [sym, index, lag, split]
pitsec = np.load(ROOT / "research" / "swarm1010" / "w2_neutral" / "data" / "betas.npz")["sec"]
rows = []
for j, s in enumerate(syms):
    y_d = R[:, j]
    if np.isfinite(y_d).sum() < 60:
        continue
    row = {"symbol": s, "is_etf": s in W2ETFS, "n_days": int(np.isfinite(y_d).sum()),
           "adv20_med_musd": round(float(np.nanmedian(adv[:, j])) / 1e6, 1)}
    for ix in ("SPY", "QQQ", "IWM", "DIA", "VXX", "TLT", "GLD"):
        b, c = bc(y_d, R[:, si[ix]])
        row[f"beta_{ix.lower()}_d"], row[f"corr_{ix.lower()}_d"] = round(b, 3), round(c, 3)
    row["beta_uup_d"], row["corr_uup_d"] = [round(v, 3) for v in bc(y_d, uup_o2c)]
    y5 = r5(j)
    for ix in ("SPY", "QQQ", "IWM", "DIA"):
        b, c = bc(y5.ravel(), idx5[ix].ravel())
        row[f"beta_{ix.lower()}_5m"], row[f"corr_{ix.lower()}_5m"] = round(b, 3), round(c, 3)
    best, bcorr, bbeta = "SPY", -1, np.nan
    for e in SECTOR:
        if e == s:
            continue
        b, c = bc(y5.ravel(), idx5[e].ravel())
        if np.isfinite(c) and c > bcorr:
            best, bcorr, bbeta = e, c, b
    if bcorr < 0.30:
        best, bbeta = "SPY", row["beta_spy_5m"]
    row["sector_etf"], row["corr_sector_5m"], row["beta_sector_5m"] = best, round(bcorr, 3), round(bbeta, 3)
    row["sector_beats_spy_by"] = round(bcorr - row["corr_spy_5m"], 3)
    # stability
    qb = []
    for q in sorted(set(quarter)):
        m = quarter == q
        b, _ = bc(y5[m].ravel(), idx5["SPY"][m].ravel())
        if np.isfinite(b):
            qb.append(b)
    row["beta_spy_5m_q_mean"], row["beta_spy_5m_q_std"] = round(float(np.mean(qb)), 3), round(float(np.std(qb)), 3)
    row["beta_spy_5m_train"] = round(bc(y5[~valid].ravel(), idx5["SPY"][~valid].ravel())[0], 3)
    row["beta_spy_5m_valid"] = round(bc(y5[valid].ravel(), idx5["SPY"][valid].ravel())[0], 3)
    row["beta_spy_pit_last"] = round(float(pb["beta_spy"][-1, j]), 3)
    if best in SECTOR:
        ps = pitsec[:, j]
        okp = ps >= -1
        row["pit_sector_agree_share"] = round(float((ps[okp] == SECTOR.index(best)).mean()), 3) if okp.any() else np.nan
    # lead-lag (1-minute, SPY / QQQ)
    for a, ix in enumerate(("spy", "qqq")):
        c = ll_all[j, a]
        row[f"ll_{ix}_lag0"] = round(float(c[0]), 4)
        row[f"ll_{ix}_lag1"] = round(float(c[1]), 4)
        row[f"ll_{ix}_sum1_5"] = round(float(np.nansum(c[1:6])), 4)
        row[f"ll_{ix}_lag1_train"] = round(float(ll_split[j, a, 1, 0]), 4)
        row[f"ll_{ix}_lag1_valid"] = round(float(ll_split[j, a, 1, 1]), 4)
        k = 1 + int(np.nanargmax(np.abs(c[1:]))) if np.isfinite(c[1:]).any() else 0
        row[f"ll_{ix}_maxlag"], row[f"ll_{ix}_maxcorr"] = k, round(float(c[k]), 4)
    # 5-minute lag 1
    x, y = idx5["SPY"][:, :-1].ravel(), y5[:, 1:].ravel()
    row["ll5_spy_lag1"] = round(bc(y, x)[1], 4)
    # relative-strength persistence (PIT daily beta)
    bt = pb["beta_spy"][:, j].astype(float)
    fo = (C5[j, :, b1030] / O0[j] - 1) * 100
    rod = (C5[j, :, b1555] / C5[j, :, b1030] - 1) * 100
    e1, e2 = fo - bt * spy_fo1030, rod - bt * spy_rod
    ok = np.isfinite(e1) & np.isfinite(e2)
    if ok.sum() >= 60:
        row["rs_persist_corr"] = round(float(np.corrcoef(e1[ok], e2[ok])[0, 1]), 3)
        row["rs_sign_agree"] = round(float((np.sign(e1[ok]) == np.sign(e2[ok])).mean()), 3)
        for nm, m in (("dip", spy_fo1030 <= -0.4), ("rally", spy_fo1030 >= 0.4)):
            mm = ok & m
            row[f"rs_persist_corr_{nm}"] = round(float(np.corrcoef(e1[mm], e2[mm])[0, 1]), 3) if mm.sum() >= 20 else np.nan
            row[f"rs_n_{nm}"] = int(mm.sum())
    rows.append(row)
    if j % 200 == 0:
        print(j, s, flush=True)
L = pd.DataFrame(rows)
L.to_csv(HERE / "linkage.csv", index=False)

# --------------- summary
st = L[~L["is_etf"]]
big = st[st["adv20_med_musd"] >= 95]


def q(x):
    x = x.dropna()
    return {"median": round(float(x.median()), 4), "p10": round(float(x.quantile(0.1)), 4), "p90": round(float(x.quantile(0.9)), 4)}


summ = {"symbols": int(len(L)), "stocks": int(len(st)), "etfs": int(L["is_etf"].sum()), "stocks_adv95": int(len(big))}
for c in ["corr_spy_d", "corr_qqq_d", "corr_iwm_d", "corr_dia_d", "corr_spy_5m", "corr_qqq_5m", "corr_iwm_5m", "corr_dia_5m",
          "beta_spy_5m", "beta_spy_d", "corr_sector_5m", "sector_beats_spy_by", "corr_vxx_d", "corr_tlt_d", "corr_gld_d",
          "corr_uup_d", "beta_spy_5m_q_std", "pit_sector_agree_share", "ll_spy_lag0", "ll_spy_lag1", "ll_spy_sum1_5",
          "ll_qqq_lag1", "ll5_spy_lag1", "rs_persist_corr", "rs_sign_agree", "rs_persist_corr_dip", "rs_persist_corr_rally"]:
    if c in L:
        summ[c] = {"stocks_adv95": q(big[c]), "all_stocks": q(st[c]), "etfs": q(L.loc[L["is_etf"], c])}
summ["best_index_5m_count_adv95"] = big[["corr_spy_5m", "corr_qqq_5m", "corr_iwm_5m", "corr_dia_5m"]].idxmax(axis=1).value_counts().to_dict()
summ["sector_counts_adv95"] = big["sector_etf"].value_counts().to_dict()
summ["beta_train_valid_corr"] = round(float(big[["beta_spy_5m_train", "beta_spy_5m_valid"]].corr().iloc[0, 1]), 3)
summ["lagcorr_profile_spy_median_adv95"] = [round(float(np.nanmedian(ll_all[[si[s] for s in big["symbol"]], 0, L_])), 4) for L_ in range(16)]
summ["lagcorr_profile_qqq_median_adv95"] = [round(float(np.nanmedian(ll_all[[si[s] for s in big["symbol"]], 1, L_])), 4) for L_ in range(16)]
summ["share_lag1_pos_both_splits_adv95"] = round(float(((big["ll_spy_lag1_train"] > 0) & (big["ll_spy_lag1_valid"] > 0)).mean()), 3)
(HERE / "linkage_summary.json").write_text(json.dumps(summ, indent=1))

# --------------- ix-leadlag tradable test (pooled)
z = np.load(DATA / "lltrade.npz")
TD, cfgs = z["TD"], list(z["cfgs"])
esyms, E = etf1m()
reg = lib.regimes()
regd = np.array([reg["regime"].get(d, "") for d in dates])
out = []
for c_i, nm in enumerate(cfgs):
    n_d, net_d, g_d, cont_d = TD[c_i, :, 0], TD[c_i, :, 1], TD[c_i, :, 2], TD[c_i, :, 3]
    N = n_d.sum()
    mu, mg = net_d.sum() / N, g_d.sum() / N
    se = np.sqrt(((net_d - n_d * mu) ** 2).sum()) / N
    seg = np.sqrt(((g_d - n_d * mg) ** 2).sum()) / N
    ix, k, h = nm.split("_")
    c = ffill_rows(E["close"][esyms.index(ix)].astype(float))
    k_, h_ = int(k[1:]), int(h[1:])
    ms = np.arange(19, 330)
    mv = np.log(c[:, ms] / c[:, ms - k_])
    th = 0.0010 if k_ == 1 else 0.0025
    nsig = int((np.abs(mv) >= th).sum())
    rr = {g: round(float(net_d[regd == g].sum() / max(1, n_d[regd == g].sum())), 2) for g in ("up", "flat", "down")}
    vv = valid
    out.append({"config": nm, "index_signals": nsig, "trades": int(N), "gross_bps": round(float(mg), 2), "gross_t": round(float(mg / seg), 2),
                "net_bps": round(float(mu), 2), "net_t": round(float(mu / se), 2),
                "index_continuation_bps": round(float(cont_d.sum() / max(1, nsig)), 2),
                "net_train": round(float(net_d[~vv].sum() / n_d[~vv].sum()), 2), "net_valid": round(float(net_d[vv].sum() / n_d[vv].sum()), 2),
                "up_net": rr["up"], "flat_net": rr["flat"], "down_net": rr["down"],
                "cost_bps": round(float((g_d.sum() - net_d.sum()) / N), 2)})
pd.DataFrame(out).to_csv(HERE / "leadlag_results.csv", index=False)
print(pd.DataFrame(out).to_string())
print(json.dumps({k: v for k, v in summ.items() if not isinstance(v, dict) or "stocks_adv95" in v}, indent=0)[:4000])
