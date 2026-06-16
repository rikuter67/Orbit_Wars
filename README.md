# Orbit Wars 再現ガイド

このガイドは、再現性を優先して運用し、同じ材料で同じ結果に到達できるようにするための実行手順です。

ここだけ読めば、**どのファイルを見て、何をしたら再現できるか**を追えるように構成しています。

---

## 1) まず押さえる前提

- 対象: 現在運用中の `highfast85` 系。
- 原則: 変更は小さい単位で行い、ローカル検証→収束確認→提出の順で進める。
- 目的: 途中で判断基準がぶれないこと（再現性を守る）。

この3点を最初に固定すると、のちの判断が揺れません。

読む順序は固定です。

- `LOG.md` : 現在の状態（何が採用候補か）。
- `SUBMISSION_LOG.md` : 過去の判断理由。
- `logs/` : 検証の生データ。

---

## 2) リポジトリ構成（再現に必要な意味）

### 2-1. 迷いを防ぐための固定ルール

再現で見失いやすいのは「どこが正本でどこが履歴か」の線引きです。
ここでは、運用で必ず使うものだけを優先し、補助資料は最後に置いています。

### 2-2. 再現コア（毎回必読）

| パス | 役割 | なぜ必要か |
|---|---|---|
| `README.md` | 再現手順、前提、コメント規則 | 入口を一つに固定するため |
| `LOG.md` | 現在採用の状態、直近の数値 | 「今の正解」がどこかを素早く確認するため |
| `SUBMISSION_LOG.md` | 全提出の意図・評価・採否 | 後から「なぜこの版を選んだか」を追跡するため |

### 2-3. 運用ルール理解（背景）

- `LAST_WEEK_STRATEGY.md` : 2P/4P 分岐と採用条件の最終ルール。なぜ top2 を守るのかがここで決まる。 
- `ORBIT_WARS_GLOSSARY.md` : Producer, top2 cut などの用語統一。意味のズレを減らす。 
- `RESEARCH_NOTES.md` : 試行・失敗を含めた探索履歴。過去の失敗を再現しないため。 
- `CHECKPOINT_PRODUCER_1211_3.md` : 運用の節目。方針転換の根拠を残す。 
- `MANUAL_RESTORE_STEPS.md` : 収束不調時の戻し手順。

### 2-4. 毎回触る実行領域（ここを理解すればほぼ運用可能）

#### `scripts/`

- `snapshot_orbit_status.py` : Kaggle状況を取り、収束ゲートの根拠を保存。
- `cautious_submit_orbit.py` : 3条件（間隔・収束・pending）を守って提出を守る。
- `post_submit_audit_orbit.py` : 送信直後の状態を確定させる。
- `orbit_path_eval_isolated.py` / `orbit_path_eval.py` : ローカルで2P/4Pを比較し、seed依存を確認。
- `orbit_batch_eval.py` : 複数候補を並列で同条件比較。

#### `candidate_builds/`

候補コードの正本はここです。再現時はこの形で固定します。

- `candidate_builds/<テーマ>/<variant>/main.py`
- `candidate_builds/<テーマ>/<variant>/orbit_lite/`

現行対象: `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/`

#### `logs/`

- `snapshot_YYYYMMDD_HHMMSS/status.md` : live収束・pending・順位の時系列。
- `local_eval_*.json` : ローカル対戦結果（2P/4P）と seed ごとの比較。

#### `submissions/`

- `submissions/<name>.tar.gz` : Kaggleへ出す提出成果物。
- 再現比較では、**真実は候補コード**なので `candidate_builds` を正として読む。

### 2-5. 補助

- `experiments/` : 試作メモ。
- `producer_live_source/` : 公開版の参照コピー。

---

## 3) 採用版の再現（highfast85）

### 3-0) 再現対象（提出コメント）

このガイドで再現するのは、以下の提出コメントと一致する版です。

`highfast85 Producer-gate | 2P switch to Producer when best_fast>=85 | iso127-138 h19 14-6-4 Producer 12-10-2 oldv2 14-10 Kuni6-2 Carbon6-2 | 4P unchanged | 20260616`

**判定ロジックの意味**

- 2人戦: `best_fast >= 85` を越える局面で Producer 的な攻勢に切り替える。
- 4人戦: 既存 h19 Producer4P を維持し、top2 落下を避ける。
- 比較相手: `h19, Producer, oldv2, Kuni, Carbon` を固定条件で評価。
- 対象データ: `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py`。
- 成果物: `submissions/highfast85_producer_gate_20260616.tar.gz`。

### 3-1) 手法の要点

- 2P は高速局面を取りこぼさないよう、閾値ベースで Producer 傾向を採用。
- 4P は生存を優先し、top2 を守る既存設計を維持。
- `Producer` を想定する公開相手が増える想定で、局面毎の極端な分岐は最小化。

### 3-2) 再現に必要なファイル

- `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py`
- `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/orbit_lite/`
- `submissions/highfast85_producer_gate_20260616.tar.gz`
- `scripts/cautious_submit_orbit.py` の `highfast85` エントリ

---

## 4) 再現手順（実行フロー）

この順番を守ると、再現結果がほぼ同じになります。

### 4-1. 環境準備（なぜ必要？）

同じ依存で走らせないと、同じコマンドでも結果がズレます。

```bash
cd /path/to/Orbit_Wars_git
python -m venv .venv-orbit311
source .venv-orbit311/bin/activate   # Windows: .venv-orbit311\Scripts\Activate
pip install --upgrade pip
pip install "kaggle-environments>=1.28.0" kaggle
```

### 4-2. コード確認（なぜ必要？）

手元の候補に設定が反映されていることを先に確認します。

```bash
grep -n "best_fast" candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py
python3 -m py_compile candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py
```

### 4-3. ローカル評価（2P）

まず 2P の改善を確認します。ここで最初に Producer への改善がないと先に進めません。

```bash
python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=candidate_builds/h19_highfast_producer_gate_20260616/highfast85 \
  --opponent slawek=submissions/slawek_producer_v2_20260613.tar.gz \
  --seeds 127,128,129,130 \
  --out logs/local_eval_20260617/highfast85_seed127_130.json
```

### 4-4. ローカル評価（4P）

2Pだけでは不十分。4P の `top2` が落ちないかを確認してから採否判断に進みます。

```bash
python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=candidate_builds/h19_highfast_producer_gate_20260616/highfast85 \
  --ffa-opponents submissions/slawek_producer_v2_20260613.tar.gz,submissions/kuni_lb1240_clean.tar.gz,submissions/carbon_top1_fork_output.tar.gz \
  --seeds 127,128 \
  --out logs/local_eval_20260617/highfast85_ffa_seed127_128.json
```

### 4-5. 収束確認（なぜ必要？）

live スコアは時間で揺れるため、短期サンプルだけで判断しません。

```bash
python3 scripts/snapshot_orbit_status.py
```

確認ルール:

- 直近100分以内に3サンプル以上
- 時間幅は最低45分以上
- score spread `<= 35.0`
- latest2 に pending がない

上記を満たさなければ提出しません。

---

## 5) 実験記録の書き方（新規チューニング時）

ここを毎回書くと、「なぜここを採用したか」を再現者に説明できます。

### 5-1. 変更前に記録

- 1方針1ファイルで作る（例: `exp/<内容>-<日付>`）。
- 記録する5点:
  - 意図（狙う相手・局面）
  - 変更箇所（`main.py` のどこ）
  - 期待効果（上げる指標）
  - 比較条件（seed・相手・2P/4P）
  - 見切り条件（失敗時に止める条件）

### 5-2. ローカル比較の必須条件

- `py_compile` が通ること
- 2P: Producer, Kuni, Carbon, oldv2
- 4P: 必要なら同じ条件で比較
- `local_eval` の json を保存
- 提出候補のみ snapshot とログを追加

### 5-3. 提案採用基準

- `Producer` 相手で悪化しない
- `4P top2` が落ちない
- `h19-like` 相手で崩れない
- 3条件が同時成立した場合のみ提案ログへ反映

---

## 6) 提出手順

提出は自動ガードを通した候補だけに限定します。

```bash
python3 scripts/cautious_submit_orbit.py highfast85
python3 scripts/post_submit_audit_orbit.py
```

- いずれか条件不一致なら提出しない
- 提出後は `LOG.md` / `SUBMISSION_LOG.md` を即時更新

---

## 7) tar.gz の作成

必要最小構成がシンプルなほど、提出再現が早くなります。

```bash
cd candidate_builds/h19_highfast_producer_gate_20260616/highfast85
tar -czf ../../../submissions/highfast85_repro_pack_20260617.tar.gz main.py orbit_lite
tar -tf ../../../submissions/highfast85_repro_pack_20260617.tar.gz
```

再現最低要素:
- `main.py`
- `orbit_lite/`

---

## 8) 提出コメントの書式（再現検証キー）

同じ形式で残すと、提出物の再検索と採択理由の追跡が速くなります。

```text
<name> | <2P方針> | <2P/4P条件> | <seed帯・評価> | <日付>
```

例:
`highfast85 Producer-gate | best_fast>=85時 Producer切替 | 4P unchanged | 2P 127-138, 4P 127-128 | 2026-06-17`

---

## 9) 運用で読むログ（最短）

- `LOG.md`: 現在採用版と最新状態
- `SUBMISSION_LOG.md`: 全提出の意思決定
- `logs/snapshot_YYYYMMDD_HHMMSS/status.md`: live 収束・pending・順位
- `logs/local_eval_*.json`: 2P/4P 比較結果
