"""Hunch learners. Owner design (2026-11-04): Hunch is ONE combined learner that uses ALL the indicators at once to
guess the active metric of the next 3-min bar; it runs as ~20 instances in parallel on ~20 tickers, plus a pooled model
that learns across all tickers together so data builds faster on the one metric.

Protocol (enforced by mcf.hunch.replay.run): at step k (one 3-min bar close, all tickers at once) every learner first
`update`s on step k-1's features and answers (bar k-1's answer resolves at bar k's close), then `predict`s step k.
No learner ever sees an answer before it is known.

Combined learners (the headline)
  LogReg      pooled online logistic regression (minibatch SGD, L2) on all features, z-scored with a running
              past-only scaler, time-of-day bucket dummies and a ticker one-hot (per-ticker intercept); shared weights
  GBT         pooled light boosted trees: depth-2 histogram trees on quantile bins of all features, logistic loss, refit
              at the start of every REFIT_SESS-th session on the previous WINDOW_SESS sessions of scored guesses only
              (walk-forward; frozen between refits - "online" at a 20-session cadence, which keeps it light)
  PerTicker   one LogReg per ticker (the "20 Hunch instances"), own scaler and weights, own ticker's guesses only
  top-k       a pooled LogReg fed only the k features ranked highest by TRAIN permutation importance (replay.py)
Diagnostic only
  Binned      one learner per indicator (bin the indicator, decayed yes/no counts per bin, guess the bin's majority);
              a small side table, not the approach
Educational only - not financial advice.
"""
from __future__ import annotations

import numpy as np

BINS = 10
HALF_SESS = 20
REFIT_SESS = 20
WINDOW_SESS = 120
STEPS_PER_SESS = 121


def tod_dummies(tod: np.ndarray) -> np.ndarray:
    """Time-of-day buckets by bar close (minutes from 09:30): <=60 (to 10:30), <=150 (12:00), <=270 (14:00),
    <=330 (15:00), later."""
    cuts = np.array([60, 150, 270, 330])
    k = np.searchsorted(cuts, tod, side="left")
    out = np.zeros((len(tod), 5))
    ok = np.isfinite(tod)
    out[np.arange(len(tod))[ok], k[ok]] = 1.0
    return out


class Scaler:
    """Running (past-only) mean / variance per column, NaN-aware, batch update (Chan et al.)."""

    def __init__(self, shape):
        self.n = np.zeros(shape)
        self.mu = np.zeros(shape)
        self.m2 = np.zeros(shape)

    def z(self, X, mu=None, m2=None, n=None):
        mu = self.mu if mu is None else mu
        m2 = self.m2 if m2 is None else m2
        n = self.n if n is None else n
        sd = np.sqrt(m2 / np.maximum(n - 1, 1.0))
        sd = np.where(sd > 0, sd, 1.0)
        return np.nan_to_num(np.clip((X - mu) / sd, -5, 5), nan=0.0)

    def update(self, X):
        ok = np.isfinite(X)
        nb = ok.sum(0)
        xs = np.where(ok, X, 0.0)
        mb = xs.sum(0) / np.maximum(nb, 1)
        vb = (np.where(ok, X - mb, 0.0) ** 2).sum(0)
        na = self.n
        tot = na + nb
        delta = mb - self.mu
        frac = np.where(tot > 0, nb / np.maximum(tot, 1), 0.0)
        self.mu = self.mu + delta * frac
        self.m2 = self.m2 + vb + np.where(tot > 0, delta ** 2 * na * nb / np.maximum(tot, 1), 0.0)
        self.n = tot


class LogReg:
    """Pooled online logistic regression: one weight vector shared by every ticker. Features are already
    ATR / % normalised; `n_groups` > 0 adds a ticker one-hot (a per-ticker intercept)."""
    name = "logreg"

    def __init__(self, n_feat: int, tod_col: int, n_groups: int = 0, lr: float = 0.02, l2: float = 1e-4):
        self.tod_col, self.G = tod_col, n_groups
        self.sc = Scaler(n_feat)
        self.w = np.zeros(n_feat + 5 + 1)
        self.wg = np.zeros(max(n_groups, 1))  # per-ticker intercepts (the ticker one-hot, stored sparse)
        self.lr, self.l2 = lr, l2
        self.rows = 0

    def _design(self, X):
        return np.hstack([self.sc.z(X), tod_dummies(X[:, self.tod_col]), np.ones((len(X), 1))])

    def _raw(self, D, g):
        r = D @ self.w
        if self.G and g is not None:
            r = r + self.wg[g]
        return r

    def proba(self, X, g=None):
        if self.rows < 2:
            return np.full(len(X), 0.5)
        return 1.0 / (1.0 + np.exp(-self._raw(self._design(X), g)))

    def predict(self, X, g=None):
        return self.proba(X, g) > 0.5

    def update(self, X, y, g=None):
        if not len(X):
            return
        if self.rows >= 2:  # gradient with the scaler as it was at guess time
            D = self._design(X)
            e = 1.0 / (1.0 + np.exp(-self._raw(D, g))) - y
            self.w -= self.lr * (D.T @ e / len(y) + self.l2 * self.w)
            if self.G and g is not None:
                self.wg -= self.lr * (np.bincount(g, weights=e, minlength=self.G) / len(y) + self.l2 * self.wg)
        self.sc.update(X)
        self.rows += len(X)

    def snapshot(self) -> dict:
        return {"w": self.w.copy(), "wg": self.wg.copy(), "mu": self.sc.mu.copy(), "m2": self.sc.m2.copy(),
                "n": self.sc.n.copy(), "rows": self.rows}

    @classmethod
    def from_snapshot(cls, snap: dict, n_feat: int, tod_col: int, n_groups: int = 0) -> "LogReg":
        m = cls(n_feat, tod_col, n_groups)
        m.w = snap["w"].copy()
        m.wg = snap["wg"].copy()
        m.sc.mu, m.sc.m2, m.sc.n = snap["mu"].copy(), snap["m2"].copy(), snap["n"].copy()
        m.rows = snap["rows"]
        return m


class PerTicker:
    """One online logistic regression per ticker (the "20 Hunch instances"), each with its own scaler and weights,
    updated on its own ticker's scored guesses only. Vectorised over tickers: W (S, d)."""
    name = "ticker"

    def __init__(self, n_sym: int, n_feat: int, tod_col: int, lr: float = 0.002, l2: float = 1e-4):
        self.S, self.F, self.tod_col = n_sym, n_feat, tod_col
        self.n = np.zeros((n_sym, n_feat))
        self.mu = np.zeros((n_sym, n_feat))
        self.m2 = np.zeros((n_sym, n_feat))
        self.W = np.zeros((n_sym, n_feat + 6))
        self.rows = np.zeros(n_sym)
        self.lr, self.l2 = lr, l2

    def _design(self, X, idx):
        sd = np.sqrt(self.m2[idx] / np.maximum(self.n[idx] - 1, 1.0))
        sd = np.where(sd > 0, sd, 1.0)
        z = np.nan_to_num(np.clip((X - self.mu[idx]) / sd, -5, 5), nan=0.0)
        return np.hstack([z, tod_dummies(X[:, self.tod_col]), np.ones((len(X), 1))])

    def proba(self, X, idx):
        p = 1.0 / (1.0 + np.exp(-(self._design(X, idx) * self.W[idx]).sum(1)))
        return np.where(self.rows[idx] >= 2, p, 0.5)

    def predict(self, X, idx):
        return self.proba(X, idx) > 0.5

    def update(self, X, y, idx):
        """X: (n, F) with one row per ticker in idx (distinct)."""
        if not len(X):
            return
        D = self._design(X, idx)
        p = 1.0 / (1.0 + np.exp(-(D * self.W[idx]).sum(1)))
        live = (self.rows[idx] >= 2)[:, None]
        self.W[idx] -= live * self.lr * ((p - y)[:, None] * D + self.l2 * self.W[idx])
        ok = np.isfinite(X)
        n = self.n[idx] + ok
        delta = np.where(ok, X - self.mu[idx], 0.0)
        mu = self.mu[idx] + np.where(ok, delta / np.maximum(n, 1), 0.0)
        self.m2[idx] += np.where(ok, delta * (np.where(ok, X, 0.0) - mu), 0.0)
        self.mu[idx] = mu
        self.n[idx] = n
        self.rows[idx] += 1


def bin_edges(X: np.ndarray, bins: int = BINS) -> list[np.ndarray]:
    """Quantile edges per column (inner cut points, unique)."""
    out = []
    qs = np.linspace(0, 1, bins + 1)[1:-1]
    for j in range(X.shape[1]):
        col = X[:, j]
        col = col[np.isfinite(col)]
        e = np.unique(np.quantile(col, qs)) if len(col) else np.array([])
        out.append(e)
    return out


def bin_codes(X: np.ndarray, edges: list[np.ndarray], bins: int = BINS) -> np.ndarray:
    """uint8 codes 0..len(edges); NaN -> `bins` (the missing bin)."""
    C = np.empty(X.shape, dtype=np.uint8)
    for j, e in enumerate(edges):
        col = X[..., j]
        c = np.searchsorted(e.astype(col.dtype), col, side="right")
        c = np.where(np.isfinite(col), c, bins)
        C[..., j] = c
    return C


class Binned:
    """All single-indicator learners at once: counts[f, bin]."""

    def __init__(self, n_feat: int, bins: int = BINS, half_steps: float = HALF_SESS * STEPS_PER_SESS):
        self.yes = np.zeros((n_feat, bins + 1))
        self.tot = np.zeros((n_feat, bins + 1))
        self.decay = 0.5 ** (1.0 / half_steps)
        self.F = n_feat
        self._ar = np.arange(n_feat)

    def proba(self, C: np.ndarray) -> np.ndarray:
        """C: (n, F) codes -> (n, F) P(yes)."""
        yes = self.yes[self._ar, C]
        tot = self.tot[self._ar, C]
        return (yes + 1.0) / (tot + 2.0)

    def predict(self, C):
        return self.proba(C) > 0.5

    def update(self, C: np.ndarray, y: np.ndarray):
        self.yes *= self.decay
        self.tot *= self.decay
        if not len(C):
            return
        B = self.yes.shape[1]
        flat = (C.astype(np.int64) + self._ar * B).ravel()
        yy = np.repeat(y[:, None], self.F, axis=1).ravel()
        self.yes += np.bincount(flat, weights=yy, minlength=self.F * B).reshape(self.F, B)
        self.tot += np.bincount(flat, minlength=self.F * B).reshape(self.F, B)


class GBT:
    """Depth-2 histogram boosted trees on bin codes. fit() on past rows only; predict() between refits."""
    name = "gbt"

    def __init__(self, n_feat: int, bins: int = BINS, rounds: int = 60, lr: float = 0.1, lam: float = 50.0,
                 max_rows: int = 200_000, seed: int = 0):
        self.F, self.B = n_feat, bins + 1
        self.rounds, self.lr, self.lam, self.max_rows = rounds, lr, lam, max_rows
        self.trees: list = []
        self.base = 0.0
        self.rng = np.random.default_rng(seed)

    def _best(self, C, g, h, m):
        F, B = self.F, self.B
        flat = (C[m].astype(np.int64) + np.arange(F) * B).ravel()
        G = np.bincount(flat, weights=np.repeat(g[m], F), minlength=F * B).reshape(F, B)
        H = np.bincount(flat, weights=np.repeat(h[m], F), minlength=F * B).reshape(F, B)
        GL, HL = np.cumsum(G, 1)[:, :-1], np.cumsum(H, 1)[:, :-1]
        Gt, Ht = G.sum(1, keepdims=True), H.sum(1, keepdims=True)
        GR, HR = Gt - GL, Ht - HL
        lam = self.lam
        gain = GL ** 2 / (HL + lam) + GR ** 2 / (HR + lam) - Gt ** 2 / (Ht + lam)
        f, t = np.unravel_index(np.argmax(gain), gain.shape)
        return int(f), int(t), float(gain[f, t])

    def fit(self, C: np.ndarray, y: np.ndarray):
        if len(y) > self.max_rows:
            idx = self.rng.choice(len(y), self.max_rows, replace=False)
            C, y = C[idx], y[idx]
        p0 = np.clip(y.mean(), 1e-3, 1 - 1e-3)
        self.base = float(np.log(p0 / (1 - p0)))
        self.trees = []
        raw = np.full(len(y), self.base)
        allm = np.ones(len(y), bool)
        for _ in range(self.rounds):
            p = 1 / (1 + np.exp(-raw))
            g, h = p - y, p * (1 - p)
            f, t, _ = self._best(C, g, h, allm)
            left = C[:, f] <= t
            node = [f, t]
            for side in (left, ~left):
                if side.sum() < 200:
                    v = -g[side].sum() / (h[side].sum() + self.lam) * self.lr
                    node.append((None, None, v, v))
                    continue
                f2, t2, _ = self._best(C, g, h, side)
                l2 = side & (C[:, f2] <= t2)
                r2 = side & ~(C[:, f2] <= t2)
                vl = -g[l2].sum() / (h[l2].sum() + self.lam) * self.lr
                vr = -g[r2].sum() / (h[r2].sum() + self.lam) * self.lr
                node.append((f2, t2, vl, vr))
            self.trees.append(node)
            raw += self._tree_out(node, C)

    @staticmethod
    def _tree_out(node, C):
        f, t, L, R = node
        left = C[:, f] <= t
        out = np.empty(len(C))
        for side, (f2, t2, vl, vr) in ((left, L), (~left, R)):
            if f2 is None:
                out[side] = vl
            else:
                out[side] = np.where(C[side, f2] <= t2, vl, vr)
        return out

    def proba(self, C: np.ndarray) -> np.ndarray:
        if not self.trees:
            return np.full(len(C), 0.5)
        raw = np.full(len(C), self.base)
        for node in self.trees:
            raw += self._tree_out(node, C)
        return 1 / (1 + np.exp(-raw))

    def predict(self, C):
        return self.proba(C) > 0.5
