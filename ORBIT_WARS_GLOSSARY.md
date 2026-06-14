# Orbit Wars Glossary

Timestamp: 2026-06-14 JST

## Leaderboard Terms

- `top2 cut`: the public leaderboard score at the top 2% boundary. If there are 4400 teams, this is roughly the score at rank 88. It is used as an approximate gold-range target, not an official medal guarantee.
- `latest2`: working hypothesis that the latest two submissions are the ones continuing to receive arena matches. This is why we avoid replacing both latest rows with unproven experiments.
- `active/team display score`: the score shown for the team on the downloaded public leaderboard. It can lag or differ from individual submission rows during live evaluation.

## Local Agent Names

These names are local labels used in evaluation scripts, not official Kaggle team names.

- `Producer`: local name for the strong public Producer V2 family from `slawekbiel/the-producer-v2`. Current main archive: `submissions/slawek_producer_v2_20260613.tar.gz`.
- `Kuni`: local baseline extracted/archived as `submissions/kuni_lb1240_clean.tar.gz`.
- `oldv2`: local name for the older `exp48_2p_regroup_4p_original` family. One historical row reached `1329.7`, but a later restore scored only `937.9`, so it is not treated as reliable current strategy.
- `Reyhan`: local/public candidate archived as `submissions/reyhan_selfcheck20_0_20260613.tar.gz`; submitted with `20勝0敗` in the comment, but live score has been weak.
- `h18_2ponly`: local Producer variant that changes only the 2P parameters and keeps 4P equivalent to Producer. It was archived for reproducibility but is not scheduled because validation was unstable.

## Current Strategic Meaning

Producer V2 is the safety baseline. New candidates must beat Producer itself locally and preserve 4P top2 stability before we risk a live submission.
