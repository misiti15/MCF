"""Merge existing_results.csv (task 1) and rv_results.csv (task 2) into results.csv. Educational only - not financial advice."""
import pandas as pd

from common import HERE

r = pd.concat([pd.read_csv(HERE / "existing_results.csv"), pd.read_csv(HERE / "rv_results.csv")], ignore_index=True)
r.to_csv(HERE / "results.csv", index=False)
(HERE / "existing_results.csv").unlink()
(HERE / "rv_results.csv").unlink()
print(len(r))
