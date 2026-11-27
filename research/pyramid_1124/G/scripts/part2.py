"""Team G Part 2: live-vs-engine gap for GEN-261027-01 and L3-gap-slope-fromopen-FD. Diagnostic only.
Educational only - not financial advice."""
import json, sys
import numpy as np, pandas as pd
INBOX = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox"
sys.path.insert(0, INBOX); sys.path.insert(0, INBOX + "/research/ultimate_1119/top10")
import os; os.chdir(INBOX)
import bench10 as B
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.gates import tod_cost_mult
G = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/G/"
P = G + "../"
TZ = "America/New_York"
cfg = load_config()
U = pd.read_csv("/home/user/MCF/data/universe.csv")
ETBF = pd.Series(np.where(U.easy_to_borrow.astype(str) == "True", 1.0, 0.0), index=U.symbol)
LAB = set(p.stem for p in B.CACHE.glob("*.parquet"))

S = pd.read_parquet(G + "live_sig.parquet").reset_index(drop=True); T = pd.read_parquet(G + "live_tr.parquet").reset_index(drop=True)
T = T[T.exit_time.notna()].copy().reset_index(drop=True)
T["date"] = T.date.astype(str).str[:10]
T["r"] = cost_r_lr8(T, cfg).astype(float)
T = T[T.r.notna()]
T["k"] = T.strategy + "|" + T.symbol + "|" + T.date + "|" + T.entry_time.astype(str).str[:16]
T = T.drop_duplicates("k")
T["fam"] = np.where(T.strategy.str.startswith("GEN"), "GEN-261027-01", "L3-fromopen")
S["fam"] = np.where(S.strategy.str.startswith("GEN"), "GEN-261027-01", "L3-fromopen")
S["bar_time"] = S["info"].str.extract(r'"bar_time": "(\d+)"')[0].astype(float)
S["spread_bps"] = S["info"].str.extract(r'"spread_bps": ([\d.]+)')[0].astype(float)
T = T.merge(S[["broker_order_id", "ref_price", "bar_time", "spread_bps"]].dropna(subset=["broker_order_id"]).drop_duplicates("broker_order_id"),
            on="broker_order_id", how="left")

bars = pd.read_parquet(G + "live_bars.parquet")
bars.index = pd.DatetimeIndex(bars.index).tz_convert(TZ)
BY = {s: g.drop(columns="symbol").sort_index() for s, g in bars.groupby("symbol")}

def walk1(b, date, start_hm, side, e, stop, tgt, touch):
    hh = b.index.hour * 100 + b.index.minute
    d = b.index.date.astype(str) == date
    sel = np.flatnonzero(d & (hh >= start_hm) & (hh < 1555)); aft = np.flatnonzero(d & (hh >= 1555))
    O, H, L, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    eps = 0.0 if touch else 0.01
    for k in sel:
        if (side == 1 and L[k] <= stop) or (side == -1 and H[k] >= stop):
            return (min(O[k], stop) if side == 1 else max(O[k], stop)), 1, hh[k]
        if tgt == tgt and ((side == 1 and H[k] >= tgt + eps) or (side == -1 and L[k] <= tgt - eps)):
            return tgt, 2, hh[k]
    if len(aft): return O[aft[0]], 0, 1555
    if len(sel): return C[sel[-1]], 0, hh[sel[-1]] + 1
    return np.nan, -1, -1

def addr(side, e, px, kind, risk, tod, gap=0.0):
    tier = 3.0 if (abs(gap) >= 20 or e < 5) else 1.0
    ec = (0.01 + e * 1e-4) * float(tod_cost_mult(np.array([tod]))[0])
    xc = (0.0 if kind == 2 else 0.01 + px * 1e-4) + (0.02 if kind == 1 else 0.0)
    bor = B.BORROW * e if side < 0 else 0.0
    g = side * (px - e)
    return g / risk, (g - tier * (ec + xc) - bor) / risk

def hm_add(hm, m):
    t = (hm // 100) * 60 + hm % 100 + m
    return (t // 60) * 100 + t % 60

def replay(rows, use_fill):
    out = []
    for r in rows.itertuples():
        b = BY.get(r.symbol)
        if b is None or not (r.bar_time == r.bar_time) or not (r.ref_price == r.ref_price):
            out.append((np.nan,) * 6); continue
        bt = int(r.bar_time); dec = hm_add(bt, 1)       # decision time = close of bar labelled bar_time
        hh = b.index.hour * 100 + b.index.minute; d = b.index.date.astype(str) == r.date
        cl = b.close.to_numpy(float)[d & (hh == bt)]
        close = float(cl[0]) if len(cl) else np.nan
        risk = abs(r.ref_price - r.stop)
        if use_fill:
            e = r.entry; st = hm_add(int(pd.Timestamp(r.entry_time).tz_convert(TZ).strftime("%H%M")), 1) if "entry_time" in rows else dec
        else:
            e = r.ref_price; st = dec
        px, kd, xt = walk1(b, r.date, st, r.side, e, r.stop, r.target if r.target == r.target else np.nan, False)
        pt, kt, _ = walk1(b, r.date, st, r.side, e, r.stop, r.target if r.target == r.target else np.nan, True)
        if px != px: out.append((close, np.nan, np.nan, np.nan, np.nan, np.nan)); continue
        rr = abs(e - r.stop)
        g, n = addr(r.side, e, px, kd, rr, dec)
        gt, nt = addr(r.side, e, pt, kt, rr, dec)
        out.append((close, g, n, gt, nt, kd))
    return pd.DataFrame(out, columns=["bar_close", "eng_gross", "eng_net", "eng_touch_gross", "eng_touch_net", "eng_kind"], index=rows.index)

res = {}
# ---------- A. live trades: entry, exit path, cost decomposition
T["lab_universe"] = T.symbol.isin(LAB)
T["risk_live"] = (T.entry - T.stop).abs()
T["gross_live"] = T.side * (T.exit - T.entry) / T.risk_live          # r_multiple-like (before costs)
T["cost_live"] = T.gross_live - T.r
a0 = replay(T, use_fill=False); a1 = replay(T, use_fill=True)
T = T.join(a0.add_prefix("ref_")).join(a1.add_prefix("fill_"))
T["entry_slip_R"] = T.side * (T.entry - T.ref_bar_close) / (T.ref_price - T.stop).abs()
T["ref_vs_close_R"] = T.side * (T.ref_price - T.ref_bar_close) / (T.ref_price - T.stop).abs()
T.drop(columns=["meta"], errors="ignore").to_parquet(G + "p2_live_trades.parquet")
for fam, x in T.groupby("fam"):
    x = x[x.fill_eng_net.notna()]
    e = {"n": len(x), "dates": [x.date.min(), x.date.max()],
         "live_net_R": x.r.mean(), "live_gross_R": x.gross_live.mean(), "live_cost_R": x.cost_live.mean(),
         "engine_from_ref_net": x.ref_eng_net.mean(), "engine_from_ref_gross": x.ref_eng_gross.mean(),
         "engine_from_fill_net": x.fill_eng_net.mean(), "engine_from_fill_gross": x.fill_eng_gross.mean(),
         "engine_from_fill_touch_net": x.fill_eng_touch_net.mean(), "engine_from_fill_touch_gross": x.fill_eng_touch_gross.mean(),
         "engine_cost_R_from_fill": (x.fill_eng_gross - x.fill_eng_net).mean(),
         "entry_slip_R_med": x.entry_slip_R.median(), "entry_slip_R_mean": x.entry_slip_R.mean(),
         "ref_vs_bar_close_R_mean": x.ref_vs_close_R.mean(),
         "live_exit_mix": x.exit_reason.value_counts(normalize=True).round(3).to_dict(),
         "engine_exit_mix": x.fill_eng_kind.map({0: "flat", 1: "stop", 2: "target"}).value_counts(normalize=True).round(3).to_dict(),
         "touch_vs_through_R": (x.fill_eng_touch_net - x.fill_eng_net).mean(),
         "path_residual_gross": (x.gross_live - x.fill_eng_touch_gross).mean(),
         "share_lab_universe": x.lab_universe.mean(),
         "live_R_lab_universe": x[x.lab_universe].r.mean(), "live_R_non_lab": x[~x.lab_universe].r.mean(),
         "n_lab": int(x.lab_universe.sum()),
         "live_R_by_window": {"<=11-04": x[x.date <= "2026-11-04"].r.mean(), ">11-04": x[x.date > "2026-11-04"].r.mean()},
         "engine_fill_net_by_window": {"<=11-04": x[x.date <= "2026-11-04"].fill_eng_net.mean(), ">11-04": x[x.date > "2026-11-04"].fill_eng_net.mean()},
         "per_account": x.groupby("account").agg(n=("r", "size"), live=("r", "mean"), eng=("fill_eng_net", "mean")).round(3).to_dict("index")}
    res[fam] = {"A_trades": e}

# ---------- B. all live signals replayed (what live filters do)
S2 = S.copy(); S2["date"] = S2.day.astype(str)
S2 = S2[S2.ref_price.notna() & S2.stop.notna()].reset_index(drop=True)
S2["k2"] = S2.strategy + S2.symbol + S2.date + S2.bar_time.astype(str)
S2 = S2.sort_values("status", ascending=False).drop_duplicates("k2").reset_index(drop=True)
s0 = replay(S2.rename(columns={}), use_fill=False)
S2 = S2.join(s0)
def reason(r):
    if r.status == "submitted": return "taken"
    s = str(r.reason)
    for k in ("not shortable/ETB", "spread", "max positions", "halted", "lot cap", "setup daily loss", "cost filter", "buying power", "crosscheck", "price below"):
        if k in s: return k
    return "other"
S2["why"] = S2.apply(reason, axis=1)
S2["lab_universe"] = S2.symbol.isin(LAB)
S2.drop(columns=["info"]).to_parquet(G + "p2_live_signals.parquet")
for fam, x in S2.groupby("fam"):
    x = x[x.eng_net.notna()]
    res[fam]["B_signals"] = x.groupby("why").agg(n=("eng_net", "size"), eng_net=("eng_net", "mean"), eng_touch=("eng_touch_net", "mean"),
                                                    lab=("lab_universe", "mean")).round(3).to_dict("index")
    res[fam]["B_all_signals_eng_net"] = round(float(x.eng_net.mean()), 4)
    res[fam]["B_spread_bps_taken_vs_skipped"] = [x[x.why == "taken"].spread_bps.median(), x[x.why == "spread"].spread_bps.median()]

# ---------- C. engine (lab) signals on the same dates (selection)
l3 = B.add_r(pd.read_parquet(P + "L3/work/trades_t1.parquet")); l3["date"] = l3.date.astype(str)
l1 = B.add_r(pd.read_parquet(P + "L1/trades_check.parquet")); l1["date"] = l1.date.astype(str)
eng = {"GEN-261027-01": l3[(l3.cfg == "A1") & (l3.ctrl == 0)], "L3-fromopen": l1[(l1.cfg == "L3-gap-slope-fromopen-FD")]}  # L3 round-1 walk is long-only: its short rows are invalid
for fam, e in eng.items():
    lv = T[(T.fam == fam) & (T.date <= "2026-11-04")]
    d0, d1 = lv.date.min(), "2026-11-04"
    ew = e[(e.date >= d0) & (e.date <= d1)]
    rules = B.TESTING_RULES if fam.startswith("GEN") else B.BOOK["primary"]
    eb = B.book(ew, rules, ETBF)
    ebt = B.book(ew, B.TESTING_RULES, ETBF)
    lsd = set(lv.symbol + "|" + lv.date); esd = set(ew.symbol + "|" + ew.date); ebsd = set(eb.symbol + "|" + eb.date)
    sv = S2[(S2.fam == fam) & (S2.date >= d0) & (S2.date <= d1)]
    svsd = set(sv.symbol + "|" + sv.date)
    lv_in = lv.symbol.isin(LAB)
    c = {"window": [d0, d1], "live_trades": len(lv), "live_R": lv.r.mean(), "live_engine_replay_R": lv.fill_eng_net.mean(),
         "engine_raw_signals": len(ew), "engine_raw_R": ew.r.mean(), "engine_booked_home": len(eb), "engine_booked_home_R": eb.r.mean(),
         "engine_booked_testing": len(ebt), "engine_booked_testing_R": ebt.r.mean(),
         "live_trades_in_lab_universe": int(lv_in.sum()),
         "live_symday_with_engine_signal": int(sum(k in esd for k in (lv.symbol + "|" + lv.date))),
         "live_signal_symdays": len(svsd), "live_signal_symdays_in_lab": int(sum(k.split("|")[0] in LAB for k in svsd)),
         "live_signal_symdays_in_lab_with_engine_signal": int(sum((k in esd) for k in svsd if k.split("|")[0] in LAB)),
         "engine_symdays_with_live_signal": int(sum(k in svsd for k in esd)), "engine_symdays": len(esd)}
    # same yardstick on matched symbol-days: engine R of engine signals whose symbol-day live traded vs not
    ew2 = ew.assign(sd=ew.symbol + "|" + ew.date)
    c["engine_R_symdays_live_traded"] = ew2[ew2.sd.isin(lsd)].r.mean(); c["n_engine_symdays_live_traded"] = int(ew2.sd.isin(lsd).sum())
    c["engine_R_symdays_live_signalled_not_traded"] = ew2[ew2.sd.isin(svsd - lsd)].r.mean()
    c["n_engine_live_sig_not_traded"] = int(ew2.sd.isin(svsd - lsd).sum())
    c["engine_R_symdays_no_live_signal"] = ew2[~ew2.sd.isin(svsd)].r.mean(); c["n_engine_no_live_signal"] = int((~ew2.sd.isin(svsd)).sum())
    eb2 = eb.assign(sd=eb.symbol + "|" + eb.date)
    c["engine_booked_R_no_live_signal"] = eb2[~eb2.sd.isin(svsd)].r.mean(); c["n_engine_booked_no_live_signal"] = int((~eb2.sd.isin(svsd)).sum())
    c["engine_booked_R_with_live_signal"] = eb2[eb2.sd.isin(svsd)].r.mean(); c["n_engine_booked_with_live_signal"] = int(eb2.sd.isin(svsd).sum())
    # by day: engine booked R/trade vs live R/trade on the same dates
    dl = lv.groupby("date").r.mean(); de = eb.groupby("date").r.mean()
    j = pd.concat([dl, de], axis=1, keys=["live", "eng"]).dropna()
    c["daily_corr_live_vs_engine"] = round(float(j.corr().iloc[0, 1]), 3) if len(j) > 2 else None
    c["n_days_both"] = len(j)
    # engine full check half and long run
    ebc = B.book(e[B.half(e.date) == "check"], rules, ETBF)
    c["engine_check_half_R_noETB"] = B.book(e[B.half(e.date) == "check"], rules, pd.Series(1.0, index=e.symbol.unique())).r.mean()
    c["engine_check_half_R"] = ebc.r.mean(); c["engine_check_half_n"] = len(ebc)
    # engine R by entry time-of-day vs live
    res[fam]["C_selection"] = {k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else v) for k, v in c.items()}
    # tod profile
    lv_t = lv.assign(h=lv.bar_time // 100); ebc_t = ebc.assign(h=ebc.tod // 100)
    res[fam]["C_tod"] = {"live": lv_t.groupby("h").r.agg(["size", "mean"]).round(3).to_dict("index"),
                         "engine_check": ebc_t.groupby("h").r.agg(["size", "mean"]).round(3).to_dict("index")}
json.dump(res, open(G + "part2.json", "w"), indent=1, default=lambda o: None if o != o else float(o) if isinstance(o, (np.floating, np.integer)) else str(o))
print(json.dumps(res, indent=1, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o)))
