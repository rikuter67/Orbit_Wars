# Orbit Wars 実験ログ（運用版）

このリポジトリの実行/提出を誰でも追えるように、**現在の状態と再現手順**を1か所にまとめたログです。  
提出済みの全文履歴は [`SUBMISSION_LOG.md`](SUBMISSION_LOG.md) に保存しています。

## 0) 先に答え（`tar` と Git）

`tar` ファイルは Git に入れられます（`git add` してコミット可能）。  
ただし実務上は次の理由で推奨しません。

- バイナリ差分がつかみにくく履歴肥大化しやすい
- 既存の履歴が大きくなり、pull/push が遅くなる
- 再現には内容（`main.py`）が優先されるため、元データよりもソース管理が重要

**運用方針（推奨）**

- Git: コード本体＋評価ログ＋再現手順を管理
- `submissions/*.tar.gz`: 参考保存なら `git lfs` または `.gitignore` と別媒体（共有Drive）運用

## 1) 役割分担と現在の最重要状態（2026-06-16 21:16 JST 時点）

### 現状（Kaggle側）

- 現行採用候補: `highfast85_producer_gate_20260616.tar.gz`
- 最新提出: `53734299`
- スコア: `1269.5`
- 順位: `109/4593 (2.37%)`
- topライン:
  - top2: `1296.2`、top3: `1252.8`、top5: `1224.3`

### 直近方針

- `h19` 系の現状版が比較的安定（4P top2保持）
- 新規アイデア（trap/avoid/preempt など）は**収束確認＋条件ゲートなしでの直接提出は見送る**

## 2) 再現フロー（最短5分）

```bash
# 1. パッケージ
pip install "kaggle-environments>=1.28.0" kaggle

# 2. リポジトリ起点
cd /mnt/c/Users/rikuter/kaggle/Orbit_Wars_git

# 3. 提出候補のアーカイブ（例: highfast85）
tar -czf /tmp/highfast85_test.tar.gz main.py

# 4. ローカル単体対戦（再現最重要）
python3 scripts/orbit_path_eval_isolated.py \
  --candidate candidate=./submissions/highfast85_producer_gate_20260616.tar.gz \
  --opponent slawek=./submissions/slawek_producer_v2_20260613.tar.gz \
  --seeds 127,128,129,130 \
  --out logs/local_eval_20260616/example_check.json

# 5. 提出
kaggle competitions submit orbit-wars -f submissions/highfast85_producer_gate_20260616.tar.gz \
  -m "highfast85_producer_gate_20260616 | 2P best_fast>=85 gate"
```

### 提出前の最低チェック

1. `py_compile` 済み（`python3 -m py_compile ...`）
2. 同一候補を2バッチ以上で同傾向確認（最小でも `--seeds` 127-130 と別帯域）
3. live スコア収束（直近 100分以上・3点以上・spread <= 35）
4. latest2 が pending でないこと

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
| `REPRODUCTION_GUIDE.md` | そのまま再現するための詳細手順 |
| `ORBIT_WARS_GLOSSARY.md` | 用語辞書（Producer/Kuni/oldv2 等） |
| `LOG.md` | 本ファイル（現況＋再現の指令） |

## 4) 主要提出履歴（要点だけ）

| 日時 (JST) | ref | コメント | スコア | 目的 |
|---|---:|---|---:|---|
| 2026-06-16 06:47 | `53734299` | highfast85 Producer-gate | `1269.5` | 現在採用候補。2P/4PのバランスとProducer戦収束を確認 |
| 2026-06-16 00:06 | `53714957` | h19 2P-only variant | `1230.8` | まず安定性を優先した生存ライン |
| 2026-06-14 02:00 | `53645538` | Producer V2 refresh | `1217.2`（初期） | latest2安全基準を満たすための保険行 |
| 2026-06-13 13:58 | `53634763` | Producer V2安全行 | `1196.7` | Producer側のベースライン確保 |

※本文字数を抑えるため、差分付きの完全版は [`SUBMISSION_LOG.md`](SUBMISSION_LOG.md) を参照。

## 5) 直近の有意イベント（要約）

- `kaggle_environments` 未導入での path eval 失敗を受け、`scripts/orbit_path_eval_isolated.py` を追加（依存汚染対策）
- Producer模倣候補を多数検証（trap/avoid/preempt/selector系）が、**h19系との自己同型対決で崩れないか**を主判定に採用
- `highfast85` の 85閾値は 127-138 系で、Producer 対 14-10〜?、2Pでの改善が確認されたため実験・提出へ

```mermaid
timeline
    title Orbit Wars 現時点の判断フロー
    2026-06-14 : Producer V2安全行をlatest2に積む
    2026-06-15 : h19 2P-only variant を実戦投入
    2026-06-16 : map-gate/behavior-gateなど多数試行
    2026-06-16 06:47 : highfast85_producer_gate が現時点採用
```

## 6) score推移（参考：h19/Producer line）

```mermaid
xychart-beta
    title "h19系 live score（収束確認用）"
    x-axis [06:30, 07:00, 08:00, 09:00, 10:00, 11:00, 12:00]
    y-axis 1220 --> 1270
    line [1235.0, 1224.9, 1231.7, 1223.3, 1227.5, 1238.1, 1238.1]
```

## 7) 運用ノート（提出時に必ず記録）

提出を行うたびに更新する項目:

- 候補名と意図
- 変更したファイル/パラメータ
- ローカル実験コマンドと`--seeds`範囲
- 最新 live スコア、直近収束情報
- 提出後の pending/complete 状況

これらは `SUBMISSION_LOG.md` と、この `LOG.md` の 3箇所（提出コマンドログ、スナップショット、反省）に反映します。  
誰かが1日後に同じ実験を再現できることを前提に、**結果と意図をセット**で残してください。

