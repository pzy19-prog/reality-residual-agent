# 幻灯片大纲（初稿）— Reasoning Architecture 赛道

状态：**DRAFT / 未经所有者审阅 / 不是成品幻灯片**。基线 `main` @ `520b7cfdf13b805c9258ab06c79a658ee62aef8b`。[来源: `git rev-parse origin/main`]

约定：

- 页序按 Rule 6.2 列出的条目：问题与目标用户、解决方案、agent 工作流或架构、技术栈、Zetaris 与 Meterless 如何使用、使用赞助技术的独特之处、产品画面、未来改进。[来源: docs/HACKATHON_RULES.md:22]
- 每条要点带 `[来源: 文件:行]`；仓库内无出处的写 `[UNKNOWN]`，需所有者的写 `[所有者填写]` / `[所有者裁决]`。合并状态标 **[main]** / **[FRZ-1 未合并]**。
- 所有涉及 eval-v3 结果或 B4 效果之处一律写"**待 eval-v3，尚无结果**"。本文不引用 System-2 任何性能数字，不写成败判定，不使用结论性措辞。[来源: docs/P3_PREREG_ADDENDUM_04.md:7; docs/P3_PREREG_ADDENDUM_05.md:7]
- "图/截图来源"一栏：仓库内已有文件，或标"待生成"（由谁生成、是否需外部服务写明）。本文未生成任何图片。
- 演讲者备注仅提示该页的事实边界，不是台词。

---

## 页 1 — 标题页

- 标题与副标题：[所有者填写]（项目名、赛道 Reasoning Architecture、团队）。[来源: docs/P3_SYSTEM2_DESIGN.md:926-936 赛道选择由所有者决定]
- 赛道原文可作副标题引用："Demonstrate a novel ability to turn data, knowledge, memory, and reasoning into reliable decisions and actions."[来源: docs/HACKATHON_RULES.md:41-44]
- 图：无；标识/Logo [所有者填写]。

## 页 2 — 问题与目标用户

- 问题：确定性快速层在受限工作包络内修正已知残差模式；当它声明"超出授权工作包络"时，如何获得有界的恢复权限，并在证据不足时拒绝行动。[来源: docs/P3_SYSTEM2_DESIGN.md:15-19]
- V0 的已记录失败模式：修正包络（显式跳过）、硬升级 fail-closed、边界放行、outcome 升级取舍、模型局限。[来源: FAILURE_MODES.md:7-16]
- 场景是合成的 2D 传送带抓放仿真；"Results say nothing about hardware."[来源: README.md:3; FAILURE_MODES.md:16]
- 目标用户：仓库中只有"operator-known configuration"和 MES/维护日志/交班记录等运维文本源的提及，没有对目标用户的明确定义。[来源: docs/P3_SYSTEM2_DESIGN.md:190, 498] [UNKNOWN: 目标用户画像] [所有者填写]
- 图/截图来源：`README.md:9-15` 的 V0 流程图（文本图，可重绘）；`FAILURE_MODES.md` 的失败模式列表（可截图）。
- 备注：V0 的 eval v2 数字是赛前工作，是否出现在本页由所有者决定（清单第 17 项）。[来源: README.md:62-83; docs/submission/DRAFT_SUBMISSION_v2.md 第 10 节]

## 页 3 — 解决方案

- 设计原则："LLM proposes; deterministic evidence disposes; authorization is explicit."[来源: docs/P3_SYSTEM2_DESIGN.md:28]
- LLM 只提出世界模型**结构**；参数由确定性拟合器估计；验证与授权是确定性的。[来源: docs/P3_SYSTEM2_DESIGN.md:21-28]
- 注册的结构空间为 14 个（4 单原语 + 6 二元 + 4 三元），DSL 原语为 `SENSOR_BIAS`、`VELOCITY_OFFSET`、`SPEED_STEP`、`ACTUATOR_DELAY`。[来源: docs/P3_SYSTEM2_DESIGN.md:104-106]
- 动作集很小：`UPDATE_MODEL_AND_REPLAN`、`PAUSE_AND_REOBSERVE`、`HUMAN_ESCALATION`。[来源: docs/P3_SYSTEM2_DESIGN.md:461-475]
- 证据不足时的行为：歧义门判 AMBIGUOUS 时 B4-strict 暂停并重观测；B4-tiebreak 允许文本在验证通过的假设间择一，但仍须通过授权门。[来源: docs/P3_SYSTEM2_DESIGN.md:399-432]
- 预注册的对照：B1、B2、B3（穷举经典 DSL 搜索）、B4-strict、B4-tiebreak；预先登记"若 B3 与 B4 持平则不能证明 LLM 必要性，且须报告"。[来源: docs/P3_SYSTEM2_DESIGN.md:631-700, 873-896]
- 图/截图来源：`docs/P3_SYSTEM2_DESIGN.md` §4 架构图（文本图）可重绘；无需外部服务。

## 页 4 — Agent 工作流与架构

- 链路：快速层 → 升级时交出证据包 → LLM 假设生成器 → 确定性 DSL 拟合器 → 反事实验证器 → 授权门 → 确定性动作执行器 → 控制器硬约束 → 证据回执。[来源: docs/P3_SYSTEM2_DESIGN.md:130-170]
- 输入隔离：只用可观测证据，真值、场景名、未来轨迹、隐藏故障状态被禁止；策略可见字段由 `src/rra/evidence/policy.py` 单点净化。[来源: docs/P3_SYSTEM2_DESIGN.md:176-203; docs/H1_EVAL_FOUNDATION.md "Policy information boundary"]
- B4 调用策略：仅当共享 B3 评估无故障证据且歧义门为 AMBIGUOUS 时才调用生成器；LLM 输出不触发或清除故障锁存，不用于拟合、验证、歧义门或授权。**[main]** [来源: docs/P3_PREREG_ADDENDUM_04.md:13, 19]
- 回合内记忆是显式结构化状态，不是向量库。[来源: docs/P3_SYSTEM2_DESIGN.md:478-494]
- 重观测保持（Addendum 05 §1）：PAUSE_AND_REOBSERVE 后目标进入保持，≥0.5 s 后在下一观测处重新评估。条款 **[main]**，实现提交在 **[FRZ-1 未合并]**（`56f36b0`、`e942024`）；本页不陈述其效果。[来源: docs/P3_PREREG_ADDENDUM_05.md:11-23; `git log main..origin/feat/frz1-b3core`]
- 图/截图来源：`docs/P3_SYSTEM2_DESIGN.md:130-170` 的文本架构图（待重绘为矢量图；无需外部服务）。
- 备注：快速层内无赞助方调用；调用发生在升级之后、仿真器冻结期间。[来源: docs/P3_PREREG_ADDENDUM_03.md:41-43]

## 页 5 — 技术栈

- 语言与运行时：Python 3.12（README、`rra` 启动器、Dockerfile、CI 固定 3.12.3）。**[main]** [来源: README.md:21; rra:7-8; Dockerfile:1; .github/workflows/ci.yml:17]
- 依赖：`numpy==2.5.4`、`pydantic>=2.6,<3`、`pytest>=8,<9`。[来源: requirements.txt:1-3]
- LLM：NVIDIA NIM（OpenAI 兼容接口），代码常量模型 `nvidia/nemotron-3.5-super-vl-120b-a12b`，思考模式默认关闭，请求按规范 JSON SHA-256 做内容寻址缓存，重放提供者只读。[来源: src/rra/llm/providers.py:13-14, 34, 51-60, 76-84]
- Zetaris：自管本地部署，标准库 REST 客户端（`POST {base}/sql-editor/sqls/run`）。[来源: src/rra/sponsor/zetaris.py:19-35; docs/SPIKE_NOTES_20261019.md:6, 12]
- Meterless：TypeScript H-MEM 参考实现（固定提交 `1742dec56a66e58eef9dda2d2b865823758ca8cd`），经 `tsx` 下的 `bridge.ts` 以 stdin/stdout JSON 行与 Python 通信，需 Node 22。[来源: bridges/meterless/README.md:1-15]
- 开发工具：Cursor 的使用方式 [所有者填写]；仓库内指路：`docs/DEV_WORKFLOW.md`、`.cursor/rules/rra.mdc`。[来源: docs/DEV_WORKFLOW.md:1-11]
- 测试与 CI：`pytest -q`；另有确定性作业（dev 种子两次运行 `rra bench`）。[来源: .github/workflows/ci.yml:1-41] 本草稿未查询 CI 结果。
- 图：技术栈示意（待生成，人工绘制；无需外部服务）。

## 页 6 — Zetaris 如何使用

- 角色（预注册）：部署数据访问与治理；不预先登记"Zetaris 改善任何注册指标"。[来源: docs/P3_PREREG_ADDENDUM_02.md:50]
- 两个分离的数据源经 Zetaris 联邦查询装配证据包：S-TELEMETRY（观测、在场事件、命令反馈）与 S-OPS（MES/设备事件、工单、交班记录、已知配置）。**[main]** [来源: docs/P3_PREREG_ADDENDUM_02.md:58-67]
- 治理即泄漏控制：只有 C1 白名单字段与 P3 §12 上下文记录可写入 Zetaris 可达的数据源；静态检查逐列枚举，白名单外字段即失败。[来源: docs/P3_PREREG_ADDENDUM_02.md:69-73]
- 等价不变量：Zetaris 装配的证据包与本地参考加载器装配的证据包，规范 JSON 的 SHA-256 须相等；等价集为 20 个 dev 回合。[来源: docs/P3_PREREG_ADDENDUM_02.md:75-81]
- 已提交回执（记录值，原样转述）：`T5: "PASS"`，20 个回合，`T3_anchor_mismatches: 0`，`T4_mismatches: 0`，`T8_reference_receipt_bytes_identical: true`；白名单回执 `extra_count: 0`；联邦查询示例 `federation_rows: 1`。[来源: artifacts/sponsor/zetaris-equivalence.json:14; artifacts/sponsor/zetaris-whitelist.json; artifacts/sponsor/zetaris-equivalence.json 字段 federation_rows]
- 评估模式披露（必须在提交材料中出现）：所有注册评估与基线 B1–B4 使用本地参考加载器，Zetaris 路径用于演示与等价回执。[来源: docs/P3_PREREG_ADDENDUM_03.md:49-51, 59-61]
- 图/截图来源：`artifacts/sponsor/zetaris-equivalence.json` 中的 `federation_sql` 与回执字段（可截图）；Zetaris UI/终端画面：待生成，需要 Zetaris 本地部署与 `ZETARIS_TOKEN`，由所有者执行。

## 页 7 — Meterless 如何使用

- 角色（预注册）：推理运行的可审计持久化与重放；不预先登记其改善任何注册指标。[来源: docs/P3_PREREG_ADDENDUM_02.md:50, 95-101]
- 每次 System-2 决策运行（证据引用 → 提议假设 → 拟合 → 验证 → 歧义门 → 授权或处置）持久化为 Meterless 记录。**[main]** [来源: docs/P3_PREREG_ADDENDUM_02.md:95-101]
- 记忆范围为回合内；其他回合只写不读，检查断言策略读取不触及 `episode_id` 不同的记录。[来源: docs/P3_PREREG_ADDENDUM_02.md:103-107]
- 决策不变性：持久化开/关在相同录制响应下须给出相同 B4 决策。[来源: docs/P3_PREREG_ADDENDUM_02.md:113-115]
- 映射：`source="rra.s2"`，`chatId=episode_id`；持久化为 `run_episode` 返回后的包装，评估者真值键在存储前被剥除。[来源: bridges/meterless/README.md:28-30; src/rra/sponsor/meterless.py:1-5, 21-24]
- 已提交回执（记录值）：20 个回合，`M1_roundtrip_mismatches: 0`，`M3_cross_episode_reads: 0`，`M4_replay_match: 20`，`M8_hidden_key_hits: 0`，`all_ok: true`；B4 块记录 `status: "PASS"`、`decisions_equal: 20`、`receipt_equal: 20`、`live_llm_calls: 0`（仅 `NO_TEXT_CONTEXT` 变体）。**[main]**；FRZ-1 分支上该文件被刷新，记录值与 main 不同，本页不比较。[来源: artifacts/sponsor/meterless-persistence.json:635, 650-660; 提交 aa3dd1c, 7e2c4a7, cb77107]
- 主办方对"Meterless 集成最低要求"的期望：[UNKNOWN]（仓库无 onboarding 结论）；参考实现 + 宿主侧桥是否满足 Rule 5.1：[所有者裁决]。[来源: docs/SPIKE_NOTES_20261019.md:33]
- 图/截图来源：`scripts/l6_persist_and_replay.py trail/replay` 的终端输出（待生成，需 Node 22 与 `setup_meterless.sh` 已执行，无外部凭据，由所有者或 Luna 执行）。

## 页 8 — 使用赞助技术的独特之处

本页文字需所有者定稿；以下只列仓库已记录、可被引用的设计特征，不作"独特"与否的判断。[来源: 任务约束]

- Zetaris 被用作结构性泄漏控制：白名单静态检查枚举每个源的每一列，且证据包必须与本地参考加载器逐位等价（SHA-256）。[来源: docs/P3_PREREG_ADDENDUM_02.md:69-81]
- Meterless 被限定在回合内、对其他回合只写不读，并由检查断言；持久化不得改变决策（开/关对照）。[来源: docs/P3_PREREG_ADDENDUM_02.md:103-115]
- NVIDIA NIM 仅在歧义门判 AMBIGUOUS 时被调用，且输出不进入拟合、验证、歧义门或授权；调用结果进入只读重放缓存，评分工件由冻结缓存、禁用网络的代码生成。[来源: docs/P3_PREREG_ADDENDUM_04.md:13, 43; docs/P3_PREREG_ADDENDUM_02.md:121-125]
- 预注册声明不主张赞助技术改善任何注册指标。[来源: docs/P3_PREREG_ADDENDUM_02.md:50]
- "独特之处"的最终措辞：[所有者填写]（Rule 6.4 要求）。[来源: docs/HACKATHON_RULES.md:24]
- 图：三栏对照（Zetaris / Meterless / NVIDIA 各自的边界）——待生成，人工绘制。

## 页 9 — 产品画面

仓库内无现成的 UI 或演示画面文件；回放 UI 是否存在：[UNKNOWN]。[来源: docs/P3_PREREG_ADDENDUM_02.md:127-137; docs/DEV_WORKFLOW.md:11]

建议的画面（均待生成；命令仅取自仓库文档）：

- 页 9a 单回合回执：`.venv/bin/python ./rra run --scenario bias --seed 7 --compensation on` 的终端输出与 `outputs/*.json`。无外部服务，任何人可执行。[来源: README.md:26]
- 页 9b 证据链回执：evidence → hypothesis → verification → authorization/disposition。[来源: docs/P3_SYSTEM2_DESIGN.md:938-960 "Minimum demo" 第 9 项] 画面来源：`artifacts/s2/b3-dev.json` 中保留决策记录的回合（该文件仅保留前 20 个 seed 的逐决策记录——此事实来自 T3 诊断报告，分支 `cloud/t3-failure-funnel`，未并入 main）。[来源: T3_failure_funnel.md §1.1（分支 b8f0e104）]
- 页 9c 一次"恢复"与一次"有依据的拒绝"并排：P3 §23 要求演示同时包含成功恢复与有依据的拒绝。具体回合 seed 需由所有者从 dev 产物中选择：[所有者裁决]。[来源: docs/P3_SYSTEM2_DESIGN.md:938-960]
- 页 9d Meterless 轨迹：`scripts/l6_persist_and_replay.py trail --run-tag demo --episode ep-014` 输出（需 Node 22，无外部凭据）。[来源: bridges/meterless/README.md:41-45]
- 页 9e Zetaris 联邦查询：UI 或终端截图，需 Zetaris 与 `ZETARIS_TOKEN`，由所有者执行。
- 不得出现 eval 种子值；截图中的 seed 仅限 `config/dev_seeds.json`。[来源: .cursor/rules/rra.mdc; docs/EVAL_PROTOCOL.md:18-19]

## 页 10 — 结果页

- 注册评估结果：**待 eval-v3，尚无结果**。eval-v3 种子未生成也未被查看。[来源: docs/P3_PREREG_ADDENDUM_05.md:7; artifacts/h1/final-eval-v3-prohibition.json:4-8]
- B4 在注册证据包下的效果：**待 eval-v3，尚无结果**。[来源: docs/P3_PREREG_ADDENDUM_04.md:7]
- 本页必须披露的预注册规则（只转述规则，不转述数字）：评估模式为本地参考加载器；若超过 50% 的 B4-tiebreak 生成器调用以 INVALID_PROPOSAL 或 PROVIDER_ERROR 回退，须报告为"由提议格式或提供者失败主导"；B4-strict 与 B3 相等按构造成立；跨机器不声称回执哈希逐位一致，评分工件在单一 runner 生成并报告其平台。[来源: docs/P3_PREREG_ADDENDUM_03.md:49-51; docs/P3_PREREG_ADDENDUM_04.md:27, 59; docs/P3_PREREG_ADDENDUM_05.md:41-45]
- 预先登记的失败解释：若 B2 或穷举 B3 与 B4 在注册指标上持平，须报告"本基准不能证明增加推理复杂度的必要性"。其呈现方式 [所有者裁决]。[来源: docs/P3_SYSTEM2_DESIGN.md:873-896]
- dev 结果是否展示、如何措辞：[所有者裁决]（含 B3 dev 中非零 `unsafe_action`；决策记录写明"结果不得作为安全成功结论"）。[来源: decisions.md:34; artifacts/s2/b3-dev.md]
- 图：待 eval-v3，尚无结果；留空占位。

## 页 11 — 局限与披露（建议页，非 Rule 6.2 必列）

- 仅合成仿真；注册评估使用本地参考加载器而非实时 Zetaris。[来源: FAILURE_MODES.md:16; docs/P3_PREREG_ADDENDUM_03.md:49-51]
- 2026-10-23 B4 dev 运行的缓存响应格式失败已在 Addendum 04 §5 披露；该次运行发送缩减版证据包，不构成注册证据包下 B4 的证据。是否在幻灯片中披露及细节：[所有者裁决]。[来源: docs/P3_PREREG_ADDENDUM_04.md:47-51]
- Addendum 05 记录的三项实现问题（重观测、replay 缺失中止、确定性范围）：条款 **[main]**，实现 **[FRZ-1 未合并]**。[来源: docs/P3_PREREG_ADDENDUM_05.md:7; `git log main..origin/feat/frz1-b3core`]
- 赛前已有工作与窗口内新工作的界线：`pre-window-freeze`（`3b56637681551f21c6b4c253be6def59389d1051`）；窗口内范围 `pre-window-freeze..main` 共 50 个提交。[来源: HACKATHON_BASELINE.md:5-7; `git rev-list --count pre-window-freeze..main`]
- Docker 镜像不含 `bridges/`、`scripts/`、`artifacts/`，Zetaris/Meterless 路径不在镜像内。[来源: Dockerfile:6-8]

## 页 12 — 未来改进

仓库内已登记、可作为"未来改进"素材的条目（取舍与措辞 [所有者裁决]）：

- 并入 `feat/frz1-b3core` 并重新生成受影响的工件。**[FRZ-1 未合并]** [来源: `git log main..origin/feat/frz1-b3core`]
- 更正 B4 请求的证据包，使之符合 Addendum 03 §2 第 4 项（该缺陷在 Addendum 04 §5.3 中被记为须在实现候选冻结前更正；main 上的更正状态 [UNKNOWN]）。[来源: docs/P3_PREREG_ADDENDUM_04.md:51]
- 在 H5、实现候选冻结之后，于隔离进程中生成 eval-v3 种子并运行注册评估：**待 eval-v3，尚无结果**。[来源: docs/EVAL_PROTOCOL.md:19; artifacts/h1/final-eval-v3-prohibition.json:10]
- 跨回合 Meterless "operations memory"：仅可作为明确标注的探索性演示功能，不得进入注册结果表。[来源: docs/P3_PREREG_ADDENDUM_02.md:109-111]
- 回放 UI（P3 最小演示要求）。[来源: docs/P3_PREREG_ADDENDUM_02.md:127-137]
- 其他方向（硬件验证、更多动作）：仓库只写了"Results say nothing about hardware"与"Action breadth is lower priority"，没有路线图。[来源: FAILURE_MODES.md:16; docs/P3_SYSTEM2_DESIGN.md:476] [UNKNOWN: 路线图]
- 图：无。

---

## 附：Rule 6.2 条目对照

| Rule 6.2 条目 | 页 |
|---|---|
| 问题与目标用户 | 2 |
| 解决方案 | 3 |
| agent 工作流或架构 | 4 |
| 技术栈 | 5 |
| Zetaris 与 Meterless 如何使用 | 6、7 |
| 使用赞助技术的独特之处 | 8 |
| 产品画面 | 9 |
| 未来改进 | 12 |
| （结果与披露，非 Rule 6.2 必列） | 10、11 |

## 附：待所有者决定

- 目标用户画像（页 2）、项目名与标识（页 1）、"独特之处"措辞（页 8）、画面中采用的回合 seed（页 9c）、dev 结果与负结果措辞（页 10）、未来改进的取舍（页 12）、Cursor 描述（页 5）。完整清单见 `DRAFT_SUBMISSION_v2.md` 第 10 节。[来源: docs/submission/DRAFT_SUBMISSION_v2.md]
