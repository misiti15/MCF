"""MF1109 (nightly 2026-11-09, pre-registered here before scoring): two targeted remedies for MF-family shorts, on the
2-year lab lists (research/history2y/data/bt_lab1104, uncapped, production costs in, locked block 2024-11..2025-02 absent).
  A  ETF1: skip MF shorts on unleveraged ETFs (name match on data/universe.csv: ETF / Trust / Fund / iShares / SPDR /
     Vanguard / Invesco / Schwab / WisdomTree / Avantis / JPMorgan / Dimensional ..., minus 2x/3x/Ultra/Bull/Bear/Inverse/
     Leveraged/Daily); A2 = all ETFs incl. leveraged.
  B  UPC1: skip MF shorts entered at/after 10:00 while the index tape is UP-confirmed (proxy of the live W60 compass
     without breadth: SPY >= +0.15% from the 09:30 open AND SPY above session VWAP AND QQQ and IWM both > 0 from open,
     at the last closed 1-min bar before entry; B = also SPY's from-open sign positive at every 15-min mark in the last
     60 min (persistence); B2 = no persistence).
Configs: 4 (A, A2, B, B2). Splits: TRAIN 2024-10 + 2025-03..2025-12, VALID 2026-01-01..2026-10-05, FORWARD-ish lab rows
after 10-05 (context). Per config: delta = -(sum R of dropped), day-clustered t of the daily delta, dropped vs kept avg,
per-setup better / worse (Remedies rule), regime split by SPY open-to-close tercile (up / flat / down).
Bar (MF lineage incl. BURST1/2 29 looks + 4): day-clustered t >= max(1.5, sqrt(2 ln 33)) = 2.64 on VALID AND delta > 0 in
TRAIN AND no MF setup worse by > 5% of its R. Educational only - not financial advice."""
import glob, re
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent; TZ = "America/New_York"
T = pd.concat(pd.read_parquet(f) for f in sorted(glob.glob(str(ROOT / "research/history2y/data/bt_lab1104/*.parquet"))))
T = T[T.setup.str.match(r"^MF\d") & (T.side == -1)].copy()
T = T[~((T.date >= "2024-11-01") & (T.date <= "2025-02-28"))]
U = pd.read_csv(ROOT / "data/universe.csv")[["symbol", "name"]]
etf = U.name.str.contains(r"\bETF\b|Trust|\bFund\b|iShares|SPDR|Vanguard|Invesco|Schwab|WisdomTree|Avantis|Dimensional|ProShares|Direxion|Global X|VanEck|First Trust|JPMorgan .*Equity|Index", case=False, regex=True)
lev = U.name.str.contains(r"2X|3X|1\.5X|Ultra|Bull|Bear|Inverse|Leveraged|Daily|Short ", case=False, regex=True)
E_all = set(U.symbol[etf]); E_unlev = set(U.symbol[etf & ~lev])
T["etf"] = T.symbol.isin(E_all); T["etf_unlev"] = T.symbol.isin(E_unlev)
# index tape
idx = {}
for s in ("SPY", "QQQ", "IWM"):
    b = pd.read_parquet(ROOT / f"data/cache_hist/1Min/{s}.parquet"); b = b[(b.index.hour * 60 + b.index.minute >= 570) & (b.index.hour * 60 + b.index.minute < 960)]
    b["date"] = b.index.strftime("%Y-%m-%d"); b["m"] = b.index.hour * 60 + b.index.minute
    g = b.groupby("date"); b["fo"] = b.close / g.open.transform("first") - 1
    if s == "SPY":
        tp = (b.high + b.low + b.close) / 3; b["vw"] = (tp * b.volume).groupby(b.date).cumsum() / b.volume.groupby(b.date).cumsum()
        b["above"] = b.close > b.vw
    idx[s] = b
spy = idx["SPY"].set_index(["date", "m"]); qqq = idx["QQQ"].set_index(["date", "m"]).fo; iwm = idx["IWM"].set_index(["date", "m"]).fo
oc = idx["SPY"].groupby("date").apply(lambda g: g.close.iloc[-1] / g.open.iloc[0] - 1)
q1, q2 = oc.quantile([1 / 3, 2 / 3]); reg = oc.map(lambda x: "up" if x >= q2 else "down" if x <= q1 else "flat")
T["m"] = (T.tod // 100) * 60 + T.tod % 100
key = list(zip(T.date, T.m - 1))
def get(ser, k):
    try: return ser.loc[k]
    except KeyError: return np.nan
T["spy_fo"] = [get(spy.fo, k) for k in key]; T["spy_above"] = [get(spy.above, k) for k in key]
T["qqq_fo"] = [get(qqq, k) for k in key]; T["iwm_fo"] = [get(iwm, k) for k in key]
def persist(d, m):
    ms = [m - 1 - 15 * i for i in range(5)]; v = [get(spy.fo, (d, x)) for x in ms if x >= 570]
    return len(v) >= 2 and all(x == x and x > 0 for x in v)
T["upc_now"] = (T.m >= 600) & (T.spy_fo >= 0.0015) & (T.spy_above == True) & (T.qqq_fo > 0) & (T.iwm_fo > 0)
T["upc_persist"] = T.upc_now.to_numpy() & np.array([persist(d, m) if u else False for d, m, u in zip(T.date, T.m, T.upc_now)], dtype=bool)
T["split"] = np.where(T.date <= "2025-12-31", "TRAIN", np.where(T.date <= "2026-10-05", "VALID", "FWD"))
T["reg"] = T.date.map(reg)
CFG = {"A_etf_unlev": "etf_unlev", "A2_etf_all": "etf", "B_upc_persist": "upc_persist", "B2_upc_now": "upc_now"}
rows, per = [], []
for c, col in CFG.items():
    for sp, g in T.groupby("split"):
        d = g[g[col]]; k = g[~g[col]]
        daily = (-g.r.where(g[col], 0)).groupby(g.date).sum()
        t = daily.mean() / (daily.std(ddof=1) / np.sqrt(len(daily))) if len(daily) > 2 and daily.std() > 0 else np.nan
        regs = {r_: round(-x.r.sum(), 1) for r_, x in d.groupby("reg")}
        rows.append(dict(config=c, split=sp, n=len(g), dropped=len(d), drop_avg=round(d.r.mean(), 4) if len(d) else None,
                         kept_avg=round(k.r.mean(), 4), base_avg=round(g.r.mean(), 4), delta_R=round(-d.r.sum(), 1),
                         t_day=round(t, 2), days=len(daily), by_regime=regs))
        if sp != "FWD":
            for s, x in g.groupby("setup"):
                dd = x[x[col]]; per.append(dict(config=c, split=sp, setup=s, n=len(x), dropped=len(dd), delta_R=round(-dd.r.sum(), 1),
                                                setup_R=round(x.r.sum(), 1)))
R = pd.DataFrame(rows); Pp = pd.DataFrame(per)
R.to_csv(HERE / "mf1109_results.csv", index=False); Pp.to_csv(HERE / "mf1109_setups.csv", index=False)
out = [f"MF shorts on 2y lists: {len(T):,} trades, setups {T.setup.nunique()}; unlev ETF share {T.etf_unlev.mean():.1%}, all-ETF {T.etf.mean():.1%}; "
       f"UP-confirmed proxy share {T.upc_persist.mean():.1%} (no persistence {T.upc_now.mean():.1%})", R.to_string(index=False)]
for c in CFG:
    v = Pp[(Pp.config == c) & (Pp.split == "VALID")]
    out.append(f"{c} VALID per setup: better {(v.delta_R > 0).sum()}, worse {(v.delta_R < 0).sum()} " + str(dict(zip(v.setup, v.delta_R))))
BAR = max(1.5, float(np.sqrt(2 * np.log(33))))
for c in CFG:
    tr = R[(R.config == c) & (R.split == "TRAIN")].iloc[0]; va = R[(R.config == c) & (R.split == "VALID")].iloc[0]
    v = Pp[(Pp.config == c) & (Pp.split == "VALID")]; worst = (v.delta_R < -0.05 * v.setup_R.abs()).any()
    ok = va.t_day >= BAR and tr.delta_R > 0 and not worst
    out.append(f"{c}: TRAIN delta {tr.delta_R:+.1f}R (t {tr.t_day}), VALID delta {va.delta_R:+.1f}R (t {va.t_day}) vs bar {BAR:.2f}; any setup worse >5%: {worst} -> {'PASS' if ok else 'fail'}")
txt = "\n".join(out); (HERE / "mf1109_out.txt").write_text(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
