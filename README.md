# Orbit Wars 再現ガイド（高再現性運用版）

この README は、同じ再現手順で同じ判断に到達できるように集約した運用ガイドです。
提出を進める際はこの本文を最初に読む前提にしてください。

---

## 1) 役割分担と現在の最重要状態（2026-06-16 21:16 JST 時点）

### 現状（Kaggle側）

- 現行採用候補: `highfast85_producer_gate_20260616.tar.gz`
- 最新提出: `53734299`
- スコア: `1269.5`
- 順位: `109/4593 (2.37%)`
- topライン:
  - top2: `1296.2`
  - top3: `1252.8`
  - top5: `1224.3`

### 直近方針

- `h19` 系の現状版が比較的安定（4P top2保持）
- 新規アイデア（`trap`/`avoid`/`preempt` など）は、
  **収束確認＋提出条件ゲートなしでの直接提出は見送る**

### ファイルごとの役割（この版で運用）

この運用では、`LOG.md` は補助扱いで、**実行判断の正本はこの README + SUBMISSION_LOG** です。

- `README.md`（ここ）: 手順・判断ルール・再現コマンドの正本
- `SUBMISSION_LOG.md`: 全提出の全履歴（正確な根拠）
- `logs/`: 収束・比較の証跡
- `candidate_builds/`: 候補版ソース
- `submissions/`: 提出物（`.tar.gz`）

---

## 2) 再現フロー（最短5分）

この順序で実行すると、現行採用版を短時間で再現できます。

### 2-1. パッケージ

```bash
pip install "kaggle-environments>=1.28.0" kaggle
```

### 2-2. リポジトリ起点

```bash
cd /mnt/c/Users/rikuter/kaggle/Orbit_Wars_git
```

### 2-3. 提出候補のアーカイブ（例: highfast85）

```bash
tar -czf /tmp/highfast85_test.tar.gz main.py
```

### 2-4. ローカル単体対戦（再現最重要）

```bash
python3 scripts/orbit_path_eval_isolated.py \
  --candidate candidate=./submissions/highfast85_producer_gate_20260616.tar.gz \
  --opponent slawek=./submissions/slawek_producer_v2_20260613.tar.gz \
  --seeds 127,128,129,130 \
  --out logs/local_eval_20260616/example_check.json
```

### 2-5. 提出（候補を採用した場合）

```bash
kaggle competitions submit orbit-wars -f submissions/highfast85_producer_gate_20260616.tar.gz \
  -m "highfast85_producer_gate_20260616 | 2P best_fast>=85 gate"
```

### 2-6. 提出前の最低チェック

- `py_compile` 済み
  - `python3 -m py_compile <candidate>/main.py`
- 同一候補を2バッチ以上で同傾向確認
  - 最低でも `--seeds 127-130` と別帯域
- live スコア収束
  - 直近 100分以上
  - 3点以上のサンプル
  - `spread <= 35`
- latest2 が `pending` でないこと

---

## 3) リポジトリ構成（最低限）

| パス | 内容 |
|---|---|
| `main.py` | ローカル起動用のエントリ（単体提出に使う最短版） |
| `candidate_builds/` | 候補実装の実験保存先 |
| `submissions/` | アーカイブ `*.tar.gz` |
| `logs/` | スナップショット、seed評価結果、差分結果 |
| `scripts/` | 評価・安全送信・ログ取得・提出監視 |
| `SUBMISSION_LOG.md` | 全提出の詳細ログ（履歴の正本） |
| `README.md` | 参照資料（規則・用語・実行コマンド） |
| `ORBIT_WARS_GLOSSARY.md` | 用語辞書（Producer/Kuni/oldv2 等） |

---

## 4) 主要提出履歴（要点だけ）

| 日時 (JST) | ref | コメント | スコア | 目的 |
|---|---:|---|---:|---|
| 2026-06-16 06:47 | `53734299` | `highfast85 Producer-gate` | `1269.5` | 現在採用候補。2P/4P のバランスと Producer 戦収束を確認 |
| 2026-06-16 00:06 | `53714957` | `h19 2P-only variant` | `1230.8` | まず安定性を優先した生存ライン |
| 2026-06-14 02:00 | `53645538` | `Producer V2 refresh` | `1217.2`（初期） | latest2安全基準を満たすための保険行 |
| 2026-06-13 13:58 | `53634763` | `Producer V2安全行` | `1196.7` | Producer側のベースライン確保 |

※本文字数を抑えるため、差分付き完全版は `SUBMISSION_LOG.md` を参照。

---

## 5) 採用版の再現（highfast85）

以下の投稿コメントと一致する版を再現します。

```text
highfast85 Producer-gate | 2P switch to Producer when best_fast>=85 | iso127-138 h19 14-6-4 Producer 12-10-2 oldv2 14-10 Kuni6-2 Carbon6-2 | 4P unchanged | 20260616
```

- 2P: `best_fast >= 85` の局面で Producer 方針へ切替
- 4P: `top2` を守る既定版構成を維持（現行挙動優先）
- 再現対象:
  - `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py`
  - `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/orbit_lite/`
  - `submissions/highfast85_producer_gate_20260616.tar.gz`

### 5-1. ローカル再現手順（最短）

```bash
cd /mnt/c/Users/rikuter/kaggle/Orbit_Wars_git
python3 -m venv .venv-orbit311
source .venv-orbit311/bin/activate  # Windows: .venv-orbit311\Scripts\Activate
pip install --upgrade pip
pip install "kaggle-environments>=1.28.0" kaggle

python3 -m py_compile candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py

python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=candidate_builds/h19_highfast_producer_gate_20260616/highfast85 \
  --opponent slawek=submissions/slawek_producer_v2_20260613.tar.gz \
  --seeds 127,128,129,130 \
  --out logs/local_eval_20260617/highfast85_seed127_130.json

python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=candidate_builds/h19_highfast_producer_gate_20260616/highfast85 \
  --ffa-opponents submissions/slawek_producer_v2_20260613.tar.gz,submissions/kuni_lb1240_clean.tar.gz,submissions/carbon_top1_fork_output.tar.gz \
  --seeds 127,128 \
  --out logs/local_eval_20260617/highfast85_ffa_seed127_128.json

python3 scripts/snapshot_orbit_status.py
```

### 5-2. 収束判定の閾値

- 最新100分以内に3点以上の記録
- 時間幅が45分以上
- score spread `<= 35.0`
- latest2 no pending

### 5-3. 提出準備（この状態でのみ）

```bash
python3 scripts/cautious_submit_orbit.py highfast85
python3 scripts/post_submit_audit_orbit.py
```

---

## 6) ログ運用とコメント規則

### SUBMISSION_LOG 追記ルール（最低）

- いつ提出したか
- 何を変えたか
- どの seed・相手で確認したか
- 収束判定結果（spread・pending・latest2）

### 提出コメントテンプレ

```text
<name> Producer-gate | <2P条件> | <seed帯と 4P条件> | <日付>
```

例:
`highfast85 | 2P best_fast>=85 | 2P iso127-138 / 4P 127-128 | 2026-06-16`

---

## 7) tar.gz 作成（再現用）

```bash
cd candidate_builds/h19_highfast_producer_gate_20260616/highfast85
tar -czf ../../../submissions/highfast85_repro_pack_20260617.tar.gz main.py orbit_lite
tar -tf ../../../submissions/highfast85_repro_pack_20260617.tar.gz
```

---

## 8) 補足: どこを先に読むか（短縮版）

この順で見れば5分で判断できます。

1. 本節 1（最重要状態）
2. 本節 2（再現フロー）
3. 本節 6（ログ運用）
4. `SUBMISSION_LOG.md`（全履歴確認）

