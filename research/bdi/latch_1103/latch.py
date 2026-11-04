"""latch_1103 core: the per-setup latched daily stop on one setup-day (PLAN.md). Educational only - not financial advice."""
import numpy as np

LEVELS = (1.5, 2.0, 3.0)


def sim_day(r, ent, ext, L):
    """r, ent, ext: trade R, entry HHMM, exit HHMM in entry order. A trade is blocked when realised R of TAKEN trades
    exited at or before its entry is <= -L (latched for the rest of the day). Returns (R with latch, n blocked or
    None, latch HHMM or None)."""
    taken = np.zeros(len(r), bool); tl = None
    for i in range(len(r)):
        if tl is None:
            done = taken[:i] & (ext[:i] <= ent[i])
            if r[:i][done].sum() <= -L + 1e-9:
                tl = int(max(ext[:i][done])) if done.any() else int(ent[i])
        if tl is not None:
            continue
        taken[i] = True
    nb = int((~taken).sum())
    return float(r[taken].sum()), (nb if tl is not None else None), tl


def next_loss_stats(r, ent, ext):
    """Point-in-time pairs for the mechanism categorizer: for each trade j, were the last two trades realised before
    its entry both losses? Returns list of (cond_two_losses, j_lost)."""
    out = []
    for j in range(len(r)):
        done = np.flatnonzero(ext[:j] <= ent[j])
        if len(done) >= 2:
            last2 = done[np.argsort(ext[done], kind="stable")][-2:]
            out.append((bool((r[last2] < 0).all()), bool(r[j] < 0)))
    return out
