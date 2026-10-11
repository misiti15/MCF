"""Task 2 (NOTES 1.4, lineage ix-gate): market-aware conditions at entry on the 48 live trade lists.
Writes gate_results.csv (one row per list x condition, incl. base rows) and data/gate_trades.parquet.
Educational only - not financial advice."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

DATA = HERE / "data"
FD = ROOT / "research" / "bdi" / "fullday"
SECTOR = "XLK XLF XLE XLV XLY XLP XLI XLB XLU XLRE XLC SMH SOXX XBI IBB KRE KBE XRT XHB ITB GDX XOP OIH IGV XME JETS".split()
CTX = ["SPY", "QQQ"] + SECTOR
PRIMARY = ["heat_fade_short", "heat_fade_long", "exhaustion_short", "MF1-945-flowsell-vwapup", "MF2-open-rsimidhi-flowsell",
           "MF3-open-flowsell-rsi5hi", "MF4-h40-open-flowsell", "MF5-flowsell-vwapup-rsi5hi", "NS1-rsidip-rsi5pop-long",
           "NS2-sma50break-overbought-short", "NS3-failed-vwap-reclaim-short", "NS4-pm-vwap-reclaim-oversold-short",
           "NS5-sma50-flush-oversold-long", "RW6G1-ns2-up3-vwap2sd-short"]
N_LINEAGE = 912 + 1052
TREQ = gates.t_required(N_LINEAGE)


def modinfo(path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def load_lists():
    tt = pd.read_parquet(ROOT / "research" / "bdi" / "timeofday" / "data" / "trades.parquet")
    cur = tt[(tt["set"] == "current") & tt["setup"].isin(PRIMARY)].copy()
    cur["list"] = cur["setup"] + "-cur"
    fd_names = {f.name[:-3] for f in FD.glob("*-FD.py")}
    full = tt[(tt["set"] == "full")].copy()
    full = full[(full["setup"] + "-FD").isin(fd_names)]
    full["list"] = full["setup"] + "-FD"
    out = pd.concat([cur, full], ignore_index=True)[["list", "date", "symbol", "tod", "side", "r"]]
    out["date"] = pd.to_datetime(out["date"]).dt.date
    return out


def main():
    lists = load_lists()
    l3 = {f.name[:-6]: modinfo(f) for f in FD.glob("L3-*-FD.py")}
    cols = ["symbol", "date", "tod", "close", "atr_d", "fromOpen", "vwapDistPct", "gap", "sma20_slope_pct", "rsi5", "dist_lod_atr",
            "r_short_t05s1", "win_short_t05s1", "r_short_t1s1", "win_short_t1s1", "r_short_t1s05", "win_short_t1s05"]
    parts, ctx, l3p = [], [], []
    keyl = set(lists["symbol"].astype(str) + "|" + lists["date"].astype(str) + "|" + lists["tod"].astype(int).astype(str))
    for mo in lib.months():
        df = lib.load_month(mo, cols)
        c = df[df["symbol"].isin(CTX)][["symbol", "date", "tod", "fromOpen", "vwapDistPct"]]
        ctx.append(c)
        for nm, m in l3.items():
            pre = df["gap"].to_numpy(float) <= -2.6573517322540283
            t = gates.lab_trades(df, m.mask(df) & pre & (df["tod"].to_numpy() >= 950) & (df["tod"].to_numpy() <= 1500),
                                 m.SIDE, m.GEOM, tod_costs=False)
            t["list"], t["side"] = nm + "-FD", m.SIDE
            l3p.append(t)
        l3k = set().union(*[set(x["symbol"].astype(str) + "|" + x["date"].astype(str) + "|" + x["tod"].astype(int).astype(str))
                            for x in l3p[-len(l3):]])
        k = df["symbol"].astype(str) + "|" + df["date"].astype(str) + "|" + df["tod"].astype(int).astype(str)
        sel = k.isin(keyl | l3k)
        parts.append(df.loc[sel, ["symbol", "date", "tod", "close", "atr_d", "fromOpen"]])
        print("month", mo, flush=True)
    fr = pd.concat(parts, ignore_index=True)
    L3 = pd.concat(l3p, ignore_index=True)
    lists = pd.concat([lists, L3[["list", "date", "symbol", "tod", "side", "r"]]], ignore_index=True)
    lists = lists.merge(fr, on=["symbol", "date", "tod"], how="left")
    miss = lists["close"].isna().mean()
    print("frame join missing share", round(miss, 5), flush=True)
    # time-of-day entry cost on top of the flat production cost
    R = 0.25 * lists["atr_d"].to_numpy(float)
    mult = gates.tod_cost_mult(lists["tod"].to_numpy(float))
    lists["r0"] = lists["r"]
    lists["r"] = lists["r0"] - (mult - 1) * (gates.SLIP_PS + lists["close"].to_numpy(float) * gates.SLIP_BPS) / R
    # context
    C = pd.concat(ctx, ignore_index=True)
    fo = C.pivot_table(index=["date", "tod"], columns="symbol", values="fromOpen")
    vw = C.pivot_table(index=["date", "tod"], columns="symbol", values="vwapDistPct")
    key = pd.MultiIndex.from_arrays([lists["date"], lists["tod"]])
    for s in ("SPY", "QQQ"):
        lists[f"{s}_fo"] = fo[s].reindex(key).to_numpy()
        lists[f"{s}_vw"] = vw[s].reindex(key).to_numpy()
    # point-in-time beta / sector (W2 betas.npz: prior 60 open sessions)
    BT = np.load(ROOT / "research" / "swarm1010" / "w2_neutral" / "data" / "betas.npz")
    syms = (ROOT / "research" / "lab_symbols.txt").read_text().split()
    dates = sorted(set(lib.daily()["date"]))
    si = {s: i for i, s in enumerate(syms)}
    di = {d: i for i, d in enumerate(dates)}
    ii = lists["symbol"].map(si).to_numpy()
    dd = lists["date"].map(di).to_numpy()
    ok = ~(pd.isna(ii) | pd.isna(dd))
    ii, dd = np.where(ok, ii, 0).astype(int), np.where(ok, dd, 0).astype(int)
    lists["beta"] = np.where(ok, BT["beta_spy"][dd, ii], np.nan)
    sec = np.where(ok, BT["sec"][dd, ii], -2)
    secname = np.where(sec >= 0, np.array(SECTOR + ["SPY"])[np.where(sec >= 0, sec, len(SECTOR))], np.where(sec == -1, "SPY", ""))
    lists["sec"] = secname
    sfo, svw = np.full(len(lists), np.nan), np.full(len(lists), np.nan)
    for s in set(secname) - {""}:
        m = secname == s
        sfo[m] = fo[s].reindex(key[m]).to_numpy()
        svw[m] = vw[s].reindex(key[m]).to_numpy()
    lists["sec_fo"], lists["sec_vw"] = sfo, svw
    lists["rs"] = lists["fromOpen"] - lists["beta"] * lists["SPY_fo"]
    lists = pd.concat([lists, bt_lists(BT, syms, dates)], ignore_index=True)
    lists.to_parquet(DATA / "gate_trades.parquet")
    print("trades", len(lists), flush=True)
    score(lists)


def bt_lists(BT, syms, dates):
    """orb20_a / intraday_momentum (production backtester trades) with context from the dense arrays at the last
    completed 5-minute bar before the entry minute (the frames stop at 15:00)."""
    from common import bars, etf1m
    meta, C5, V5, O0, CL = bars()
    esyms, E = etf1m()
    si = {s: i for i, s in enumerate(syms)}
    di = {d: i for i, d in enumerate(dates)}
    ND = len(dates)
    vwap, fo5 = {}, {}
    for e in CTX:
        k = esyms.index(e)
        h = np.fmax.reduceat(np.nan_to_num(E["high"][k], nan=-np.inf), np.arange(0, 390, 5), axis=1)
        lo = np.fmin.reduceat(np.nan_to_num(E["low"][k], nan=np.inf), np.arange(0, 390, 5), axis=1)
        c = C5[si[e]].astype(float)
        v = np.nan_to_num(E["volume"][k]).reshape(ND, 78, 5).sum(2)
        typ = (np.where(np.isfinite(h), h, c) + np.where(np.isfinite(lo), lo, c) + c) / 3
        vw = np.cumsum(np.nan_to_num(typ) * v, 1) / np.where(np.cumsum(v, 1) > 0, np.cumsum(v, 1), np.nan)
        vwap[e] = (c - vw) / vw * 100
        fo5[e] = (c / O0[si[e]][:, None] - 1) * 100
    b = pd.read_parquet(ROOT / "research" / "history2y" / "data" / "bt_trades.parquet")
    b["date"] = pd.to_datetime(b["date"]).dt.date
    b = b[b["date"].isin(di)].reset_index(drop=True)
    em = b["entry_time"].dt.hour * 60 + b["entry_time"].dt.minute
    bi = ((em - 575) // 5).to_numpy()
    d = b["date"].map(di).to_numpy()
    j = b["symbol"].map(si).to_numpy()
    out = pd.DataFrame({"list": b["strategy"] + "-cur", "date": b["date"], "symbol": b["symbol"],
                        "tod": (b["entry_time"].dt.hour * 100 + b["entry_time"].dt.minute).to_numpy(),
                        "side": np.where(b["side"] == 1, "long", "short")})
    Rd = (b["entry"] - b["stop"]).abs().to_numpy(float)
    mult = gates.tod_cost_mult(out["tod"].to_numpy(float))
    out["r0"] = b["r_multiple"].to_numpy(float)
    out["r"] = out["r0"] - (mult - 1) * (gates.SLIP_PS + b["entry"].to_numpy(float) * gates.SLIP_BPS) / Rd
    out["close"], out["atr_d"] = b["entry"].to_numpy(float), np.nan
    out["fromOpen"] = (C5[j, d, bi] / O0[j, d] - 1) * 100
    for e in ("SPY", "QQQ"):
        out[f"{e}_fo"], out[f"{e}_vw"] = fo5[e][d, bi], vwap[e][d, bi]
    out["beta"] = BT["beta_spy"][d, j]
    sec = BT["sec"][d, j]
    out["sec"] = np.where(sec >= 0, np.array(SECTOR)[np.maximum(sec, 0)], np.where(sec == -1, "SPY", ""))
    sf, sv = np.full(len(out), np.nan), np.full(len(out), np.nan)
    for e in set(out["sec"]) - {""}:
        m = out["sec"].to_numpy() == e
        sf[m], sv[m] = fo5[e][d[m], bi[m]], vwap[e][d[m], bi[m]]
    out["sec_fo"], out["sec_vw"] = sf, sv
    out["rs"] = out["fromOpen"] - out["beta"] * out["SPY_fo"]
    # parity of the rebuilt SPY vwapDistPct with the frames' (bars 09:50..15:00), reported
    return out


def conditions(t):
    s = np.where(t["side"].to_numpy() == "long", 1.0, -1.0)
    g = lambda c: t[c].to_numpy(float)
    agree = lambda x, dz=0.0: (s * x) > dz
    against = lambda x: (s * x) < 0
    beta = g("beta")
    hasb = np.isfinite(beta) & (t["sec"].to_numpy() != "")
    return {
        "F1_spy_vwap": (agree(g("SPY_vw")), None),
        "F2_qqq_vwap": (agree(g("QQQ_vw")), None),
        "F3_spy_fo": (agree(g("SPY_fo")), None),
        "F4_sec_fo": (agree(g("sec_fo")), hasb),
        "F5_sec_vwap": (agree(g("sec_vw")), hasb),
        "F6_rs_with": (agree(g("rs")), hasb),
        "F7_rs_against": (against(g("rs")), hasb),
        "F8_beta_leg": (agree(beta * g("SPY_fo"), 0.20), hasb),
        "F9_spy_vwap_against": (against(g("SPY_vw")), None),
        "F10_sec_fo_against": (against(g("sec_fo")), hasb),
        "F11_low_beta": (beta <= 1.0, hasb),
        "F12_high_beta": (beta > 1.0, hasb),
        "N1_spy_vwap_dz10": (agree(g("SPY_vw"), 0.10), None),
        "N2_qqq_vwap_dz10": (agree(g("QQQ_vw"), 0.10), None),
        "N3_sec_fo_dz10": (agree(g("sec_fo"), 0.10), hasb),
        "N4_spy_fo_dz15": (agree(g("SPY_fo"), 0.15), None),
        "N5_rs_with_dz25": (agree(g("rs"), 0.25), hasb),
        "Z1_beta_size": (np.clip(1.0 / np.where(beta > 0, beta, np.nan), 0.5, 2.0), hasb),
        "Z2_half_against": (np.where(agree(g("SPY_vw")), 1.0, 0.5), None),
    }


NEIGH = {"F1_spy_vwap": "N1_spy_vwap_dz10", "N1_spy_vwap_dz10": "F1_spy_vwap", "F2_qqq_vwap": "N2_qqq_vwap_dz10",
         "N2_qqq_vwap_dz10": "F2_qqq_vwap", "F4_sec_fo": "N3_sec_fo_dz10", "N3_sec_fo_dz10": "F4_sec_fo",
         "F3_spy_fo": "N4_spy_fo_dz15", "N4_spy_fo_dz15": "F3_spy_fo", "F6_rs_with": "N5_rs_with_dz25",
         "N5_rs_with_dz25": "F6_rs_with"}


def stats(tr, reg):
    if not len(tr):
        return {"n": 0}
    s = gates.summary(tr)
    rs = gates.regime_split(tr, reg)
    wf = gates.walk_forward(tr, exclude_months=lib.LOCKED_MONTHS)
    v = np.asarray([str(d) > "2025-12-31" for d in tr["date"]])
    busiest = tr.groupby("date").size().max() / len(tr)
    return {"n": s["n"], "exp": s["exp_r"], "se": s.get("se"), "t": s.get("t"), "ex_best_day": s.get("ex_best_day"),
            "up": rs["up"].get("exp_r"), "up_n": rs["up"].get("n", 0), "flat": rs["flat"].get("exp_r"),
            "down": rs["down"].get("exp_r"), "down_n": rs["down"].get("n", 0), "regime_pass": rs["pass"],
            "wf": wf["share_positive"], "train": float(tr["r"][~v].mean()) if (~v).any() else np.nan,
            "valid": float(tr["r"][v].mean()) if v.any() else np.nan, "n_train": int((~v).sum()), "n_valid": int(v.sum()),
            "busiest": round(float(busiest), 4)}


def score(t):
    reg = lib.regimes()
    rows = []
    for nm, tl in t.groupby("list"):
        tl = tl[np.isfinite(tl["r"])].reset_index(drop=True)
        base_all = stats(tl[["date", "symbol", "r"]], reg)
        rows.append({"list": nm, "cond": "BASE", "base_scope": "all", **base_all})
        cond = conditions(tl)
        hasb = cond["F4_sec_fo"][1]
        base_b = stats(tl.loc[hasb, ["date", "symbol", "r"]], reg)
        rows.append({"list": nm, "cond": "BASE_beta", "base_scope": "beta", **base_b})
        for cn, (val, scope) in cond.items():
            sc = np.ones(len(tl), bool) if scope is None else scope
            base = base_all if scope is None else base_b
            sub = tl.loc[sc, ["date", "symbol", "r"]].reset_index(drop=True)
            if cn.startswith("Z"):
                w = np.asarray(val, float)[sc]
                tw = sub.copy()
                tw["r"] = sub["r"].to_numpy() * w * len(w) / w.sum()
                st = stats(tw, reg)
                kept_blk = (np.nan, np.nan)
            else:
                k = np.asarray(val, bool)[sc]
                st = stats(sub[k], reg)
                bl = gates.summary(sub[~k]) if (~k).sum() > 1 else {"n": 0}
                kept_blk = (bl.get("exp_r", np.nan), bl.get("n", 0))
                if st["n"] > 1 and bl.get("n", 0) > 1 and st.get("se") and bl.get("se"):
                    st["t_kept_vs_blocked"] = round((st["exp"] - bl["exp_r"]) / np.hypot(st["se"], bl["se"]), 2)
            rows.append({"list": nm, "cond": cn, "base_scope": "all" if scope is None else "beta",
                         "base_exp": base["exp"], "base_n": base["n"], "base_train": base["train"], "base_valid": base["valid"],
                         "blocked_exp": kept_blk[0], "blocked_n": kept_blk[1], **st})
        print(nm, flush=True)
    R = pd.DataFrame(rows)
    # plateau, verdicts
    R["plateau_exp"] = np.nan
    for i, r in R.iterrows():
        nb = NEIGH.get(r["cond"])
        if nb:
            m = (R["list"] == r["list"]) & (R["cond"] == nb)
            R.at[i, "plateau_exp"] = R.loc[m, "exp"].iloc[0]
    R["t_req"] = TREQ
    c = R["cond"].str[:1].isin(["F", "N", "Z"])
    R["improves_train_valid"] = c & (R["train"] > R["base_train"]) & (R["valid"] > R["base_valid"])
    R["passes_bar"] = (c & (R["n"] >= 150) & (R["exp"] > 0) & (R["t"].fillna(0) >= TREQ) & R["regime_pass"].fillna(False).astype(bool)
                       & (R["wf"].fillna(0) >= 0.6) & (R["ex_best_day"].fillna(-1) > 0) & (R["busiest"] <= 0.10)
                       & (R["plateau_exp"].isna() | (R["plateau_exp"] > 0)) & R["improves_train_valid"])
    R.to_csv(HERE / "gate_results.csv", index=False)
    print("configs", int(c.sum()), "pass", int(R["passes_bar"].sum()), flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "score":
        score(pd.read_parquet(DATA / "gate_trades.parquet"))
    else:
        main()
