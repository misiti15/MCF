"""Check that the RW6G1 module reproduces the trend-guard study's RW6 + G1k2 result (n 424, +0.2637R) on the open
two-year history. Educational only - not financial advice."""
import glob, importlib.util, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT)]
from mcf.research import gates as G

TG = ROOT / "research/bdi/trendguard/data"
sig = pd.read_parquet(TG / "signals.parquet")
sig = sig[sig.setup == "RW6 bdi-rw-ns2-up3"].copy()
sig["date"] = sig["date"].astype(str)
days = set(zip(sig.symbol, sig.date))
feat = pd.concat(pd.read_parquet(p, columns=["symbol", "date", "tod", "high", "low", "close", "volume"]) for p in sorted(glob.glob(str(TG / "feat/*.parquet"))))
feat["date"] = feat["date"].astype(str)
feat = feat[[k in days for k in zip(feat.symbol, feat.date)]].sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
# base layers: the raw RW6 signal bars (lab frame) -> flag them; the module's base mask must agree on these bars
spec = importlib.util.spec_from_file_location("m", Path(__file__).parent / "RW6G1-ns2-up3-vwap2sd-short.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
block = m.vwap_band_block(feat)
feat["block"] = block
s = sig.merge(feat[["symbol", "date", "tod", "block"]], on=["symbol", "date", "tod"], how="left")
print("signal bars", len(s), "missing feat rows", int(s.block.isna().sum()))
s = s[s.block == False].sort_values(["symbol", "date", "tod"]).drop_duplicates(["symbol", "date"])
r = G.prod_r(s.r_frame.to_numpy(), s.win_frame.to_numpy(), s.close.to_numpy(), s.atr_d.to_numpy(), "t1s1")
print("module G1k2: n", len(r), "exp", round(float(np.nanmean(r)), 4), "(study: n 424, exp 0.2637)")
