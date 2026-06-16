# Restore Decision 2026-06-16

## Current State

- Latest experimental submission: `53734299` / `highfast85_producer_gate_20260616.tar.gz`
- Stable baseline submission: `53714957` / `h19_s14t14_2ponly_producer4p_20260614.tar.gz`
- Do not restore or submit anything before `2026-06-16 18:47 JST`.
- Do not submit after `18:47 JST` unless the latest score is converged by script.

## Check Sequence

Run from `/mnt/c/Users/rikuter/kaggle/Orbit_Wars`:

```bash
python3 scripts/snapshot_orbit_status.py
```

Copy the new snapshot into the Git checkout, then run from `/mnt/c/Users/rikuter/kaggle/Orbit_Wars_git`:

```bash
python3 scripts/convergence_report_orbit.py 53734299 --window 5 --max-spread 8 --min-age-points 5
python3 scripts/restore_readiness_orbit.py
```

## Decision Rules

Keep waiting if either script says not ready:

- `convergence_report_orbit.py` prints `NOT_CONVERGED`
- `restore_readiness_orbit.py` prints `restore_readiness=NO`

Restore h19 only if all are true:

- Current time is after `2026-06-16 18:47 JST`
- Latest `highfast85` score has converged
- `highfast85` remains materially below h19
- No stronger offline candidate has cleared h19 plus Producer gates

If restoring, use:

```bash
python3 scripts/cautious_submit_orbit.py h19_safety_restore
```

The submit script itself has safety gates for minimum submit gap, pending latest2 rows, and latest-score convergence. If it aborts, do not bypass it manually.

## Current Interpretation

Local evidence says `highfast85` can be strong on non-Producer baselines, but Producer repair is inconsistent:

- seeds `139,140`: highfast thresholds beat Producer `4-0`
- seeds `141,142`: `highfast85` lost Producer `0-4`
- action-detect variants tied Producer but lost h19 badly

If live converges low, prefer `h19_safety_restore` over another threshold-only highfast submission.
