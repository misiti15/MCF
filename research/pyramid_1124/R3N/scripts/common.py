"""PYRAMID R3N shared pieces: gen2 grammar (prims copied verbatim from research/bdi/ex30/gen2/gen.py via ast), costs,
rule modules for bench10. Educational only - not financial advice."""
from __future__ import annotations
import ast, os, sys
from pathlib import Path
import numpy as np, pandas as pd

INBOX = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(INBOX)); sys.path.insert(0, str(INBOX / "research/ultimate_1119/top10"))
import bench10 as B  # noqa
from mcf.research import gates as GT  # noqa
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")

_src = (INBOX / "research/bdi/ex30/gen2/gen.py").read_text()
_fn = [n for n in ast.parse(_src).body if isinstance(n, ast.FunctionDef) and n.name == "prims"][0]
_ns = {"np": np, "pd": pd}
exec(compile(ast.Module(body=[_fn], type_ignores=[]), "gen2_prims", "exec"), _ns)
prims = _ns["prims"]

TRIG_L = ["vwdn", "hod", "bulldiv", "beardiv", "uwick", "lwick", "rsi5dn", "macdup", "macddn", "flowup", "flowdn", "wide",
          "inside", "round", "dry"]
TRIG_S = ["vwdn", "lod", "bulldiv", "beardiv", "uwick", "lwick", "rsi5dn", "macdup", "macddn", "flowup", "wide", "inside",
          "round", "dry"]
CTX_ALL = ["fo_up", "fo_dn", "fo_flat", "gap_up", "gap_dn", "gap_flat", "pp_hi", "pp_lo", "d20_hi", "d20_lo", "slope_up",
           "slope_dn", "abv_pdh", "blw_pdl", "inside_pd", "rsi_hi", "rsi_lo", "vr_lo", "vs_hi", "heat_hi", "heat_lo", "bp_hi",
           "bp_lo", "vol_hi", "vol_lo", "vw_up", "vw_dn", "spy_up", "spy_dn", "spy_flat", "br_hi", "br_lo", "br_mid", "rs_up",
           "rs_dn"]
CTX_L = [c for c in CTX_ALL if c not in ("spy_up", "spy_dn", "spy_flat", "br_hi", "br_lo", "br_mid", "blw_pdl")]
CTX_S = [c for c in CTX_ALL if c not in ("br_hi", "br_lo", "br_mid", "gap_dn", "abv_pdh")]
assert len(TRIG_L) == 15 and len(TRIG_S) == 14 and len(CTX_L) == 28 and len(CTX_S) == 30
ALLP = sorted(set(TRIG_L + TRIG_S + CTX_L + CTX_S))
BIT = {p: np.uint64(1) << np.uint64(i) for i, p in enumerate(ALLP)}
WINS = {"W1": (1000, 1130), "W2": (1130, 1400), "W3": (1000, 1500)}
GEOMS = ("t1s1", "t05s1", "t1s05")
ADV = 95e6
ETB = pd.read_parquet(HERE.parent / "L2" / "etb_rate.parquet").rate


def family(c):
    f = c.split("_")[0]
    return "volume" if c in ("vr_lo", "vs_hi") else ("pd" if c in ("abv_pdh", "blw_pdl", "inside_pd") else f)


def lab_r(df, side, geom):
    """lab-basis production R for every row (gates.prod_r + x3 extended tier + short borrow)."""
    rr = df[f"r_{side}_{geom}"].to_numpy(float)
    win = df[f"win_{side}_{geom}"].to_numpy(float)
    c, a, tod = df.close.to_numpy(float), df.atr_d.to_numpy(float), df.tod.to_numpy(float)
    out = np.full(len(df), np.nan)
    ok = np.isfinite(rr) & (a > 0) & np.isfinite(c)
    R = 0.25 * a[ok]
    prod = GT.prod_r(rr[ok], win[ok], c[ok], a[ok], geom, tod=tod[ok])
    gross = rr[ok] + 2 * GT.SLIP_PS / R
    tier = np.where((np.abs(df.gap.to_numpy(float)[ok]) >= 20) | (c[ok] < 5), 3.0, 1.0)
    r = gross - tier * (gross - prod)
    if side == "short":
        r = r - 1.2e-4 * c[ok] / R
    out[ok] = r
    return out


def base_ok(df, side):
    """universe filters per side (gate G for longs; ETB + not gap-down for shorts)."""
    m = (np.nan_to_num(df.adv20.to_numpy(float)) >= ADV) & (df.close.to_numpy(float) >= 5)
    if side == "long":
        with np.errstate(invalid="ignore"):
            m &= df.spy_fo.to_numpy(float) >= 0
    else:
        m &= df.symbol.astype(str).map(ETB).fillna(0).to_numpy(float) >= 0.9
        with np.errstate(invalid="ignore"):
            m &= df.gap.to_numpy(float) > -1.0
    return m


def ensure_cols(df):
    for c in ("breadth", "spy_fo"):
        if c not in df.columns:
            df[c] = np.nan
    return df


class RuleMod:
    """bench10-compatible module: mask(df) = trigger & contexts & universe filters (window/ADV applied by bench10)."""
    def __init__(self, rule):
        self.rule = rule
        self.SIDE, self.GEOM = rule["side"], rule["geom"]

    def mask(self, df):
        df = ensure_cols(df.copy())
        P = prims(df)
        m = P[self.rule["trig"]].copy()
        for c in self.rule["ctx"]:
            m &= P[c]
        return m & base_ok(df, self.SIDE)


def rule_name(r):
    return f"N-{r['side'][0].upper()}-{r['trig']}" + "".join("+" + c for c in r["ctx"]) + f"-{r['win']}-{r['geom']}"
