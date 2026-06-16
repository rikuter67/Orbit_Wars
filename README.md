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

この運用では、実行判断の正本はこの README + `SUBMISSION_LOG.md` です。

- `README.md`（ここ）: 手順・判断ルール・再現コマンドの正本
- `SUBMISSION_LOG.md`: 全提出の全履歴（正確な根拠）
- `logs/`: 収束・比較の証跡
- `candidate_builds/`: 候補版ソース
- `submissions/`: 提出物（`.tar.gz`）

---

## 2) 再現フロー（最短5分）※現状最強版（highfast85）

この順序で実行すると、現行採用版を短時間で同条件再現できます。

### 2-0. 再現対象（現状最強版）

再現すべき版:

```text
highfast85 Producer-gate | 2P switch to Producer when best_fast>=85 |
iso127-138 h19 14-6-4 Producer 12-10-2 oldv2 14-10 Kuni6-2 Carbon6-2 | 4P unchanged | 20260616
```

- 2P: `best_fast >= 85` のとき Producer へ切替
- 4P: 4Pトップ2維持の既定挙動を維持
- ファイル:
  - `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py`
  - `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/orbit_lite/`
  - `submissions/highfast85_producer_gate_20260616.tar.gz`

### 2-1. パッケージ

```bash
pip install "kaggle-environments>=1.28.0" kaggle
```

### 2-2. リポジトリ起点

```bash
cd /path/to/repo/Orbit_Wars_git
```

※あなたの環境に合わせて `path/to/repo` を実際のパスに置き換えてください。

### 2-3. 提出候補のアーカイブ（例: highfast85）

```bash
cd candidate_builds/h19_highfast_producer_gate_20260616/highfast85
tar -czf ../../../submissions/highfast85_repro_pack_20260617.tar.gz main.py orbit_lite
```

### 2-4. ローカル単体対戦（再現最重要）

ここが通らない候補は、提出前で止めます。まずローカルで「再現性」を担保し、
それが成立してから live へ進みます。

- `py_compile`：構文や import エラーを最初に潰す。
- 2P単体対戦：`Producer` に対する優位性（勝敗の傾向）が安定しているかを見る。
- FFA補完対戦：`4P`で top2 が崩れやすい相手（Kuni / carbon / oldv2）へ影響がないか見る。

再現順:

1. まず `py_compile` で採用版本体を検証
2. `submissions/` 版で2P・4Pを同一 seed で検証
3. `candidate_builds/.../highfast85/` 版でも同一条件で再検証

意図:

- 2Pと4Pを同じ評価フローで見る。
- seed を固定して再現可能性を担保する。
- 条件を満たさなければ提出ルートへ進まない。

期待される出力（重要）:

- `logs/local_eval_20260616/example_check.json` が生成される。
- `summary` 配下の `wins` / `losses` / `draws`（または同等項目）で、期待した方向性が見える。

異常時:

- JSONが生成されない場合は、`kaggle-environments` のimport、`--candidate` のパス、seed指定を再確認。
- 予想外に悪化していたら、その候補はここで止めて提出に進まない。

```bash
# まず構文エラーと import 破損を除外
python3 -m py_compile candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py

# 2P再現（Producer との直接比較）
python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=candidate_builds/h19_highfast_producer_gate_20260616/highfast85 \
  --opponent slawek=./submissions/slawek_producer_v2_20260613.tar.gz \
  --seeds 127,128,129,130 \
  --out logs/local_eval_20260617/highfast85_seed127_130.json

# 4P補完チェック（top2崩れがないか）
python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=candidate_builds/h19_highfast_producer_gate_20260616/highfast85 \
  --ffa-opponents ./submissions/slawek_producer_v2_20260613.tar.gz,./submissions/kuni_lb1240_clean.tar.gz,./submissions/carbon_top1_fork_output.tar.gz \
  --seeds 127,128 \
  --out logs/local_eval_20260617/highfast85_ffa_seed127_128.json

# まず tar 版で最低1回実行（提出直前の再現）
python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=./submissions/highfast85_producer_gate_20260616.tar.gz \
  --opponent slawek=./submissions/slawek_producer_v2_20260613.tar.gz \
  --seeds 127,128,129,130 \
  --out logs/local_eval_20260616/example_check.json

# 4P補完チェック（top2崩れがないか）
python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=./submissions/highfast85_producer_gate_20260616.tar.gz \
  --ffa-opponents submissions/slawek_producer_v2_20260613.tar.gz,submissions/kuni_lb1240_clean.tar.gz,submissions/carbon_top1_fork_output.tar.gz \
  --seeds 127,128,129,130 \
  --out logs/local_eval_20260616/example_check_ffa.json
```

### 2-5. 提出（候補を採用した場合）

このコマンドは、採用判断が最終確定した時だけ実行します。
ここは「最終提出手段」なので、`2-6` の最低チェックを先に満たすことが前提です。

目的:

- ローカル再現と検証済み候補を、Kaggle公式経路で提出する。
- コメントに再現キーを残して、後で提出履歴から判別可能にする。

補足:

- 再現した seed 条件を壊さないため、コマンドは毎回同じ名前でログを保存しておく。
- 失敗した場合は `scripts/cautious_submit_orbit.py` の条件（pending、3時間、latest2）を確認してから再試行する。

採用時の提出準備（最低限）:

```bash
python3 scripts/cautious_submit_orbit.py highfast85
python3 scripts/post_submit_audit_orbit.py
```

期待される出力:

- 提出ID（ref）と最新 status が CLI に返る。
- コメント文字列が `-m` で完全一致で残る。

異常時:

- pending が直前で重なっていたり、認証情報不足なら提出は失敗。
- その場合は `2-6` の提出前チェックを再チェックして、`scripts/cautious_submit_orbit.py` を推奨。

```bash
kaggle competitions submit orbit-wars -f submissions/highfast85_producer_gate_20260616.tar.gz \
  -m "highfast85_producer_gate_20260616 | 2P best_fast>=85 gate"
```

### 2-6. 提出前の最低チェック

以下は提出可否の最終ゲートです。どれか1つでも満たさなければ提出前の状態を凍結せず、ここで止めます。

#### 2-6-a. コード整合チェック

- `py_compile` 済み
  - `python3 -m py_compile <candidate>/main.py`

#### 2-6-b. 一貫性チェック

- 同一候補を2バッチ以上で同傾向確認
  - 最低でも `--seeds 127-130` と別帯域

#### 2-6-c. 収束チェック（live）

- live スコア収束
  - 直近 100分以上
  - 3点以上のサンプル
  - `spread <= 35`
- （収束補足）
  - 最新100分以内に3点以上
  - 時間幅が45分以上
  - `score spread <= 35.0`
  - latest2 no pending

#### 2-6-d. 進行保護チェック

- latest2 が `pending` でないこと

それぞれの理由:

- `py_compile`: 構文エラーで提出しても提出ログだけが増える事故を防ぐ。
- 2バッチ確認: seed 依存の偏りを避ける。
- live収束: 時間で揺れる点を防ぐ。
- pending確認: 替わられた提出状態の上書き競合を避ける。

---

## 3) リポジトリ構成（木構造）

```text
Orbit_Wars/
├─ README.md
│  └─ 運用ルール、最短再現手順、提出手順（これが読む第一資料）
├─ SUBMISSION_LOG.md
│  └─ 全提出の詳細履歴（差分・判定理由）
├─ ORBIT_WARS_GLOSSARY.md
│  └─ Producer / oldv2 / Kuni など用語の意味
├─ candidate_builds/
│  ├─ h19_highfast_producer_gate_20260616/highfast85/
│  │  ├─ main.py
│  │  │  └─ 採用版エージェント本体
│  │  └─ orbit_lite/
│  │     └─ 高速化・経路計算・行動選択ロジック
│  └─ ※他実験版の候補（比較・再現材料）
├─ scripts/
│  ├─ orbit_path_eval_isolated.py
│  │  └─ 2P/4Pを固定seedで再現比較する最重要評価スクリプト
│  ├─ cautious_submit_orbit.py
│  │  └─ pending/時間間隔を確認して提出する安全ゲート
│  ├─ post_submit_audit_orbit.py
│  │  └─ 提出後の整合チェックの簡易監査
│  ├─ convergence_report_orbit.py
│  │  └─ live収束の判定補助
│  ├─ snapshot_orbit_status.py
│  │  └─ 提出直前の状態ファイル作成
│  ├─ trace_orbit_actions.py / trace_orbit_game.py
│  │  └─ ゲーム行動と対局トレース解析
│  └─ その他: orbit_batch_eval.py, restore_readiness_orbit.py, next_orbit_monitor_time.py
│     └─ バッチ評価、提出準備、監視・補助用
├─ submissions/
│  ├─ highfast85_producer_gate_20260616.tar.gz
│  │  └─ Kaggle提出用の現行採用版（現場提出物）
│  ├─ slawek_producer_v2_20260613.tar.gz
│  │  └─ 比較相手（producer系ベンチ）
│  └─ その他: 過去提出 tar.gz（比較実験履歴）
├─ logs/
│  ├─ local_eval_YYYYMMDD/*.json
│  │  └─ ローカル再現結果
│  ├─ snapshot_YYYYMMDD_*/status.md
│  │  └─ 提出時の状態記録（時間、top、submission名など）
│  └─ その他のCSV/JSON
│     └─ 特徴量・比較ログ（再現検証の材料）
├─ producer_live_source/
│  └─ 参照用の producer 本体（ベースライン比較）
└─ experiments/
   └─ 試験版実装置き場（最終提出前の試行ログ）
```

この木を読むだけで、見たい情報がどこにあるか追えます。
（本版で再現運用に必須なのは `README.md`、`SUBMISSION_LOG.md`、`scripts/`、`candidate_builds/.../highfast85/`、`submissions/`、`logs/`）

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
