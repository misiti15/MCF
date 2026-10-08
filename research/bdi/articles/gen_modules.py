"""Write deployable `type: lab` modules for the chosen finalists (default parameters only, as scored).
Usage: python research/bdi/articles/gen_modules.py <results row index> ...   Educational only - not financial advice."""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
X = lambda k, s: f"_x({s} * c('{k}'), {s} * c('{k}_prev'))"
TRIG = {   # (code(s), new columns, description(side))
    "macdx": (lambda s: X("macdh_12_26_9", s), ["macdh_12_26_9", "macdh_12_26_9_prev"],
              lambda s: f"MACD(12,26,9) line crosses {'above' if s > 0 else 'below'} its signal line"),
    "bbtouch": (lambda s: "c('bbz_lo_20') <= -2" if s > 0 else "c('bbz_hi_20') >= 2", ["bbz_lo_20", "bbz_hi_20"],
                lambda s: f"bar {'low touches the lower' if s > 0 else 'high touches the upper'} Bollinger(20,2) band"),
    "squeeze": (lambda s: f"(c('bbw_pctl_prev') <= 0.2) & ({s} * c('bbz_c_20') > 2)", ["bbw_pctl_prev", "bbz_c_20"],
                lambda s: f"Bollinger squeeze (width in lowest 20% of 60 bars) then close {'above upper' if s > 0 else 'below lower'} band"),
    "stochx": (lambda s: "(c('stk_14') > c('std_14')) & (c('stk_14_prev') <= c('std_14_prev')) & (c('stk_14_prev') < 20)" if s > 0
               else "(c('stk_14') < c('std_14')) & (c('stk_14_prev') >= c('std_14_prev')) & (c('stk_14_prev') > 80)",
               ["stk_14", "std_14", "stk_14_prev", "std_14_prev"],
               lambda s: f"Stochastic(14,3,3) %K crosses {'above %D from below 20' if s > 0 else 'below %D from above 80'}"),
    "dmix": (lambda s: f"(c('adx_14') >= 25) & " + X("dmi_14", s), ["adx_14", "dmi_14", "dmi_14_prev"],
             lambda s: f"ADX(14) >= 25 and {'+DI crosses above -DI' if s > 0 else '-DI crosses above +DI'}"),
    "obvdiv": (lambda s: "c('obv_bull') > 0" if s > 0 else "c('obv_bear') > 0", ["obv_bull", "obv_bear"],
               lambda s: f"OBV divergence: price at a 20-bar {'low' if s > 0 else 'high'} that OBV does not confirm"),
    "emax": (lambda s: X("ema_9_21", s), ["ema_9_21", "ema_9_21_prev"],
             lambda s: f"EMA9 crosses {'above' if s > 0 else 'below'} EMA21 (5-min)"),
    "smax": (lambda s: X("sma_20_50", s), ["sma_20_50", "sma_20_50_prev"],
             lambda s: f"5-min SMA20 crosses {'above' if s > 0 else 'below'} SMA50"),
    "rsix": (lambda s: "(c('rsi14') > 30) & (c('rsi14_prev') <= 30)" if s > 0 else "(c('rsi14') < 70) & (c('rsi14_prev') >= 70)",
             ["rsi14", "rsi14_prev"], lambda s: f"RSI(14) crosses back {'above 30' if s > 0 else 'below 70'}"),
    "vwapx": (lambda s: X("vwapd", s), ["vwapd", "vwapd_prev"], lambda s: f"close crosses {'above' if s > 0 else 'below'} VWAP"),
    "pivx": (lambda s: f"_x({s} * (c('close') - c('piv_p')), {s} * (c('close_prev') - c('piv_p')))", ["piv_p", "close_prev"],
             lambda s: f"close crosses {'above' if s > 0 else 'below'} the classic pivot P (prior day H/L/C)"),
    "s1r1hold": (lambda s: "(c('low') <= c('piv_s1')) & (c('close') > c('piv_s1'))" if s > 0
                 else "(c('high') >= c('piv_r1')) & (c('close') < c('piv_r1'))", ["piv_s1", "piv_r1"],
                 lambda s: "low tags pivot S1 and closes back above" if s > 0 else "high tags pivot R1 and closes back below"),
    "r1s1break": (lambda s: "_x(c('close') - c('piv_r1'), c('close_prev') - c('piv_r1'))" if s > 0
                  else "_x(c('piv_s1') - c('close'), c('piv_s1') - c('close_prev'))", ["piv_r1", "piv_s1", "close_prev"],
                  lambda s: "close breaks above pivot R1" if s > 0 else "close breaks below pivot S1"),
    "fib": (lambda s: "(c('upleg') > 0) & (c('hod') > c('lod')) & (c('low') <= c('hod') - 0.618 * (c('hod') - c('lod'))) & (c('close') > c('hod') - 0.618 * (c('hod') - c('lod')))" if s > 0
            else "(c('upleg') < 1) & (c('hod') > c('lod')) & (c('high') >= c('lod') + 0.618 * (c('hod') - c('lod'))) & (c('close') < c('lod') + 0.618 * (c('hod') - c('lod')))",
            ["hod", "lod", "upleg"], lambda s: f"61.8% Fibonacci retracement of today's {'up' if s > 0 else 'down'}-leg tagged and held"),
    "aroonx": (lambda s: X("aroon_25", s), ["aroon_25", "aroon_25_prev"],
               lambda s: f"Aroon(25) {'up crosses above down' if s > 0 else 'down crosses above up'}"),
    "ichix": (lambda s: "(c('close') > c('ichi_top')) & (c('close_prev') <= c('ichi_top_prev')) & (c('ichi_tk') > 0)" if s > 0
              else "(c('close') < c('ichi_bot')) & (c('close_prev') >= c('ichi_bot_prev')) & (c('ichi_tk') < 0)",
              ["ichi_top", "ichi_bot", "ichi_top_prev", "ichi_bot_prev", "ichi_tk", "close_prev"],
              lambda s: f"close breaks {'above' if s > 0 else 'below'} the Ichimoku cloud with Tenkan {'>' if s > 0 else '<'} Kijun"),
    "tkx": (lambda s: X("ichi_tk", s), ["ichi_tk", "ichi_tk_prev"],
            lambda s: f"Ichimoku Tenkan crosses {'above' if s > 0 else 'below'} Kijun"),
}
FILT = {
    "adx25": (lambda s: "c('adx_14') >= 25", ["adx_14"], lambda s: "ADX(14) >= 25 (trending)"),
    "adxlo": (lambda s: "c('adx_14') < 20", ["adx_14"], lambda s: "ADX(14) < 20 (no trend)"),
    "vwap_with": (lambda s: f"{s} * c('vwapDistPct') > 0", [], lambda s: f"price {'above' if s > 0 else 'below'} VWAP"),
    "vwap_against": (lambda s: f"{s} * c('vwapDistPct') < 0", [], lambda s: f"price {'below' if s > 0 else 'above'} VWAP"),
    "dsma20_with": (lambda s: f"{s} * (c('close') - c('d_sma20')) > 0", ["d_sma20"],
                    lambda s: f"price {'above' if s > 0 else 'below'} the daily SMA20 (prior closes)"),
    "dsma20_against": (lambda s: f"{s} * (c('close') - c('d_sma20')) < 0", ["d_sma20"],
                       lambda s: f"price {'below' if s > 0 else 'above'} the daily SMA20 (prior closes)"),
    "drsi_with": (lambda s: f"{s} * (c('d_rsi14') - 50) > 0", ["d_rsi14"],
                  lambda s: f"daily RSI14 (prior closes) {'> 50' if s > 0 else '< 50'}"),
    "vol15": (lambda s: "c('volumeRatio') >= 1.5", [], lambda s: "bar volume >= 1.5x its 20-bar average"),
    "obv_with": (lambda s: f"{s} * c('obv_slope') > 0", ["obv_slope"], lambda s: f"10-bar OBV slope {'rising' if s > 0 else 'falling'}"),
    "macdh_with": (lambda s: f"{s} * c('macdh_12_26_9') > 0", ["macdh_12_26_9"],
                   lambda s: f"MACD histogram {'> 0' if s > 0 else '< 0'}"),
    "ema_with": (lambda s: f"{s} * c('ema_9_21') > 0", ["ema_9_21"], lambda s: f"EMA9 {'>' if s > 0 else '<'} EMA21"),
    "open_with": (lambda s: f"{s} * c('fromOpen') > 0", [], lambda s: f"stock {'up' if s > 0 else 'down'} from the open"),
}
WIN = {"am": (950, 1130), "pm": (1130, 1500), "all": (950, 1500)}
SHORT = {"adx25": "adx", "adxlo": "noadx", "vwap_with": "vwap", "vwap_against": "antivwap", "dsma20_with": "dsma",
         "dsma20_against": "antidsma", "drsi_with": "drsi", "vol15": "vol", "obv_with": "obv", "macdh_with": "macdh",
         "ema_with": "ema", "open_with": "open"}

TEMPLATE = '''"""{tag} - BDI article-indicator setup (research/bdi/articles, 2026-10-08).
Side {side}, exit {geom} (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
Train {tr_n} trades, {tr_exp:+.3f}R/trade (day-t {tr_t:.2f}); valid {va_n} trades, {va_exp:+.3f}R/trade (day-t {va_t:.2f}),
after the production haircut. {n_cfg} configurations tried. NOT YET SCORED ON THE LOCKED HOLDOUTS.
Needs the article columns: LabStrategy must join research/bdi/articles/features.py::article_features(hist,
(ctx.prev_high, ctx.prev_low, ctx.prev_close), daily_closes) onto its frame (see NOTES.md "Deployment").
Educational only - not financial advice."""
import numpy as np

SIDE = "{side}"
GEOM = "{geom}"
LAYERS = {layers!r}
REQUIRES = {requires!r}   # columns from article_features (beyond the standard lab frame)


def mask(df) -> np.ndarray:
    missing = [k for k in REQUIRES if k not in df]
    if missing:
        raise KeyError(f"{{__name__}}: lab frame lacks article columns {{missing}} (add article_features to LabStrategy)")

    def c(k):
        return df[k].to_numpy(dtype=float)

    def _x(a, ap):
        return (a > 0) & (ap <= 0)

    tod = c("tod")
    with np.errstate(invalid="ignore"):
        return ({conds}) & (tod >= {lo}) & (tod <= {hi})
'''


def write(x, n_cfg):
    s = 1 if x.trigger_side == "long" else -1
    side = x.side
    fs = [f for f in str(x.filters).split("+") if f and f != "nan"]
    tc, tcols, td = TRIG[x.trigger]
    conds = [f"({tc(s)})"] + [f"({FILT[f][0](1 if side == 'long' else -1)})" for f in fs]
    req = list(dict.fromkeys(tcols + [k for f in fs for k in FILT[f][1]]))
    sd = 1 if side == "long" else -1
    layers = [td(s)] + [FILT[f][2](sd) for f in fs]
    lo, hi = WIN[x.window]
    layers.append(f"{lo // 100:02d}:{lo % 100:02d}-{hi // 100:02d}:{hi % 100:02d} ET")
    fam = "fade-" if x.family == "C" else ""
    tag = "-".join(["BDI", fam + x.trigger] + [SHORT[f] for f in fs] + [x.window, side])
    body = TEMPLATE.format(tag=tag, side=side, geom=x.geom, tr_n=int(x.tr_n), tr_exp=x.tr_exp, tr_t=x.tr_t, va_n=int(x.va_n),
                           va_exp=x.va_exp, va_t=x.va_t, n_cfg=n_cfg, layers=layers, requires=req,
                           conds=" & ".join(conds), lo=lo, hi=hi)
    p = HERE / f"{tag}.py"
    p.write_text(body)
    return p


if __name__ == "__main__":
    import json
    r = pd.read_csv(HERE / "results.csv")
    n_cfg = json.loads((HERE / "counts.json").read_text())["total_incl_plateau"]
    for i in map(int, sys.argv[1:]):
        print(write(r.loc[i], n_cfg))
