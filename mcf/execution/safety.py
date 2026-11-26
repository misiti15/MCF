"""Friday 11-27 safety switches (pre-built, every one OFF by default; config `risk:`). Educational only - not financial advice.

None of these ever flattens or closes a lot: each one only blocks NEW entries (or, B8, only logs what it would block).
  LATCH-OPEN  risk.latch_counts_open      per-setup latch counts closed + marked-to-market open R (neveragain_1125 G1-2)
  HS-SCALE    risk.scaled_halt            account no-new-entries halt at closed + open R <= -X,
                                          X = clip(k x sigma, floor x N, cap x N) (hsscale_1125 SCALED-K4)
  SHOCK-V     risk.shock_v                glitch failsafe: closed + open R falls fast -> no new entries + alert (hsscale_1125)
  B8 shadow   risk.netbeta_shadow         net beta-weighted open R per 1% SPY past the budget -> journal tag only
                                          (squeeze_1125 R1-B8)
A flag applies only in the accounts listed in its `accounts:` (default [primary]) AND when it is switched on.
"""

from __future__ import annotations

import json
import math
from collections import deque

import pandas as pd

ACCOUNTS_DEFAULT = ("primary",)


def _accounts(block, default=ACCOUNTS_DEFAULT) -> set[str]:
    acc = (block or {}).get("accounts") if isinstance(block, dict) else None
    return {str(a) for a in (default if acc is None else acc)}


def _on(block, acct: str) -> bool:
    """A dict flag block {enabled: bool, accounts: [...]} is active in `acct`."""
    return isinstance(block, dict) and bool(block.get("enabled", False)) and acct in _accounts(block)


def risk_cfg(cfg: dict) -> dict:
    return (cfg or {}).get("risk") or {}


def cost_basis(cfg: dict) -> bool:
    """True when the account's loss stops count R after costs (account.loss_stops_cost_r_accounts), i.e. realized R is
    on the same basis as the open marks (always R after costs). LATCH-OPEN / HS-SCALE / SHOCK-V add the two, so they run
    only in such accounts; elsewhere they stay off with a warning (mixed raw + cost R would be wrong)."""
    acct = str((cfg or {}).get("account_name", "primary"))
    return acct in {str(a) for a in (((cfg or {}).get("account") or {}).get("loss_stops_cost_r_accounts") or [])}


def gate_cost_basis(cfg: dict, name: str, on: bool) -> tuple[bool, str | None]:
    """(active, why-not) for a switch that adds realized + open R: refused (warning printed) outside cost-R accounts."""
    if on and not cost_basis(cfg):
        why = (f"{name} switched on but account {(cfg or {}).get('account_name', 'primary')!r} is not in "
               f"account.loss_stops_cost_r_accounts (realized R raw, open marks R after costs): kept OFF")
        print(f"WARNING: {why}")
        return False, why
    return on, None


def latch_open_on(cfg: dict) -> bool:
    rk = risk_cfg(cfg)
    acct = str((cfg or {}).get("account_name", "primary"))
    acc = rk.get("latch_counts_open_accounts")
    return bool(rk.get("latch_counts_open", False)) and acct in {str(a) for a in (ACCOUNTS_DEFAULT if acc is None else acc)}


def latch_open_r(cfg: dict) -> float | None:
    v = risk_cfg(cfg).get("latch_open_r")
    return abs(float(v)) if v else None              # 3 and -3 both mean "at -3R"


# ------------------------------------------------------------------------------------------------ HS-SCALE
class ScaledHalt:
    """SCALED-K4 level X = clip(k x sigma, floor x N, cap x N) in R. sigma = std of the lineup's simulated daily CLOSED R over
    the trailing 250 sessions (min 120), recomputed every Friday and at any lineup change (hsscale_1125). Live cannot
    simulate the lineup, so sigma is supplied in config (`sigma_r`, computed by the research run). Missing / invalid
    sigma -> X = cap x N (where the scaled rule sits most weeks) and the status says so. N = setups trading live in the
    account (runner sets it). N unknown (0) -> inactive."""

    def __init__(self, block: dict | None, acct: str):
        b = block or {}
        self.enabled = _on(b, acct)
        self.k = float(b.get("k", 4))
        self.floor = float(b.get("floor_per_setup", 2.5))
        self.cap = float(b.get("cap_per_setup", 8))
        s = b.get("sigma_r")
        try:
            s = float(s) if s is not None else None
        except (TypeError, ValueError):
            s = None
        self.sigma = s if s is not None and math.isfinite(s) and s > 0 else None
        self.n = int(b.get("n_setups") or 0)          # runner overrides with the live lineup size

    def level(self) -> tuple[float | None, str]:
        if self.n <= 0:
            return None, "no setups (N=0)"
        lo, hi = self.floor * self.n, self.cap * self.n
        if self.sigma is None:
            return hi, "sigma missing: cap x N"
        return min(max(self.k * self.sigma, lo), hi), "k x sigma clipped"

    def status(self) -> dict:
        x, src = self.level()
        return {"enabled": self.enabled, "k": self.k, "sigma_r": self.sigma, "n_setups": self.n,
                "x_r": None if x is None else round(x, 3), "x_source": src}


# ------------------------------------------------------------------------------------------------ SHOCK-V
class ShockV:
    """SHOCK-V (hsscale_1125 Layer 1): V1 = account closed + open R falls >= max(v1_floor, v1_frac x X) within v1_min
    minutes; V2 = falls >= max(v2_floor, v2_frac x X) within v2_min minutes. A fall = the highest sample in the window
    minus the current one. Fires when V1 or V2 holds on `confirm_polls` consecutive polls. Action (runner): no new entries
    for the session + alert. Never a flatten. X = the HS-SCALE level when that is known, else 0 (floors only: the more
    sensitive side)."""

    def __init__(self, block: dict | None, acct: str):
        b = block or {}
        self.enabled = _on(b, acct)
        self.v1_min, self.v1_floor, self.v1_frac = float(b.get("v1_min", 2)), float(b.get("v1_floor_r", 8)), float(b.get("v1_frac_x", 0.5))
        self.v2_min, self.v2_floor, self.v2_frac = float(b.get("v2_min", 10)), float(b.get("v2_floor_r", 12)), float(b.get("v2_frac_x", 0.75))
        self.confirm = max(1, int(b.get("confirm_polls", 2)))
        self.hist: deque = deque()
        self.streak = 0
        self.fired: dict | None = None
        self.last: dict | None = None
        self.skipped = 0

    def thresholds(self, x: float | None) -> tuple[float, float]:
        x = float(x) if x is not None and math.isfinite(float(x)) else 0.0
        return max(self.v1_floor, self.v1_frac * x), max(self.v2_floor, self.v2_frac * x)

    def update(self, now, value: float | None, x: float | None = None) -> dict | None:
        """Add one poll's account closed + open R. Returns the fire record the first time it fires (else None).
        value None / non-finite (marks failed, stale data) -> sample skipped, streak kept."""
        if value is None or not math.isfinite(float(value)):
            self.skipped += 1
            return None
        now = pd.Timestamp(now)
        v = float(value)
        self.hist.append((now, v))
        keep = pd.Timedelta(minutes=max(self.v1_min, self.v2_min))
        while self.hist and self.hist[0][0] < now - keep:
            self.hist.popleft()
        t1, t2 = self.thresholds(x)
        d1 = max(h for t, h in self.hist if t >= now - pd.Timedelta(minutes=self.v1_min)) - v
        d2 = max(h for t, h in self.hist if t >= now - pd.Timedelta(minutes=self.v2_min)) - v
        hit = d1 >= t1 or d2 >= t2
        self.streak = self.streak + 1 if hit else 0
        self.last = {"at": str(now), "r": round(v, 3), "drop_v1": round(d1, 3), "drop_v2": round(d2, 3),
                     "thr_v1": round(t1, 3), "thr_v2": round(t2, 3), "streak": self.streak}
        if self.fired is None and self.streak >= self.confirm:
            self.fired = {**self.last, "rule": "V1" if d1 >= t1 else "V2"}
            return self.fired
        return None

    def status(self) -> dict:
        return {"enabled": self.enabled, "fired": self.fired, "last": self.last, "skipped_samples": self.skipped}


# ------------------------------------------------------------------------------------------------ B8 shadow
def shrunk_beta(stock_closes: pd.Series, spy_closes: pd.Series, n: int = 60, min_obs: int = 20) -> float:
    """squeeze_1125 PREREG beta: daily-return beta to SPY over the prior `n` sessions (>= min_obs, else 1.0), shrunk
    0.67 x b + 0.33, clipped to [-3, 3]. Pass closes strictly before the trade date (point in time)."""
    try:
        r = pd.concat([stock_closes.pct_change(), spy_closes.pct_change()], axis=1).dropna().tail(n)
        if len(r) < min_obs:
            return 1.0
        var = float(r.iloc[:, 1].var())
        if not var > 0:
            return 1.0
        b = float(r.iloc[:, 0].cov(r.iloc[:, 1])) / var
        return float(min(max(0.67 * b + 0.33, -3.0), 3.0)) if math.isfinite(b) else 1.0
    except Exception:
        return 1.0


def load_betas(path: str | None) -> tuple[dict[str, float], str]:
    """symbol -> beta from a JSON file {symbol: beta} written before the open (values as shrunk_beta gives them; clipped
    again to [-3, 3]). Missing / unreadable file -> {} and every lot uses beta 1.0 (the PREREG default)."""
    if not path:
        return {}, "none: beta 1.0 for every lot"
    try:
        with open(path) as f:
            raw = json.load(f)
        out = {}
        for k, v in (raw or {}).items():
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if math.isfinite(v):
                out[str(k)] = min(max(v, -3.0), 3.0)
        return out, f"file {path} ({len(out)} symbols; others 1.0)"
    except Exception as e:
        return {}, f"file {path} unreadable ({type(e).__name__}): beta 1.0 for every lot"


class NetBetaShadow:
    """B8 (squeeze_1125 R1): each open lot carries b_i = side x beta x 0.01 x entry / risk_per_share x share still held
    (R per +1% SPY); NB = sum over the account's open lots. A new SHORT would be blocked while NB <= -B, a new LONG while
    NB >= +B. SHADOW ONLY: the runner tags the journaled entry (info.netbeta_shadow) and counts it; it never blocks."""

    def __init__(self, block: dict | None, acct: str):
        b = block or {}
        self.enabled = _on(b, acct)
        self.budget = float(b.get("budget_r_per_pct", 8))
        self.betas, self.source = load_betas(b.get("betas_path")) if self.enabled else ({}, "off")
        self.evaluated = self.would_block = 0
        self.by_setup: dict[str, int] = {}
        self.last: dict | None = None

    def beta(self, sym: str) -> float:
        return float(self.betas.get(sym, 1.0))

    def net(self, lots) -> tuple[float, int]:
        """lots: iterable of (symbol, side, entry, stop, frac). Lots without a usable entry/stop are skipped (count)."""
        nb, skipped = 0.0, 0
        for sym, side, entry, stop, frac in lots:
            try:
                rps = abs(float(entry) - float(stop))
                if not rps > 0 or not math.isfinite(rps):
                    skipped += 1
                    continue
                nb += int(side) * self.beta(sym) * 0.01 * float(entry) / rps * float(frac)
            except (TypeError, ValueError):
                skipped += 1
        return nb, skipped

    def judge(self, side: int, nb: float) -> bool:
        return (side == -1 and nb <= -self.budget) or (side == 1 and nb >= self.budget)

    def status(self) -> dict:
        return {"enabled": self.enabled, "budget_r_per_pct": self.budget, "beta_source": self.source,
                "evaluated": self.evaluated, "would_block": self.would_block, "would_block_by_setup": dict(self.by_setup),
                "last": self.last}
