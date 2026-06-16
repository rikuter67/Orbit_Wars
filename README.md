# Orbit Wars 実験用ワークスペース（再現重視）

このリポジトリは **Orbit Wars** 用の実験コードと提出管理を行う作業場です。  
`git push` 可能な基準リポジトリとして、今後は **`/mnt/c/Users/rikuter/kaggle/Orbit_Wars_git`** を使います。

## 今後の運用ルール

- `main` は保守用。  
- 実験は `exp/<experiment-name>-YYYYMMDD` 形式のブランチで行う。
- 提出や比較結果は同名ブランチで管理し、`SUBMISSION_LOG.md` に意思決定を残す。
- `scripts/cautious_submit_orbit.py` を使って、提出前に 3 時間ルールと収束チェックを通す。
- `GitHub` は `https://github.com/rikuter67/Orbit_Wars`。

## ディレクトリ構成（短縮）

- `candidate_builds/`: 週次の候補バリアント（実験フォルダ）。
- `experiments/`: ローカル限定の試作。
- `submissions/`: 実提出アーカイブ（`.tar.gz`）。
- `scripts/`: ローカル評価、提出ゲート、ログ取得。
- `logs/`: `snapshot_YYYY.../status.md` やローカル評価結果。
- `SUBMISSION_LOG.md`: いつ、何を、なぜ、提出/不提出したかの履歴。

## 最短スタートアップ

```bash
cd /mnt/c/Users/rikuter/kaggle/Orbit_Wars_git
python -m venv .venv-orbit311
source .venv-orbit311/bin/activate  # Windowsなら Scripts\Activate
pip install "kaggle-environments>=1.28.0" kaggle torch
```

### ローカル比較例（2P）

```bash
python3 scripts/orbit_path_eval_isolated.py \
  --candidate test=experiments/low_value_trapguard \
  --opponent slawek=submissions/slawek_producer_v2_20260613.tar.gz \
  --seeds 127,128,129,130 \
  --out logs/local_eval_20260617/repro_check.json
```

### 提出準備（推奨）

1. `scripts/snapshot_orbit_status.py` で現状の提出状態を記録。  
2. `python3 scripts/cautious_submit_orbit.py <candidate_key>`（キーは `scripts/cautious_submit_orbit.py` の `CANDIDATES`）
3. `python3 scripts/post_submit_audit_orbit.py` で提出直後監査を `SUBMISSION_LOG.md` に追記。

### 再提出アーカイブ作成

```bash
cd candidate_builds/h19_producer_mapgate_20260616/highfast85  # 例: candidate directory
tar -czf ../submissions/repro_test_20260617.tar.gz main.py orbit_lite
```

## 再現性のルール（他人が回せる状態にするため）

- パス依存を避けるため、運用スクリプトは固定の `/mnt/.../Orbit_Wars` パスを使わず、リポジトリから相対参照に寄せる。
- 変更は最小単位のブランチで行い、PR/コミット単位で実験ログと紐付ける。
- 新規提出物は必ず `submissions/` に保存し、圧縮内容（`main.py` + `orbit_lite/`）を確認してから提出する。

## 既存ノートへの入り口

- `SUBMISSION_LOG.md`: 提出意思決定の時系列ログ
- `LAST_WEEK_STRATEGY.md`: 直近の方針（優先）
- `RESTORE_DECISION_20260616.md`: リカバリ判断の記録
- `ORBIT_WARS_GLOSSARY.md`: 用語メモ

## チェック項目（他者引き継ぎ）

- [ ] ブランチ名が `exp/...` 形式か  
- [ ] 主要ファイル変更後に `python -m py_compile` を通したか  
- [ ] ローカル評価JSONが保存されたか  
- [ ] `snapshot_orbit_status.py` と `SUBMISSION_LOG.md` が更新されているか  
- [ ] 提出時コメント（`CANDIDATES` の message）に変更要点が入っているか
