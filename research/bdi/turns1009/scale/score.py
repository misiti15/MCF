"""Score every (condition, side, line) from the per-session aggregates (NOTES 1.5-1.6).
    python score.py A|B   -> data/scores_{A,B}.parquet
Educational only - not financial advice."""
import sys

import numpy as np
import pandas as pd

from common import COND_IDS, DATA, LINES, NC, TRAIN_END, lib, open_dates

T_BAR = 4.58
LINE_NAMES = LINES + [f"{g}_hedged" for g in LINES]


def setup():
    dates = open_dates()
    ds = np.array([str(d) for d in dates])
    reg = lib.regimes()["regime"]
    regime = np.array([reg.get(d, "flat") for d in dates])
    per = pd.PeriodIndex(pd.to_datetime(ds), freq="M")
    months = sorted(set(per))
    mi = np.array([months.index(p) for p in per])
    folds = []
    for i in range(len(months) - 3):
        w = months[i:i + 4]
        if all((b - a).n == 1 for a, b in zip(w, w[1:])):
            folds.append(i + 3)
    return {"train": ds <= TRAIN_END, "valid": ds > TRAIN_END, "regime": regime, "mi": mi, "nm": len(months),
            "folds": folds, "dates": dates}


def name(combo):
    return " & ".join(COND_IDS[i].split()[1] if False else COND_IDS[i] for i in combo if i < NC)


def stats(n_d, s_d, S):
    """Vectorised stats over configs: n_d, s_d [nc, D]."""
    n = n_d.sum(1)
    tot = s_d.sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        mu = tot / n
        se = np.sqrt(((s_d - n_d * mu[:, None]) ** 2).sum(1)) / n
        out = {"n": n, "days": (n_d > 0).sum(1), "exp": mu, "t": mu / se}
        b = s_d.argmax(1)
        r = np.arange(len(n))
        out["ex_best"] = (tot - s_d[r, b]) / (n - n_d[r, b])
        out["busiest"] = n_d.max(1) / n
        for k in ("train", "valid"):
            m = S[k]
            out[f"{k}_n"] = n_d[:, m].sum(1)
            out[f"{k}_exp"] = s_d[:, m].sum(1) / out[f"{k}_n"]
        for k in ("up", "flat", "down"):
            m = S["regime"] == k
            out[f"{k}_n"] = n_d[:, m].sum(1)
            out[f"{k}_exp"] = s_d[:, m].sum(1) / out[f"{k}_n"]
        nm = np.zeros((len(n), S["nm"]))
        sm = np.zeros((len(n), S["nm"]))
        for j in range(S["nm"]):
            m = S["mi"] == j
            nm[:, j] = n_d[:, m].sum(1)
            sm[:, j] = s_d[:, m].sum(1)
        f = S["folds"]
        ok = nm[:, f] >= 10
        pos = (sm[:, f] > 0) & ok
        out["wf_share"] = pos.sum(1) / np.maximum(ok.sum(1), 1)
        out["wf_folds"] = ok.sum(1)
    return out


def score(tag):
    S = setup()
    z = np.load(DATA / f"agg{tag}.npz")
    rows = []
    for side in ("long", "short"):
        a = z[side].astype(np.float64)
        combos = z[f"combos_{side}"]
        b = z[f"base_{side}"]
        names = [name(c) for c in combos]
        ncond = np.array([(np.asarray(c) < NC).sum() for c in combos])
        fires = a[:, 0].sum(1)
        diag = {"fires": fires}
        with np.errstate(invalid="ignore", divide="ignore"):
            for i, k in enumerate((2, 3, 4)):
                base_rate = b[1 + i].sum() / b[0].sum()
                diag[f"p_turn{k}"] = a[:, 1 + i].sum(1) / fires
                diag[f"lift{k}"] = diag[f"p_turn{k}"] / base_rate
                diag[f"cover{k}"] = a[:, 1 + i].sum(1) / b[1 + i].sum()
                tr = S["train"]
                diag[f"lift{k}_train"] = (a[:, 1 + i][:, tr].sum(1) / a[:, 0][:, tr].sum(1)) / (b[1 + i][tr].sum() / b[0][tr].sum())
            diag["fires_train"] = a[:, 0][:, S["train"]].sum(1)
            fb = a[:, 4].sum(1)
            diag["lift_close_raw3"] = (a[:, 5].sum(1) / fb) / (b[5].sum() / b[4].sum())
            diag["lift_close_res3"] = (a[:, 6].sum(1) / fb) / (b[6].sum() / b[4].sum())
            diag["lift_close_raw2"] = (a[:, 7].sum(1) / fb) / (b[7].sum() / b[4].sum())
            diag["lift_close_res2"] = (a[:, 8].sum(1) / fb) / (b[8].sum() / b[4].sum())
            diag["false_alarm2"] = 1 - diag["p_turn2"]
        for li, ln in enumerate(LINE_NAMES):
            hedged = li >= 4
            n_d = a[:, 14] if hedged else a[:, 9]
            s_d = a[:, 15 + li - 4] if hedged else a[:, 10 + li]
            st = stats(n_d, s_d, S)
            df = pd.DataFrame({"side": side, "cond": names, "ncond": ncond, "line": ln, **st,
                               **{k: v for k, v in diag.items()}})
            df["combo"] = [tuple(int(x) for x in c) for c in combos]
            rows.append(df)
    out = pd.concat(rows, ignore_index=True)
    out["pass"] = ((out.n >= 150) & (out.up_n >= 30) & (out.down_n >= 30) & (out.up_exp > 0) & (out.down_exp > 0)
                   & (out.t >= T_BAR) & (out.wf_share >= 0.6) & (out.ex_best > 0) & (out.busiest <= 0.10)
                   & (out.train_exp > 0) & (out.valid_exp > 0))
    out["combo"] = out["combo"].astype(str)
    out.to_parquet(DATA / f"scores_{tag}.parquet", index=False)
    return out


def baselines(tag="A"):
    S = setup()
    z = np.load(DATA / f"agg{tag}.npz")
    rows = []
    for side in ("long", "short"):
        for kind in ("base", "first"):
            b = z[f"{kind}_{side}"]
            for li, ln in enumerate(LINE_NAMES):
                hedged = li >= 4
                n_d = (b[14] if hedged else b[9])[None]
                s_d = (b[15 + li - 4] if hedged else b[10 + li])[None]
                st = stats(n_d, s_d, S)
                rows.append({"side": side, "baseline": "every eligible bar" if kind == "base" else "first bar 09:50",
                             "line": ln, **{k: float(v[0]) for k, v in st.items()}})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "A"
    o = score(tag)
    print(len(o), "lines;", int(o["pass"].sum()), "pass")
