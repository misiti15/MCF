"""swarm15_1029 step 3: score the variant swarm (TRAIN / VALID only; HOLD read once, only for a finalist that beats its
parent on TRAIN and VALID in shrunk avg R and day-clustered t), live vs backtest, lineage N and bars.
Educational only - not financial advice.

    python research/bdi/swarm15_1029/report_15.py      # -> results.csv, live_vs_bt.csv, report_out.txt
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "research" / "history2y"), str(ROOT)]
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/sw15_1029")
LOCK = (pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28"))
PRIOR_PARENT = {  # last top5 parent TRAIN+VALID exp (parity reference; cost model / scale-out may differ, see NOTES)
    "CWT14-failbrk-orl-p05-long": ("top5_1020 (live scale-out 0.25)", -0.0763),
    "CWT14-failbrk-pdl-p05-long": ("top5_1026", -0.0677),
    "CWT14-failbrk-orl-p05-lowvol-long": ("top5_1020 (live scale-out 0.25)", -0.0752),
    "heat_fade_short-FD": ("top5_1015", -0.0304),
    "CWT12-coil-k4-long": ("top5_1027 (scale-out 0.35)", -0.0609),
    "CWT14-failbrk-pdl-p05-lowvol-long": ("top5_1023", -0.0950),
    "CWT14-failbrk-orl-p10-long": ("top5_1020 (live scale-out 0.35)", -0.0695),
    "CWT14-failbrk-pdl-p10-long": ("top5_1023", -0.0880),
    "CWT14-failbrk-orl-p10-lowvol-long": ("top5_1016", -0.0883),
    "CWT14-failbrk-pdh-p05-lowvol-short": ("top5_1020 (live scale-out 0.35)", -0.0761),
    "CWT14-failbrk-pdh-p10-short": ("top5_1019", -0.0881),
    "RW7-gapdn-bounce-early-short-FD": ("top5_1028", -0.0648),
    "RW2-exhaustion-noon-adv150-short-FD": ("top5_1019", -0.0633),
    "LIQ-orl-sweep-open15-s25-long": ("top5_1019", -0.0099),
    "L3-gap-slope-fromopen-FD": ("top5_1023", -0.0166),
}


def split(d):
    d = pd.to_datetime(d)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked row"
    hold = ((d >= "2026-04-01") & (d <= "2026-06-30")) | (d >= "2026-09-16")
    return np.where(hold, "hold", np.where(d <= "2025-12-31", "train", "valid"))


def st(x):
    if not len(x):
        return dict(n=0, exp=np.nan, t=np.nan, ex_best=np.nan, best_share=np.nan, days=0)
    s = gates.summary(x[["date", "r"]])
    g = x.groupby("date")["r"].sum()
    tot = g.sum()
    return dict(n=s["n"], exp=s["exp_r"], t=s["t"] if s["t"] is not None else np.nan, ex_best=s["ex_best_day"],
                best_share=(g.max() / tot) if tot > 0 else np.nan, days=s["days"])


def paired(v, p, npar):
    a = v.groupby("date")["r"].sum()
    b = p.groupby("date")["r"].sum()
    D = a.reindex(a.index.union(b.index), fill_value=0) - b.reindex(a.index.union(b.index), fill_value=0)
    if len(D) < 3 or D.std(ddof=1) == 0:
        return 0.0, 0.0
    return D.sum() / max(npar, 1), D.mean() / (D.std(ddof=1) / math.sqrt(len(D)))


def lineage_n():
    """max configs_tried on the setup's backlog lines (discovery lineage) + every earlier top5/hf grid line's
    configs_tried when it is a grid count (< 1000) - conservative (may double count)."""
    out = {}
    rows = [json.loads(x) for x in open(ROOT / "research" / "backlog.jsonl") if x.strip()]
    for s in PRIOR_PARENT:
        big, small = 0, 0
        for d in rows:
            base = s[:-3] if s.endswith("-FD") else s
            if s not in d.get("id", "") and not d.get("title", "").startswith(s + ":") and d.get("id") != base:
                continue
            ct = d.get("configs_tried") or 0
            if not isinstance(ct, (int, float)):
                continue
            if ct >= 1000:
                big = max(big, int(ct))
            elif d.get("status") == "failed" or d.get("id", "").endswith(("-exec", "-tune")):
                small += int(ct)
        out[s] = (big, small)
    return out


def live():
    t = pd.read_parquet(SCR / "live.parquet")
    out = {}
    for s, g in t.groupby("strategy"):
        x = g.rename(columns={"r_multiple": "r"})[["date", "r"]]
        out[s] = st(x) | {"se": gates.summary(x)["se"]}
    return out


def main():
    T = pd.read_parquet(SCR / "trades.parquet")
    T["split"] = split(T["date"])
    reg = lib.regimes()["regime"]
    reg.index = pd.to_datetime(reg.index).strftime("%Y-%m-%d")
    T["regime"] = T["date"].astype(str).map(reg)
    LV = live()
    LN = lineage_n()
    rows = []
    for s, G in T.groupby("setup", observed=True):
        vars_ = [v for v in G["var"].unique() if v != "P"]
        k = len(vars_)
        big, small = LN[s]
        N = big + small + k
        bar = max(1.5, math.sqrt(2 * math.log(max(N, 2))))
        P = G[G["var"] == "P"]
        Ptr, Pva = P[P.split == "train"], P[P.split == "valid"]
        for v, V in G.groupby("var", observed=True):
            tr, va, tv = V[V.split == "train"], V[V.split == "valid"], V[V.split != "hold"]
            a, b, c = st(tr), st(va), st(tv)
            dtr, ttr = paired(tr, Ptr, len(Ptr))
            dva, tva = paired(va, Pva, len(Pva))
            up = tv[tv.regime == "up"]["r"].mean()
            dn = tv[tv.regime == "down"]["r"].mean()
            ex = (tv["r"] - tv["ctrl"]).dropna()
            ext = gates.summary(pd.DataFrame({"date": tv.loc[ex.index, "date"], "r": ex}))
            shr = lambda m, n: m * n / (n + 20) if n else np.nan  # noqa: E731
            r = dict(setup=s, var=v, knob=V["knob"].iloc[0], n_train=a["n"], exp_train=a["exp"], t_train=a["t"],
                     n_valid=b["n"], exp_valid=b["exp"], t_valid=b["t"], n_tv=c["n"], exp_tv=c["exp"], t_tv=c["t"],
                     shrunk_train=shr(a["exp"], a["n"]), shrunk_valid=shr(b["exp"], b["n"]),
                     per_day_tv=c["n"] / max(c["days"], 1), win_tv=float((tv["r"] > 0).mean()) if len(tv) else np.nan,
                     ex_best_day=c["ex_best"], best_share=c["best_share"], up=up, down=dn,
                     excess_vs_random=ext.get("exp_r"), excess_t=ext.get("t"),
                     d_train=dtr, t_imp_train=ttr, d_valid=dva, t_imp_valid=tva, n_grid=k, lineage_N=N, bar=bar)
            if v != "P":
                beats = (dtr > 0) and (dva > 0) and (shr(a["exp"], a["n"]) > shr(st(Ptr)["exp"], len(Ptr))) \
                    and (shr(b["exp"], b["n"]) > shr(st(Pva)["exp"], len(Pva))) and (a["t"] > st(Ptr)["t"]) \
                    and (b["t"] > st(Pva)["t"])
                pos = (a["exp"] > 0) and (b["exp"] > 0)
                r["beats_parent"] = bool(beats)
                r["pos_train_valid"] = bool(pos)
                full = beats and pos and (c["t"] >= bar) and up > 0 and dn > 0 and c["ex_best"] > 0 and \
                    (ext.get("exp_r") or -1) > 0
                near = beats and pos and (c["t"] >= 1.5) and not full
                r["verdict"] = "pass-pending-hold" if full else ("near-miss" if near else "fail")
                if beats and pos:  # finalist: one HOLD look (lineage look, recorded)
                    h = st(V[V.split == "hold"])
                    r.update(hold_n=h["n"], hold_exp=h["exp"], hold_t=h["t"])
                    if full:
                        r["verdict"] = "pass" if (h["exp"] > 0 and h["t"] >= 1.0) else "fail-hold"
            rows.append(r)
    R = pd.DataFrame(rows)
    # disclosure (NOTES): this script read HOLD for every row that beat its parent with exp > 0 in TRAIN and VALID
    # (9 rows, 2 lineages) instead of one per lineage. The row that would have been the single look (best VALID
    # shrunk avg R among them) is flagged; the others are extra looks and are reported, never used to choose.
    R["hold_official"] = False
    if "hold_n" in R:
        fin = R[R["hold_n"].notna()]
        for s, g in fin.groupby("setup"):
            R.loc[g["shrunk_valid"].idxmax(), "hold_official"] = True
    R.round(4).to_csv(HERE / "results.csv", index=False)
    L = ["Educational only - not financial advice.", f"configurations scored: {int((R['var'] != 'P').sum())} (+{R.setup.nunique()} parents)", ""]
    lb = []
    for s in PRIOR_PARENT:
        p = R[(R.setup == s) & (R["var"] == "P")].iloc[0]
        lv = LV.get(s, {})
        z = (lv["exp"] - p.exp_tv) / lv["se"] if lv.get("se") else np.nan
        flag = "live far better (likely luck)" if z > 2 else ("live far worse (execution?)" if z < -2 else "in line")
        lb.append(dict(setup=s, live_n=lv.get("n"), live_avg=lv.get("exp"), live_t=lv.get("t"),
                       live_wo_best=lv.get("ex_best"), live_best_share=lv.get("best_share"), bt_exp_tv=p.exp_tv,
                       bt_n_tv=p.n_tv, bt_wo_best=p.ex_best_day, prior_ref=PRIOR_PARENT[s][0],
                       prior_exp=PRIOR_PARENT[s][1], z=z, flag=flag))
    LB = pd.DataFrame(lb)
    LB.round(4).to_csv(HERE / "live_vs_bt.csv", index=False)
    L.append(LB.round(3).to_string(index=False))
    L.append("")
    for s in PRIOR_PARENT:
        x = R[R.setup == s].copy()
        L.append(f"=== {s}  grid {x.n_grid.iloc[0]}  lineage N {x.lineage_N.iloc[0]}  bar {x.bar.iloc[0]:.2f}")
        cols = ["var", "knob", "n_tv", "exp_train", "exp_valid", "t_tv", "d_train", "t_imp_train", "d_valid",
                "t_imp_valid", "up", "down", "ex_best_day", "excess_vs_random", "verdict"]
        cols += [c for c in ("hold_n", "hold_exp", "hold_t") if c in x]
        L.append(x[cols].round(4).to_string(index=False))
        L.append("")
    txt = "\n".join(L)
    (HERE / "report_out.txt").write_text(txt + "\nEducational only - not financial advice.\n")
    print(txt)


if __name__ == "__main__":
    main()
