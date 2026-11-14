"""ICCSET-2 - empirical-Bayes shrunk ICC per setup and n_eff for verdicts (Lead lead-20261112-0300-1). Descriptive, 0 configs.
Input: iccset_setups.csv (iccset.py). se of ICC(1) (Fisher/Donner approx, k days, k0 ~ trades/day):
  se^2 = 2 (1-r)^2 (1+(k0-1) r)^2 / (k0 (k0-1) (k-1)).
Between-setup variance tau^2 = max(0, var(icc) - mean(se^2)); weight w = tau^2 / (tau^2 + se^2); icc_s = w icc + (1-w) 0.19.
Also: same for setups with 20-39 trades (not in iccset) gets pure prior 0.19 (listed by n_eff only).
    python -I shrink.py <iccset_setups.csv>        Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
D = pd.read_csv(sys.argv[1]); P = 0.19
k0 = D.per_day.clip(lower=1.01); r = D.icc.clip(-0.2, 0.95); k = D.days
D["se"] = np.sqrt(2 * (1 - r) ** 2 * (1 + (k0 - 1) * r) ** 2 / (k0 * (k0 - 1) * (k - 1)))
tau2 = max(0.0, D.icc.var() - (D.se ** 2).mean())
D["w"] = tau2 / (tau2 + D.se ** 2); D["icc_s"] = D.w * D.icc + (1 - D.w) * P
D["n_eff_s"] = D.n / (1 + (D.per_day - 1) * D.icc_s.clip(lower=0))
D["n_eff_ratio"] = D.n_eff_s / D.n
print(f"{len(D)} setups; var(raw ICC) {D.icc.var():.4f}, mean se^2 {(D.se**2).mean():.4f} -> tau^2 {tau2:.4f} (tau {np.sqrt(tau2):.3f}); "
      f"median weight on own ICC {D.w.median():.2f}")
print(f"shrunk ICC quartiles {D.icc_s.quantile([.1,.25,.5,.75,.9]).round(3).to_dict()}; n_eff/n median {D.n_eff_ratio.median():.2f}")
pd.set_option("display.width", 200)
c = ["setup", "n", "days", "per_day", "icc", "se", "icc_s", "n_eff_s"]
print("\nall setups by shrunk ICC (low = record worth more per trade):")
print(D.sort_values("icc_s")[c].round(3).to_string(index=False))
D.to_csv("iccset_shrunk.csv", index=False); print("Educational only - not financial advice.")
