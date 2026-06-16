# Orbit Wars 再現・運用ガイド（最短版）

このリポジトリでやることは1つです。

1) 実装を再現する
2) ローカルでテストする
3) 収束条件を満たしたら提出する

ここでは高最優先の再現対象を固定し、同じ結果を他人が再現できる状態にします。

---

## 今最優先の提出再現対象

- `H19 highfast85 Producer-gate | 2P switch to Producer when best_fast>=85 | iso127-138 h19 14-6-4 Producer 12-10-2 oldv2 14-10 Kuni6-2 Carbon6-2 | 4P unchanged | 20260616`

再現に必要なもの:

- `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py`
- `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/orbit_lite/`
- `submissions/highfast85_producer_gate_20260616.tar.gz`
- `scripts/cautious_submit_orbit.py` の `highfast85` エントリ

---

## 5分で動ける手順

### A. 環境準備

```bash
cd /path/to/your/Orbit_Wars_git
python -m venv .venv-orbit311
source .venv-orbit311/bin/activate  # Windows なら .venv-orbit311\Scripts\Activate
pip install --upgrade pip
pip install "kaggle-environments>=1.28.0" kaggle torch
```

### B. まずは差分だけ確認する（重要）

```bash
git status
```

`highfast85` 版が 90→85 になっているかを確認:

```bash
grep -n "best_fast" candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py
```

期待: `>= 85.0`（highfast90なら `>= 90.0`）。

### C. 最低限ローカルチェック

#### 2Pローカル評価

```bash
python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=candidate_builds/h19_highfast_producer_gate_20260616/highfast85 \
  --opponent slawek=submissions/slawek_producer_v2_20260613.tar.gz \
  --seeds 127,128,129,130 \
  --out logs/local_eval_20260617/highfast85_seed127_130.json
```

#### 4P（必要なら）

```bash
python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=candidate_builds/h19_highfast_producer_gate_20260616/highfast85 \
  --ffa-opponents submissions/slawek_producer_v2_20260613.tar.gz,submissions/kuni_lb1240_clean.tar.gz,submissions/carbon_top1_fork_output.tar.gz \
  --seeds 127,128 \
  --out logs/local_eval_20260617/highfast85_ffa_seed127_128.json
```

### D. 提出アーカイブの整合を作る

```bash
cd candidate_builds/h19_highfast_producer_gate_20260616/highfast85
tar -czf ../../../submissions/highfast85_repro_pack_20260617.tar.gz main.py orbit_lite
```

この `tar.gz` を提出するなら、`main.py + orbit_lite` だけが入っていることを確認。

### E. 提出前のゲート通し

```bash
python3 scripts/snapshot_orbit_status.py
python3 scripts/cautious_submit_orbit.py highfast85
python3 scripts/post_submit_audit_orbit.py
```

`python3 scripts/cautious_submit_orbit.py highfast85` が通過するまで提出しない。

---

## 提出コメントの固定文（コピペ）

以下を `CANDIDATES` のメッセージとして使う（再現固定）:

`H19 highfast85 Producer-gate | 2P switch to Producer when best_fast>=85 | iso127-138 h19 14-6-4 Producer 12-10-2 oldv2 14-10 Kuni6-2 Carbon6-2 | 4P unchanged | 20260616`

---

## 変更後はここに残す

- `SUBMISSION_LOG.md`（提出/非提出の判断）
- `logs/` の `snapshot_YYYYMMDD_HHMMSS/status.md`（提出前後）
- `logs/local_eval_...json`（評価結果）

---

## ざっくり構成（迷わないため）

- `candidate_builds/`：提出候補（highfast85など）
- `experiments/`：ローカル実験
- `submissions/`：提出用圧縮ファイル
- `scripts/`：評価・提出ゲート
- `logs/`：実行ログ/スナップショット

---

## 失敗しやすいポイント

- `main.py` や `orbit_lite/` を除いて圧縮すると壊れる
- 毎回日付でブランチ名を付けるのではなく、内容で名前を付ける
- `py_compile` を通さないまま提出する

```bash
python3 -m py_compile candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py
```

---

## 参考

- `SUBMISSION_LOG.md`
- `LAST_WEEK_STRATEGY.md`
- `RESTORE_DECISION_20260616.md`
- `ORBIT_WARS_GLOSSARY.md`
