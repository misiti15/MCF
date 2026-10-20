"""Per-setup scorecard over the last N sessions (owner 2026-10-09: 4 sessions before a removal
decision; was 3).

Live (paper) results per setup next to what its backtest expected (config/validation.json, or a setup's own
expected_r in config/scorecard_expectations.json). Few trades decide nothing on their own: the verdict only flags
setups to review. Written to <state>/reports/scorecard.json for the live page and the EOD email.
Educational only — not financial advice.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from ..setup_names import name as setup_name

ROOT = Path(__file__).resolve().parents[2]


def _expected() -> dict[str, float]:
    out: dict[str, float] = {}
    v = ROOT / "config" / "validation.json"
    if v.exists():
        for k, x in json.loads(v.read_text()).get("setups", {}).items():
            if x.get("apr_jun_exp_r") is not None:
                out[k] = float(x["apr_jun_exp_r"])
    cwt = ROOT / "research" / "bdi" / "cwt" / "live" / "verify.json"   # Testing 2 (CWT) modules: scored expectancy
    if cwt.exists():
        for k, x in json.loads(cwt.read_text()).items():
            if isinstance(x, dict) and x.get("exp_scored") is not None:
                out.setdefault(k, float(x["exp_scored"]))
    e = ROOT / "config" / "scorecard_expectations.json"
    if e.exists():
        out.update({k: float(x) for k, x in json.loads(e.read_text()).items()})
    return out


def build(trades: pd.DataFrame, sessions: int = 4, playing_time: dict | None = None, cfg: dict | None = None,
          account: str | None = None, whatif: pd.DataFrame | None = None) -> dict:
    """playing_time: the account's playing-time report (mcf/report/playing_time.py), stored as card['playing_time'].
    cfg/account: adds the since-start leaderboard (all setups enabled in this account, traded or not)."""
    extra = {}
    if playing_time is not None:
        extra["playing_time"] = playing_time
    if cfg is not None:
        extra["leaderboard"] = leaderboard(trades, cfg, account or "primary", whatif)
        extra["generated"] = pd.Timestamp.now(tz="America/New_York").strftime("%Y-%m-%d %H:%M ET")
    if trades is None or not len(trades):
        return {"sessions": 0, "window": "no trades yet", "setups": [], **extra}
    days = sorted(trades["date"].astype(str).unique())[-sessions:]
    tr = trades[trades["date"].astype(str).isin(days)]
    exp = _expected()
    rows = []
    for s, g in tr.groupby("strategy"):
        r = g["r_multiple"].astype(float)
        e = exp.get(s)
        if len(g) < 10:
            verdict = "too few trades"
        elif e is not None and r.mean() < e - 0.15:
            verdict = "below backtest - review"
        elif r.mean() > 0:
            verdict = "positive so far"
        else:
            verdict = "negative so far"
        rows.append({"setup": s, "name": setup_name(s), "trades": int(len(g)), "win_rate": round(float((g["pnl"] > 0).mean()), 3),
                     "avg_r": round(float(r.mean()), 3), "pnl": round(float(g["pnl"].sum()), 2),
                     "expected_r": None if e is None else round(e, 3), "verdict": verdict})
    rows.sort(key=lambda x: x["avg_r"], reverse=True)
    from .eod import tod_table   # cumulative time-of-day tracking (owner 2026-10-09), all sessions so far

    tod = tod_table(trades)
    by_time = [{"bucket": x.bucket, "trades": int(x.trades), "win_rate": round(float(x.win), 3),
                "avg_r": round(float(x.avg_r), 3), "pnl": round(float(x.pnl), 2)} for x in tod.itertuples()]
    return {"sessions": len(days), "window": f"{days[0]} to {days[-1]}", "setups": rows, "by_time": by_time,
            "note": "Paper results; a scorecard flags setups to review, it does not prove or disprove an edge.", **extra}


SHRINK_N = 20   # ranking shrinks avg R toward 0 by n / (n + 20): 5 lucky trades do not outrank 80 steady ones


def leaderboard(trades: pd.DataFrame, cfg: dict | None, account: str, whatif: pd.DataFrame | None = None) -> list[dict]:
    """Since-start results per setup in this account (owner 2026-10-12: rank, win rate, live trades, account),
    including enabled setups with no trades yet. The dashboard merges the accounts' lists. Report only.
    whatif: the account's what-if run (signals not taken, simulated). Its sim_* fields are SIMULATED playing time
    (owner 2026-10-13): never part of trades / win_rate / avg_r / P/L / score."""
    wi = whatif if whatif is not None and len(whatif) else pd.DataFrame(columns=["strategy", "r_multiple"])
    exp = _expected()
    strat = (cfg or {}).get("strategies", {}) or {}
    enabled = {k for k, v in strat.items() if isinstance(v, dict) and v.get("enabled")}
    t = trades if trades is not None and len(trades) else pd.DataFrame(columns=["strategy", "date", "pnl", "r_multiple"])
    rows = []
    for s in sorted(enabled | set(t["strategy"].dropna().astype(str))):
        g = t[t["strategy"] == s]
        r = g["r_multiple"].astype(float)
        n = int(len(g))
        days = sorted(g["date"].astype(str).unique())
        recent = g[g["date"].astype(str).isin(sorted(t["date"].astype(str).unique())[-4:])]
        win, loss = g.loc[g["pnl"] > 0, "pnl"].sum(), -g.loc[g["pnl"] < 0, "pnl"].sum()
        meta = strat.get(s) if isinstance(strat.get(s), dict) else {}
        avg = float(r.mean()) if n else None
        aw, al = (float(r[r > 0].mean()) if (r > 0).any() else None), (float(-r[r <= 0].mean()) if (r <= 0).any() else None)
        sd = float(r.std(ddof=1)) if n > 1 else 0.0
        rows.append({
            "setup": s, "name": setup_name(s), "account": account, "live": s in enabled,
            "former_primary": bool(meta.get("former_primary")),
            "trades": n, "sessions_traded": len(days), "first": days[0] if days else None, "last": days[-1] if days else None,
            "win_rate": round(float((g["pnl"] > 0).mean()), 3) if n else None,
            "avg_r": None if avg is None else round(avg, 3),
            "total_r": round(float(r.sum()), 2) if n else 0.0,
            "pnl": round(float(g["pnl"].sum()), 2) if n else 0.0,
            "profit_factor": round(float(win / loss), 2) if n and loss > 0 else None,
            # owner 2026-10-19: win rate needed to break even at this setup's own average win / loss size (R),
            # and a t-stat on avg R (how sure: about 2 = solid, under 1 = noise). Ranking stays on score.
            "avg_win_r": None if aw is None else round(aw, 3), "avg_loss_r": None if al is None else round(al, 3),
            "breakeven_wr": round(al / (aw + al), 3) if aw and al else None,
            "t_stat": round(avg / (sd / n ** 0.5), 2) if n > 1 and sd > 0 else None,
            # exact sums so the dashboard can merge one setup's records from several accounts (owner 2026-10-20)
            "n_win": int((r > 0).sum()), "win_r_sum": round(float(r[r > 0].sum()), 4),
            "loss_r_sum": round(float(-r[r <= 0].sum()), 4), "r_sq_sum": round(float((r ** 2).sum()), 4),
            "win_pnl": round(float(win), 2), "loss_pnl": round(float(loss), 2), "days": days,
            "recent_trades": int(len(recent)), "recent_avg_r": round(float(recent["r_multiple"].astype(float).mean()), 3) if len(recent) else None,
            "expected_r": None if exp.get(s) is None else round(exp[s], 3),
            "score": round(avg * n / (n + SHRINK_N), 4) if n else None,
            **_sim(wi[wi["strategy"] == s]),
        })
    return rows


def _sim(w: pd.DataFrame) -> dict:
    """SIMULATED (what-if) results of a setup's signals not taken; labelled sim_* and kept apart from live results."""
    r = w["r_multiple"].astype(float)
    return {"sim_trades": int(len(r)), "sim_win_rate": round(float((r > 0).mean()), 3) if len(r) else None,
            "sim_avg_r": round(float(r.mean()), 3) if len(r) else None}


def save(card: dict, state_dir: str | Path) -> Path:
    p = Path(state_dir) / "reports" / "scorecard.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(card, indent=1))
    return p
