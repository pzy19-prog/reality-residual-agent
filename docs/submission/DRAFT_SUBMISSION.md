# Reasoning Architecture 赛道提交说明（草稿）

状态：**DRAFT / 未经所有者审阅 / 不是提交内容**。[来源: 本文件约定]

## 0. 草稿元信息

- 起草基线：`main` 头 `54f5006`，与任务核对值一致，无需改写。[来源: `git log -1` → 54f5006 "Merge pull request #21 from pzy19-prog/docs/prereg-addendum-04"]
- 引用格式：`[来源: 文件:行]` 或 `[来源: sha]`；仓库内找不到依据的写 `[UNKNOWN]`；需所有者填写的写 `[所有者填写]`。[来源: 本文件约定]
- eval-v3 状态：种子值尚未生成也未被查看（`final_eval_v3_seed_values_created=false`、`final_eval_v3_seed_values_inspected=false`），`config/eval_seeds_v3.json` 不存在。本文所有涉及 eval-v3 结果或 B4 效果之处一律写"**待 eval-v3，尚无结果**"。[来源: docs/P3_PREREG_ADDENDUM_04.md:7; artifacts/h1/final-eval-v3-prohibition.json:4-8]
- 本文不含"成功/失败/负结果"的措辞决定；这类决定列在末尾第 10 节。[来源: 任务约束；见第 10 节]
- 本文不引用 System-2（B3/B4）任何性能数字；仓库已提交的 B3 dev 数字位于 `artifacts/s2/b3-dev.md`，其解读由所有者决定。[来源: artifacts/s2/b3-dev.md:1-24; decisions.md:33]
- 已合并到 main 与仅在 PR #20 分支（`feat/l5b-b4`，head `c852566`，状态 open，未合并）上的内容，在第 3 节与各节中分别标注 **[main]** / **[PR#20 仅分支]**。[来源: `gh api repos/pzy19-prog/reality-residual-agent/pulls/20` → state=open, merged=false, head sha c852566db1e10d4e267eb32f3a8f3912d9685db7]

## 1. 赛道与规则背景

- 选定赛道：Reasoning Architecture；设计文档默认目标为该赛道，且写明"赛道选择仍为所有者在提交前的决定"。[来源: docs/P3_SYSTEM2_DESIGN.md:926-936]
- 赛道原文："Demonstrate a novel ability to turn data, knowledge, memory, and reasoning into reliable decisions and actions."[来源: docs/HACKATHON_RULES.md:41-44]
- 赛道编号：2026-09-28 快照中为 TRACK 04，2026-10-11 页面中为 TRACK 03。[来源: docs/HACKATHON_RULES.md:13-14]
- 构建窗口：2026-10-22 00:00 UTC 至 2026-10-27 23:45 UTC；P3 与 H1 文档里的 10-15/10-20 日期已由 Addendum 03 §1 作废。[来源: docs/HACKATHON_RULES.md:145; docs/P3_PREREG_ADDENDUM_03.md:11-19]
- `docs/HACKATHON_RULES.md` 是 2026-10-11T07:08:28Z 的快照，内含新旧两版规则。[来源: docs/HACKATHON_RULES.md:2]
- Rule 5.1 旧版："Any language, framework, model or cloud, including closed-source APIs and sponsor credits."；新版："Every submission must integrate Zetaris and Meterless, and teams must use Cursor for development."[来源: docs/HACKATHON_RULES.md:19]
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
- 成功标准与评估结果：**待 eval-v3，尚无结果**。[来源: docs/P3_PREREG_ADDENDUM_04.md:7; docs/EVAL_PROTOCOL.md:19]

## 3. 架构与代码布局

### 3.1 逻辑架构

- 快速层（System-1）→ 在 `ESCALATE` / `correction_infeasible` / outcome escalation 时交出证据包（Evidence Packet）→ LLM 假设生成器 → 确定性 DSL 拟合器 → 反事实验证器 → 授权门 → 确定性动作执行器 → 控制器硬约束 → 证据回执（receipt）。[来源: docs/P3_SYSTEM2_DESIGN.md:130-170]
- 输入隔离：System-2 只能使用可观测证据（残差历史、观测位置/时间戳、命令与终态结果、分类器历史、回合内假设状态、维护日志、MES 事件、交班记录、操作员已知配置）；真值、场景名、未来轨迹、隐藏故障状态等被禁止。[来源: docs/P3_SYSTEM2_DESIGN.md:176-203]
- 策略可见字段由 `src/rra/evidence/policy.py` 作为唯一结构化净化器限定。[来源: docs/H1_EVAL_FOUNDATION.md "Policy information boundary" 一节]
- 回合内记忆是显式结构化状态，不是向量库；不要求跨回合学习。[来源: docs/P3_SYSTEM2_DESIGN.md:478-494]
- 快速层内不发生赞助方基础设施调用；调用只发生在升级之后、仿真器冻结期间。[来源: docs/P3_PREREG_ADDENDUM_03.md:41-43]

### 3.2 代码模块（按分支分列）

| 模块 | 位置 | 所在分支 |
|---|---|---|
| System-2 确定性核心（DSL、拟合器、验证器、授权、B3） | `src/rra/s2/*` | **[main]** [来源: `git ls-tree main` src/rra/s2/; decisions.md:32-33] |
| NIM 提供者、重放缓存、假设提议器 | `src/rra/llm/{providers,adapter}.py` | **[main]** [来源: src/rra/llm/providers.py:1-14; decisions.md:25-31] |
| v3 上下文族（六个模板族） | `src/rra/eval/context_v3.py` | **[main]** [来源: decisions.md:27] |
| Zetaris 客户端与两源证据包路径 | `src/rra/sponsor/zetaris.py`, `scripts/l3_*` | **[main]**（PR #18，合并提交 d54faa7） [来源: git log: 92dac5a, d54faa7] |
| Meterless 持久化与重放桥 | `src/rra/sponsor/meterless.py`, `bridges/meterless/*`, `scripts/l6_persist_and_replay.py` | **[main]**（PR #17，合并提交 90054ca） [来源: git log: 8eb7492, 90054ca] |
| `s2-b3-dev` 命令 | `src/rra/cli.py` | **[main]** [来源: src/rra/cli.py:132-133] |
| B4-strict / B4-tiebreak 回合行为、`s2-b4-dev` 运行器、`src/rra/eval/b4_dev.py`、`scripts/l6_b4_meterless_replay.py`、`tests/test_b4_episode.py`、`artifacts/s2/b4-dev.json`、386 条 `artifacts/llm_cache/*.json` | 见左 | **[PR#20 仅分支]**，不在 main [来源: `git diff --stat main...pr20`；`git merge-base --is-ancestor 92e2b89 main` 返回非零] |

- main 上 `artifacts/sponsor/meterless-persistence.json` 的汇总里 B4 一项为 "DEFERRED: L5/D4"；PR #20 修改了该文件。[来源: artifacts/sponsor/meterless-persistence.json（main）summary.B4; `git diff --stat main...pr20`]
- main 上 `artifacts/llm_cache/` 仅有 2 个文件；PR #20 分支树内为 386 个。[来源: `ls artifacts/llm_cache`（main）；`git ls-tree -r pr20 --name-only | grep -c llm_cache` = 386]

## 4. Zetaris 与 Meterless 如何集成

### 4.1 预注册的角色与边界

- 预注册声明：不预先登记"Zetaris 或 Meterless 改善任何注册指标"的主张；其角色是部署数据访问、治理、可审计的持久化与重放。任何此类主张需要在 eval-v3 生成前另立带日期的修订。[来源: docs/P3_PREREG_ADDENDUM_02.md:50]
- 评估模式披露：所有注册评估（eval v3）与基线 B1–B4 使用本地参考加载器；Zetaris 路径用于演示和等价回执，不用于注册评估。提交材料必须披露该评估模式。[来源: docs/P3_PREREG_ADDENDUM_03.md:49-51, 59-61; docs/P3_PREREG_ADDENDUM_02.md:83-87]

### 4.2 Zetaris — 证据数据平面 [main]

- 设计角色：System-2 证据包由两个分离的数据源通过 Zetaris 联邦查询装配：S-TELEMETRY（观测、在场事件、命令反馈）与 S-OPS（MES/设备事件、工单、交班记录、已知配置）。[来源: docs/P3_PREREG_ADDENDUM_02.md:58-67]
- 治理作为结构性泄漏控制：只有 C1 白名单字段与 P3 §12 上下文记录可写入 Zetaris 可达的数据源；静态检查枚举每个源的每一列，白名单外字段即失败。[来源: docs/P3_PREREG_ADDENDUM_02.md:69-73]
- 等价不变量：Zetaris 装配的证据包与本地参考加载器装配的证据包，其规范 JSON 的 SHA-256 在等价集上必须相等；等价集为 20 个 dev 回合，仅用 dev 种子。[来源: docs/P3_PREREG_ADDENDUM_02.md:75-81]
- 已提交的回执（记录值，原样转述）：`T5: "PASS"`，20 个回合，`T1_schema_extra` 各表均为空，`T3_anchor_mismatches: 0`，`T4_mismatches: 0`，`T8_reference_receipt_bytes_identical: true`，`base_git_sha: 2a3b52dcf15cf352064f064e2a8b499c4fe06280`，记录环境 Python 3.12.3。[来源: artifacts/sponsor/zetaris-equivalence.json（main）]
- 白名单回执：`extra_count: 0`，schema `rra.l3.whitelist.v1`。[来源: artifacts/sponsor/zetaris-whitelist.json（main）]
- 联邦查询示例：一条跨 `RRA_L3_TELEMETRY` 与 `RRA_L3_OPS` 的 JOIN，`federation_rows: 1`。[来源: artifacts/sponsor/zetaris-equivalence.json（main）字段 federation_sql, federation_rows]
- 客户端：标准库 REST 客户端，调用 `POST {base}/sql-editor/sqls/run`，令牌从环境变量 `ZETARIS_TOKEN` 读取，错误信息中令牌被替换为 `[REDACTED]`。[来源: src/rra/sponsor/zetaris.py:14-37]
- 本草稿未运行任何 Zetaris 实时调用，上述数字均为仓库已提交的记录值。[来源: 任务约束]
- 访问路径（赛前探针）：自管本地部署（Docker Compose 包），API 令牌到期日 2026-11-17。[来源: docs/SPIKE_NOTES_20261019.md:6, 12]
- 在场的 Docker 镜像不含 Zetaris/Meterless 路径：`Dockerfile` 仅复制 `requirements.txt`、`src`、`config` 与 `rra` 启动器，不含 `bridges/`、`scripts/`、`artifacts/`。[来源: Dockerfile:4-8]

### 4.3 Meterless — 推理运行持久化与重放 [main]；B4 部分 [PR#20 仅分支]

- 设计角色：每次 System-2 决策运行（证据引用 → 提议假设 → 拟合 → 验证结果 → 歧义门 → 授权或处置）持久化为 Meterless 管理的记录，用于检视推理轨迹、回放，以及演示证据链。[来源: docs/P3_PREREG_ADDENDUM_02.md:95-101]
- 记忆范围：回合内；注册运行中 Meterless 对其他回合只写不读，并有检查断言策略读取不触及 `episode_id` 不同的记录。[来源: docs/P3_PREREG_ADDENDUM_02.md:103-107]
- 决策不变性：持久化不得改变决策；在等价集上，持久化开/关须在相同的录制 LLM 响应下给出相同的 B4 决策。[来源: docs/P3_PREREG_ADDENDUM_02.md:113-115]
- 实现：Python 通过 stdin/stdout JSON 行与 `bridge.ts` 通信；桥导入固定版本的 Meterless H-MEM 参考实现，在 `tsx` 下运行；Meterless 提交固定为 `1742dec56a66e58eef9dda2d2b865823758ca8cd`；映射为 `source="rra.s2"`，`chatId=episode_id`。[来源: bridges/meterless/README.md:1-30]
- 持久化是在 `run_episode` 返回之后运行的包装，不触碰回合本身；评估者真值键在存储前被剥除。[来源: src/rra/sponsor/meterless.py:1-5, 21-24]
- main 上已提交的回执（记录值，原样转述）：20 个回合，`M1_roundtrip_mismatches: 0`，`M2_production_decisions_equal: 20`，`M3_cross_episode_reads: 0`，`M3_negative_refused: 20`，`M4_replay_match: 20`，`M5_identical: 20`，`M8_hidden_key_hits: 0`，`all_ok: true`；B4 一项为 "DEFERRED: L5/D4"。[来源: artifacts/sponsor/meterless-persistence.json（main）summary]
- **[PR#20 仅分支]** PR 描述自述 "Update Meterless B4 persistence verification to PASS for 20/20 episodes" 与 "B-4: Meterless off/on matched decisions and receipt hashes 20/20"。这是 PR 描述文字，未合并，本草稿未在 main 上核对。[来源: PR #20 描述（`gh api repos/pzy19-prog/reality-residual-agent/pulls/20` .body）]
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
- 实现 [main]：兼容 OpenAI 接口的 NIM 客户端，端点 `https://integrate.api.nvidia.com/v1`，代码常量模型 `nvidia/nemotron-3.5-super-vl-120b-a12b`，密钥从环境变量 `NVIDIA_API_KEY` 读取，请求按规范 JSON 的 SHA-256 做内容寻址缓存，重放提供者只读。[来源: src/rra/llm/providers.py:13-14, 50-60, 77-84]
- 默认关闭思考模式（`chat_template_kwargs={"enable_thinking": false}`），并纳入规范化请求与缓存键；决策记录写明服务端返回的模型名为 `private/nvidia/nemotron-3.5-super-120b-a12b`，与代码常量 `nvidia/nemotron-3.5-super-vl-120b-a12b` 不同。[来源: decisions.md:31; src/rra/llm/providers.py:14] [UNKNOWN: 两个名称之间的关系，仓库无说明]
- 提议器只接受可观测证据包和上下文文本，用 Pydantic 校验输出，忽略数值参数并记录未知 ID。[来源: decisions.md:28]
- B4 调用策略（Addendum 04 §1.1）：仅当共享 B3 评估在该决策点无故障证据且歧义门结果为 AMBIGUOUS 时才调用生成器，其余决策点不调用 LLM。[来源: docs/P3_PREREG_ADDENDUM_04.md:13]
- LLM 输出不触发或清除故障锁存，不用于参数拟合、验证、歧义门或授权。[来源: docs/P3_PREREG_ADDENDUM_04.md:19]
- B4 的运行代码（`s2-b4-dev`、两种 B4 回合行为）在 **[PR#20 仅分支]**，不在 main。[来源: `git diff --stat main...pr20`; `git show pr20:src/rra/cli.py` 第 134 行含 s2-b4-dev]
- NVIDIA 对注册指标的贡献：**待 eval-v3，尚无结果**。[来源: docs/P3_PREREG_ADDENDUM_04.md:7]
- 赛前探针记录：20 个并行请求均返回 HTTP 200；小 `max_tokens` 时可见内容可能为空，`max_tokens=1500` 返回了内容。[来源: docs/SPIKE_NOTES_20261019.md:17-18]

## 6. 可复现步骤

以下只列仓库文档已有的命令；本草稿未执行任何会访问 Zetaris、Meterless 或 NVIDIA 的实时调用，也未使用任何密钥。[来源: 任务约束]

### 6.1 V0 与评估框架（无外部服务）[main]

- 需要 Python 3.11；`python3.11 -m venv .venv`，`.venv/bin/pip install -r requirements.txt`。[来源: README.md:21-25]
- 运行单回合：`.venv/bin/python ./rra run --scenario bias --seed 7 --compensation on`。[来源: README.md:26]
- dev 冒烟基准：`RRA_SEED_FILE=config/dev_seeds.json .venv/bin/python ./rra bench`。[来源: README.md:37-39]
- Docker：`docker build -t reality-residual-agent .`，然后 `docker run --rm -e RRA_SEED_FILE=/app/config/dev_seeds.json reality-residual-agent rra bench`。[来源: README.md:43-46]
- 不带 `RRA_SEED_FILE` 的 `rra bench` 默认读取冻结的 eval v2 种子 2000–2099，而该集合已按协议"使用一次"；复现请使用 dev 种子。[来源: README.md:33; docs/EVAL_PROTOCOL.md:18]
- System-2 B3 dev 对照：`rra s2-b3-dev`，仅读取 dev 种子，默认输出到 `artifacts/s2`。[来源: src/rra/cli.py:132-133; decisions.md:33]
- 依赖：`numpy==2.5.4`、`pydantic>=2.6,<3`、`pytest>=8,<9`。[来源: requirements.txt:1-3]
- main 上全量 pytest 的通过数：[UNKNOWN]（本草稿未运行测试；PR #20 描述自述 "pytest 190 passed / 4 skipped"，属 PR 分支且为自述）。[来源: PR #20 描述 B-6]

### 6.2 Zetaris 路径 [main]（需要外部服务与凭据，由所有者执行）

- 先决条件：自管 Zetaris 本地部署（docker compose 网络 `zetaris_default`）、环境变量 `ZETARIS_TOKEN`。[来源: scripts/l3_zetaris_up.sh:5-6; src/rra/sponsor/zetaris.py:19-21]
- 起源服务与注册：`scripts/l3_zetaris_up.sh` 启动 `rra-l3-pg`（Postgres 16）与 `rra-l3-ops` 两个源容器并注册。[来源: scripts/l3_zetaris_up.sh:7-27]
- 等价检查：`scripts/l3_equivalence.py`；密钥审计：`scripts/l3_secret_audit.py`。[来源: scripts/l3_equivalence.py:1; scripts/l3_secret_audit.py:7]
- 具体参数与输出位置以脚本为准：[UNKNOWN]（本草稿未逐一核对各脚本的命令行参数）。[来源: 本草稿未运行脚本]

### 6.3 Meterless 路径 [main]（需要 Node 22）

- `scripts/setup_meterless.sh`：幂等；克隆 Meterless 到 `bridges/meterless/vendor/Meterless` 并检出 `1742dec56a66e58eef9dda2d2b865823758ca8cd`，运行 `npm ci --ignore-scripts`。[来源: bridges/meterless/README.md:9-15]
- 持久化与重放：`.venv/bin/python scripts/l6_persist_and_replay.py run --run-tag demo --seeds 14`；`trail` 与 `replay` 子命令见同一文件。[来源: bridges/meterless/README.md:41-46; scripts/l6_persist_and_replay.py:3-8]
- 实时桥测试：`RRA_METERLESS_LIVE=1 .venv/bin/python -m pytest tests/test_meterless_bridge.py -q`。[来源: bridges/meterless/README.md:46]

### 6.4 NVIDIA 路径 [main]（需要 `NVIDIA_API_KEY`，由所有者执行）

- 单次实时烟测脚本：`scripts/nemotron_smoke.py`（"One authorized live NIM smoke call with at most two backoff retries"）。[来源: scripts/nemotron_smoke.py:1]
- 注册 B4 结果必须由冻结响应缓存、禁用网络的代码生成；实时运行只用于填充缓存；回执必须可由产物内容按代码规则重算，且两次连续生成的回执须一致。[来源: docs/P3_PREREG_ADDENDUM_04.md:43]
- B4 dev 运行与离线重放命令：`rra s2-b4-dev`，**[PR#20 仅分支]**；其参数以 PR 分支的 `src/rra/cli.py` 为准。[来源: `git show pr20:src/rra/cli.py` 第 134 行]
- eval-v3 的复现步骤：**待 eval-v3，尚无结果**；种子仅在 H5、实现候选冻结之后、在隔离进程中生成。[来源: docs/EVAL_PROTOCOL.md:19; artifacts/h1/final-eval-v3-prohibition.json:10]

## 7. Cursor 使用方式

[所有者填写]

- 本节不写任何 Cursor 使用情况的描述。[来源: 任务约束]
- 仅供所有者查阅的仓库内现有记录（指路，不构成对使用方式的说明）：`docs/DEV_WORKFLOW.md`、`.cursor/rules/`。[来源: docs/DEV_WORKFLOW.md:1-11; `ls .cursor/rules`]
- 规则状态：新版 Rule 5.1/6.4 要求 Cursor；所有者记录 2026-10-22 起为可选，公告不在仓库中。[来源: docs/HACKATHON_RULES.md:19, 24; 所有者任务说明] [UNKNOWN: 当前以哪一版为准]

## 8. 赛前已有工作 vs 窗口内新工作

### 8.1 界线定义

- `v0-baseline` 为不可变的原始 V0 快照；该标签对象为 `11c45959397f029f5cb9eedfaa498514ec185b74`，指向提交 `546e82aefd4e07bf304d79c63dcffe6dd4b7c4ee`。[来源: HACKATHON_BASELINE.md:5; `git rev-parse v0-baseline v0-baseline^{commit}`]
- `pre-window-freeze` 标签对象为 `7dccc2532e3b248e2e93e274ace0fd659db1745f`，指向提交 `3b56637681551f21c6b4c253be6def59389d1051`（提交时间 2026-10-19 22:38:27 +0800），是 `main` 的祖先。[来源: `git rev-parse pre-window-freeze pre-window-freeze^{commit}`; `git log -1 --format=%ci pre-window-freeze`; `git merge-base --is-ancestor pre-window-freeze main`]
- 声明：从 `pre-window-freeze` 可达的一切均为赛前已有工作；窗口内新工作为 `pre-window-freeze..<提交 sha>` 范围；`v0-baseline` 之后的提交并不全是窗口内工作。[来源: HACKATHON_BASELINE.md:7]
- `p3-prereg` 标签对象 `a7c640b8debbf612490fa216c896b4d1b91a4d77`；`rra-v0-freeze-01` 标签对象 `b5bbaa13976f62ef7b0e8ff73e8327d08228a251`。[来源: `git rev-parse p3-prereg rra-v0-freeze-01`]
- 范围统计：`pre-window-freeze..main` 共 42 个提交，最早为 `b8d884a`（2026-10-22 21:11:38 +0800），最晚为 `54f5006`。[来源: `git rev-list --count pre-window-freeze..main`; `git log --format='%h %ci %s' pre-window-freeze..main`]
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
- v3 上下文族、提议器、NIM 重放缓存与烟测运行器：`9ff81e1`、`bb8eb49`、`f65ba5b`。[来源: `git log pre-window-freeze..main`; decisions.md:25-30]
- Cursor 规则与开发流程记录：`cf611a2`（PR #14）。[来源: `git log pre-window-freeze..main`; docs/DEV_WORKFLOW.md:1-11]
- B3 dev 评估命令及后续修复（PR #12、#13、#15、#16）。[来源: `git log pre-window-freeze..main`: 7ea70ce, cbc1f8a, 345b6f9, 198ab6a, 2a3b52d]
- Meterless 持久化/重放桥：`8eb7492`（PR #17，合并 `90054ca`）。[来源: `git log pre-window-freeze..main`]
- Zetaris 两源证据包路径：`92dac5a`（PR #18，合并 `d54faa7`）。[来源: `git log pre-window-freeze..main`]
- L5a 卫生 + 重放键 + 结构 ID：`ab509d3`（PR #19，合并 `2ff7a6b`）。[来源: `git log pre-window-freeze..main`]
- Addendum 04（B4 调用策略登记）：`3319655`（PR #21，合并 `54f5006`）。[来源: `git log pre-window-freeze..main`; docs/P3_PREREG_ADDENDUM_04.md:1-9]
- **[PR#20 仅分支]** B4-strict/B4-tiebreak、`s2-b4-dev`、LLM 缓存与 B4 Meterless 验证：提交 `92e2b89`、`c852566`，未合并，尚不属于 main，因此也尚未处于 `pre-window-freeze..main` 范围内。[来源: `git log main..pr20`; PR #20 state=open]
- 修改 `v0-baseline`/赛前文件的窗口内改动（例如 `src/rra/evidence/episode.py`、`src/rra/sim/world.py`）需逐个划分新旧：[UNKNOWN]（本草稿未做逐文件、逐行的新旧划分）。[来源: HACKATHON_BASELINE.md:57, 60]

## 9. 局限与未完成项

### 9.1 已在仓库中书面记录的

- PR #20 未合并；其证据包为缩减版（观测仅含 time/observed_x/nominal_x；反馈仅含 issued_time/execution_time/accepted/success；无在场事件；已知配置仅含 dt 与 tolerance），不符合 Addendum 03 §2 第 4 项，被记为须在实现候选冻结前更正的待修缺陷；该次运行的结果不构成注册证据包下 B4 的证据。[来源: docs/P3_PREREG_ADDENDUM_04.md:51]
- 2026-10-23 dev 运行披露：386 条缓存响应中，71 条解析为 `{items:[...]}`，310 条解析为 JSON 但形状不符，5 条因 token 上限停止（4 条截断不可解析，1 条无内容）。[来源: docs/P3_PREREG_ADDENDUM_04.md:47]
- 该次运行中多数 B4-tiebreak 调用以 INVALID_PROPOSAL 回退；B4-tiebreak 与 B4-strict 或 B3 的差异被记录为由格式失败主导，不是文本上下文效应的证据。[来源: docs/P3_PREREG_ADDENDUM_04.md:49]
- 报告规则：若超过 50% 的 B4-tiebreak 生成器调用以 INVALID_PROPOSAL 或 PROVIDER_ERROR 回退，则 B4-tiebreak 结果须报告为"由提议格式或提供者失败主导"，且不得据此宣称文本上下文有收益或代价（H3；P3 §19 第 6 项）。[来源: docs/P3_PREREG_ADDENDUM_04.md:59]
- 按 Addendum 04 §6.1，每个 B4 变体须报告：LLM 调用数；合法提议、INVALID_PROPOSAL、PROVIDER_ERROR 与截断输出的计数；gate_reason 分布。[来源: docs/P3_PREREG_ADDENDUM_04.md:57]
- B4-strict 与 B3 的决策结果相等是按构造成立的，不是经验发现。[来源: docs/P3_PREREG_ADDENDUM_04.md:27]
- 请求格式（提示词、响应格式约束、解码设置、模型标识）可在实现候选冻结前更改，但不得使用 eval-v3。[来源: docs/P3_PREREG_ADDENDUM_04.md:53]
- eval-v3：种子未生成；B4 在注册证据包下的结果：**待 eval-v3，尚无结果**。[来源: docs/P3_PREREG_ADDENDUM_04.md:7; artifacts/h1/final-eval-v3-prohibition.json:4-8]
- main 上 B3 dev 的已提交产物含非零 `unsafe_action` 计数；决策记录写明"结果不得作为安全成功结论"。本草稿不引用其数字。[来源: artifacts/s2/b3-dev.md:1-24; decisions.md:33]
- V0 已知失败模式（修正包络、硬升级 fail-closed、边界放行、outcome 升级取舍、模型局限）及仿真器理想化声明："Results say nothing about hardware."[来源: FAILURE_MODES.md:7-16]
- 评估仅在合成仿真中；注册评估使用本地参考加载器而非实时 Zetaris。[来源: FAILURE_MODES.md:16; docs/P3_PREREG_ADDENDUM_03.md:49-51]
- Meterless：`npm audit` 在参考实现的 dev 依赖中报告 9 项（3 中、4 高、2 严重），按探针记录为仅 dev、未修复。[来源: docs/SPIKE_NOTES_20261019.md:31]
- 跨回合 Meterless "operations memory" 仅可作为明确标注的探索性演示功能，不得出现在注册结果表中；在 main 上是否已实现：[UNKNOWN]。[来源: docs/P3_PREREG_ADDENDUM_02.md:109-111]
- 最小演示要求的"回放 UI 由 Cursor 原生 agent 实现"：当前是否存在：[UNKNOWN]。[来源: docs/P3_PREREG_ADDENDUM_02.md:127-137; docs/DEV_WORKFLOW.md:11]
- 演示视频、幻灯片（Rule 6.1/6.2）：仓库内不存在对应文件。[来源: `git ls-tree -r main --name-only` 无相应文件] [UNKNOWN: 外部是否已存在]
- 日期/环境不一致备注：README 要求 Python 3.11，而 Zetaris 与 Meterless 回执记录的运行环境为 Python 3.12.3；两者关系未在仓库说明。[来源: README.md:21; artifacts/sponsor/zetaris-equivalence.json; artifacts/sponsor/meterless-persistence.json]
- 赛前 H1 文档与 P3 设计文档中仍保留 10-15/10-20 的旧窗口日期，以 Addendum 03 §1 为准。[来源: docs/H1_EVAL_FOUNDATION.md:5; docs/P3_SYSTEM2_DESIGN.md:9; docs/P3_PREREG_ADDENDUM_03.md:13]
- `decisions.md` 引用了 `REPORT_D1.md`，该文件不在仓库内。[来源: decisions.md:32; `ls` 无 REPORT_D1.md]

### 9.2 本草稿未完成的部分

- 对 PR #20 分支上的代码和产物，本草稿只做了文件清单与 PR 描述转述，没有运行、没有逐行审阅。[来源: 本草稿工作过程；`git diff --stat main...pr20`]
- 没有核对 main 上全部测试是否通过；没有重跑任何确定性基准。[来源: 任务约束（不运行实时调用）；本草稿未执行 pytest]

## 10. 需所有者裁决 / 填写清单

1. **[所有者填写]** 第 7 节 Cursor 使用方式（Rule 6.4 要求；本草稿未编造）。 [来源: 本清单项；依据见前文对应章节]
2. **[所有者裁决]** Cursor 规则状态：2026-10-22 "可选"公告不在仓库，需提供公告原文或链接并决定提交说明按哪一版规则写（状态 UNKNOWN）。 [来源: 本清单项；依据见前文对应章节]
3. **[所有者裁决]** 对"成功/失败/负结果"的整体措辞：包括 H1/H6 预注册的负面发现框架（B2 持平、B3 与 B4 持平时的表述）、B3 dev 中非零 `unsafe_action` 与 `Recoverable challenge success` 如何呈现、V0 基线数字是否出现在提交说明中。本草稿一律未作决定。 [来源: 本清单项；依据见前文对应章节]
4. **[所有者裁决]** B4 在 2026-10-23 dev 运行中的格式失败（Addendum 04 §5）：提交说明是否披露、披露到何种细节；§6.2 的 50% 报告规则最终对 eval-v3 的适用方式。 [来源: 本清单项；依据见前文对应章节]
5. **[所有者裁决]** PR #20 是否并入 main 再提交；若不并入，B4 相关内容是否从提交说明移除或标注为"未合并"。缩减版证据包（A04 §5.3）的修复状态与时间。 [来源: 本清单项；依据见前文对应章节]
6. **[所有者填写]** 主办方对集成深度的期望：2026-10-21 onboarding 的结论、Meterless 的"组件"与"最小集成"要求（SPIKE_NOTES UNKNOWN，原样保留在第 4.4 节）。 [来源: 本清单项；依据见前文对应章节]
7. **[所有者裁决]** 是否把"参考实现 + 宿主侧桥"表述为满足 Rule 5.1 的 Meterless 集成。 [来源: 本清单项；依据见前文对应章节]
8. **[所有者填写]** 赛道最终选择（设计文档写明由所有者在提交前决定；规则快照中编号为 TRACK 03）。 [来源: 本清单项；依据见前文对应章节]
9. **[所有者填写]** 演示视频（1–4 分钟）与幻灯片的位置；回放 UI 是否存在；Zetaris 令牌到期日 2026-11-17 对评审期演示可用性的影响；NVIDIA 速率限制（UNKNOWN）。 [来源: 本清单项；依据见前文对应章节]
10. **[所有者裁决]** 窗口内对赛前文件的改动（如 `episode.py`、`world.py`）如何向评委划分新旧，以及是否在提交表单中单独声明赛前组件（Rule 5.4）。 [来源: 本清单项；依据见前文对应章节]
11. **[所有者裁决]** Docker 镜像目前不含 `bridges/`、`scripts/`、`artifacts/`：是否需要在提交说明中说明 Zetaris/Meterless 路径的复现边界，或另行提供镜像。 [来源: 本清单项；依据见前文对应章节]
12. **[所有者核实]** `nvidia/nemotron-3.5-super-vl-120b-a12b` 与服务端返回的 `private/nvidia/nemotron-3.5-super-120b-a12b` 之间的关系，以及提交说明中应写哪一个。 [来源: 本清单项；依据见前文对应章节]
13. **[所有者核实]** Python 3.11（README）与 3.12.3（赞助方回执）的差异是否需要在复现步骤中说明。 [来源: 本清单项；依据见前文对应章节]
14. **eval-v3**：待 eval-v3，尚无结果。所有涉及 eval-v3 或 B4 效果的段落须在 eval-v3 完成并按 Addendum 04 §6 报告规则处理后，才可由所有者决定措辞。 [来源: 本清单项；依据见前文对应章节]
