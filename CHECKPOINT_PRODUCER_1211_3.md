# Orbit Wars チェックポイント: Producer 1211.3

タイムスタンプ: 2026-06-14 JST

このチェックポイントは、リセット直後の更新前に `1211.3` へ収束していたライブ Producer V2 状態を固定します。

## ライブ時点

- 安定完了行: `53645538`
- ファイル: `slawek_producer_v2_20260613.tar.gz`
- コメント: `cautious latest2 producer_v2 safety refresh 20260614`
- `logs/snapshot_20260614_124418_status.md` 時点スコア: `1211.3`
- 同時点の順位: `300/4424`（`6.78%`）
- 同時点の Top2 カット: `1288.1`

UTC 日次提出リセット後の `12:44 JST` に Producer を再更新しました。

- 新規行: `53658218`
- `logs/snapshot_20260614_124449_status.md`: `PENDING`
- `logs/snapshot_20260614_125219_status.md`: `COMPLETE`、初期スコア `690.5`
- この提出後の latest2: Producer refresh + Producer complete

`690.5` 行は新規復帰中の Producer 完了行として扱い、新しい候補の証拠とはしない。
この行の再確認が終わるまでは別候補の提出を入れない。

## 含めるべきファイル

- `submissions/slawek_producer_v2_20260613.tar.gz`
  - SHA256: `c12baa59adf2d980cab0e432666526592155f15ada0ba1b947782aedf0f89bca`
- `producer_live_source/`
  - Producer V2 のソースを抽出し、ローカル理解と派生版作成に利用する。
- `scripts/`
  - 提出保護・スナップショット保存・監査・ローカル評価用ヘルパー。
- `logs/snapshot_20260614_124418_status.md`
  - 1211.3 の最終基準となるスナップショット。
- `logs/snapshot_20260614_124449_status.md`
  - リセット後に Producer を再提出してすぐ作成したスナップショット。
- `ORBIT_WARS_GLOSSARY.md`,
  `SUBMISSION_LOG.md`
  - 用語集、時系列証跡を同梱する。

## 次の研究方向

次の研究は「Producer 類似相手」を直接想定して進める。
新規施策・派生候補・対戦相手モデリング実験はすべて `main` から分岐したブランチで行い、`main` 側は再現用・証跡用に保つ。

Kaggle 提出コメントは「コードを開かなくても意味が読める」形式に統一する。  
以下を推奨:

`Base family | concrete change | local evidence | date`

例:

- `ProducerV2 baseline refresh | no code change | latest2 safety | 20260614`
- `ProducerV2 2P-only variant | H18 ROI1.3 beta1.8 | Producer との対戦 17-11 | 4Pはそのまま | 20260614`

直近の実装ノート:

- 多くの対戦相手は Producer のクローン／近似版であるという仮定。
- Producer の候補ターゲット選定、safe-drain での攻撃サイズ、regroup 先を予測する。
- Producer は我々の1手を評価して返す一方で、相手を「ほとんど無行動」と見積もる盲点を狙う。必要なら粗い強化余力マージンで補正する。
- ライブ提出前に `producer_live_source` に対して counter-Producer 候補をローカル検証すること。
