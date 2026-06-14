# Orbit Wars Checkpoint: Producer 1211.3

Timestamp: 2026-06-14 JST

This checkpoint preserves the live Producer V2 state that had converged to
`1211.3` before the post-reset refresh.

## Live State

- Stable completed row: `53645538`
- File: `slawek_producer_v2_20260613.tar.gz`
- Comment: `cautious latest2 producer_v2 safety refresh 20260614`
- Public score at snapshot `logs/snapshot_20260614_124418_status.md`: `1211.3`
- Rank at that snapshot: `300/4424` (`6.78%`)
- Top 2% cut at that snapshot: `1288.1`

At `12:44 JST`, another Producer refresh was submitted after the UTC daily
submission reset:

- New row: `53658218`
- Status in `logs/snapshot_20260614_124449_status.md`: `PENDING`
- Latest two rows after this submit: Producer pending + Producer complete

## Included Files

- `submissions/slawek_producer_v2_20260613.tar.gz`
  - SHA256: `c12baa59adf2d980cab0e432666526592155f15ada0ba1b947782aedf0f89bca`
- `producer_live_source/`
  - Extracted Producer V2 source used for local understanding and variants.
- `scripts/`
  - Guarded submit, snapshot, audit, and local eval helpers.
- `logs/snapshot_20260614_124418_status.md`
  - Authoritative 1211.3 status snapshot.
- `logs/snapshot_20260614_124449_status.md`
  - Snapshot immediately after the post-reset Producer refresh submit.
- `LAST_WEEK_STRATEGY.md`, `RESEARCH_NOTES.md`, `ORBIT_WARS_GLOSSARY.md`,
  `SUBMISSION_LOG.md`
  - Strategy, research notes, glossary, and chronological evidence.

## Next Research Direction

The next branch of work should target Producer-like opponents directly:

- Model that many opponents are Producer clones or close variants.
- Predict Producer's shortlists, safe-drain attack sizes, and regroup destinations.
- Exploit the blind spot that Producer scores our single launch while projecting
  opponents as mostly do-nothing, then patches that with a coarse reinforcement
  margin.
- Test counter-Producer variants locally against `producer_live_source` before
  any live submission.
