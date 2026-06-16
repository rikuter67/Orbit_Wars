# Orbit Wars 運用ガイド（再現性重視版）

このリポジトリは、**コードを再現できる形で実験し、公開提出までの判断を残して運用する**ことが目的です。  
ここを読むだけで、誰でも同じ結果に近づけることを狙っています。

---

## 0) まずここを読めば分かること

この README で、下記がすべて分かるようにしています。

- 何が入っているか（どのファイルに何を置くか）
- 何をどう変えたか（意図→変更点→狙う結果）
- どう再現して評価するか（コピペコマンド）
- いつ提出するか（ゲート条件）

この順番で読むと迷いません。

1. `## 2) このリポジトリの全体像`  
   「構成を把握」
2. `## 3.5) なぜこの版になったか`  
   「改良の経緯」
3. `## 5) 再現実験の基本フロー`  
   「再現コマンド」
4. `## 7) いつ提出するか`  
   「提出条件」
5. `SUBMISSION_LOG.md`  
   「過去決定の理由」

---

## 1) 何を目指すか（簡単版）

1. 既存版（公開提出中の本命）を壊さない  
2. 新しい改善案を小さく作る  
3. ローカルで比較評価する  
4. 収束条件を満たしたものだけ提出する  

評価時のルールは「再現可能性」「失敗しにくさ」「提出理由の追跡可能性」を優先します。

---

## 2) このリポジトリの全体像（誰が見ても分かる）

```
Orbit_Wars_git/
  README.md
  LOG.md
  SUBMISSION_LOG.md
  LAST_WEEK_STRATEGY.md
  RESTORE_DECISION_20260616.md
  ORBIT_WARS_GLOSSARY.md
  CHECKPOINT_PRODUCER_1211_3.md
  RESEARCH_NOTES.md
  MANUAL_RESTORE_STEPS.md

  scripts/                  # 評価・提出・監査スクリプト
  candidate_builds/         # 実験候補（2P/4Pのパラメータ差し替えなど）
  experiments/              # 試作中の実験ノート（再現用）
  logs/                     # ゲート結果・比較結果の保存先
  submissions/              # 提出用アーカイブを置く（原則コミットしない）
  producer_live_source/      # 参照用に抽出した公開ベース
```

### 主要ディレクトリの意味

- `scripts/`
  - `snapshot_orbit_status.py`  
    Kaggleの提出状況とスコア収束を確認して保存する
  - `cautious_submit_orbit.py`  
    3時間ルール・latest2・保留行・収束ゲートを自動チェックして提出する
  - `post_submit_audit_orbit.py`  
    提出直後に最新状態を監査する
  - `orbit_path_eval_isolated.py` / `orbit_path_eval.py`  
    ローカルでの対戦評価（提出実行に近い形式）
- `candidate_builds/`
  - 本命（例: `h19_highfast_producer_gate_20260616/highfast85`）の候補コードを保存
  - `main.py` + `orbit_lite/` のセットで1候補を再現
- `logs/`
  - `snapshot_YYYYMMDD_HHMMSS/status.md`  
    提出前後のライブ状態を固定
  - `local_eval_*.json`  
    ローカル評価結果
- `SUBMISSION_LOG.md`
  - どの版をなぜ出したか、提出・検証の意思決定履歴
- `LOG.md`
  - 現在の最終状態の短い要約

### GitHubで共有して他人に渡すときの最短読む順

**まず見る順番**
1. `README.md`（全体方針・再現手順）
2. `SUBMISSION_LOG.md`（どの版を採用したかと理由）
3. `LOG.md`（現時点の要約）
4. 該当候補ディレクトリ `candidate_builds/.../.../main.py`
5. 対戦記録 `logs/local_eval_*.json` と `logs/snapshot_*/status.md`

**共有時の固定説明文（コピペ用）**
`候補版: <name> / 根拠: <勝率改善と収束ログ> / 提出状態: <提出可否> / 最終更新: <YYYY-MM-DD>`

---

## 3) 現在の最優先で再現すべき提出版（固定）

以下は現時点の再現対象:

`H19 highfast85 Producer-gate | 2P switch to Producer when best_fast>=85 | iso127-138 h19 14-6-4 Producer 12-10-2 oldv2 14-10 Kuni6-2 Carbon6-2 | 4P unchanged | 20260616`

再現に必要:

- `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py`
- `candidate_builds/h19_highfast_producer_gate_20260616/highfast85/orbit_lite/`
- `submissions/highfast85_producer_gate_20260616.tar.gz`
- `scripts/cautious_submit_orbit.py` の `highfast85` エントリ

---

## 3.5) なぜこの版になったか（改良の経緯）

この版は、次の方針を順に試して安定したものです。

1. **まずは安定基盤を固定**  
   `Producer系` はライブでの土台としてまず復帰時に守り、`latest2` を安全に保った。
2. **新案の失敗を局地化**  
   「map gate」「グローバル切替」「早期積極/保守寄り」「multisize」など複数軸を試したが、  
   2P/4P のどちらか一方だけではなく、総合的に崩れやすいことが分かった。
3. **対戦相手の傾向を前提化**  
   投稿者側で最頻出になる相手は `Producer系` が高確率と見て、  
   2Pは `best_fast>=85` で Producer へ分岐する挙動を重視した。
4. **提出は単発 + 収束条件優先**  
   候補ごとの差分を増やすと、収束未確認のまま手当たり次第で壊れるため、  
   ローカル比較→live収束確認→1件提出→ログ追記の順に制限した。

決定根拠（短く言うと）:
- `Producer` と同系統の相手に対して明確に不利にならないこと
- `4P top2` での安定性を落とさないこと
- 収束ゲートを守ること
- `highfast85` が上記を満たす一貫性が高いこと

今後の拡張もこの4点を外れたら、どれだけ数字が良く見えても採用しない。

---

## 4) まず最初に見るべきもの（運用の起点）

1. `LOG.md`  
   今いちばん重要な状態（最新提出、ランク、カットライン、次の作業）を確認
2. `SUBMISSION_LOG.md`  
   直近の意思決定、検証結果、提出コメントを確認
3. 最新の `logs/snapshot_.../status.md`  
   ライブ状態が収束しているか確認

---

## 5) 再現実験の基本フロー（5〜10分）

### 5-1. 環境準備

```bash
cd /path/to/Orbit_Wars_git
python -m venv .venv-orbit311
source .venv-orbit311/bin/activate   # Windows: .venv-orbit311\Scripts\Activate
pip install --upgrade pip
pip install "kaggle-environments>=1.28.0" kaggle torch
```

### 5-2. 今回版が正しく取り込まれているか確認

```bash
git status
grep -n "best_fast" candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py
```

期待値: `best_fast` が `85.0` 以上（旧版比較では `90.0` など）。

### 5-3. 最低チェック（提出前の必須）

```bash
python3 -m py_compile candidate_builds/h19_highfast_producer_gate_20260616/highfast85/main.py
python3 scripts/snapshot_orbit_status.py
```

### 5-4. ローカル評価（2P）

```bash
python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=candidate_builds/h19_highfast_producer_gate_20260616/highfast85 \
  --opponent slawek=submissions/slawek_producer_v2_20260613.tar.gz \
  --seeds 127,128,129,130 \
  --out logs/local_eval_20260617/highfast85_seed127_130.json
```

上のコマンドが `ModuleNotFoundError` か `resolve_episode_seed` エラーで止まる場合は、以下を先に実行してから再試行してください。

```bash
export KAGGLE_ENVS_SRC=/tmp/kaggle-environments-src
python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=... \
  --opponent slawek=submissions/slawek_producer_v2_20260613.tar.gz \
  --seeds 127,128,129,130 \
  --out logs/local_eval_20260617/highfast85_seed127_130.json
```

### 5-5. ローカル評価（4P、必要なとき）

```bash
python3 scripts/orbit_path_eval_isolated.py \
  --candidate highfast85=candidate_builds/h19_highfast_producer_gate_20260616/highfast85 \
  --ffa-opponents submissions/slawek_producer_v2_20260613.tar.gz,submissions/kuni_lb1240_clean.tar.gz,submissions/carbon_top1_fork_output.tar.gz \
  --seeds 127,128 \
  --out logs/local_eval_20260617/highfast85_ffa_seed127_128.json
```

### 5-6. 結果確認

- `logs/local_eval_*.json` が作成される  
- 勝敗は「勝ち-負け（必要なら引き分け）」形式で読む  
- 本命候補より明確に良いか、悪くなったかを確認

---

## 6) 新規チューニングの進め方（誰が見ても追えるように）

### 6-1. まずは分離ブランチ

```bash
git checkout -b exp/意図_日付_短い名前
```

例: `exp/h19-producer-target-bonus-20260616`

### 6-2. 変更内容を「意図 + 箇所 + 期待効果」で記録

例:
- 意図: Producer相手で2Pの初手有利を伸ばす
- 変更: `main.py` の `early_score_bonus` を 1.2→1.4 に変更
- 期待: early-game の防御不足を減らす

### 6-3. ファイルを小さく増やす

候補は各々1箱にまとめる:
- `candidate_builds/xxx/variant_name/main.py`
- `candidate_builds/xxx/variant_name/orbit_lite/`

### 6-4. ローカル比較（必ず前提版と同条件）

- `py_compile`  
- 2P 対 Producer  
- 2P 対旧版対照群（Kuni / Carbon / oldv2）  
- 4P FFA（必要時）

### 6-5. 記録ルール（これを必須化）

- `SUBMISSION_LOG.md` の時系列ログへ追記
- `logs/local_eval_YYYYMMDD/*.json` を保存
- `logs/snapshot_YYYYMMDD_HHMMSS/status.md` を提出前後で保存

### 6-6. 変更意図の記録テンプレート（必須）

新規候補の `main.py` を作る前に、以下 1行をコメントでもログでも残す。

```
意図: [相手/フェーズの弱点をどう解消するか]
変更: [どこを変えるか: 例 best_fast, S,T,ROI,beta,max_waves,再探索条件]
理由: [なぜこの変更が効くと考えたか（仮説）]
反証条件: [どの指標で失敗とみなすか]
期待: [2P対Producer改善 or 4P top2維持など]
```

例:
- 意図: 2Pでの初期序盤、Producer型の過剰進攻に対抗する
- 変更: `best_fast` を 90→85 に変更
- 理由: 速い序盤局面での Producer 行動を模倣し、取り違えを減らすため
- 反証条件: 4P top2 を落とす、Kuni/oldv2の差が悪化
- 期待: Producerに対する不利ターンの減少、スコア収束後のライブでの維持

---

## 7) いつ提出するか（提出ゲート）

`scripts/cautious_submit_orbit.py` に同梱されている安全条件を満たす場合のみ提出。

実質チェック:

1. 直前 100分程度の最新2行が収束している  
2. `latest2` が保留中でない  
3. 前回提出から3時間空けている  
4. 2P/4P の改善が、テスト帯で再現できている  

提出コマンド:

```bash
python3 scripts/cautious_submit_orbit.py highfast85
```

提出後:

```bash
python3 scripts/post_submit_audit_orbit.py
```

---

## 8) 提出物（tar.gz）の作り方

**重要**: `tar.gz` は再現に必要ですが、Gitで大量に運用しない方針。  
まずは内容記録で再作成可能にし、`submissions/` は参照置場にします。

```bash
cd candidate_builds/h19_highfast_producer_gate_20260616/highfast85
tar -czf ../../../submissions/highfast85_repro_pack_20260617.tar.gz main.py orbit_lite
tar -tf ../../../submissions/highfast85_repro_pack_20260617.tar.gz
```

`tar` には最低限必要な2点:
- `main.py`
- `orbit_lite/`

これ以外は入れない。

---

## 9) 提出コメントの書き方（誰が見ても分かる形式）

提出時コメントは「人が読んで意図が分かる文字列」に固定する。  
例:

`H19 highfast85 Producer-gate | 2P switch to Producer when best_fast>=85 | iso127-138 h19 14-6-4 Producer 12-10-2 oldv2 14-10 Kuni6-2 Carbon6-2 | 4P unchanged | 20260616`

最低限含める4項目:
- ベース戦略名
- 主変更点
- ローカル検証の結果要約
- 実験日

---

## 10) これだけ見れば分かるチェックリスト（提出前）

- [ ] `main.py` / 依存の `py_compile` が通る  
- [ ] 2P/4P 比較ログが保存されている  
- [ ] `snapshot_orbit_status.py` が収束と直近スナップショットを作成  
- [ ] `cautious_submit_orbit.py` を通過  
- [ ] `SUBMISSION_LOG.md` に「なぜその版を出したか」を記入  
- [ ] `LOG.md` へ最終状態を更新  

---

## 11) 関連資料

- `SUBMISSION_LOG.md`
- `LOG.md`
- `LAST_WEEK_STRATEGY.md`
- `RESTORE_DECISION_20260616.md`
- `ORBIT_WARS_GLOSSARY.md`
