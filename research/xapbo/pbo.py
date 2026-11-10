"""XA-PBO (guild Builder, Lead lead-20261110-0300-3): probability of backtest overfitting by combinatorially symmetric
cross-validation (CSCV; Bailey, Borwein, Lopez de Prado & Zhu, 2014), our own implementation.

Input: a T x N matrix of per-day P&L (rows = sessions in time order, columns = the configs a study tried).
  1. Split the rows into S contiguous blocks of equal size (S even; leftover rows dropped from the end).
  2. For each of the C(S, S/2) ways to pick S/2 blocks as in-sample (IS), the rest out-of-sample (OOS):
     - n* = the config with the best IS metric (mean daily P&L, or Sharpe = mean / sd);
     - w = relative OOS rank of n* among the N configs, in (0, 1); logit lambda = ln(w / (1 - w)).
  3. PBO = share of splits with lambda <= 0 (the IS winner lands at or below the OOS median).
  Also: degradation = OLS slope of OOS metric on IS metric for the chosen configs (< 0 = IS winners decay), and
  p_oos_loss = share of splits where the chosen config's OOS mean is < 0.
Noise check (selftest): mean PBO over noise draws ~0.5 but sd ~0.24 per draw - a single study's PBO is itself noisy.
Reading: PBO ~ 0.5 = picking the best config is no better than picking at random (overfit selection); PBO near 0 = the
IS winner usually stays above the OOS median. PBO says nothing about whether ANY config is profitable: report it next
to BAR90 / avg R, never instead of them.
    python pbo.py --selftest
    python pbo.py <trades file> <config col> <date col> <value col> [S] [metric]   (sums value per date x config; days
                                                                                   with no trade count as 0)
Educational only - not financial advice."""
import itertools, sys
import numpy as np, pandas as pd


def _metric(X, kind):
    mu = X.mean(axis=0)
    if kind == "mean": return mu
    sd = X.std(axis=0, ddof=1)
    return np.where(sd > 0, mu / np.where(sd > 0, sd, 1), 0.0)


def pbo(M, S=16, metric="sharpe", max_splits=None, seed=0):
    M = np.asarray(M, float)
    T, N = M.shape
    assert S % 2 == 0 and S >= 4 and N >= 2, "S even >= 4, N >= 2"
    L = T // S; assert L >= 2, "too few rows for S blocks"
    blocks = [np.arange(i * L, (i + 1) * L) for i in range(S)]
    combos = list(itertools.combinations(range(S), S // 2))
    if max_splits and len(combos) > max_splits:
        rng = np.random.default_rng(seed); combos = [combos[i] for i in rng.choice(len(combos), max_splits, replace=False)]
    lam, isv, oosv, oosmean = [], [], [], []
    for c in combos:
        is_ = np.concatenate([blocks[i] for i in c]); oos = np.concatenate([blocks[i] for i in range(S) if i not in c])
        mi, mo = _metric(M[is_], metric), _metric(M[oos], metric)
        n = int(np.argmax(mi))
        rank = (mo < mo[n]).sum() + 0.5 * ((mo == mo[n]).sum() - 1) + 1     # 1..N, ties averaged
        w = rank / (N + 1)
        lam.append(np.log(w / (1 - w))); isv.append(mi[n]); oosv.append(mo[n]); oosmean.append(M[oos, n].mean())
    lam, isv, oosv = np.array(lam), np.array(isv), np.array(oosv)
    slope = float(np.polyfit(isv, oosv, 1)[0]) if np.ptp(isv) > 0 else float("nan")
    return dict(pbo=round(float((lam <= 0).mean()), 3), splits=len(lam), S=S, N=N, T_used=S * L, metric=metric,
                median_logit=round(float(np.median(lam)), 3), degradation_slope=round(slope, 3),
                p_oos_loss=round(float((np.array(oosmean) < 0).mean()), 3))


def matrix(df, cfg, date, val):
    return df.pivot_table(index=date, columns=cfg, values=val, aggfunc="sum").sort_index().fillna(0.0)


def selftest():
    rng = np.random.default_rng(1)
    v0 = [pbo(rng.normal(0, 1, (480, 20)), 10, "sharpe")["pbo"] for _ in range(20)]
    v1 = []
    for _ in range(10):
        m = rng.normal(0, 1, (480, 20)); m[:, 3] += 0.35; v1.append(pbo(m, 10, "sharpe")["pbo"])
    assert 0.40 <= np.mean(v0) <= 0.60, v0
    assert np.mean(v1) <= 0.05, v1
    print(f"selftest ok: pure noise mean PBO {np.mean(v0):.3f} over 20 draws (sd {np.std(v0):.3f}: ONE study's PBO is noisy), "
          f"one real edge mean PBO {np.mean(v1):.3f}")


if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest(); sys.exit()
    f, cfg, date, val = sys.argv[1:5]; S = int(sys.argv[5]) if len(sys.argv) > 5 else 16
    kind = sys.argv[6] if len(sys.argv) > 6 else "sharpe"
    df = pd.read_parquet(f) if f.endswith(".parquet") else pd.read_csv(f)
    M = matrix(df, cfg, date, val)
    print(f"{f}: {M.shape[0]} days x {M.shape[1]} configs {list(M.columns)}")
    print(pbo(M.to_numpy(), S, kind))
    print("Educational only - not financial advice.")
