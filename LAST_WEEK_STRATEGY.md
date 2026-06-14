# Orbit Wars Last Week Strategy

Timestamp: 2026-06-14 01:05 JST

## Current Decision

Do not submit a new experimental variant before the 08:30 target.

The safest validated 08:30 plan is to keep the latest two submissions as Producer-family rows. The current automation does this with guarded Producer refreshes at 02:00, 05:05, and 08:25 JST, with audits around each action. The guard refuses to submit if the latest row is too recent or either latest-two row is pending.

## Evidence

- Latest live safety row: `slawek_producer_v2_20260613.tar.gz`, ref `53634763`, score `1191.2` at the 01:01 snapshot.
- Reyhan `20勝0敗` was submitted as requested: ref `53640054`, description includes `20勝0敗`, but current score is only `1042.1`.
- The old `exp48_2p_regroup_4p_original.tar.gz` row reached `1329.7` historically, but its later restore submission scored only `937.9`, so it is not reliable enough to anchor current latest-two strategy.
- `producer_ffa_guard` was initially promising, but additional validation reversed it:
  - 2P extra check: `3-5` vs Producer.
  - 4P extra check: same top2 as Producer but wins `6/24` vs Producer `12/24`.
- The 2026-06-14 Producer-neighborhood grid did not find a submit-worthy replacement:
  - `h18_roi13_beta18`: combined 2P `6-6` vs Producer across seeds 40-45.
  - `h16_roi14_beta20`: combined 2P `6-6` vs Producer across seeds 40-45.
  - 4P same-seed check: both variants top2 `12/12`, wins `5/12`; Producer top2 `12/12`, wins `6/12`.

## Final-Week Direction

Primary direction: Producer V2 as the base, unchanged Producer 4P, and a gated 2P-only aggression branch.

The only local signal that still looks useful is lower ROI / lower reinforcement-beta aggression in 2P. It improves or holds up against several public baselines, but it has not beaten Producer itself. This should be explored as a conditional branch, not as a full replacement.

Team-shared operating policy as of 2026-06-14:

- Treat `slawekbiel/the-producer-v2` as the stable baseline. Its live rows have converged around the high-1100s, while many local/public hybrids looked good briefly and then collapsed.
- Understand Producer first, then make many small Producer-family changes rather than large rewrites.
- Filter variants locally, but submit to Live one at a time and observe convergence before the next move.
- Optimize 2P and 4P separately: 2P can justify controlled aggression; 4P should preserve Producer's cautious top2 consistency.
- Because nearby ranks likely contain similar public-code families, direct improvement must include beating Producer/self-like agents, not only older public baselines.

## Work Order

1. Preserve latest-two safety with Producer refreshes.
2. Build 2P-only routed variants that leave 4P exactly equal to Producer.
3. Run larger 2P validation against Producer, Kuni, oldv2, Reyhan, and the public candidate pool.
4. Add map-feature routing only if one variant wins on a clear subset of maps and does not degrade the rest.
5. Submit only if the candidate beats Producer directly by a meaningful margin and keeps 4P top2/win metrics at least equal.

## Submission Gate

A new candidate should not be submitted unless it satisfies all of:

- Latest-two safety row is Producer and complete.
- No pending submissions.
- At least 3 hours since the previous submit.
- 2P direct vs Producer wins by a clear margin on a broader seed set.
- 4P top2 is not below Producer and win count is not meaningfully worse.
- Submission comment includes the exact local evidence summary.
