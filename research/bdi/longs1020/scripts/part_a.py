"""Part A: index-level dip-bounce longs (SPY -> SPXL, QQQ -> TQQQ), 96 configs + 8 parents + 8 A2, with controls.
All four exits from the 1-minute simulator (entry at the next 1-minute open after the decision bar).
Outputs: results_A.csv, trades_A.csv. Educational only - not financial advice."""
import itertools

import numpy as np
import pandas as pd

from common import HERE, SCR, regimes, split_of
from mcf.research import gates

PAIRS = {"SPY": "SPXL", "QQQ": "TQQQ"}
DIPS = ("abs015", "abs030", "rel020")
TRIGS = ("rec20", "vwap", "hl", "brd")
EXITS = ("t1s1", "t05s1", "holdtr", "time60")
WIN = (950, 1030)


def stats(r, dates):
    t = pd.DataFrame({"date": dates, "r": r}).dropna()
    return gates.summary(t)


def load():
    idx5 = pd.read_parquet(SCR / "idx5.parquet")
    idx5["date"] = pd.to_datetime(idx5["date"]).dt.date
    ctx = pd.read_parquet(SCR / "ctx.parquet")
    ctx["date"] = pd.to_datetime(ctx["date"]).dt.date
    sim = pd.read_parquet(SCR / "sim.parquet")
    sim["date"] = pd.to_datetime(sim["date"]).dt.date
    sim = sim[sim.symbol.isin(["SPXL", "TQQQ"])].set_index(["symbol", "date", "tod"]).sort_index()
    etf = pd.read_parquet(SCR / "etf_rows.parquet")
    etf["date"] = pd.to_datetime(etf["date"]).dt.date
    return idx5, ctx, sim, etf


def signal_table(idx5, ctx, etf, sig):
    X = idx5[idx5.sym == sig].copy()
    a = etf[etf.symbol == sig].groupby("date").agg(atr_d=("atr_d", "first"), c0=("close", "first"))
    X = X.merge(a, left_on="date", right_index=True, how="inner")      # sessions with a frame row (atr_d)
    X["atrp"] = X["atr_d"] / X["c0"] * 100
    X = X.merge(ctx[["date", "tod", "breadth", "brdmin"]], on=["date", "tod"], how="left")
    X = X.sort_values(["date", "tod"]).reset_index(drop=True)
    g = X.groupby("date")
    for k in ("c", "h", "l", "vwap", "fo"):
        X["p_" + k] = g[k].shift(1)
    return X


def first_trigger(X, dip, trig, extra=None):
    thr = {"abs015": 0.15, "abs030": 0.30}.get(dip)
    lim = -X["atrp"] * 0.20 if dip == "rel020" else -thr
    dipped = X["runmin"] <= lim
    if trig == "rec20":
        tr = X["fo"] >= X["runmin"] + 0.2 * X["runmin"].abs()
    elif trig == "vwap":
        tr = (X["c"] > X["vwap"]) & (X["p_c"] <= X["p_vwap"])
    elif trig == "hl":
        tr = (X["l"] > X["p_l"]) & (X["c"] > X["p_h"])
    else:
        tr = (X["breadth"] >= X["brdmin"] + 0.10) & (X["fo"] > X["p_fo"])
    m = dipped & tr & (X["tod"] >= WIN[0]) & (X["tod"] <= WIN[1])
    if extra is not None:
        m &= extra
    first = X[m].groupby("date").head(1)
    # first bar on which the dip condition holds inside the window (for the same-day control)
    d0 = X[dipped & (X["tod"] <= WIN[1])].groupby("date")["tod"].first()
    return first[["date", "tod", "fo"]], d0


def parent_trades(sig, dip_pct, dip_by):
    d = pd.read_parquet(SCR / "idx1" / f"{sig}.parquet")
    d["date"] = d.index.date
    end = d.index + pd.Timedelta(minutes=1)
    d["end"] = end.hour * 100 + end.minute
    out = []
    for day, g in d.groupby("date"):
        o = g["open"].iloc[0]
        rl = g["low"].cummin().to_numpy()
        e = g["end"].to_numpy()
        thr = o * (1 - dip_pct / 100)
        dip = (rl <= thr) & (e <= dip_by)
        if not dip.any():
            continue
        i1 = int(np.argmax(dip))
        cl = g["close"].to_numpy()
        for i in range(i1, len(g)):
            if e[i] > 1005:
                break
            if e[i] < 950:
                continue
            if cl[i] >= rl[i] + 0.2 * (o - rl[i]):
                out.append((day, int(e[i]), (cl[i] / o - 1) * 100))
                break
    return pd.DataFrame(out, columns=["date", "tod", "fo"])


def main():
    idx5, ctx, sim, etf = load()
    reg = regimes()
    rows, trades = [], []
    tabs = {s: signal_table(idx5, ctx, etf, s) for s in PAIRS}
    sessions = {s: sorted(set(tabs[s]["date"])) for s in PAIRS}
    # recovery threshold for A2 (train median at 10:00 on dip days; PLAN: feature with max |train AUC - 0.5|)
    P = pd.read_csv(HERE / "predictors.csv")
    best = P.loc[(P["auc_train"] - 0.5).abs().idxmax()]
    feat = best["feature"]
    rec_med = {}
    for s in PAIRS:
        pr = pd.read_csv(HERE / f"predictors_rows_{s}.csv")
        rec_med[s] = float(pr[pr.split == "train"][feat].median())
    print("A2 feature", feat, best["sym"], best["auc_train"], rec_med)

    def ctrl_all(s, ex):
        ins = PAIRS[s]
        out = {}
        for sp in ("train", "valid"):
            ds = [d for d in sessions[s] if split_of([d])[0] == sp]
            v = []
            for tod in range(950, 1035, 5):
                tt = tod
                key = [(ins, d, tt) for d in ds]
                v.append(sim.reindex(key)["s_" + ex].to_numpy(float))
            out[sp] = float(np.nanmean(np.concatenate(v)))
        return out

    CA = {(s, ex): ctrl_all(s, ex) for s in PAIRS for ex in EXITS}
    for s, ex in CA:
        rows.append(dict(cfg=f"CTRL-all-{s}-{ex}", part="A-control", signal=s, exit=ex, train_exp=round(CA[s, ex]["train"], 4),
                         valid_exp=round(CA[s, ex]["valid"], 4)))

    def score(cfg, part, s, ex, tr, d0, parent_key=None):
        ins = PAIRS[s]
        key = list(zip([ins] * len(tr), tr["date"], tr["tod"]))
        r = sim.reindex(key)["s_" + ex].to_numpy(float)
        T = pd.DataFrame({"cfg": cfg, "date": tr["date"].to_numpy(), "tod": tr["tod"].to_numpy(), "r": r,
                          "spy_fo": tr["fo"].to_numpy()})
        T["split"] = split_of(T["date"])
        T["regime"] = T["date"].map(reg)
        T = T.dropna(subset=["r"])
        rec = dict(cfg=cfg, part=part, signal=s, instrument=ins, exit=ex)
        for sp in ("train", "valid"):
            g = T[T.split == sp]
            st = gates.summary(g[["date", "r"]])
            nses = sum(1 for d in sessions[s] if split_of([d])[0] == sp)
            rec.update({f"{sp}_n": st.get("n", 0), f"{sp}_exp": st.get("exp_r"), f"{sp}_t": st.get("t"),
                        f"{sp}_per_day": round(st.get("n", 0) / nses, 3), f"{sp}_ex_best": st.get("ex_best_day"),
                        f"{sp}_ctrl_all": round(CA[s, ex][sp], 4)})
            # same-day control: every window bar from the first dipped bar, same days
            if d0 is not None and len(g):
                v = []
                for d in g["date"]:
                    t0 = d0.get(d, 950)
                    ks = [(ins, d, tt) for tt in range(max(950, t0), 1035, 5) if tt % 100 < 60]
                    v.append(np.nanmean(sim.reindex(ks)["s_" + ex].to_numpy(float)))
                rec[f"{sp}_ctrl_same"] = round(float(np.nanmean(v)), 4)
        for k in ("up", "flat", "down"):
            st = gates.summary(T[T.regime == k][["date", "r"]])
            rec[f"{k}_n"], rec[f"{k}_exp"] = st.get("n", 0), st.get("exp_r")
        bt = T[T.spy_fo <= -0.3]
        st = gates.summary(bt[["date", "r"]])
        rec["badtape_n"], rec["badtape_exp"] = st.get("n", 0), st.get("exp_r")
        st = gates.summary(T[["date", "r"]])
        rec["all_n"], rec["all_exp"], rec["all_t"], rec["all_ex_best"] = st.get("n", 0), st.get("exp_r"), st.get("t"), st.get("ex_best_day")
        rows.append(rec)
        trades.append(T)
        return rec

    for s, dip, trig, ex in itertools.product(PAIRS, DIPS, TRIGS, EXITS):
        tr, d0 = first_trigger(tabs[s], dip, trig)
        score(f"A-{s}-{dip}-{trig}-{ex}", "A", s, ex, tr, d0)
    # parents
    for s, (dp, by) in {"SPY": (0.5, 945), "QQQ": (1.0, 955)}.items():
        tr = parent_trades(s, dp, by)
        tr = tr[tr.date.isin(set(sessions[s]))]
        for ex in EXITS:
            score(f"P-{'IDX5' if s == 'SPY' else 'IDX1'}-{s}-{ex}", "A-parent", s, ex, tr, None)
    # A2
    R = pd.DataFrame([r for r in rows if r.get("part") == "A"]).sort_values("train_t", ascending=False).head(8)
    for _, r in R.iterrows():
        s, dip, trig, ex = r["cfg"].split("-")[1:5]
        X = tabs[s]
        recov = (X["fo"] - X["runmin"]) / X["runmin"].abs()
        extra = recov >= rec_med[s] if feat == "recovery" else None
        tr, d0 = first_trigger(X, dip, trig, extra)
        score(f"A2-{s}-{dip}-{trig}-{ex}-{feat}", "A2", s, ex, tr, d0)
    res = pd.DataFrame(rows)
    res.to_csv(HERE / "results_A.csv", index=False)
    pd.concat(trades, ignore_index=True).to_csv(HERE / "trades_A.csv.gz", index=False)
    cols = ["cfg", "train_n", "train_exp", "train_t", "train_ctrl_all", "train_ctrl_same", "valid_n", "valid_exp", "valid_t",
            "valid_ctrl_all", "valid_ctrl_same", "down_n", "down_exp", "badtape_exp"]
    print(res[res.part != "A-control"][cols].sort_values("valid_t", ascending=False).to_string())
    print(res[res.part == "A-control"][["cfg", "train_exp", "valid_exp"]].to_string())


if __name__ == "__main__":
    main()
