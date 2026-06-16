# Orbit Wars 再現ガイド

このガイドは、現在運用している提出版を再現するための最短手順と、実験ログの残し方をまとめています。

---

## 1) まず押さえる前提

- 本ガイドの対象は `highfast85` 系の運用版です。
- 変更は「小さく積む」「ローカル検証」「収束確認」の順で進めます。
- 再現は常に同じ順番で、同じファイルを読めば同じ判断に到達できるようにします。

必要に応じて読む順序は固定です。
- 現状把握: `LOG.md`
- 過去判断の根拠: `SUBMISSION_LOG.md`
- 実験ログとスナップショット: `logs/`

---

## 2) リポジトリ構成（再現に必要な意味）

```text
Orbit_Wars_git/
  README.md                  ← この説明
  LOG.md                     ← 現在運用版の要約
  SUBMISSION_LOG.md          ← 提出理由・履歴・判定理由
  LAST_WEEK_STRATEGY.md      ← 最終運用ルール
  RESTORE_DECISION_20260616.md
  ORBIT_WARS_GLOSSARY.md
  RESEARCH_NOTES.md
  CHECKPOINT_PRODUCER_1211_3.md
  MANUAL_RESTORE_STEPS.md
  archive/
    decisions/
      restore_decision_20260616.md   ← 過去の復元判断メモ（必要時）

  scripts/                  ← 再現・検証・提出・監査の実行スクリプト
  candidate_builds/         ← 候補版のソース
  logs/                     ← ローカル評価結果とライブ収束ログ
  experiments/              ← 試作メモ（必要時）
  submissions/              ← Kaggle提出用tar
  producer_live_source/      ← 参照用公開版の取り込み
```

### scripts/

- `snapshot_orbit_status.py`  
  Kaggle提出状況を取得して、最新2行の状態、保留、順位/カットを `logs/snapshot_*.md` に保存。
- `cautious_submit_orbit.py`  
  提出前に安全条件（時間間隔・収束・pending有無）をチェックして提出。
- `post_submit_audit_orbit.py`  
  提出直後に状態を再確認し、snapshot更新と運用ログ追加の起点を作る。
- `orbit_path_eval_isolated.py` / `orbit_path_eval.py`  
  候補をローカルで直接対戦させる。`orbit_path_eval_isolated.py` は環境依存を避けやすい。
- `orbit_batch_eval.py`（補助）  
  同形状候補同士の一括比較。

### candidate_builds/

- 候補コードは次の形で1セット保持します。
  - `candidate_builds/<テーマ>/<variant>/main.py`
  - `candidate_builds/<テーマ>/<variant>/orbit_lite/`
- 例: `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py`

### logs/

- `snapshot_YYYYMMDD_HHMMSS/status.md`  
  時刻ごとのlive状態。収束確認の基準資料。
- `local_eval_*.json`  
  2P/4Pのローカル評価結果。採点・対戦相手・seedを残す。

### submissions/

- `submissions/<name>.tar.gz` は Kaggle 提出時点の再現物。
- 参照用として保存し、再現は `candidate_builds` 側を正として行います。

### archive/

- `decisions/restore_decision_20260616.md` は 6/16 の復元判断を記録した履歴ノート。
- 日々の再現・提出フローには不要なため、提出可否の判断は `LOG.md` と `SUBMISSION_LOG.md` で完結させます。

---

## 3) 採用版の再現（highfast85）

### 3-1) 手法の要点

- **2P**: 速い局面（`best_fast` が閾値以上）で Producer 系の挙動を優先する。
- **4P**: 既存安定設定を維持し、top2維持を優先。
- **方針**: `Producer模倣相手` が増える前提で、局面ごとの攻守を変えすぎず、
  既存版の崩れを避ける。

### 3-2) 再現に必要なファイル

- `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py`
- `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/orbit_lite/`
- `submissions/highfast85_producer_gate_20260616.tar.gz`
- `scripts/cautious_submit_orbit.py` の highfast85 エントリ

---

## 4) 再現手順（実行フロー）

### 4-1. 環境準備

```bash
cd /path/to/Orbit_Wars_git
python -m venv .venv-orbit311
source .venv-orbit311/bin/activate   # Windows: .venv-orbit311\Scripts\Activate
pip install --upgrade pip
pip install "kaggle-environments>=1.28.0" kaggle
```

### 4-2. コード確認

```bash
grep -n "best_fast" candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py
python3 -m py_compile candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py
```

### 4-3. ローカル評価（2P）

```bash
python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=candidate_builds/h19_highfast_producer_gate_20260616/highfast85 \
  --opponent slawek=submissions/slawek_producer_v2_20260613.tar.gz \
  --seeds 127,128,129,130 \
  --out logs/local_eval_20260617/highfast85_seed127_130.json
```

### 4-4. ローカル評価（4P）

```bash
python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=candidate_builds/h19_highfast_producer_gate_20260616/highfast85 \
  --ffa-opponents submissions/slawek_producer_v2_20260613.tar.gz,submissions/kuni_lb1240_clean.tar.gz,submissions/carbon_top1_fork_output.tar.gz \
  --seeds 127,128 \
  --out logs/local_eval_20260617/highfast85_ffa_seed127_128.json
```

### 4-5. 収束確認

```bash
python3 scripts/snapshot_orbit_status.py
```

確認項目:
- 直近100分以内に3サンプル以上ある
- 最低45分以上の時間幅
- score spread が `<= 35.0`
- latest2 に保留（pending）がない

---

## 5) 実験記録の書き方（新規チューニング時）

### 5-1. 変更前に記録する

1ファイル1方針で切る。命名規則:

- `exp/<内容>-<日付>`（例: `exp/h19-producer-opponent-check-20260617`）

変更は、最低次の5点を残す。

- 意図: どの相手/局面を狙うか
- 変更箇所: `main.py` のどこを触るか
- 期待効果: どの指標を上げるか
- 比較条件: seed / 対戦相手 / 2P/4P
- 失敗条件: どこで見切るか

### 5-2. ローカル比較の必須

- `py_compile` が通る
- 2P: Producer, Kuni, Carbon, oldv2
- 4P: 必要時、同条件で比較
- `local_eval` のログを保存
- 提出に使う候補のみ snapshot と評価ログを追加

### 5-3. 承認基準

- `Producer` 相手で悪化しない
- `4P top2` が落ちない
- `h19-like`（既存版想定相手）で崩れない
- 上記満たしてから提案ログへ反映

---

## 6) 提出手順

```bash
python3 scripts/cautious_submit_orbit.py highfast85
python3 scripts/post_submit_audit_orbit.py
```

- いずれかの条件が外れていれば提出しない。
- 提出後は、`LOG.md` / `SUBMISSION_LOG.md` を即時更新。

---

## 7) tar.gzの作り方

```bash
cd candidate_builds/h19_highfast_producer_gate_20260616/highfast85
tar -czf ../../../submissions/highfast85_repro_pack_20260617.tar.gz main.py orbit_lite
tar -tf ../../../submissions/highfast85_repro_pack_20260617.tar.gz
```

再現に必要最小:
- `main.py`
- `orbit_lite/`

---

## 8) 提出コメントの最小形式

```text
<h1>highfast85 | <2P方針> | <2P/4Pの条件> | <seed帯・評価結果> | <日付>
```

例:
`highfast85 Producer-gate | best_fast>=85時 Producer切替 | 4P unchanged | 2P 127-138, 4P 127-128 | 2026-06-17`

---

## 9) 運用で見るログ（最短）

- `LOG.md`: 現在採用版・最新値・次アクション
- `SUBMISSION_LOG.md`: 判断理由、却下・採用の分岐
- `logs/snapshot_YYYYMMDD_HHMMSS/status.md`: 収束・保留・順位
- `logs/local_eval_*.json`: ローカル比較勝敗
