"""primary1029 scoring of the pre-declared configs (PLAN.md) on the open two-year history.
Usage: python eval.py <scratch> <round>   -> results_r<round>.csv, appends counts.json. Educational only - not financial advice."""
import sys, json, math
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import sim
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib
S = Path(sys.argv[1]); RND = int(sys.argv[2])
sig = sim.load(S / "p3" / "p3bt")
_d = lib.daily()[["symbol", "date", "open"]].copy(); _d["date"] = _d["date"].astype(str)
sig = sig.merge(_d.rename(columns={"open": "day_open"}), on=["symbol", "date"], how="left")
sig["from_open"] = sig.entry / sig.day_open - 1
_c = pd.concat([lib.load_context(m) for m in lib.months() if m not in lib.LOCKED_MONTHS], ignore_index=True)[["date", "tod", "breadth_open"]]
_c["date"] = _c["date"].astype(str)
sig = sig.merge(_c, on=["date", "tod"], how="left")
sig = sig.sort_values(["date", "tod", "prio", "tie"]).reset_index(drop=True)
reg = lib.regimes(); reg = reg.reset_index() if "date" not in reg else reg
reg["date"] = pd.to_datetime(reg["date"]).dt.date.astype(str)
REG = dict(zip(reg.date, reg.regime))
SESS = sorted(set(sig.date))
PRIOR_N = 4


def w_poll(tr): return 1.0 / tr.poll_n
def w_later_half(tr): return np.where(tr.lot_seq >= 2, 0.5, 1.0)
def w_harm(tr): return 1.0 / tr.lot_seq
def w_prof(th, low=0.5):
    return lambda tr: np.where((tr.lot_seq >= 2) & ~(tr.open_unr >= th), low, 1.0)
def w_poll_prof(th):
    def f(tr):
        later = (tr.lot_seq >= 2) & (tr.poll_k == 1) | (tr.lot_seq > tr.poll_k)    # a lot that joins lots from an EARLIER poll
        base = 1.0 / tr.poll_n
        return np.where(later & ~(tr.open_unr >= th), 0.5 * base, base)
    return f
def w_fam_brake(n, w=0.5): return lambda tr: np.where((tr.fam == "S") & (tr.fam_stops >= n), w, 1.0)
def w_day_brake(x, w=0.5): return lambda tr: np.where(tr.day_real <= x, w, 1.0)

CONFIGS = {1: {
    "W1_pollsplit": dict(w=w_poll), "W2_later_half": dict(w=w_later_half), "W3_harmonic": dict(w=w_harm),
    "W4_prof025": dict(w=w_prof(0.25)), "W5_poll_prof025": dict(w=w_poll_prof(0.25)),
    "W6_tick15": dict(w=w_later_half, block=lambda c: c["lot_seq"] >= 3),
    "B5_fam1_symday": dict(block=lambda c: c["fam"] == "S" and c["sym_fam_lots"] >= 1),
    "B6_later_if_prof025": dict(block=lambda c: c["lot_seq"] >= 2 and not (c["open_unr"] >= 0.25)),
    "B7_noreentry60": dict(block=lambda c: c["tgt_ago"] == c["tgt_ago"] and c["tgt_ago"] <= 60),
    "D0_STP_2R": dict(block=lambda c: c["setup_real"] <= -2),
    "D1_sym2stops": dict(block=lambda c: c["sym_stops"] >= 2),
    "D2_fam3stops_half": dict(w=w_fam_brake(3)), "D3_day4_half": dict(w=w_day_brake(-4)), "D4_day8_half": dict(w=w_day_brake(-8)),
}}
STP = lambda c: c["setup_real"] <= -2
def both(a, b): return lambda tr: np.asarray(a(tr), float) * np.asarray(b(tr), float)
def w_acct_brake(n, w=0.5): return lambda tr: np.where(tr.acct_stops >= n, w, 1.0)
CONFIGS[2] = {
    "R2a_D0_fam3half": dict(block=STP, w=w_fam_brake(3)), "R2b_D0_fam2half": dict(block=STP, w=w_fam_brake(2)),
    "R2c_D0_fam4half": dict(block=STP, w=w_fam_brake(4)), "R2d_D0_fam5half": dict(block=STP, w=w_fam_brake(5)),
    "R2e_D0_fam3_w033": dict(block=STP, w=w_fam_brake(3, 1 / 3)),
    "R2f_D0_fam3block": dict(block=lambda c: STP(c) or (c["fam"] == "S" and c["fam_stops"] >= 3)),
    "R2g_D0_pollsplit": dict(block=STP, w=w_poll), "R2h_D0_poll_fam3": dict(block=STP, w=both(w_poll, w_fam_brake(3))),
    "R2i_D0_acct3half": dict(block=STP, w=w_acct_brake(3)), "R2j_D0_acct4half": dict(block=STP, w=w_acct_brake(4)),
}
def w_famnet(x, w=0.5): return lambda tr: np.where((tr.fam == "S") & (tr.fam_real <= x), w, 1.0)
CONFIGS[3] = {"R3a_D0_famnet2half": dict(block=STP, w=w_famnet(-2)), "R3b_D0_famnet3half": dict(block=STP, w=w_famnet(-3)),
              "R3c_D0_famnet4half": dict(block=STP, w=w_famnet(-4)),
              "R3d_D0_fam3_and_neg": dict(block=STP, w=lambda tr: np.where((tr.fam == "S") & (tr.fam_stops >= 3) & (tr.fam_real < 0), 0.5, 1.0))}
def w_fo(cond): return lambda tr: np.where((tr.fam == "S") & (tr.side == -1) & cond(tr), 0.5, 1.0)
CONFIGS[4] = {"R4a_D0_gapdn_above_open_half": dict(block=STP, w=w_fo(lambda tr: (tr.gap < 0) & (tr.from_open > 0))),
              "R4b_D0_above_open_half": dict(block=STP, w=w_fo(lambda tr: tr.from_open > 0)),
              "R4c_D0_above_open1pct_half": dict(block=STP, w=w_fo(lambda tr: tr.from_open > 0.01)),
              "R4d_D0_gapdn_above_open_skip": dict(block=lambda c: STP(c) or (c["fam"] == "S" and c["side"] == -1 and c["gap"] < 0 and c["from_open"] > 0))}
def w_br(x, w=0.5): return lambda tr: np.where((tr.fam == "S") & (tr.side == -1) & (tr.breadth_open >= x), w, 1.0)
CONFIGS[5] = {"R5a_D0_breadth055_half": dict(block=STP, w=w_br(0.55)), "R5b_D0_breadth060_half": dict(block=STP, w=w_br(0.60)),
              "R5c_D0_breadth065_half": dict(block=STP, w=w_br(0.65)),
              "R5d_D0_breadth060_skip": dict(block=lambda c: STP(c) or (c["fam"] == "S" and c["side"] == -1 and c["breadth_open"] >= 0.60))}
BASE = {5: dict(block=STP), 4: dict(block=STP), 1: {}, 2: dict(block=STP), 3: dict(block=STP), 2: dict(block=STP)}
# B5 note: sym_fam_lots counts OPEN family lots; a per-day cap needs lots taken today -> handled in run() via seen set
NEEDS_DAYSEEN = {"B5_fam1_symday"}


def maxdd(day):
    c = day.cumsum(); return float((c.cummax() - c).max())


def metrics(tr, w):
    tr = tr.assign(w=w, wr=w * tr.r)
    day = tr.groupby("date").wr.sum().reindex(SESS, fill_value=0.0)
    q = np.sort(day.to_numpy()); k = max(1, int(round(0.05 * len(q))))
    return dict(n=len(tr), avgR=tr.r.mean(), R_per_risk=tr.wr.sum() / tr.w.sum(), totR=tr.wr.sum(), worst=q[0], cvar5=q[:k].mean(),
                red=int((day < 0).sum()), maxdd=maxdd(day), day_sd=day.std(), mean_w=tr.w.mean()), day


def run(cfg, name):
    blk = cfg.get("block")
    if name in NEEDS_DAYSEEN:
        seen = {}
        def blk(c):
            key = (c["date"], c["symbol"])
            if c["fam"] != "S":
                return False
            if key in seen:
                return True
            seen[key] = 1; return False
    tr = sim.simulate(sig, block=blk)
    w = cfg["w"](tr) if "w" in cfg else np.ones(len(tr))
    return tr, np.asarray(w, float)


def row(name, tr, w, pday=None, pcvar_days=None):
    out = {"config": name}
    for part, msk in (("all", np.ones(len(tr), bool)), ("train", (tr.date <= sim.TRAIN_END).to_numpy()), ("valid", (tr.date > sim.TRAIN_END).to_numpy())):
        global SESS
        keep = SESS
        SESS = [d for d in keep if part == "all" or (d <= sim.TRAIN_END) == (part == "train")]
        m, day = metrics(tr[msk], w[msk]); SESS = keep
        for k, v in m.items():
            out[f"{part}_{k}"] = v
        if part == "all":
            alld = day
    rg = tr.date.map(REG).to_numpy()
    for k in ("up", "down"):
        msk = rg == k; out[f"{k}_Rpr"] = (w[msk] * tr.r.to_numpy()[msk]).sum() / w[msk].sum()
    if pday is not None:
        dd = alld - pday
        se = dd.std(ddof=1) / math.sqrt(len(dd)); out["d_day"] = dd.mean(); out["d_t"] = dd.mean() / se if se > 0 else np.nan
        cd = dd[pcvar_days]; out["d_cvar_days"] = cd.mean(); out["d_cvar_t"] = cd.mean() / (cd.std(ddof=1) / math.sqrt(len(cd)))
        tri = np.array([x <= sim.TRAIN_END for x in dd.index])
        for k, m in (("train", tri), ("valid", ~tri)):
            x = dd[m]; out[f"d_{k}"] = x.mean(); out[f"d_{k}_se"] = x.std(ddof=1) / math.sqrt(len(x))
        rr = np.array([REG.get(x) for x in dd.index])
        out["d_up"] = dd[rr == "up"].mean(); out["d_down"] = dd[rr == "down"].mean()
    return out, alld


if __name__ == "__main__":
    ptr, pw = run(BASE[RND], "PARENT")
    prow, pday = row("PARENT", ptr, pw)
    q = pday.sort_values(); pcd = q.index[:max(1, int(round(0.05 * len(q))))]
    rows = [prow]
    grid = CONFIGS[RND]
    ncount = 0
    for name, cfg in grid.items():
        tr, w = run(cfg, name)
        r, _ = row(name, tr, w, pday, pcd); r["round"] = RND; rows.append(r); ncount += 1
        if "w" in cfg:      # uniform-exposure control
            mw = w.mean(); r2, uday = row(f"U({name})", ptr, np.full(len(ptr), mw), pday, pcd); r2["round"] = RND; rows.append(r2); ncount += 1
            _, cday = row(name, tr, w)
            dd = cday - uday; tri = np.array([x <= sim.TRAIN_END for x in dd.index])
            for k, m in (("all", np.ones(len(dd), bool)), ("train", tri), ("valid", ~tri)):
                x = dd[m]; r[f"vsU_{k}"] = x.mean(); r[f"vsU_{k}_t"] = x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))
            x = dd[pcd]; r["vsU_cvar_days"] = x.mean(); r["vsU_cvar_t"] = x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))
        print(name, "done", flush=True)
    cf = HERE / "counts.json"
    cnt = json.loads(cf.read_text()) if cf.exists() else {"prior_related": PRIOR_N, "rounds": {}}
    cnt["rounds"][str(RND)] = ncount
    N = cnt["prior_related"] + sum(cnt["rounds"].values()); cnt["N"] = N; cnt["bar"] = round(max(1.5, math.sqrt(2 * math.log(N))), 3)
    cf.write_text(json.dumps(cnt, indent=1))
    df = pd.DataFrame(rows); df.to_csv(HERE / f"results_r{RND}.csv", index=False)
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 60)
    cols = ["config", "all_n", "all_avgR", "all_R_per_risk", "all_totR", "all_worst", "all_cvar5", "all_red", "all_maxdd", "all_day_sd",
            "train_cvar5", "valid_cvar5", "train_red", "valid_red", "train_totR", "valid_totR", "train_R_per_risk", "valid_R_per_risk",
            "up_Rpr", "down_Rpr", "d_day", "d_t", "d_cvar_days", "d_cvar_t", "all_mean_w",
            "vsU_all", "vsU_all_t", "vsU_train_t", "vsU_valid_t", "vsU_cvar_days", "vsU_cvar_t"]
    if len(sys.argv) > 3:      # re-score only (no count change)
        cnt["rounds"][str(RND)] = ncount
    print("N", N, "bar", cnt["bar"]); print(df[[c for c in cols if c in df]].round(3).to_string(index=False))
