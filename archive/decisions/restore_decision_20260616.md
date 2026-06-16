# 復元判断（2026-06-16）

## 現在の状態

- 最新の実験提出: `53734299` / `highfast85_producer_gate_20260616.tar.gz`
- 安全基準となるベース提出: `53714957` / `h19_s14t14_2ponly_producer4p_20260614.tar.gz`
- `2026-06-16 18:47 JST` までは復元・新規提出を行わない。
- `18:47 JST` 以降も、最新スコアがスクリプトで収束判定を通すまでは提出しない。

`2026-06-16 16:45 JST` 時点の最新観測:

- `highfast85`: `1150.0`
- `h19`: `1241.9`
- `convergence_report_orbit.py`: `NOT_CONVERGED`
- `restore_readiness_orbit.py`: `restore_readiness=NO`
- 備考: 短い窓では spread が `0.0` になることがあるが、点数の経過時間と直近スパン条件は待機ゲートを満たしていない。

## チェック手順

`/mnt/c/Users/rikuter/kaggle/Orbit_Wars` で実行:

```bash
python3 scripts/snapshot_orbit_status.py
```

新しく作成したスナップショットを Git チェックアウト側へコピーし、次を `/mnt/c/Users/rikuter/kaggle/Orbit_Wars_git` から実行:

```bash
python3 scripts/convergence_report_orbit.py 53734299 --window 5 --max-spread 8 --min-age-points 5
python3 scripts/restore_readiness_orbit.py
```

## 判断ルール

`NOT_CONVERGED` または `restore_readiness=NO` が出たら待機継続。

h19 を復元して提出する条件（すべて満たすこと）:

- 現在時刻が `2026-06-16 18:47 JST` を過ぎている
- 最新 `highfast85` のスコアが収束している
- `highfast85` が h19 より十分劣っている
- h19 と Producer の両方のゲートをクリアするオフライン候補がまだない

復元提出する場合:

```bash
python3 scripts/cautious_submit_orbit.py h19_safety_restore
```

提出スクリプトは、最小間隔、latest2 pending、最新スコア収束のガードを持っている。失敗したときは手動で回避しないこと。

## 現在の解釈

ローカル証拠は `highfast85` が非Producer基盤では強い場面がある一方、Producer相手の修復は不安定であることを示す。

- seed `139,140`: highfast 閾値版は Producer に `4-0`
- seed `141,142`: `highfast85` は Producer に `0-4`
- action-detect 系は Producer と互角だったが、h19 には悪影響。

live 側が低いまま収束するなら、閾値だけ変えた highfast の追加提出より `h19_safety_restore` を優先する。
