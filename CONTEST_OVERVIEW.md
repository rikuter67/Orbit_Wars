# Orbit Wars コンペ概要

## 1. 競技ルール（要点）

- 盤面は 100x100。
- 惑星を奪うことで所有権と艦隊を制するゲーム。
- 各ターン、各自の惑星は生産量 `production` 分の船を追加する。
- コミットした行動（1手）:
  - `[from_planet_id, angle_in_radians, num_ships]`
- 勝敗はゲーム終了時の「自陣惑星上の艦隊数 + 行動中の艦隊数」で決まる。

## 2. 主要なゲーム特性

- 中央付近の惑星は毎ターン回転する。
- 太陽に入った艦隊は消滅する。
- 彗星は一時的な惑星として出現し、時間経過で消える。
- 艦隊速度は船数に依存し、最大で大きい方が速い（1隻で1ターン、上限は約6）。

## 3. 評価時の2Pと4P差

- 2P（2人戦）: 相手を早めに詰める価値が高く、攻めの判断が効きやすい。
- 4P（4人戦）: 無理な突進は消耗で `top2` を崩しやすい。
- そのため、実運用では「2Pを伸ばしつつ4Pの上位維持」を重視する。

## 4. 入力観測（`obs`）の主な要素

- `player`: 自分プレイヤーID（0-3）
- `planets`: 惑星リスト
  - `[id, owner, x, y, radius, ships, production]`
- `fleets`: 移動中艦隊リスト
  - `[id, owner, x, y, angle, from_planet_id, ships]`
- `angular_velocity`: 内側惑星の回転速度
- `initial_planets`, `comet_planet_ids`: 盤面初期/彗星情報

## 5. このリポジトリでの使い分け

- `README.md`: 再現手順、提出判断、運用ルール（最短で使えるガイド）
- `CONTEST_OVERVIEW.md`: コンペ仕様とゲームの前提整理（今回追加）
- `SUBMISSION_LOG.md`: 提出履歴と根拠
- `scripts/*`, `candidate_builds/*`, `submissions/*`, `logs/*`: 実験・再現・提出・証跡

## 6. ここを読む順番（短縮版）

1. `CONTEST_OVERVIEW.md`（何のゲームかの理解）
2. `README.md`（現実運用）
3. 実行ログ/提出ログ（`logs/`, `SUBMISSION_LOG.md`）
