"""One cost-in R for every report (LR2) and the live cost model behind pnl_adj (LR8). Owner yes 2026-11-11.

R after costs (LR2) = pnl_adj / (|entry - stop| x shares). pnl_adj is the broker (Alpaca paper) P/L minus the modelled
real-book costs, booked per trade by mcf.execution.reconcile. Rows without pnl_adj (what-if / backtest simulations,
whose r_multiple already carries the engine's costs) keep r_multiple. The raw broker R stays in the journal
(`r_multiple`) and is shown only where it is labelled raw (`r_raw` after with_cost_r). Dollars stay Alpaca dollars
(owner rule 2026-11-05): the cost model lives in R only.

Live cost model (LR8, research/live_ready/NOTES.md "Proposed cost model"), applied to trades dated on/after
costs.live_model.effective_from (2026-11-12); earlier trades were BOOKED with the flat stop allowance
(costs.stop_slippage_per_share), and every report re-costs them with LR8 (DQ-P3, with_cost_r / cost_r_lr8: one basis):
  stop exits          max($0.02, 4 bps x price) per share on top of the paper fill (replaces the flat $0.02)
  target (limit)      filled AT the limit: any paper price improvement is given back
  market exits        max($0.01, 1 bp x price) per share (flatten, time stop, scale-out, unprotected close)
  entry               1 bp x entry price per share (latency / impact cushion)
  fees                SEC Section 31 on sell notional, FINRA TAF per share sold (capped per trade), CAT per share per
                      side; dated rates in config (costs.live_model.fees, with sources)
Educational only - not financial advice."""

from __future__ import annotations

import math

import pandas as pd

R_LABEL = "R after costs"
MARKET_EXITS = ("flatten", "timestop", "scaleout", "unprotected", "spy_exit")   # spy_exit: SPYEXIT 2026-11-16


# ----------------------------------------------------------------------------------------------------- LR2: R after costs
def cost_r(df: pd.DataFrame) -> pd.Series:
    """Per-row R after costs: pnl_adj / risk where pnl_adj and the risk are known, else r_multiple."""
    if df is None or not len(df):
        return pd.Series(dtype=float)
    raw = pd.to_numeric(df["r_multiple"], errors="coerce") if "r_multiple" in df else pd.Series(float("nan"), index=df.index)
    if "pnl_adj" not in df or not {"entry", "stop", "shares"} <= set(df.columns):
        return raw.astype(float)
    risk = (pd.to_numeric(df["entry"], errors="coerce") - pd.to_numeric(df["stop"], errors="coerce")).abs() \
        * pd.to_numeric(df["shares"], errors="coerce").abs()
    adj = pd.to_numeric(df["pnl_adj"], errors="coerce")
    ok = adj.notna() & risk.notna() & (risk > 0)
    out = raw.astype(float).copy()
    out[ok] = adj[ok] / risk[ok]
    return out


_LR8_CFG: dict = {}


def _report_cfg() -> dict | None:
    """The config whose costs.live_model the reports use for the one LR8 basis (DQ-P3), loaded once per process."""
    if "cfg" not in _LR8_CFG:
        try:
            from .config import load_config

            _LR8_CFG["cfg"] = {"costs": (load_config().get("costs") or {})}
        except Exception:
            _LR8_CFG["cfg"] = None
    return _LR8_CFG["cfg"]


def with_cost_r(df: pd.DataFrame | None, cfg: dict | None = None, lr8_basis: bool = True) -> pd.DataFrame | None:
    """A copy whose r_multiple is R after costs; the raw broker R moves to r_raw. Idempotent.

    DQ-P3 (owner yes 2026-11-18, "we want to underestimate potential, not overestimate"): every report reads ONE cost
    basis - rows dated before costs.live_model.effective_from (2026-11-12) are re-costed with the LR8 model
    (cost_r_lr8), so a record spanning 11-12 no longer mixes the old flat stop allowance with LR8 (pre-11-12 rows
    ~0.04R lower per trade). The journal's pnl_adj is never changed. lr8_basis=False gives the booked basis."""
    if df is None:
        return df
    if "r_raw" in df.columns:
        return df
    out = df.copy()
    out["r_raw"] = out["r_multiple"] if "r_multiple" in out else float("nan")
    if len(out):
        out["r_multiple"] = cost_r_lr8(df, cfg if cfg is not None else _report_cfg()) if lr8_basis else cost_r(df)
    return out


# ----------------------------------------------------------------------------------------------------- LR8: live costs
def live_model(cfg: dict | None) -> dict | None:
    m = ((cfg or {}).get("costs") or {}).get("live_model")
    return m if isinstance(m, dict) and m.get("enabled", True) else None


def applies(model: dict | None, day) -> bool:
    if not model:
        return False
    eff = model.get("effective_from")
    return eff is None or str(day)[:10] >= str(eff)[:10]


def rate_on(entries, day) -> dict:
    """The dated fee entry in effect on `day` (latest `from` <= day); {} when none applies."""
    best = {}
    for e in entries or []:
        if str(e.get("from", "0000"))[:10] <= str(day)[:10] and str(e.get("from", "0000")) >= str(best.get("from", "")):
            best = e
    return best


def fees(side: int, entry: float, qty: float, parts, day, model: dict) -> dict:
    """Regulatory fees ($) of one lot: SEC on sell notional, TAF on shares sold (capped per sale), CAT both sides."""
    f = model.get("fees") or {}
    sells = [(qty, entry)] if side == -1 else [(q, px) for q, px, *_ in parts]
    sell_notional = sum(q * px for q, px in sells)
    sec = rate_on(f.get("sec_per_million"), day).get("rate", 0.0) * sell_notional / 1e6
    taf_r = rate_on(f.get("taf"), day)
    taf = sum(min(q * float(taf_r.get("per_share", 0.0)), float(taf_r.get("max_per_trade", math.inf))) for q, _ in sells)
    cat_r = rate_on(f.get("cat"), day)
    shares_out = sum(q for q, *_ in parts)
    cat = float(cat_r.get("per_share_side", 0.0)) * (qty + shares_out)
    return {"sec": sec, "taf": taf, "cat": cat}


def lot_costs(side: int, entry: float, qty: float, parts, target, day, model: dict) -> dict:
    """$ costs of one closed lot under the live model. parts = [(qty, price, reason), ...] of its exit fills (reasons
    as reconcile names them: stop / target / flatten / timestop / scaleout / unprotected)."""
    stop_min, stop_bps = float(model.get("stop_min_per_share", 0.02)), float(model.get("stop_bps", 4.0))
    mkt_min, mkt_bps = float(model.get("market_exit_min_per_share", 0.01)), float(model.get("market_exit_bps", 1.0))
    out = {"stop": 0.0, "target": 0.0, "market": 0.0, "entry": float(model.get("entry_bps", 1.0)) * entry / 1e4 * qty}
    for q, px, why in ((p[0], p[1], p[2]) for p in parts):
        if why == "stop":
            out["stop"] += max(stop_min, stop_bps * px / 1e4) * q
        elif why == "target":
            if model.get("target_at_limit", True) and target is not None and not pd.isna(target):
                better = side * (px - float(target))   # paper price improvement over the limit, given back
                if better > 0:
                    out["target"] += better * q
        elif why in MARKET_EXITS:
            out["market"] += max(mkt_min, mkt_bps * px / 1e4) * q
    out.update(fees(side, entry, qty, parts, day, model))
    out["total"] = sum(v for k, v in out.items())
    return out


def pnl_adj(pnl: float, side: int, entry: float, qty: float, parts, target, day, cfg: dict | None) -> tuple[float, str]:
    """(pnl_adj, model tag) for one lot: the live model from its effective date, else the flat stop allowance."""
    model = live_model(cfg)
    if applies(model, day):
        return pnl - lot_costs(side, entry, qty, parts, target, day, model)["total"], "lr8"
    flat = float(((cfg or {}).get("costs") or {}).get("stop_slippage_per_share", 0.02))
    return pnl - flat * sum(p[0] for p in parts if p[2] == "stop"), "flat"


def parts_from_row(row) -> list[tuple[float, float, str]]:
    """A journal trade's exit fills: meta exit_parts (reason:qty@px,...) when booked in several parts, else one part
    (shares @ exit, exit_reason; 'scaled+X' -> X, breakeven -> stop)."""
    g = row.get if hasattr(row, "get") else (lambda k, d=None: getattr(row, k, d))
    meta = str(g("meta", "") or "")
    for tok in meta.split(";"):
        if tok.startswith("exit_parts="):
            out = []
            for p in tok[len("exit_parts="):].split(","):
                try:
                    why, rest = p.split(":", 1)
                    q, px = rest.split("@", 1)
                    out.append((float(q), float(px), why))
                except ValueError:
                    continue
            if out:
                return out
    why = str(g("exit_reason", "") or "")
    why = why.split("+", 1)[1] if why.startswith("scaled+") else why
    why = "stop" if why == "breakeven" else why
    return [(float(g("shares", 0) or 0), float(g("exit", 0) or 0), why)]


# ------------------------------------------------------------------------- W8-DQ: one cost basis across the 11-12 change
def cost_r_lr8(df: pd.DataFrame, cfg: dict | None) -> pd.Series:
    """Per-row R after costs with the LR8 live model applied to EVERY live row, whatever its date (research / report
    only; the journal's pnl_adj is never changed). Before costs.live_model.effective_from (2026-11-12) the journal booked
    only the flat stop allowance, so a since-start average mixes two cost bases (~0.04R per trade apart on the live
    journals, crunch W8). Rows on/after the effective date keep their booked pnl_adj; rows without pnl_adj (what-if /
    backtest) keep r_multiple; rows without a risk keep cost_r. The model's fee rates are taken as of the effective date
    for earlier rows (the rates in force then are the same dated entries)."""
    out = cost_r(df)
    model = live_model(cfg)
    if model is None or df is None or not len(df) or "pnl_adj" not in df:
        return out
    eff = str(model.get("effective_from") or "0000")[:10]
    pre = df["pnl_adj"].notna() & (df["date"].astype(str).str[:10] < eff) if "date" in df else df["pnl_adj"].notna()
    need = [c for c in ("side", "entry", "stop", "shares", "pnl", "exit", "date") if c not in df]
    if need and pre.any():
        # QA 11-21 C1: a caller that drops these columns silently kept the old cost basis on every pre-11-12 row
        raise KeyError(f"cost_r_lr8 needs columns {need} to re-cost pre-{eff} live rows")
    for i, row in df.iterrows():
        if pd.isna(row.get("pnl_adj")) or str(row.get("date"))[:10] >= eff:
            continue
        try:
            risk = abs(float(row["entry"]) - float(row["stop"])) * abs(float(row["shares"]))
            if not risk > 0:
                continue
            tgt = row.get("target")
            tgt = None if tgt is None or pd.isna(tgt) else float(tgt)
            c = lot_costs(int(row["side"]), float(row["entry"]), float(row["shares"]), parts_from_row(row), tgt,
                          str(row.get("date"))[:10], model)["total"]
            out[i] = (float(row["pnl"]) - c) / risk
        except (TypeError, ValueError, KeyError):
            continue
    return out
