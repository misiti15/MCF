"""MarcoFlow's original heat score at its ±30 alert level (baseline for comparison)."""
LONG_AT, SHORT_AT = 30.0, -30.0


def score(df):
    return df["heat"].to_numpy()
