"""Write the lab modules for the finalists with t >= 2 (PLAN.md; none clears the 4.90 bar).
Educational only - not financial advice."""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
FN = pd.read_csv(HERE / "finalists.csv")
ROB = {r["i"]: r for r in json.load(open(HERE / "robust.json"))}

HEAD = '''"""{name} - swarm1017 rework of {parent} (research/swarm1017/rework-ns, Stage {stage}).
Side {side}, exit {geom} (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars. Run with min_adv 95000000 and
window [{w0}, {w1}] (bar close ET){refire}.
Open 2-year history (locked block excluded), production costs: n {n_all} ({per_day}/day), exp {exp_all:+.3f}R, day-clustered t
{t_gate} - BELOW the lineage bar {bar} (N_lineage {nlin}); train n {n_tr} {exp_tr:+.3f}R, valid n {n_va} {exp_va:+.3f}R; up
{up_exp:+.3f} / down {dn_exp:+.3f}; walk-forward share {wf_share}; excess over same-minute random {xs_all:+.3f}R (t {xt_all:.2f});
deflated Sharpe {dsr}. NOT scored on the locked block. A near-miss for the Testing account at most, not primary.
{note}
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "{side}"
GEOM = "{geom}"
LAYERS = {layers!r}


def _keys(df):
    if "symbol" in df and "date" in df:     # offline frames hold many symbol-days
        return pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    return np.zeros(len(df), dtype=np.int64)  # live: one symbol, today's bars


def _prev(df, k, key):
    x = df[k].to_numpy(dtype=float)
    p = np.r_[np.nan, x[:-1]]
    p[np.r_[True, key[1:] != key[:-1]]] = np.nan
    return p


def _dow(df):
    if "date" in df:
        return pd.to_datetime(df["date"]).dt.dayofweek.to_numpy()
    return pd.DatetimeIndex(df.index).dayofweek.to_numpy()


def _spy_fo(df):
    # SPY % from its open at the same bar. NOT in the live lab frame today (live code needed); without it -> no trades.
    if "spy_fo" not in df:
        return np.full(len(df), np.nan)
    return df["spy_fo"].to_numpy(dtype=float)
'''

GUARD = '''

def vwap_band_block(df, k: float) -> np.ndarray:
    """As research/bdi/live1009/RW6G1-ns2-up3-vwap2sd-short.py with band width k: True where a short is blocked
    (close above VWAP and a close above VWAP + k SD since the last close at or below VWAP, same day)."""
    if "volume" not in df:
        return np.ones(len(df), dtype=bool)  # fail safe
    key = _keys(df)
    h, l, c, v = (df[x].to_numpy(dtype=float) for x in ("high", "low", "close", "volume"))
    tp = (h + l + c) / 3
    g = pd.Series(key)
    cv = pd.Series(v).groupby(g).cumsum().to_numpy().copy()
    cv[cv == 0] = np.nan
    vw = pd.Series(tp * v).groupby(g).cumsum().to_numpy() / cv
    var = pd.Series(tp * tp * v).groupby(g).cumsum().to_numpy() / cv - vw * vw
    sd = np.sqrt(np.clip(var, 0, None))
    with np.errstate(invalid="ignore"):
        beyond = c - vw > 0
        seg = pd.Series((~beyond).astype(np.int64)).groupby(g).cumsum().to_numpy()
        band = c - (vw + k * sd) > 0
        flag = pd.Series(band).groupby(key.astype(np.int64) * 100_000 + seg).cummax().to_numpy()
    return beyond & flag
'''

SPECS = {
    0: ("RWN1-rw6g1-rsi65-k25-t05s1-short", "RW6G1 thresholds RSI14 >= 65 (was 60), band guard k 2.5 (was 2), exit t05s1 (was t1s1).",
        ["close crosses above the 5-min SMA50 on this bar", "stock up > 3% from the open", "RSI(14) >= 65",
         "no unresolved close above VWAP + 2.5 SD", "09:50-11:30 ET (bar close)"],
        "(sma50 > 0) & (p_sma50 <= 0) & (fo > 3) & (rsi >= 65) & (tod >= 950) & (tod <= 1130)", 2.5),
    1: ("RWN2-ns2-wed-nearhod-t05s1-short", "NS2 + Wednesday only + within 0.25 daily ATR of the high of day; exit t05s1. Day-of-week filter: no known mechanism - treat as likely selection noise.",
        ["close crosses above the 5-min SMA50 on this bar", "RSI(14) >= 60", "stock up > 2% from the open", "Wednesday",
         "close within 0.25 daily ATR of the high of day", "09:50-11:30 ET"],
        "(sma50 > 0) & (p_sma50 <= 0) & (rsi >= 60) & (fo > 2) & (dow == 2) & (col('dist_hod_atr') < 0.25) & (tod >= 950) & (tod <= 1130)", None),
    2: ("RWN3-ns3-spyup-early-short", "NS3 only while SPY is above its open, 09:50-10:30. Needs SPY fromOpen in the live lab frame (live code needed).",
        ["close crosses above VWAP on this bar", "close above the 5-min SMA50", "stock down > 2% from the open",
         "SPY above its open (same bar) [live code needed]", "09:50-10:30 ET"],
        "(vwap > 0) & (p_vwap <= 0) & (sma50 > 0) & (fo < -2) & (spy > 0) & (tod >= 950) & (tod <= 1030)", None),
    3: ("RWN4-ns2-spyup05-notfri-t05s1-short", "NS2 only while SPY is > 0.5% above its open, not Fridays; exit t05s1. Needs SPY fromOpen (live code needed).",
        ["close crosses above the 5-min SMA50 on this bar", "RSI(14) >= 60", "stock up > 2% from the open",
         "SPY > 0.5% above its open (same bar) [live code needed]", "not Friday", "09:50-11:30 ET"],
        "(sma50 > 0) & (p_sma50 <= 0) & (rsi >= 60) & (fo > 2) & (spy > 0.5) & (dow != 4) & (tod >= 950) & (tod <= 1130)", None),
    4: ("RWN5-ns3-mon-weakrs-short", "NS3 on Mondays when the stock is weaker than SPY from the open. Day-of-week filter: no known mechanism - likely selection noise. Needs SPY fromOpen (live code needed).",
        ["close crosses above VWAP on this bar", "close above the 5-min SMA50", "stock down > 2% from the open",
         "Monday", "stock fromOpen below SPY fromOpen [live code needed]", "09:50-11:30 ET"],
        "(vwap > 0) & (p_vwap <= 0) & (sma50 > 0) & (fo < -2) & (dow == 0) & (fo - spy < 0) & (tod >= 950) & (tod <= 1130)", None),
    5: ("RWN6-rw6g1-atrhi-short", "RW6G1 restricted to high 5-min ATR% names (atrPct >= 0.50, train top tercile); refire cooldown 1 as the live parent.",
        ["close crosses above the 5-min SMA50 on this bar", "stock up > 3% from the open", "RSI(14) >= 60",
         "5-min ATR >= 0.50% of price", "no unresolved close above VWAP + 2 SD", "09:50-11:30 ET (bar close)"],
        "(sma50 > 0) & (p_sma50 <= 0) & (fo > 3) & (rsi >= 60) & (col('atrPct') >= 0.50) & (tod >= 950) & (tod <= 1130)", 2.0),
}
BODY = '''

def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float)

    key = _keys(df)
    rsi, fo, tod = col("rsi"), col("fromOpen"), col("tod")
    sma50, vwap = col("sma50_dist_pct"), col("vwapDistPct")
    p_sma50, p_vwap = _prev(df, "sma50_dist_pct", key), _prev(df, "vwapDistPct", key)
    dow, spy = _dow(df), _spy_fo(df)
    with np.errstate(invalid="ignore"):
        m = {expr}
    return {ret}
'''
J = json.load(open(HERE / "gate_summary.json"))
rows = []
for i, (name, note, layers, expr, k) in SPECS.items():
    r = FN.iloc[i]
    w0, w1 = r.win.split("-")
    txt = HEAD.format(name=name, parent=r.parent, stage=r.stage, side=r.side, geom=r.geom, w0=int(w0), w1=int(w1),
                      refire=", refire: true, refire_cooldown: 1" if r.refire else "", n_all=int(r.n_all),
                      per_day=ROB[i]["per_day"], exp_all=r.exp_all, t_gate=r.t_gate, bar=J["bar"], nlin=J["n_lineage"],
                      n_tr=int(r.n_tr), exp_tr=r.exp_tr, n_va=int(r.n_va), exp_va=r.exp_va, up_exp=r.up_exp,
                      dn_exp=r.dn_exp, wf_share=r.wf_share, xs_all=r.xs_all, xt_all=r.xt_all, dsr=ROB[i]["dsr"],
                      note=note, layers=layers)
    if k is not None:
        txt += GUARD
    txt += BODY.format(expr=expr, ret=f"m & ~vwap_band_block(df, {k})" if k is not None else "m")
    (HERE / "modules" / f"{name}.py").write_text(txt)
    rows.append({"i": i, "name": name, "k": k})
json.dump(rows, open(HERE / "modules" / "index.json", "w"), indent=1)
print(rows)
