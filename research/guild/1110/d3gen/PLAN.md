# D3GEN — does a stricter screen rank the live GEN setups? (Builder, frozen 2026-11-10 ~09:00 ET, before any score)

*Educational only — not financial advice.* Observer D3 / Lead lead-20261110-0700-2 (P2). 0 configs (a ranking test).
- Setups: every GEN-* setup in config/account_gen.yaml with a 2-year lab list (bt_lab1104 for t* geoms, bt_hold lists for
  hold/holdtr) AND >= 10 live paper trades (mcf-data-gen journal, run_id 1; R = pnl_adj / (|entry - stop| x shares)).
- **No leak:** each setup is re-screened only on lab trades dated BEFORE its own generation date (gen.date).
- Old score = the yaml `gen.screen.score` (also reported: screen valid exp_r).
- New scores (pre-declared): **S1 = worst calendar-quarter mean R** (primary); S2 = share of quarters with mean R > 0;
  S3 = all-folds-positive flag. Quarters with < 20 trades skipped. Locked block absent.
- Test: Spearman rank correlation with live avg R (and live avg R w/o best day), old vs new; the stricter screen 'wins'
  only if S1's Spearman > the old score's AND > 0 with a one-sided permutation p <= 0.10 (1,000 shuffles).
- Also: XA-PBO over the setups' pre-gen daily lab P&L (selection informativeness), p_oos_loss.
- If S1 does not rank live better, the honest reading for the owner: no screen we have ranks GEN, so GEN's live slots buy
  data, not candidates (owner's call).
