# Reasoning Architecture 赛道提交说明（草稿 v3）

状态：**DRAFT / 未经所有者审阅 / 不是提交内容**。[来源: 本文件约定]

## 0. 草稿元信息

- 本文件是 T2 草稿（`cloud/t2-submission-draft` @ `70ff21f6eb9d406e228052ca80150880749022d8`，`docs/submission/DRAFT_SUBMISSION.md`，sha256 `d3cbd3c5e4a16b821bb54320ee6803efabf80bf37c79ed6c526ee3da4bf4b181`）逐节更新到当前 `main` 的版本。[来源: `git show origin/cloud/t2-submission-draft:docs/submission/DRAFT_SUBMISSION.md | sha256sum`] [v2 更新]
- 本文件是 v2 草稿（`docs/submission/DRAFT_SUBMISSION_v2.md`，`cloud/t5-submission-refresh` @ `937188e14abb98e6743d759bd13982b8b919cf25`，sha256 `effb0303d991c5fc525f8bb93d8135921e47c9a7c87ed2cd38249ec23945b020`）按 T4 审查结论与所有者 2026-10-24 裁决 R1–R5 更新的版本。v2 的 [v2 更新] 标记原样保留，本次改动行尾标 [v3 更新]。 [来源: 本文件约定] [v3 更新]
- v3 使用的新输入：T4 = `docs/_review/T4_frz1_review.md` @ `cloud/t4-frz1-review` `550cdc6464ba6c4825a2eab3d23b577b84a9a26a`（sha256 `f5a89ee6423d6ec27969e4f3ce4fe4980ac6c4b709e0405ce3a08b07f22365d0`，对 `feat/frz1-b3core` `cb771079c1c119d73d0ebd0e24704a1935731cea` 的审查）；T3 = `docs/_diag/T3_failure_funnel.md` @ `cloud/t3-failure-funnel` `b8f0e104fbc62e3495f8371cec9ba4b5588b647e`；T1 = `docs/_review/T1_pr20_review.md` @ `cloud/t1-pr20-review` `1baed167a4545cf0df0a5960ca56287411a88d27`。引用写作 `T4 §x`。本草稿未重跑任何代码。 [v3 更新]
- 失败模式的完整说明在同目录 `FAILURE_MODES_DRAFT.md`（中英双语）；本文第 9A 节为一行一个的摘要。 [v3 更新]
- 起草基线：`main` 头 `520b7cfdf13b805c9258ab06c79a658ee62aef8b`（与任务核对值一致，无需改写）。[来源: `git rev-parse origin/main`；`git log -1` → 520b7cf "Merge pull request #23 from pzy19-prog/docs/prereg-addendum-05"] [v2 更新]
- v3 起草时 `main` 头仍为 `520b7cfdf13b805c9258ab06c79a658ee62aef8b`（`git rev-parse HEAD` 核对）。 [v3 更新]
- 本文未完成项：无因预算中止的项。第 9.2 节列出的是本草稿未做的核对工作。[来源: 本草稿工作过程]
- 引用格式：`[来源: 文件:行]` 或 `[来源: sha]`；仓库内找不到依据的写 `[UNKNOWN]`；需所有者填写的写 `[所有者填写]` / `[所有者裁决]`。改动过的条目行尾标 `[v2 更新]`。[来源: 本文件约定] v3 起，所有 dev 数字另标"dev，非注册结果"。 [v3 更新]
- 合并状态标注：**[main]** = 已在 `520b7cf` 上；**[FRZ-1 未合并]** = 仅在分支 `feat/frz1-b3core` @ `cb771079c1c119d73d0ebd0e24704a1935731cea`（相对 main 的 merge-base 为 `9fe17301c899abd9b2bf715ea7e62f0b47643e3d`，未合并）。[来源: `git log main..origin/feat/frz1-b3core`；`git merge-base main origin/feat/frz1-b3core`] [v2 更新]
- eval-v3 状态：种子值尚未生成也未被查看（`final_eval_v3_seed_values_created=false`、`final_eval_v3_seed_values_inspected=false`），`config/eval_seeds_v3.json` 不存在。本文所有涉及 eval-v3 结果或 B4 效果之处一律写"**待 eval-v3，尚无结果**"。本草稿未打开 `config/eval_seeds*.json`。[来源: docs/P3_PREREG_ADDENDUM_04.md:7; docs/P3_PREREG_ADDENDUM_05.md:7; artifacts/h1/final-eval-v3-prohibition.json:4-8]
- 本文不含"成功/失败/负结果"的措辞决定；这类决定列在末尾第 10 节。[来源: 任务约束；见第 10 节]
- 本文正文不引用 System-2（B3/B4）的性能数字，以免未经所有者审阅的结果出现在叙述中；第 9A 节与 `FAILURE_MODES_DRAFT.md` 为披露失败模式而转录 T1/T3/T4 的 dev 计数，一律标"dev，非注册结果"，其解读仍由所有者决定。已提交 B3 dev 数字位于 `artifacts/s2/b3-dev.md`（main 版本与 FRZ-1 分支版本的数字不同）。[来源: artifacts/s2/b3-dev.md; `git show origin/feat/frz1-b3core:artifacts/s2/b3-dev.md`; decisions.md:34; T4 §0] [v3 更新]
- PR #20（B4）已合并到 main：合并提交 `9fe1730`（2026-10-24 07:32:28 +0800）；PR #22（Python 3.12）合并提交 `612b06e`（07:32:11 +0800）；PR #23（Addendum 05）合并提交 `520b7cf`（09:12:21 +0800）。T2 草稿中全部"[PR#20 仅分支]"标注已过期，本文改标 [main]。[来源: `git log --format='%h %ci %s' pre-window-freeze..main`] [v2 更新]

## 1. 赛道与规则背景

- 选定赛道：Reasoning Architecture；设计文档默认目标为该赛道，且写明"赛道选择仍为所有者在提交前的决定"。[来源: docs/P3_SYSTEM2_DESIGN.md:926-936]
- 赛道原文："Demonstrate a novel ability to turn data, knowledge, memory, and reasoning into reliable decisions and actions."[来源: docs/HACKATHON_RULES.md:41-44]
- 赛道编号：2026-09-28 快照中为 TRACK 04，2026-10-11 页面中为 TRACK 03。[来源: docs/HACKATHON_RULES.md:13-14]
- 构建窗口：2026-10-22 00:00 UTC 至 2026-10-27 23:45 UTC；P3 与 H1 文档里的 10-15/10-20 日期已由 Addendum 03 §1 作废。[来源: docs/HACKATHON_RULES.md:145; docs/P3_PREREG_ADDENDUM_03.md:11-19]
- `docs/HACKATHON_RULES.md` 是 2026-10-11T07:08:28Z 的快照，内含新旧两版规则。[来源: docs/HACKATHON_RULES.md:2]
- 评分权重（新版页面）：Impact 30, Technical 20, Innovation 15, Demo 15, Product & UX 10, Sponsor tech 10；新版页面上"30 bonus points"为 NOT FOUND ON PAGE，旧版快照有最高 30 分加分项。[来源: docs/HACKATHON_RULES.md:17, 175] [v2 更新]
- Rule 5.1 旧版："Any language, framework, model or cloud, including closed-source APIs and sponsor credits."；新版："Every submission must integrate Zetaris and Meterless, and teams must use Cursor for development."[来源: docs/HACKATHON_RULES.md:19]
- Rule 6.1 新版：1–4 分钟演示视频，展示主流程、agent 如何解决所选挑战、关键功能、Zetaris 与 Meterless 如何集成；Rule 6.2 新版：幻灯片，覆盖问题与目标用户、解决方案、agent 工作流或架构、技术栈、Zetaris 与 Meterless 如何使用、使用赞助技术的独特之处、产品画面、未来改进；Rule 6.3 新版：含全部源码与 README（setup、usage、dependencies）的 GitHub 仓库。[来源: docs/HACKATHON_RULES.md:21-23] [v2 更新]
- Rule 6.4 新版要求说明：Zetaris 与 Meterless 如何集成、Cursor 如何使用、NVIDIA 技术贡献在哪里、对赞助技术的使用有何独特之处；旧版此条为 NOT FOUND ON PAGE。[来源: docs/HACKATHON_RULES.md:24]
- 所有者记录：2026-10-22 主办方宣布 Cursor 改为可选。该公告不在仓库中，其真实状态未知。[来源: 所有者任务说明（非仓库文件）] [UNKNOWN: 公告原文与适用范围；仓库中无依据]
- 因此本草稿对 Cursor 的处理见第 7 节：不假设"必须"或"可选"任一版本成立。[来源: docs/HACKATHON_RULES.md:19 与上条所有者记录并存]

## 2. 问题与方法

- 起点是 RRA V0：一个确定性的快速层基线，在受限工作包络内修正已知残差模式，对不可行修正显式跳过，超出策略边界时升级（escalate）。[来源: docs/P3_SYSTEM2_DESIGN.md:15]
- 提出的问题：当快速层声明"超出授权工作包络"时，System-2 推理器能否通过提出可证伪的世界模型假设、以结构化与非结构化证据为依据、通过确定性反事实验证，来获得有界的恢复权限，并在证据不足时拒绝行动。[来源: docs/P3_SYSTEM2_DESIGN.md:17-19]
- 设计原则："LLM proposes; deterministic evidence disposes; authorization is explicit."；LLM 不直接控制执行器，也不接收仿真器真值。[来源: docs/P3_SYSTEM2_DESIGN.md:28, 172-174]
- 结构、参数估计、验证、授权四件事被分离：LLM 只提出模型结构，参数由确定性拟合器估计。[来源: docs/P3_SYSTEM2_DESIGN.md:21-28; 另见 H2 一节约 100-102 行]
- 注册的可恢复结构空间为 14 个：4 个单原语 + 6 个二元组合 + 4 个三元组合；四个 DSL 原语为 `SENSOR_BIAS`、`VELOCITY_OFFSET`、`SPEED_STEP`、`ACTUATOR_DELAY`。[来源: docs/P3_SYSTEM2_DESIGN.md:104-106; docs/H1_EVAL_FOUNDATION.md:25 起 "Registered world" 一节]
- 预注册假设 H1–H6 已写入设计文档；其中 H1 写明"System-2 预期不会在仅含可恢复场景的 V0 上击败 B2"，H6 写明 LLM 必要性是可证伪的主张，且否定结果必须报告。[来源: docs/P3_SYSTEM2_DESIGN.md:85-128]
- 基线族：B1（V0 策略在修正后的 v3 框架上）、B2（宽边界静态策略）、B3（穷举经典 DSL 搜索 + 拟合 + 验证，无人为预算上限）、B4-strict、B4-tiebreak。[来源: docs/P3_SYSTEM2_DESIGN.md:631-700]
- 歧义门（common-action / ambiguity gate）：若 `|V|≥2` 且不存在公共安全动作，则判为 AMBIGUOUS，验证并未选出动作；B4-strict 此时 `PAUSE_AND_REOBSERVE`，B4-tiebreak 允许文本在验证通过的假设间择一，但仍须通过授权门。[来源: docs/P3_SYSTEM2_DESIGN.md:399-432]
- 动作集保持很小：`UPDATE_MODEL_AND_REPLAN`、`PAUSE_AND_REOBSERVE`、`HUMAN_ESCALATION`。[来源: docs/P3_SYSTEM2_DESIGN.md:461-475]
- 失败解释已预先登记：若 B2 或穷举 B3 与 B4 在注册指标上持平，则"本基准不能证明增加推理复杂度的必要性"，且该结论必须被报告。[来源: docs/P3_SYSTEM2_DESIGN.md:873-896]
- B4-strict 与 B3 决策结果相等是按构造成立的；"穷举 B3 与两个 B4 变体匹配"的检验以 B4-tiebreak 判定。[来源: docs/P3_PREREG_ADDENDUM_04.md:27] [v2 更新]
- 成功标准与评估结果：**待 eval-v3，尚无结果**。[来源: docs/P3_PREREG_ADDENDUM_04.md:7; docs/EVAL_PROTOCOL.md:19]

## 3. 架构与代码布局

### 3.1 逻辑架构

- 快速层（System-1）→ 在 `ESCALATE` / `correction_infeasible` / outcome escalation 时交出证据包（Evidence Packet）→ LLM 假设生成器 → 确定性 DSL 拟合器 → 反事实验证器 → 授权门 → 确定性动作执行器 → 控制器硬约束 → 证据回执（receipt）。[来源: docs/P3_SYSTEM2_DESIGN.md:130-170]
- 输入隔离：System-2 只能使用可观测证据（残差历史、观测位置/时间戳、命令与终态结果、分类器历史、回合内假设状态、维护日志、MES 事件、交班记录、操作员已知配置）；真值、场景名、未来轨迹、隐藏故障状态等被禁止。[来源: docs/P3_SYSTEM2_DESIGN.md:176-203]
- 策略可见字段由 `src/rra/evidence/policy.py` 作为唯一结构化净化器限定。[来源: docs/H1_EVAL_FOUNDATION.md "Policy information boundary" 一节]
- 回合内记忆是显式结构化状态，不是向量库；不要求跨回合学习。[来源: docs/P3_SYSTEM2_DESIGN.md:478-494]
- 快速层内不发生赞助方基础设施调用；调用只发生在升级之后、仿真器冻结期间。[来源: docs/P3_PREREG_ADDENDUM_03.md:41-43]

### 3.2 代码模块（按合并状态分列）

| 模块 | 位置 | 状态 |
|---|---|---|
| System-2 确定性核心（DSL、拟合器、验证器、授权、B3） | `src/rra/s2/*` | **[main]** [来源: `git ls-tree main` src/rra/s2/; decisions.md:33-34] |
| NIM 提供者、重放缓存、假设提议器 | `src/rra/llm/{providers,adapter}.py` | **[main]** [来源: src/rra/llm/providers.py:1-14; decisions.md:28-32] |
| v3 上下文族（六个模板族） | `src/rra/eval/context_v3.py` | **[main]** [来源: decisions.md:28] |
| Zetaris 客户端与两源证据包路径 | `src/rra/sponsor/zetaris.py`, `scripts/l3_*` | **[main]**（PR #18，合并提交 d54faa7） [来源: git log: 92dac5a, d54faa7] |
| Meterless 持久化与重放桥 | `src/rra/sponsor/meterless.py`, `bridges/meterless/*`, `scripts/l6_persist_and_replay.py` | **[main]**（PR #17，合并提交 90054ca） [来源: git log: 8eb7492, 90054ca] |
| `s2-b3-dev` 命令 | `src/rra/cli.py` | **[main]** [来源: src/rra/cli.py:132-133] |
| B4-strict / B4-tiebreak 回合行为、`s2-b4-dev` 运行器、`src/rra/eval/b4_dev.py`、`scripts/l6_b4_meterless_replay.py`、`tests/test_b4_episode.py`、`artifacts/s2/b4-dev.json` | 见左 | **[main]**（PR #20，提交 92e2b89、c852566，合并提交 9fe1730） [来源: `git log --format='%h %s' pre-window-freeze..main`；`git diff --stat 54f5006 main`；src/rra/cli.py:134-138, 157-162] [v2 更新] |
| 386 条 `artifacts/llm_cache/*.json` | `artifacts/llm_cache/` | **[main]** [来源: `ls artifacts/llm_cache \| wc -l` = 386] [v2 更新] |
| `s2-b4-dev` 的 `--nproc`、`--subset`（"registered L1g 33-seed subset"）、`--replay`（"run offline from artifacts/llm_cache"）选项 | `src/rra/cli.py` | **[main]** [来源: src/rra/cli.py:136-138] [v2 更新] |
| Addendum 05 的实现提交（见第 3A 节） | `src/rra/evidence/episode.py`、`src/rra/llm/adapter.py`、`src/rra/s2/fitter.py`、`src/rra/runtime.py` 等 | **[FRZ-1 未合并]** [来源: `git diff --stat main origin/feat/frz1-b3core`] [v2 更新] |
| Python 3.12 运行时（CI、Dockerfile、`rra` 启动器、README） | `.github/workflows/ci.yml`、`Dockerfile`、`rra`、`README*.md` | **[main]**（PR #22，提交 745f8a8，合并提交 612b06e） [来源: `git show --stat 745f8a8`；decisions.md:16] [v2 更新] |

- main 上 `artifacts/sponsor/meterless-persistence.json` 的汇总里 B4 一项现为记录字符串 `"PASS: B4_TIEBREAK meterless off/on decisions 20/20, receipt hashes 20/20"`；T2 草稿时为 "DEFERRED: L5/D4"。以上为文件记录值，本草稿未重跑。[来源: artifacts/sponsor/meterless-persistence.json:635, 650-660] [v2 更新]
- main 上 `artifacts/llm_cache/` 现为 386 个文件（T2 草稿时 main 上为 2 个）。[来源: `ls artifacts/llm_cache \| wc -l`] [v2 更新]
- main 上 `artifacts/s2/b4-dev.json`：schema `rra.s2.b4-dev.v1`，`subset: true`，`episode_count: 33`，4 个文本变体，`llm_calls: 376`，运行时 Python 3.12.3 / NumPy 2.5.4。仅转述元数据，不引用其指标。[来源: artifacts/s2/b4-dev.json 顶层字段] [v2 更新]

## 3A. Addendum 05 与实现状态

本节只陈述 Addendum 05 的条款及 `feat/frz1-b3core` 上与之对应的提交，不陈述任何效果。[来源: 任务约束] [v2 更新]

- Addendum 05：日期 2026-10-24，"BUILD-WINDOW PROTOCOL AMENDMENT / PRE-REGISTRATION BEFORE EVAL-V3 GENERATION / NOT A RESULT"；提交 `a7dfa14`、`cabff0a`，合并提交 `520b7cf` **[main]**。[来源: docs/P3_PREREG_ADDENDUM_05.md:1-5; `git log`] [v2 更新]
- 触发背景（原文转述）：两项只读诊断指出三个问题——`PAUSE_AND_REOBSERVE` 之后实现并未主动重观测；replay 模式下缓存缺失被转为 proposal error 并静默回退而进程退出码仍为 0；另一台机器上同 Python/NumPy 版本时 130 个 per-seed B3 回执哈希中 115 个不同（指标与所查决策相同；原因为末位浮点差异与拟合网格平局翻转）。该补遗不由任何 eval-v3 结果触发。[来源: docs/P3_PREREG_ADDENDUM_05.md:7] [v2 更新]
- 补遗声明不移动或改写 `p3-prereg`，不改动 P3 设计文档与 Addendum 01–04。[来源: docs/P3_PREREG_ADDENDUM_05.md:9] [v2 更新]

| Addendum 05 条款 | 条款内容（转述） | FRZ-1 未合并分支上的对应提交（按提交主题） | 状态 |
|---|---|---|---|
| §1.1–1.5 重观测保持 | 快速层升级且 System-2 决策为 PAUSE_AND_REOBSERVE 时，目标进入保持而非当步记为 escalated；保持期内不发快速层命令；首次 ≥ 上次评估后 0.5 s 的观测处重新评估；以 `;REOBSERVE_EXHAUSTED` 结束的条件；B3、B4-strict、B4-tiebreak 同样适用，B1、B2 不变 [来源: docs/P3_PREREG_ADDENDUM_05.md:11-23] | `56f36b0` "Reobserve paused targets before terminal escalation"；`e942024` "Fix S2 reobserve hold termination"；测试 `tests/test_frz1_reobserve.py`。`71ce80d` "Latch hard faults when evidence windows are empty" 使空 fault 窗口时也 latch，是 Addendum 05 未列出的行为改动，不是 §1.4 的实现提交；§1.4 的 latch 终止由 `episode.py:533-535, 589-593` 实现，测试 `test_hard_fault_latch_ends_an_existing_reobserve_hold` [来源: T4 §1 表 §1.4、§1.6] | [FRZ-1 未合并]；T4：§1.1、§1.2、§1.5 已实现（§1.1 入口为窄读法，**R1** 已由所有者 2026-10-24 裁决）；§1.3 已实现，"充分条件"读法按 **R2** 维持现状；§1.4 部分（窗口终点用名义计划；6 次已有终态后再次进入保持；target_switch、episode_end、s2_non_pause 无测试） [v3 更新] |
| §2 参数网格平局 | 目标值在 `1e-12 × max(1, |minimum|)` 内视为平局，取平局中最小的网格值 [来源: docs/P3_PREREG_ADDENDUM_05.md:25-27] | `67bc419` "Choose the lowest grid point for near-tied fits"（改动 `src/rra/s2/fitter.py`，测试 `tests/test_s2.py`） | [FRZ-1 未合并]；T4 §1：已实现（`fitter.py:61-69`），一维 speed-step 平局有测试，actuator-delay 一维与 (tau, delay) 二维平局无测试 [v3 更新] |
| §3.1 replay 缓存缺失 | 评分用 B4 工件在 replay 模式生成时，缓存缺失以非零退出中止，不作 proposal 回退 [来源: docs/P3_PREREG_ADDENDUM_05.md:31] | `244b670` "Propagate replay cache misses from the adapter"（改动 `src/rra/llm/adapter.py`，测试 `tests/test_llm_adapter.py`） | [FRZ-1 未合并]；T4 §1：已实现（`adapter.py:108-109`、`b4_dev.py:46-48`），只有适配器层测试，无 `rra s2-b4-dev --replay` 端到端退出码测试；T4 §5 的 CLI 实测：首次缓存缺失时退出码 1，输出目录无文件 [v3 更新] |
| §3.2 无生成器 | 无假设生成器运行 B4 变体是配置错误并中止 [来源: docs/P3_PREREG_ADDENDUM_05.md:33] | `7ca3268` "Reject B4 episodes without a proposer"；`6d0b205` "Remove the unreachable missing-proposer fallback" | [FRZ-1 未合并]；T4 §1：已实现（`episode.py:132-133`，测试 `test_b4_episode.py:135`；`6d0b205` 删除了 `NO_PROPOSER` 回退） [v3 更新] |
| §3.3 `llm_calls` 计数口径 | 按（seed, 文本变体）在两个 B4 变体合计计数，并另报各变体提议器调用 [来源: docs/P3_PREREG_ADDENDUM_05.md:35] | FRZ-1 的 12 个提交均未触及此部分。共享 `_MemoizedProposer`，汇总表里 `llm_calls` 只记在 `B4_STRICT`，`B4_TIEBREAK` 记 0（`b4_dev.py:120-121`）；"另行分开报告"没有显式字段，只能从逐行 `B4_*_proposal_rank` 列表长度推出；已提交的 `b4-dev.json` 未在 FRZ-1 上重新生成 [来源: T4 §1 表 §3.3、§7-7] | 部分；未显式分列 [v3 更新] |
| §3.4 浮点序列化 | B4 请求中浮点数四舍五入到 6 位小数 [来源: docs/P3_PREREG_ADDENDUM_05.md:37] | 在 FRZ-1 头上未找到：证据包放原始浮点（`episode.py:692-705`），`adapter.py:79-82` 直接 `json.dumps`，`src/rra/llm/`、`src/rra/eval/context_v3.py` 中没有 `round(` [来源: T4 §1 表 §3.4] | 未实现于 FRZ-1；**R5** 已由所有者 2026-10-24 裁决：§3.4 由所有者在本地实现，B4 缓存将在注册 runner 上 live 重建（本草稿未见该实现）。实现后的效果：**待 eval-v3，尚无结果** [v3 更新] |
| §4.1 平台记录 | 回执在被哈希内容之外记录 Python、NumPy 版本、机器架构、CPU 型号、BLAS 库 [来源: docs/P3_PREREG_ADDENDUM_05.md:41] | `154522b` "Record runtime platform details in evaluation artifacts"（新增 `src/rra/runtime.py`） | [FRZ-1 未合并]；T4 §1：记录部分已实现（`src/rra/runtime.py:10-32`，从哈希内容排除），BLAS 取自 NumPy 构建配置而非运行时加载的库，CPU 型号只从 `/proc/cpuinfo` 读；b3_dev/b4_dev 层的哈希排除无测试。注册 runner 按 **R4**（所有者 2026-10-24 裁决）为所有者本地机器：Intel i7-10750H，Python 3.12.3，NumPy 2.5.4，scipy-openblas 0.3.34 [v3 更新] |
| §4.2–4.3 确定性范围 | 不声称跨机器逐位一致；eval-v3 所有工件在同一 runner 生成并报告其平台 [来源: docs/P3_PREREG_ADDENDUM_05.md:43-45] | §4.2 是流程条款，T4 §3 按此执行（同机两次运行 0/130 个 B3 哈希不同；对已提交工件 115/130 不同，dev，非注册结果）；§4.3 在代码层面未找到 eval-v3 生成路径 [来源: T4 §1 表 §4.2、§4.3；§3] | eval-v3：**待 eval-v3，尚无结果** [v3 更新] |

- FRZ-1 分支上不属于 Addendum 05 条款的其他提交：`afa2aa6` "Resolve L3 base git SHA at runtime"（改动 `scripts/l3_equivalence.py`）；`aa3dd1c`、`7e2c4a7`、`cb77107` 三次刷新 `artifacts/s2/b3-dev.*` 与 `artifacts/sponsor/meterless-persistence.json`（提交主题分别为 "Refresh FRZ-1 B3 development artifacts"、"Refresh FRZ-1 artifacts after final code review"、"Refresh B3 artifacts after reobserve fix"）。[来源: `git log main..origin/feat/frz1-b3core`; `git diff --stat main origin/feat/frz1-b3core`] [v2 更新]
- 分支相对 main 的差异中，`docs/P3_PREREG_ADDENDUM_05.md` 显示为被删除，原因是该分支从 `9fe1730`（早于 Addendum 05 合并）分出；这是分支基线造成的，不是该分支删除了补遗。[来源: `git merge-base`；`git diff --stat main origin/feat/frz1-b3core` → docs/P3_PREREG_ADDENDUM_05.md 54 行删除；`git show origin/feat/frz1-b3core:docs/P3_PREREG_ADDENDUM_05.md` 不存在] [v2 更新]
- main 上现状：`src/rra/evidence/episode.py:625-628` 仅在新的升级上升沿或尚未尝试过的不可行状态时调用 System-2，`:832-834` 把 `system2_next_retry` 设为 `observation.time+0.5`，`:835-842` 同步把目标记为 `escalated`——这是 Addendum 05 §1 触发背景所引用的行为。[来源: src/rra/evidence/episode.py:625-628, 832-842; docs/P3_PREREG_ADDENDUM_05.md:7] [v2 更新]
- main 上 `src/rra/llm/adapter.py:106` 仍捕获 `OSError`（含 `ReplayCacheMiss`）并返回带 error 的空 Proposal。[来源: src/rra/llm/adapter.py:106; src/rra/llm/providers.py:51] [v2 更新]
- Addendum 05 §5 新增的停止条件（实现缺陷，非结果）：保持期目标未按 §1.2 重评估；回合结束时目标无终态；replay 模式生成的评分 B4 工件含缓存缺失回退；B4 运行无生成器。[来源: docs/P3_PREREG_ADDENDUM_05.md:47-53] [v2 更新]
- 合并 FRZ-1 与否、合并后哪些工件需重生成：[所有者裁决]（见第 10 节第 15 项）。[来源: 本清单项] [v2 更新]
- 所有者 2026-10-24 裁决（已定）在本节条款上的落点：R1——§1.1 保持入口取窄读法，只有快速层 ESCALATE 路径上的 PAUSE 进入保持（FRZ-1 现状）；R2——§1.3 维持 FRZ-1 现状、不改代码，88/5（保持对象被授权后解除了保持前已有的 `safe_stop`，结局 miss）在提交材料中披露；R4——注册 runner 为所有者本地机器；R5——§3.4 由所有者本地实现。[来源: 所有者裁决 2026-10-24；T4 §7-1、§7-2、§7-9、§7-6] [v3 更新]
- T4 §1.1 列出的无测试分支：保持中目标被授权的路径；`s2_non_pause` 结束；`target_switch` 与 `episode_end` 结束；同一步内 `window_end` 结束后再次进入保持；B4 下的保持；§2 的 actuator-delay 一维/二维平局；§3.1 端到端非零退出；§4.1 b3_dev/b4_dev 哈希排除；latch 在 `presence` 路径上结束保持。[来源: T4 §1.1] [v3 更新]

## 4. Zetaris 与 Meterless 如何集成

### 4.1 预注册的角色与边界

- 预注册声明：不预先登记"Zetaris 或 Meterless 改善任何注册指标"的主张；其角色是部署数据访问、治理、可审计的持久化与重放。任何此类主张需要在 eval-v3 生成前另立带日期的修订。[来源: docs/P3_PREREG_ADDENDUM_02.md:50]
- 评估模式披露：所有注册评估（eval v3）与基线 B1–B4 使用本地参考加载器；Zetaris 路径用于演示和等价回执，不用于注册评估。提交材料必须披露该评估模式。[来源: docs/P3_PREREG_ADDENDUM_03.md:49-51, 59-61; docs/P3_PREREG_ADDENDUM_02.md:83-87]

### 4.2 Zetaris — 证据数据平面 [main]

- 设计角色：System-2 证据包由两个分离的数据源通过 Zetaris 联邦查询装配：S-TELEMETRY（观测、在场事件、命令反馈）与 S-OPS（MES/设备事件、工单、交班记录、已知配置）。[来源: docs/P3_PREREG_ADDENDUM_02.md:58-67]
- 治理作为结构性泄漏控制：只有 C1 白名单字段与 P3 §12 上下文记录可写入 Zetaris 可达的数据源；静态检查枚举每个源的每一列，白名单外字段即失败。[来源: docs/P3_PREREG_ADDENDUM_02.md:69-73]
- 等价不变量：Zetaris 装配的证据包与本地参考加载器装配的证据包，其规范 JSON 的 SHA-256 在等价集上必须相等；等价集为 20 个 dev 回合，仅用 dev 种子。[来源: docs/P3_PREREG_ADDENDUM_02.md:75-81]
- 已提交的回执（记录值，原样转述）：`T5: "PASS"`，20 个回合，`T1_schema_extra` 各表均为空，`T3_anchor_mismatches: 0`，`T4_mismatches: 0`，`T8_reference_receipt_bytes_identical: true`，`base_git_sha: 2a3b52dcf15cf352064f064e2a8b499c4fe06280`，记录环境 Python 3.12.3。[来源: artifacts/sponsor/zetaris-equivalence.json:14, 17, 225（main）] [v2 更新: 行号已按 main 当前文件核对；内容与 T2 一致]
- 白名单回执：`extra_count: 0`，schema `rra.l3.whitelist.v1`。[来源: artifacts/sponsor/zetaris-whitelist.json（main）]
- 联邦查询示例：一条跨 `RRA_L3_TELEMETRY` 与 `RRA_L3_OPS` 的 JOIN，`federation_rows: 1`。[来源: artifacts/sponsor/zetaris-equivalence.json（main）字段 federation_sql, federation_rows]
- 客户端：标准库 REST 客户端，调用 `POST {base}/sql-editor/sqls/run`，令牌从环境变量 `ZETARIS_TOKEN` 读取，错误信息中令牌被替换为 `[REDACTED]`。[来源: src/rra/sponsor/zetaris.py:19-35]
- `scripts/l3_equivalence.py` 在 FRZ-1 分支上有改动（提交 `afa2aa6` "Resolve L3 base git SHA at runtime"）；main 上回执中的 `base_git_sha` 为上述固定值。[来源: `git show --stat afa2aa6`; artifacts/sponsor/zetaris-equivalence.json:17] **[FRZ-1 未合并]** [v2 更新]
- 本草稿未运行任何 Zetaris 实时调用，上述数字均为仓库已提交的记录值。[来源: 任务约束]
- 访问路径（赛前探针）：自管本地部署（Docker Compose 包），API 令牌到期日 2026-11-17。[来源: docs/SPIKE_NOTES_20261019.md:6, 12]
- 在场的 Docker 镜像不含 Zetaris/Meterless 路径：`Dockerfile` 仅复制 `requirements.txt`、`src`、`config` 与 `rra` 启动器，不含 `bridges/`、`scripts/`、`artifacts/`。[来源: Dockerfile:4-8] [v2 更新: 基础镜像现为 `python:3.12-slim`（Dockerfile:1），复制范围不变]

### 4.3 Meterless — 推理运行持久化与重放 [main]

- 设计角色：每次 System-2 决策运行（证据引用 → 提议假设 → 拟合 → 验证结果 → 歧义门 → 授权或处置）持久化为 Meterless 管理的记录，用于检视推理轨迹、回放，以及演示证据链。[来源: docs/P3_PREREG_ADDENDUM_02.md:95-101]
- 记忆范围：回合内；注册运行中 Meterless 对其他回合只写不读，并有检查断言策略读取不触及 `episode_id` 不同的记录。[来源: docs/P3_PREREG_ADDENDUM_02.md:103-107]
- 决策不变性：持久化不得改变决策；在等价集上，持久化开/关须在相同的录制 LLM 响应下给出相同的 B4 决策。[来源: docs/P3_PREREG_ADDENDUM_02.md:113-115]
- 实现：Python 通过 stdin/stdout JSON 行与 `bridge.ts` 通信；桥导入固定版本的 Meterless H-MEM 参考实现，在 `tsx` 下运行；Meterless 提交固定为 `1742dec56a66e58eef9dda2d2b865823758ca8cd`；映射为 `source="rra.s2"`，`chatId=episode_id`。[来源: bridges/meterless/README.md:1-30]
- 持久化是在 `run_episode` 返回之后运行的包装，不触碰回合本身；评估者真值键在存储前被剥除。[来源: src/rra/sponsor/meterless.py:1-5, 21-24]
- main 上已提交的回执（记录值，原样转述）：20 个回合，`M1_roundtrip_mismatches: 0`，`M2_production_decisions_equal: 20`，`M3_cross_episode_reads: 0`，`M3_negative_refused: 20`，`M4_replay_match: 20`，`M5_identical: 20`，`M8_hidden_key_hits: 0`，`all_ok: true`。[来源: artifacts/sponsor/meterless-persistence.json summary（main）]
- **[main]** B4 持久化验证（PR #20 并入）：回执 `B4` 块记录 `status: "PASS"`、`provider: "ReplayProvider"`、`cache_dir: "artifacts/llm_cache"`、`s2_variant: "B4_TIEBREAK"`、`text_variant: "NO_TEXT_CONTEXT"`、`seed_source: "artifacts/s2/diag-d1g.json:first-20"`、`episode_count: 20`、`decisions_equal: 20`、`receipt_equal: 20`、`live_llm_calls: 0`；对应脚本 `scripts/l6_b4_meterless_replay.py`。以上为文件记录值，本草稿未重跑，也未在本机核对该脚本的输出。[来源: artifacts/sponsor/meterless-persistence.json:635, 650-660; scripts/l6_b4_meterless_replay.py:1] [v2 更新]
- 该 B4 回执仅覆盖 `NO_TEXT_CONTEXT` 变体的 20 个 dev 回合，使用重放缓存。其他文本变体上是否同样记录：[UNKNOWN]（未在该 JSON 块中见到）。[来源: artifacts/sponsor/meterless-persistence.json:650-660] [v2 更新]
- `artifacts/sponsor/meterless-persistence.json` 在 FRZ-1 分支上被三次刷新（`aa3dd1c`、`7e2c4a7`、`cb77107`），main 上的记录值与分支上的不同；本草稿不比较二者。[来源: `git diff --stat main origin/feat/frz1-b3core`] **[FRZ-1 未合并]** [v2 更新]
- 赛前探针对 Meterless 的记录：开源路径 GO；参考实现为 TypeScript，RRA 为 Python，需要宿主侧适配器；检索看起来是词法/确定性的，不适合作为 RRA 的核心检索。[来源: docs/SPIKE_NOTES_20261019.md:22-30]

### 4.4 主办方对集成深度的期望（原样列出，未假设已解决）

- [UNKNOWN] Which Meterless component the organizers mean and what minimum "integration" they expect; to be asked at the 2026-10-21 onboarding call. [来源: docs/SPIKE_NOTES_20261019.md:33]
- [UNKNOWN] 2026-10-21 onboarding call 是否发生、结论为何：仓库中无记录。[来源: 全仓库检索无此记录；docs/SPIKE_NOTES_20261019.md:33 仅有计划]
- [UNKNOWN] Registering a local Postgres container as a source; the JDBC path (port 10000 is exposed); the §4.3 SHA-256 equivalence against the reference loader; throughput and latency; any hackathon-specific limits.（这是赛前探针的原文；后续的 `artifacts/sponsor/zetaris-equivalence.json` 含有 Postgres 注册语句与等价回执，但探针文档本身未更新，且"主办方限制"一项无任何记录。）[来源: docs/SPIKE_NOTES_20261019.md:13; artifacts/sponsor/zetaris-equivalence.json（main）字段 registration_sql]
- [UNKNOWN] The per-minute and daily rate limits (NVIDIA). [来源: docs/SPIKE_NOTES_20261019.md:20]
- [NOT VERIFIED] The H-MEM conformance suite (engines/hmem), the World Model and Markovian engines, the Gaia/Relay/Swarms Windows apps, Nightshift. Scout Intent is spec-only per its README. [来源: docs/SPIKE_NOTES_20261019.md:32]
- [UNKNOWN] 主办方是否将"参考实现 + 宿主侧桥"视为满足 Rule 5.1 的集成：仓库中无依据。[来源: docs/SPIKE_NOTES_20261019.md:33; docs/P3_PREREG_ADDENDUM_02.md:117-119]
- 以上各项仍悬而未决；本草稿不对它们作任何假设。[来源: docs/SPIKE_NOTES_20261019.md:35-36 "No integration design is decided here"]

## 5. NVIDIA 技术用在哪里

- 位置：NVIDIA NIM / Nemotron 是 B4 假设生成器的提供者，位于可替换适配器之后；NVIDIA 组件不用于参数拟合、验证、歧义门或授权。[来源: docs/P3_PREREG_ADDENDUM_02.md:121-125]
- Rule 5.2 使 NVIDIA 成为可选项；设计文档保留它是因为它是 B4 的 LLM。[来源: docs/P3_PREREG_ADDENDUM_02.md:123; docs/HACKATHON_RULES.md:155]
- 实现 [main]：兼容 OpenAI 接口的 NIM 客户端，端点 `https://integrate.api.nvidia.com/v1`，代码常量模型 `nvidia/nemotron-3.5-super-vl-120b-a12b`，密钥从环境变量 `NVIDIA_API_KEY` 读取，请求按规范 JSON 的 SHA-256 做内容寻址缓存，重放提供者只读。[来源: src/rra/llm/providers.py:13-14, 51-60, 76-84]
- 默认关闭思考模式（`chat_template_kwargs={"enable_thinking": false}`），并纳入规范化请求与缓存键；决策记录写明服务端返回的模型名为 `private/nvidia/nemotron-3.5-super-120b-a12b`，与代码常量 `nvidia/nemotron-3.5-super-vl-120b-a12b` 不同。[来源: decisions.md:32; src/rra/llm/providers.py:14, 34, 58] [UNKNOWN: 两个名称之间的关系，仓库无说明] [v2 更新: decisions.md 行号随 PR #22 新增一行后下移一行]
- 提议器只接受可观测证据包和上下文文本，用 Pydantic 校验输出，忽略数值参数并记录未知 ID。[来源: decisions.md:29]
- B4 调用策略（Addendum 04 §1.1）：仅当共享 B3 评估在该决策点无故障证据且歧义门结果为 AMBIGUOUS 时才调用生成器，其余决策点不调用 LLM。[来源: docs/P3_PREREG_ADDENDUM_04.md:13]
- LLM 输出不触发或清除故障锁存，不用于参数拟合、验证、歧义门或授权。[来源: docs/P3_PREREG_ADDENDUM_04.md:19]
- **[main]** B4 的运行代码（`s2-b4-dev`、两种 B4 回合行为）：`src/rra/cli.py:134-138, 157-162`；`src/rra/eval/b4_dev.py` 中读穿提供者 `_ReadThroughProvider` 在非 `replay_only` 时构造 `NvidiaNimProvider`，`replay_only` 时仅 `ReplayProvider`。[来源: src/rra/cli.py:134-138, 157-162; src/rra/eval/b4_dev.py:28-32, 216] [v2 更新]
- B4 在 replay 模式下缓存缺失的处理：main 上 `ReplayCacheMiss` 在适配器被捕获为 proposal error（见第 3A 节）；Addendum 05 §3.1 要求评分工件在 replay 生成时缺失即中止，对应实现在 **[FRZ-1 未合并]**。[来源: src/rra/llm/adapter.py:106; docs/P3_PREREG_ADDENDUM_05.md:31; 提交 244b670] [v2 更新]
- NVIDIA 对注册指标的贡献：**待 eval-v3，尚无结果**。[来源: docs/P3_PREREG_ADDENDUM_04.md:7]
- 赛前探针记录：20 个并行请求均返回 HTTP 200；小 `max_tokens` 时可见内容可能为空，`max_tokens=1500` 返回了内容。[来源: docs/SPIKE_NOTES_20261019.md:17-18]

## 6. 可复现步骤

以下只列仓库文档已有的命令；本草稿未执行任何会访问 Zetaris、Meterless 或 NVIDIA 的实时调用，也未使用任何密钥。[来源: 任务约束]

### 6.1 V0 与评估框架（无外部服务）[main]

- 需要 Python 3.12；`python3.12 -m venv .venv`，`.venv/bin/pip install -r requirements.txt`。`rra` 启动器在 Python 版本不是 3.12 时退出并提示 "RRA requires Python 3.12"。[来源: README.md:21-25; rra:7-8（`git diff 54f5006 main -- rra`）; Dockerfile:1; .github/workflows/ci.yml:17] [v2 更新]
- 运行单回合：`.venv/bin/python ./rra run --scenario bias --seed 7 --compensation on`。[来源: README.md:26]
- dev 冒烟基准：`RRA_SEED_FILE=config/dev_seeds.json .venv/bin/python ./rra bench`。[来源: README.md:37-39]
- Docker：`docker build -t reality-residual-agent .`，然后 `docker run --rm -e RRA_SEED_FILE=/app/config/dev_seeds.json reality-residual-agent rra bench`。[来源: README.md:44-45]
- 不带 `RRA_SEED_FILE` 的 `rra bench` 默认读取冻结的 eval v2 种子 2000–2099，而该集合已按协议"使用一次"；复现请使用 dev 种子。[来源: README.md:33; docs/EVAL_PROTOCOL.md:18]
- System-2 B3 dev 对照：`rra s2-b3-dev`，仅读取 dev 种子，默认输出到 `artifacts/s2`。[来源: src/rra/cli.py:132-133, 152-155; decisions.md:34]
- 依赖：`numpy==2.5.4`、`pydantic>=2.6,<3`、`pytest>=8,<9`。[来源: requirements.txt:1-3]
- FRZ-1 头 `cb771079c1c119d73d0ebd0e24704a1935731cea` 上全量 pytest（云 VM，Python 3.12.3 venv，命令 `python -m pytest -q -rfEs`，已取消 `NVIDIA_API_KEY`/`ZETARIS_TOKEN`）：200 passed，4 skipped，0 failed；4 个 skipped 为 Meterless live（3 个，需 `RRA_METERLESS_LIVE=1`）和 Zetaris live（1 个，opt-in）。[来源: T4 §2] **[FRZ-1 未合并]** [v3 更新]
- main 头上全量 pytest 的计数：[UNKNOWN]（本草稿未运行测试；T1 在 PR #20 head `c852566` 上为 192 passed、4 skipped（T1 §8），该 sha 不是当前 main 头）。[来源: T1 §8] [v3 更新]
- CI 在 `push` 与 `pull_request` 上运行 `pytest -q`，另有一个 `determinism` 作业用 dev 种子两次运行 `rra bench`；两者均固定 Python 3.12.3。该配置存在不代表 CI 当前状态，本草稿未查询 CI 结果。[来源: .github/workflows/ci.yml:1-41] [v2 更新]
- README 中的 "冻结 eval v2 结果" 表是 V0 快速层的赛前结果；README 文末写明"赛中 System-2 层应解决该状态的恢复决策"。[来源: README.md:62-83; HACKATHON_BASELINE.md:66-73] [v2 更新]

### 6.2 Zetaris 路径 [main]（需要外部服务与凭据，由所有者执行）

- 先决条件：自管 Zetaris 本地部署（docker compose 网络 `zetaris_default`）、环境变量 `ZETARIS_TOKEN`。[来源: scripts/l3_zetaris_up.sh:5-6; src/rra/sponsor/zetaris.py:19-21]
- 起源服务与注册：`scripts/l3_zetaris_up.sh` 启动 `rra-l3-pg`（Postgres 16）与 `rra-l3-ops` 两个源容器并注册。[来源: scripts/l3_zetaris_up.sh:7-27]
- 等价检查：`scripts/l3_equivalence.py`；密钥审计：`scripts/l3_secret_audit.py`。[来源: scripts/l3_equivalence.py:1; scripts/l3_secret_audit.py:7]
- 具体参数与输出位置以脚本为准：[UNKNOWN]（本草稿未逐一核对各脚本的命令行参数）。[来源: 本草稿未运行脚本]

### 6.3 Meterless 路径 [main]（需要 Node 22）

- `scripts/setup_meterless.sh`：幂等；克隆 Meterless 到 `bridges/meterless/vendor/Meterless` 并检出 `1742dec56a66e58eef9dda2d2b865823758ca8cd`，运行 `npm ci --ignore-scripts`。[来源: bridges/meterless/README.md:9-15]
- 持久化与重放：`.venv/bin/python scripts/l6_persist_and_replay.py run --run-tag demo --seeds 14`；`trail` 与 `replay` 子命令见同一文件（`--episode ep-014`）。[来源: bridges/meterless/README.md:41-45; scripts/l6_persist_and_replay.py:309-315]
- 实时桥测试：`RRA_METERLESS_LIVE=1 .venv/bin/python -m pytest tests/test_meterless_bridge.py -q`。[来源: bridges/meterless/README.md:46]
- B4 持久化验证脚本：`scripts/l6_b4_meterless_replay.py`（读取重放缓存）；其命令行用法：[UNKNOWN]（本草稿未逐行核对，且 `bridges/meterless/README.md` 未列出该脚本）。[来源: scripts/l6_b4_meterless_replay.py:1; bridges/meterless/README.md] [v2 更新]

### 6.4 NVIDIA 路径 [main]（实时调用需要 `NVIDIA_API_KEY`，由所有者执行）

- 单次实时烟测脚本：`scripts/nemotron_smoke.py`（"One authorized live NIM smoke call with at most two backoff retries"）。[来源: scripts/nemotron_smoke.py:1]
- 注册 B4 结果必须由冻结响应缓存、禁用网络的代码生成；实时运行只用于填充缓存；回执必须可由产物内容按代码规则重算，且两次连续生成的回执须一致。[来源: docs/P3_PREREG_ADDENDUM_04.md:43]
- **[main]** B4 dev 运行：`rra s2-b4-dev [--output-dir DIR] [--nproc N] [--subset] [--replay]`；`--replay` 为 "run offline from artifacts/llm_cache"，此时 `_ReadThroughProvider` 不构造实时提供者；不加 `--replay` 时会构造 `NvidiaNimProvider`，其构造要求 `NVIDIA_API_KEY`，因此由所有者执行。[来源: src/rra/cli.py:134-138, 157-162; src/rra/eval/b4_dev.py:30-32; src/rra/llm/providers.py:82-84] [v2 更新]
- eval-v3 的复现步骤：**待 eval-v3，尚无结果**；种子仅在 H5、实现候选冻结之后、在隔离进程中生成。[来源: docs/EVAL_PROTOCOL.md:19; artifacts/h1/final-eval-v3-prohibition.json:10]

## 7. Cursor 使用方式

[所有者填写]

- 本节不写任何 Cursor 使用情况的描述。[来源: 任务约束]
- 仅供所有者查阅的仓库内现有记录（指路，不构成对使用方式的说明）：`docs/DEV_WORKFLOW.md`、`.cursor/rules/rra.mdc`。[来源: docs/DEV_WORKFLOW.md:1-11; `ls .cursor/rules`] [v2 更新: 文件名按 main 核对]
- 规则状态：新版 Rule 5.1/6.4 要求 Cursor；所有者记录 2026-10-22 起为可选，公告不在仓库中。[来源: docs/HACKATHON_RULES.md:19, 24; 所有者任务说明] [UNKNOWN: 当前以哪一版为准]

## 8. 赛前已有工作 vs 窗口内新工作

### 8.1 界线定义

- `v0-baseline` 为不可变的原始 V0 快照；该标签对象为 `11c45959397f029f5cb9eedfaa498514ec185b74`，指向提交 `546e82aefd4e07bf304d79c63dcffe6dd4b7c4ee`。[来源: HACKATHON_BASELINE.md:5; `git rev-parse v0-baseline v0-baseline^{commit}`]
- `pre-window-freeze` 标签对象为 `7dccc2532e3b248e2e93e274ace0fd659db1745f`，指向提交 `3b56637681551f21c6b4c253be6def59389d1051`（提交时间 2026-10-19 22:38:27 +0800），是 `main` 的祖先。[来源: `git rev-parse pre-window-freeze pre-window-freeze^{commit}`; `git log -1 --format=%ci pre-window-freeze`; `git merge-base --is-ancestor pre-window-freeze main`]
- 声明：从 `pre-window-freeze` 可达的一切均为赛前已有工作；窗口内新工作为 `pre-window-freeze..<提交 sha>` 范围；`v0-baseline` 之后的提交并不全是窗口内工作。[来源: HACKATHON_BASELINE.md:7]
- `p3-prereg` 标签对象 `a7c640b8debbf612490fa216c896b4d1b91a4d77`；`rra-v0-freeze-01` 标签对象 `b5bbaa13976f62ef7b0e8ff73e8327d08228a251`。[来源: `git rev-parse p3-prereg rra-v0-freeze-01`]
- 范围统计：`pre-window-freeze..main` 共 50 个提交，最早为 `b8d884a`（2026-10-22 21:11:38 +0800），最晚为 `520b7cf`（2026-10-24 09:12:21 +0800）。[来源: `git rev-list --count pre-window-freeze..main`; `git log --format='%h %ci %s' pre-window-freeze..main`] [v2 更新: T2 草稿为 42 个提交、最晚 54f5006]
- 窗口起点是 2026-10-22T00:00:00Z；上条范围内各提交时间戳均在 +0800 时区下为 10-22 21:11 之后。[来源: HACKATHON_BASELINE.md:5; `git log --format=%ci pre-window-freeze..main`]
- 本草稿根据 `pre-window-freeze` 的提交时间戳核对了界线的先后，但未核实主办方如何判定资格。[来源: HACKATHON_BASELINE.md:7 "does not by itself establish eligibility or how the organizers will judge"] [UNKNOWN: 主办方的资格判定方式]

### 8.2 赛前已有（声明为 pre-existing）

- V0 组件：种子化 2D 传送带世界、名义抓取规划器、残差监视器与启发式扰动分类器、纠正器（±0.5 s 有界时间修正、可行性检查、固定 fail-closed 残差阈值）、确定性控制器、回合运行器、JSON 回执、同种子开/关基准、dev/eval 工具与盲评协议、CLI、Dockerfile、测试、文档与规则快照。[来源: HACKATHON_BASELINE.md:9-18]
- V0 不含 LLM 集成，也未使用 Zetaris、Meterless 或 NVIDIA；V0 开发未使用 Cursor。[来源: HACKATHON_BASELINE.md:20]
- 赛前基础设施提交（CI 与工具设置，非提交评审内容）：`90821fc55d7581a156c68ec3cadc135738ff4ab6`、`a1287c3386044c4723a68378e870090eca87f032`、`38f8ce139bf90de659a192f4456821dcff0db4a8`。[来源: HACKATHON_BASELINE.md:22-29]
- 赛前 P3 预注册：4 个文档提交，`879dab82ab24344e0ece9a868f0a5466388203b9` 至 `024ea2e3e66b91f5a2157a66c073493e7107e109`。[来源: HACKATHON_BASELINE.md:35-37]
- 赛前 H1 评估基础：18 个提交，`095ea10b3ad3b1a2d7b81c841c7cd7bacfed3f79` 至 `b0288da5cf7a924ce9b47b0ea9f7d6248f5f6bd0`，改动 `src/rra/eval/*`、`src/rra/evidence/*`、`src/rra/sim/*`、`artifacts/h1/`、`config/v3_contracts.json` 及若干文档；声明 H1 改动了运行时/源码实现，不能被描述为仅工具配置。[来源: HACKATHON_BASELINE.md:39-64]
- 赛前 Addendum 01–03 与赛前赞助方探针笔记（`docs/SPIKE_NOTES_20261019.md`）按其自述为赛前预注册/设计输入。[来源: docs/P3_PREREG_ADDENDUM_01.md:3-5; docs/P3_PREREG_ADDENDUM_02.md:3; docs/P3_PREREG_ADDENDUM_03.md:3; docs/SPIKE_NOTES_20261019.md:3]
- V0 的已提交数字（`v0-baseline`，blind eval v2，100 个种子，补偿开）逐字引用如下，属赛前工作，此处不作解读：nominal 成功率 1.000；moving-mid 0.849；load-mid 0.656；combo 0.007。[来源: HACKATHON_BASELINE.md:66-73]

### 8.3 窗口内新工作（`pre-window-freeze..main`）

- System-2 确定性核心与升级交接：`b8d884a`、`ccbefb3`。[来源: `git log pre-window-freeze..main`]
- v3 上下文族、提议器、NIM 重放缓存与烟测运行器：`9ff81e1`、`bb8eb49`、`f65ba5b`。[来源: `git log pre-window-freeze..main`; decisions.md:28-31]
- Cursor 规则与开发流程记录：`cf611a2`（PR #14）。[来源: `git log pre-window-freeze..main`; docs/DEV_WORKFLOW.md:1-11]
- B3 dev 评估命令及后续修复（PR #12、#13、#15、#16）。[来源: `git log pre-window-freeze..main`: 7ea70ce, cbc1f8a, 345b6f9, 198ab6a, 2a3b52d]
- Meterless 持久化/重放桥：`8eb7492`（PR #17，合并 `90054ca`）。[来源: `git log pre-window-freeze..main`]
- Zetaris 两源证据包路径：`92dac5a`（PR #18，合并 `d54faa7`）。[来源: `git log pre-window-freeze..main`]
- L5a 卫生 + 重放键 + 结构 ID：`ab509d3`（PR #19，合并 `2ff7a6b`）。[来源: `git log pre-window-freeze..main`]
- Addendum 04（B4 调用策略登记）：`3319655`（PR #21，合并 `54f5006`）。[来源: `git log pre-window-freeze..main`; docs/P3_PREREG_ADDENDUM_04.md:1-9]
- **[main]** B4-strict/B4-tiebreak、`s2-b4-dev`、LLM 缓存与 B4 Meterless 验证：提交 `92e2b89`、`c852566`，经 PR #20 合并为 `9fe1730`，现处于 `pre-window-freeze..main` 范围内。[来源: `git log pre-window-freeze..main`] [v2 更新]
- **[main]** Python 3.12 运行时：`745f8a8`，PR #22 合并为 `612b06e`。[来源: `git log pre-window-freeze..main`; decisions.md:16] [v2 更新]
- **[main]** Addendum 05：`a7dfa14`、`cabff0a`，PR #23 合并为 `520b7cf`。[来源: `git log pre-window-freeze..main`] [v2 更新]
- **[FRZ-1 未合并]** 分支 `feat/frz1-b3core` 上 12 个提交（`7ca3268` 至 `cb77107`），作者均为 Xifeng Ming，时间 2026-10-24 07:58–09:17 +0800，不属于 `pre-window-freeze..main`。[来源: `git log --format='%h %ci %an %s' main..origin/feat/frz1-b3core`] [v2 更新]
- 修改 `v0-baseline`/赛前文件的窗口内改动（例如 `src/rra/evidence/episode.py`、`src/rra/sim/world.py`）需逐个划分新旧：[UNKNOWN]（本草稿未做逐文件、逐行的新旧划分）。[来源: HACKATHON_BASELINE.md:57, 60]

## 9. 局限与未完成项

### 9.1 已在仓库中书面记录的

- PR #20 已合并（`9fe1730`）。Addendum 04 §5.3 记录：2026-10-23 dev 运行（提交 92e2b89）发送的是缩减版证据包（观测仅含 time/observed_x/nominal_x；反馈仅含 issued_time/execution_time/accepted/success；无在场事件；已知配置仅含 dt 与 tolerance），不符合 Addendum 03 §2 第 4 项，被记为须在实现候选冻结前更正的实现缺陷；该次运行的结果不构成注册证据包下 B4 的证据。T1 §5 逐字段对照，并通过读 `c852566` 的代码确认该时点证据包仍是缩减形式（未检视存储的请求）。该缺陷在 main 与 FRZ-1 上的修复状态：[UNKNOWN，待 T6 核对]。[来源: docs/P3_PREREG_ADDENDUM_04.md:51; T1 §5] [v3 更新]
- 2026-10-23 dev 运行披露：386 条缓存响应中，71 条解析为 `{items:[...]}`，310 条解析为 JSON 但形状不符，5 条因 token 上限停止（4 条截断不可解析，1 条无内容）。[来源: docs/P3_PREREG_ADDENDUM_04.md:47]
- 该次运行中多数 B4-tiebreak 调用以 INVALID_PROPOSAL 回退；B4-tiebreak 与 B4-strict 或 B3 的差异被记录为由格式失败主导，不是文本上下文效应的证据。[来源: docs/P3_PREREG_ADDENDUM_04.md:49]
- 报告规则：若超过 50% 的 B4-tiebreak 生成器调用以 INVALID_PROPOSAL 或 PROVIDER_ERROR 回退，则 B4-tiebreak 结果须报告为"由提议格式或提供者失败主导"，且不得据此宣称文本上下文有收益或代价（H3；P3 §19 第 6 项）。[来源: docs/P3_PREREG_ADDENDUM_04.md:59]
- 按 Addendum 04 §6.1，每个 B4 变体须报告：LLM 调用数；合法提议、INVALID_PROPOSAL、PROVIDER_ERROR 与截断输出的计数；gate_reason 分布。[来源: docs/P3_PREREG_ADDENDUM_04.md:57]
- B4-strict 与 B3 的决策结果相等是按构造成立的，不是经验发现。[来源: docs/P3_PREREG_ADDENDUM_04.md:27]
- 请求格式（提示词、响应格式约束、解码设置、模型标识）可在实现候选冻结前更改，但不得使用 eval-v3。[来源: docs/P3_PREREG_ADDENDUM_04.md:53]
- Addendum 05 §5 新增的实现缺陷类别已在第 3A 节转述；main 与 FRZ-1 分支在这些条款上的实现状态不同（见第 3A 节表）。[来源: docs/P3_PREREG_ADDENDUM_05.md:47-53] [v2 更新]
- Addendum 05 §4.2：不声称跨机器的回执哈希逐位一致；触发背景记录了另一台机器上 130 个 per-seed B3 回执哈希中 115 个不同。[来源: docs/P3_PREREG_ADDENDUM_05.md:7, 43] [v2 更新]
- eval-v3：种子未生成；B4 在注册证据包下的结果：**待 eval-v3，尚无结果**。[来源: docs/P3_PREREG_ADDENDUM_04.md:7; artifacts/h1/final-eval-v3-prohibition.json:4-8]
- main 上 B3 dev 的已提交产物含非零 `unsafe_action` 计数；决策记录写明"结果不得作为安全成功结论"。本草稿不引用其数字；FRZ-1 分支上刷新后的 `b3-dev.md` 数字与 main 不同，同样不引用。[来源: artifacts/s2/b3-dev.md; decisions.md:34; `git show origin/feat/frz1-b3core:artifacts/s2/b3-dev.md`] [v2 更新]
- V0 已知失败模式（修正包络、硬升级 fail-closed、边界放行、outcome 升级取舍、模型局限）及仿真器理想化声明："Results say nothing about hardware."[来源: FAILURE_MODES.md:7-16]
- 评估仅在合成仿真中；注册评估使用本地参考加载器而非实时 Zetaris。[来源: FAILURE_MODES.md:16; docs/P3_PREREG_ADDENDUM_03.md:49-51]
- Meterless：`npm audit` 在参考实现的 dev 依赖中报告 9 项（3 中、4 高、2 严重），按探针记录为仅 dev、未修复。[来源: docs/SPIKE_NOTES_20261019.md:31]
- 跨回合 Meterless "operations memory" 仅可作为明确标注的探索性演示功能，不得出现在注册结果表中；在 main 上是否已实现：[UNKNOWN]。[来源: docs/P3_PREREG_ADDENDUM_02.md:109-111]
- 最小演示要求的"回放 UI 由 Cursor 原生 agent 实现"：当前是否存在：[UNKNOWN]。[来源: docs/P3_PREREG_ADDENDUM_02.md:127-137; docs/DEV_WORKFLOW.md:11]
- 演示视频、幻灯片（Rule 6.1/6.2）：仓库内不存在对应文件（本分支新增的 `DECK_OUTLINE.md`、`VIDEO_SCRIPT.md` 为初稿，不是成品）。[来源: `git ls-tree -r main --name-only` 无相应文件] [UNKNOWN: 外部是否已存在] [v2 更新]
- ~~日期/环境不一致备注：README 要求 Python 3.11，而 Zetaris 与 Meterless 回执记录的运行环境为 Python 3.12.3~~ —— 该条已过期：README 现写 "需要 Python 3.12"，CI 固定 3.12.3，回执记录环境为 3.12.3。[来源: README.md:21; .github/workflows/ci.yml:17, 30; artifacts/sponsor/zetaris-equivalence.json:225; artifacts/sponsor/meterless-persistence.json:631; decisions.md:16] [v2 更新: 已由 612b06e 解决]
- 历史文档残留：`decisions.md` 中 "RRA V0 freeze v2" 一节写明当时"固定使用 Python 3.11 venv"，属历史记录；decisions.md:16 写明 3.11 时期的历史结果保留为历史记录。[来源: decisions.md:24; decisions.md:16] [v2 更新]
- 赛前 H1 文档与 P3 设计文档中仍保留 10-15/10-20 的旧窗口日期，以 Addendum 03 §1 为准。[来源: docs/H1_EVAL_FOUNDATION.md:5; docs/P3_SYSTEM2_DESIGN.md:9; docs/P3_PREREG_ADDENDUM_03.md:13]
- `decisions.md` 引用了 `REPORT_D1.md`，该文件不在仓库内。[来源: decisions.md:33; `ls` 无 REPORT_D1.md] [v2 更新: 行号 +1]
- T1/T3/T4 诊断报告均未并入 main：T1 `docs/_review/T1_pr20_review.md`（`cloud/t1-pr20-review` @ `1baed167a4545cf0df0a5960ca56287411a88d27`）、T3 `docs/_diag/T3_failure_funnel.md`（`cloud/t3-failure-funnel` @ `b8f0e104fbc62e3495f8371cec9ba4b5588b647e`，基线 `54f5006`）、T4 `docs/_review/T4_frz1_review.md`（`cloud/t4-frz1-review` @ `550cdc6464ba6c4825a2eab3d23b577b84a9a26a`）。它们的 dev 计数只出现在第 9A 节与 `FAILURE_MODES_DRAFT.md`，均标"dev，非注册结果"。[来源: 各报告头部] [v3 更新]

### 9.2 本草稿未完成的部分

- 本草稿未运行、未逐行审阅 main 上 PR #20 的代码和产物，只做了文件清单、命令行选项与产物元数据核对。[来源: 本草稿工作过程；`git diff --stat 54f5006 main`] [v2 更新]
- 对 FRZ-1 分支，v3 不再只读提交主题：条款与实现的对应以 T4 的逐条审查为准（见第 3A 节）；本草稿自己没有审阅 FRZ-1 代码，也没有重跑 T4 的脚本。 [v3 更新]
- 没有核对 main 上全部测试是否通过；没有重跑任何确定性基准；没有查询 CI 结果。[来源: 任务约束（不运行实时调用）；本草稿未执行 pytest] [v2 更新]
- v3 新增的未完成项：main 头上的 pytest 计数；缩减版证据包在 main 与 FRZ-1 上的修复状态（待 T6 核对）；T1/T3/T4 的数字未独立复算。 [v3 更新]

## 9A. 失败模式摘要（每个失败模式一行；全文见 `FAILURE_MODES_DRAFT.md`） [v3 更新]

所有数字均为 dev，非注册结果；eval-v3 与 B4 效果：待 eval-v3，尚无结果。最终表态句均为 [所有者裁决]。

| 编号 | 失败模式 | 一行摘要 | 当前处置 |
|---|---|---|---|
| A | episode 级 `safe_stop` 主导可恢复挑战 | 775 个 recoverable challenge 中 298 个在首次 S2 调用时 `safe_stop` 已为 True 而被跳过；成功 84/775（dev，非注册结果）[T4 §4.6] | 按裁决披露不修（R3） |
| B | 快速层升级太晚，保持来不及重评估 | 177 个保持对象进入时刻中位 7.1 s，153 个已越过拾取点，149 个无任何重评估（dev，非注册结果）[T4 §4.1] | 已有补遗并在 FRZ-1 实现（未合并）；升级时机已登记待修 |
| C | 观测不足 6 个即调用 System-2，PAUSE 后不重观测 | 33 seed 子集 498 次调用中 352 次 n<6（dev，非注册结果）[T3 §1.2a]；FRZ-1 窄读法之外 1412 + 140 次 PAUSE 不进入保持 [T4 §4.6] | 已有补遗（A05 §1）并在 FRZ-1 实现（未合并）；入口范围按 R1 取窄读法，范围外按裁决披露不修 |
| D | 嵌套结构 AMBIGUOUS | n≥6 的 146 次调用中 116 次 AMBIGUOUS（33 seed 子集）；FRZ-1 的 82 次重评估中 42 次 AMBIGUOUS（dev，非注册结果）[T3 C4；T4 §4.2] | 已登记待修；B4 效果待 eval-v3，尚无结果 |
| E | replay 缓存缺失被静默降级为 PROVIDER_ERROR 并退出 0 | PR #20 head 上 `--replay` 退出 0、`llm_calls` 62 对 376（dev，非注册结果）[T1 §4]；FRZ-1 上首次缺失即退出码 1 [T4 §5] | 已修复并有补遗（A05 §3.1），实现在 FRZ-1（未合并）；端到端测试缺口已登记 |
| F | 跨机器 receipt 哈希差异 | 130 个逐 seed B3 哈希中 115 个不同，metrics 与所查决策相同（dev，非注册结果）[A05 Trigger；T3 §6；T4 §3] | 平局规则与范围声明已有补遗（A05 §2、§4）；注册 runner 按 R4；§3.4 由所有者本地实现（R5），效果待 eval-v3，尚无结果 |
| G | 缩减版证据包（A04 §5.3） | 缺在场事件组及多个白名单字段 [T1 §5]；2026-10-23 dev 运行 386 条缓存响应中 310 条形状不符（dev，非注册结果）[A04 §5.1] | 修复状态 [UNKNOWN，待 T6 核对] |
| H | 88/5 的 `safe_stop` 解除行为 | 保持对象被授权后解除了保持前已有的 `safe_stop`，结局 miss；解释 wrong 589→588、miss 96→97（dev，非注册结果）[T4 §4.5] | 按裁决披露不修（R2） |
| I | 已提交 B3 历史中的早期授权与 sensor_bias 重复扣除 | `1cc7d07` 版 8 个 s2_authorized unsafe，现 s2 来源为 0（dev，非注册结果）[T3 §2.2、§3.2] | 历史；早期授权路径是否仍可达已登记待修 |
| J | 当前 7 个 unsafe 均为快速层命令（补充） | 全部在含 ACTUATOR_DELAY 的 case，其中 6 个与 B1 同 episode 终态相同（dev，非注册结果）[T3 §2.1] | 已登记；R1–R5 未涉及 |

## 10. 需所有者裁决 / 填写清单

（T2 清单全部保留；被后续合并解决的项标"已由 <sha> 解决"，不删除。）

1. **[所有者填写]** 第 7 节 Cursor 使用方式（Rule 6.4 要求；本草稿未编造）。 [来源: 本清单项；依据见前文对应章节]
2. **[所有者裁决]** Cursor 规则状态：2026-10-22 "可选"公告不在仓库，需提供公告原文或链接并决定提交说明按哪一版规则写（状态 UNKNOWN）。 [来源: 本清单项；依据见前文对应章节]
3. **[所有者裁决]** 对"成功/失败/负结果"的整体措辞：包括 H1/H6 预注册的负面发现框架（B2 持平、B3 与 B4 持平时的表述）、B3 dev 中非零 `unsafe_action` 与 `Recoverable challenge success` 如何呈现、V0 基线数字是否出现在提交说明中。本草稿一律未作决定。 [来源: 本清单项；依据见前文对应章节]
4. **[所有者裁决]** B4 在 2026-10-23 dev 运行中的格式失败（Addendum 04 §5）：提交说明是否披露、披露到何种细节；§6.2 的 50% 报告规则最终对 eval-v3 的适用方式。 [来源: 本清单项；依据见前文对应章节]
5. **[所有者裁决]** ~~PR #20 是否并入 main 再提交~~ —— 并入决定**已由 `9fe1730` 解决**（PR #20 已合并）。仍未解决的部分：缩减版证据包（A04 §5.3）在 main 上的修复状态与时间（见第 9.1 节第一条，状态 UNKNOWN）；B4 相关内容在提交说明中如何标注。 [来源: `git log`；docs/P3_PREREG_ADDENDUM_04.md:51] [v2 更新] 缩减包修复状态现标 [UNKNOWN，待 T6 核对]。 [v3 更新]
6. **[所有者填写]** 主办方对集成深度的期望：2026-10-21 onboarding 的结论、Meterless 的"组件"与"最小集成"要求（SPIKE_NOTES UNKNOWN，原样保留在第 4.4 节）。 [来源: 本清单项；依据见前文对应章节]
7. **[所有者裁决]** 是否把"参考实现 + 宿主侧桥"表述为满足 Rule 5.1 的 Meterless 集成。 [来源: 本清单项；依据见前文对应章节]
8. **[所有者填写]** 赛道最终选择（设计文档写明由所有者在提交前决定；规则快照中编号为 TRACK 03）。 [来源: 本清单项；依据见前文对应章节]
9. **[所有者填写]** 演示视频（1–4 分钟）与幻灯片的位置；回放 UI 是否存在；Zetaris 令牌到期日 2026-11-17 对评审期演示可用性的影响；NVIDIA 速率限制（UNKNOWN）。本分支的 `DECK_OUTLINE.md` 与 `VIDEO_SCRIPT.md` 为供所有者修改的初稿。 [来源: 本清单项；依据见前文对应章节] [v2 更新]
10. **[所有者裁决]** 窗口内对赛前文件的改动（如 `episode.py`、`world.py`）如何向评委划分新旧，以及是否在提交表单中单独声明赛前组件（Rule 5.4）。 [来源: 本清单项；依据见前文对应章节]
11. **[所有者裁决]** Docker 镜像目前不含 `bridges/`、`scripts/`、`artifacts/`：是否需要在提交说明中说明 Zetaris/Meterless 路径的复现边界，或另行提供镜像。（`Dockerfile` 复制范围在 PR #22 后未变，仍未解决。） [来源: Dockerfile:6-8；依据见前文对应章节] [v2 更新]
12. **[所有者核实]** `nvidia/nemotron-3.5-super-vl-120b-a12b` 与服务端返回的 `private/nvidia/nemotron-3.5-super-120b-a12b` 之间的关系，以及提交说明中应写哪一个。 [来源: 本清单项；依据见前文对应章节]
13. **[所有者核实]** ~~Python 3.11（README）与 3.12.3（赞助方回执）的差异是否需要在复现步骤中说明~~ —— **已由 `612b06e` 解决**（PR #22；README、`rra` 启动器、Dockerfile、CI 均为 3.12，见 6.1 节）。 [来源: README.md:21; rra; Dockerfile:1; decisions.md:16] [v2 更新]
14. **eval-v3**：待 eval-v3，尚无结果。所有涉及 eval-v3 或 B4 效果的段落须在 eval-v3 完成并按 Addendum 04 §6 报告规则处理后，才可由所有者决定措辞。 [来源: 本清单项；依据见前文对应章节]
15. **[所有者裁决]**（新增）`feat/frz1-b3core`（Addendum 05 的实现分支，未合并）是否并入 main、何时并入，以及并入后提交说明引用哪一版 `artifacts/s2/b3-dev.*` 与 `artifacts/sponsor/meterless-persistence.json`（main 与分支上的记录值不同）。 [来源: 第 3A 节；`git diff --stat main origin/feat/frz1-b3core`] [v2 更新] T4 对 FRZ-1 与 Addendum 05 的逐条对照见第 3A 节；T4 §7 另列 9 项待裁决，其中 R1、R2、R3、R4、R5 已裁决（见下）。 [v3 更新]
16. **[所有者裁决]**（新增）~~Addendum 05 §3.3、§3.4 在实现中的对应状态（本草稿标 UNKNOWN）~~ —— 对应状态已由 T4 确认（§3.3 部分；§3.4 在 FRZ-1 上未找到）；§3.4 已由 R5 裁决由所有者本地实现。仍未解决：提交说明是否披露 Addendum 05 的触发背景（含跨机器回执哈希差异的诊断）；§3.3 是否需要显式的分列字段（T4 §7-7）。 [来源: 第 3A 节；docs/P3_PREREG_ADDENDUM_05.md:7; T4 §1、§7-7] [v3 更新]
17. **[所有者裁决]**（新增）README 中 "冻结 eval v2 结果" 表是 V0 的赛前结果，提交说明是否保留该表及其位置；B3/B4 的 dev 数字是否出现在幻灯片/视频中（`DECK_OUTLINE.md` 的结果页留空为"待 eval-v3，尚无结果"）。 [来源: README.md:62-83; 本分支 DECK_OUTLINE.md] [v2 更新]
18. **已由所有者 2026-10-24 裁决（R1）**：Addendum 05 §1.1 保持入口取窄读法——只有快速层 ESCALATE 路径上的 PAUSE 进入保持（FRZ-1 现状）；infeasible 触发（1412 次）与 outcome escalation（140 次）的 PAUSE（dev，非注册结果）不进入保持，作为范围披露。 [来源: 所有者裁决；T4 §7-1] [v3 更新]
19. **已由所有者 2026-10-24 裁决（R2）**：§1.3 维持 FRZ-1 现状，不改代码；88/5（保持对象被授权后解除了保持前已有的 `safe_stop`，结局 miss）在提交材料中披露。 [来源: 所有者裁决；T4 §7-2；FAILURE_MODES_DRAFT.md §H] [v3 更新]
20. **已由所有者 2026-10-24 裁决（R3）**：episode 级 `safe_stop` 主导 84/775（T4 C2）不在本次冻结范围内，作为失败模式披露。 [来源: 所有者裁决；T4 §7-10；FAILURE_MODES_DRAFT.md §A] [v3 更新]
21. **已由所有者 2026-10-24 裁决（R4）**：注册 runner 为所有者本地机器（Intel i7-10750H，Python 3.12.3，NumPy 2.5.4，scipy-openblas 0.3.34）。 [来源: 所有者裁决；T4 §7-9] [v3 更新]
22. **已由所有者 2026-10-24 裁决（R5）**：§3.4 由所有者在本地实现；B4 缓存将在注册 runner 上 live 重建。（T4 §7-6 的 live 重新生成由谁、在哪台 runner、什么预算：以此裁决为准；预算数字本草稿不写。）效果：待 eval-v3，尚无结果。 [来源: 所有者裁决；T4 §7-6] [v3 更新]
23. **[所有者裁决]**（新增）`FAILURE_MODES_DRAFT.md` 每个失败模式的最终对外表态句；失败模式 J（当前 7 个 unsafe 均为快速层命令）是否披露与如何表述；T4 §7 其余未裁决项（第 3、4、5、7、8、11 项）。 [来源: FAILURE_MODES_DRAFT.md；T4 §7] [v3 更新]

## 附：与 T2 草稿的差异表

| 节号 | 旧内容摘要（T2 草稿） | 新内容摘要（v2） | 依据 |
|---|---|---|---|
| 0 元信息 | 基线 `54f5006`；PR #20 为 open、head `c852566`，标注 [PR#20 仅分支] | 基线 `520b7cf`；PR #20 已合并（`9fe1730`），标注改为 [main] / [FRZ-1 未合并]；新增 PR #22、#23 合并信息 | `git log pre-window-freeze..main` |
| 0 B3 数字 | 引用 `b3-dev.md` 但不引数字 | 同样不引数字；补注 FRZ-1 分支版本数字与 main 不同 | artifacts/s2/b3-dev.md; `git show origin/feat/frz1-b3core:artifacts/s2/b3-dev.md` |
| 1 规则 | 无 Rule 6.1–6.3 与评分权重 | 新增 Rule 6.1–6.3 转述与评分权重 | docs/HACKATHON_RULES.md:17,21-23,175 |
| 2 方法 | 无 B4-strict 与 B3 相等的说明 | 新增"按构造成立，检验以 B4-tiebreak 判定" | docs/P3_PREREG_ADDENDUM_04.md:27 |
| 3.2 模块表 | B4 运行器、b4_dev.py、l6_b4 脚本、b4-dev.json、386 缓存标 [PR#20 仅分支]；main 上缓存 2 个 | 全部标 [main]；缓存 386 个；新增 CLI 选项行、Python 3.12 行、FRZ-1 行 | `git diff --stat 54f5006 main`; `ls artifacts/llm_cache`; src/rra/cli.py:134-138 |
| 3.2 meterless 回执 | B4 一项为 "DEFERRED: L5/D4" | B4 一项为记录字符串 "PASS: B4_TIEBREAK … 20/20"，并转述 B4 块字段（仅为记录值） | artifacts/sponsor/meterless-persistence.json:635, 650-660 |
| 3A（新增） | 无 | Addendum 05 条款与 FRZ-1 对应提交表，无效果陈述 | docs/P3_PREREG_ADDENDUM_05.md; `git log main..origin/feat/frz1-b3core` |
| 4.2 Zetaris | 回执行号泛指；Dockerfile:4-8 | 补行号；Dockerfile 现为 python:3.12-slim；补 `afa2aa6` [FRZ-1 未合并] | artifacts/sponsor/zetaris-equivalence.json:14,17,225; Dockerfile:1,6-8 |
| 4.3 Meterless | 标题含 "B4 部分 [PR#20 仅分支]"；PR 描述转述 | 标题仅 [main]；以 JSON 记录值替换 PR 描述转述；补充只覆盖 NO_TEXT_CONTEXT 变体；FRZ-1 刷新注记 | artifacts/sponsor/meterless-persistence.json:635,650-660; 提交 aa3dd1c, 7e2c4a7, cb77107 |
| 5 NVIDIA | B4 运行代码在 [PR#20 仅分支]；decisions.md:31 | B4 代码 [main]，补 `_ReadThroughProvider` 行为；replay 缺失处理 main/FRZ-1 对照；decisions.md 行号 +1 | src/rra/eval/b4_dev.py:28-32,216; src/rra/llm/adapter.py:106; 提交 244b670 |
| 6.1 复现 | "需要 Python 3.11"，`python3.11 -m venv` | "需要 Python 3.12"，`python3.12 -m venv`；启动器与 CI/Docker 同；删除 PR #20 描述自述的 pytest 数字；补 CI 说明与 README eval v2 表说明 | README.md:21-25; rra; Dockerfile:1; ci.yml:17,30 |
| 6.3 Meterless | 无 B4 持久化脚本 | 补 `scripts/l6_b4_meterless_replay.py`，用法 UNKNOWN | scripts/l6_b4_meterless_replay.py |
| 6.4 NVIDIA | `rra s2-b4-dev` 标 [PR#20 仅分支]，参数以分支为准 | 标 [main]，列出 `--nproc/--subset/--replay`；`--replay` 离线，否则构造实时提供者（需密钥） | src/rra/cli.py:134-138; src/rra/eval/b4_dev.py:30-32 |
| 7 Cursor | `.cursor/rules/` | 指路到 `.cursor/rules/rra.mdc` | `ls .cursor/rules` |
| 8.1 范围统计 | 42 个提交，最晚 54f5006 | 50 个提交，最晚 520b7cf | `git rev-list --count pre-window-freeze..main` |
| 8.3 窗口内工作 | PR #20 项标 [PR#20 仅分支]，"尚不属于 main" | 改标 [main]；新增 PR #22、#23；新增 FRZ-1 的 12 个提交 [FRZ-1 未合并] | `git log` |
| 9.1 局限 | 首条："PR #20 未合并"；Python 3.11 vs 3.12.3 不一致条 | 首条改为已合并，缩减包缺陷是否修复 UNKNOWN；Python 条划去并注"已由 612b06e 解决"；新增 Addendum 05、T3 报告指路、B3 数字版本差异 | docs/P3_PREREG_ADDENDUM_04.md:51; README.md:21; decisions.md:16 |
| 9.2 未完成 | 只做 PR #20 清单与描述转述 | 改为 PR #20 已并入后的核对范围；FRZ-1 只读主题；未查 CI | 本草稿工作过程 |
| 10 清单 | 14 项 | 14 项全部保留；第 5 项"并入决定"标已由 `9fe1730` 解决；第 13 项标已由 `612b06e` 解决；新增第 15–17 项 | `git log`; 第 3A 节 |


## 附：与 v2 的差异表（v3）

| 节号 | v2 内容摘要 | v3 内容摘要 | 依据 |
|---|---|---|---|
| 标题、0 元信息 | 草稿 v2；T2→v2 说明 | 草稿 v3；新增 v2 底稿 sha、T1/T3/T4 输入 sha、指向 `FAILURE_MODES_DRAFT.md`；重申 main 头 `520b7cf`；dev 数字标注规则 | `git rev-parse HEAD`；各输入文件头部 |
| 0 性能数字 | 不引用任何 System-2 性能数字 | 正文仍不引用；第 9A 节与失败模式文档转录 T1/T3/T4 的 dev 计数并标"dev，非注册结果" | T1、T3、T4 |
| 3A 表 §1.1–1.5 | `71ce80d` 对应关系 UNKNOWN；状态仅 [FRZ-1 未合并] | `71ce80d` 为 Addendum 05 未列出的行为改动；§1.4 的 latch 由 `episode.py:533-535, 589-593` 实现；逐条状态与测试缺口 | T4 §1 |
| 3A 表 §2、§3.1、§3.2、§4.1、§4.2–4.3 | 仅提交主题 | 补 T4 的实现位置、测试缺口、CLI 实测；§4.1 注册 runner 按 R4 | T4 §1、§5；R4 |
| 3A 表 §3.3 | [UNKNOWN] | 部分：`llm_calls` 只记在 B4_STRICT，无显式分列字段 | T4 §1 表 §3.3 |
| 3A 表 §3.4 | [UNKNOWN] | FRZ-1 上未找到；R5：所有者本地实现 | T4 §1 表 §3.4；R5 |
| 3A 新增 bullet | — | R1/R2/R4/R5 在条款上的落点；T4 §1.1 无测试分支 | 所有者裁决；T4 §1.1 |
| 6.1 pytest | main 上 [UNKNOWN] | FRZ-1 头上 200 passed / 4 skipped / 0 failed；main 头仍 [UNKNOWN] | T4 §2；T1 §8 |
| 9.1 缩减包 | 修复状态 UNKNOWN | 补 T1 §5 的逐字段确认；修复状态 [UNKNOWN，待 T6 核对] | T1 §5 |
| 9.1 诊断报告指路 | 仅 T3，不引用数字 | T1/T3/T4 指路；数字只在 9A 与失败模式文档，标 dev | 各报告 |
| 9.2 未完成 | FRZ-1 只读主题 | 条款对应以 T4 为准；新增 v3 未完成项 | 本草稿工作过程 |
| 9A（新增） | — | 失败模式摘要 A–J | FAILURE_MODES_DRAFT.md |
| 10 清单 | 17 项 | 第 5、15、16 项补注；新增第 18–22 项（R1–R5，已由所有者 2026-10-24 裁决）与第 23 项 | 所有者裁决；T4 §7 |