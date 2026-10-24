# 提交表单声明框架（给所有者填写）

状态：**DRAFT / 框架 / 未经所有者审阅 / 不是提交内容**。本文件只列出需要所有者回答的问题和可供引用的仓库证据位置；所有声明内容、措辞与取舍留给所有者。[来源: 本文件约定]

## 0. 记号与范围

- 起草基线：`main` 头 `349d1e68ebf196f9f3b25d5e2f6746b6029401fe`（`git rev-parse HEAD`）。2026-10-24。
- `[所有者填写]` = 内容由所有者撰写，本文件不预填；`[所有者核实]` = 本文件给出候选清单，是否成立由所有者核对；`[所有者裁决]` = 由所有者决定，本文件只陈述事实与出处，不给建议措辞；`[UNKNOWN]` = 仓库中无依据。
- 本文件不评价任何开发做法，不判定合规与否，不替所有者决定披露措辞。
- 本文件未运行任何访问 Zetaris、Meterless 或 NVIDIA 的命令，未使用任何密钥。
- 规则文本来源：`docs/HACKATHON_RULES.md`，2026-10-11T07:08:28Z 的快照，内含旧版与新版两套条文（文件第 2 行）。本文凡引用规则，均给出该文件的行号。

---

## 1. Rule 6.4 — "how Cursor was used during development"

### 1.1 规则原文

- 新版 Rule 6.4："A clear explanation of how Zetaris and Meterless were integrated, how Cursor was used during development, where NVIDIA technology contributes, and what was unique about your use of the sponsor technologies." [来源: docs/HACKATHON_RULES.md:24, 171]
- 旧版 Rule 6.4：NOT FOUND ON PAGE。[来源: docs/HACKATHON_RULES.md:24]

### 1.2 需要所有者回答的问题

以下问题没有预设答案。每项的回答均为 **[所有者填写]**。

1. Cursor 在开发的哪些环节被使用过？（编辑器 / 终端 / Cursor Agent / 其他功能；按时间或按模块回答均可）
   - 回答：[所有者填写]
2. 哪些模块或提交中有 Cursor 参与？参与到什么程度？
   - 回答：[所有者填写]
3. 开发在 Cursor 中进行的方式：本地 WSL remote 工作区？终端代理是否在 Cursor 内运行？
   - 回答：[所有者填写]
4. `.cursor/rules/rra.mdc` 的作用，它在什么时候被加载、是否影响过实际开发？
   - 回答：[所有者填写]
5. Addendum 02 §7 提到“至少一个有界组件（演示 / 回放 UI）由 Cursor 原生 agent 实现”：该组件现在是否存在？由谁、用什么实现？
   - 回答：[所有者填写]
6. 开发中没有使用 Cursor 的部分，是哪些？
   - 回答：[所有者填写]
7. 评审若要核对，应指向哪些仓库内位置？（可从 1.3 选取，也可补充仓库外材料）
   - 回答：[所有者填写]
8. 以上回答中，哪些有仓库内的记录佐证，哪些只有所有者的记忆或仓库外材料？
   - 回答：[所有者填写]

### 1.3 可供引用的仓库证据位置（只列位置，不构成对使用方式的说明）

| 位置 | 内容（事实转述） | 出处 |
|---|---|---|
| `.cursor/rules/rra.mdc` | Cursor 规则文件，`alwaysApply: true`；首次提交 `cf611a2`（2026-10-22 22:06:08 +0800，PR #14）。文件第 84 行含一条关于提交信息中不带 AI 共同作者或 AI 生成署名行的规则 | `.cursor/rules/rra.mdc:1-5, 84`；`git log --format='%h %ci %an %s' -- .cursor docs/DEV_WORKFLOW.md` |
| `docs/DEV_WORKFLOW.md` | 逐模块的作者工具与审查者表（`s2-core`、`llm-context`、`cursor-rules` 三行，PR 列均为“待定”）；文末一句：开发在 Cursor 的 WSL remote 中进行，终端 agent 运行在 Cursor 内，回放 UI 将由 Cursor 原生 agent 实现 | `docs/DEV_WORKFLOW.md:1-11`（同一提交 `cf611a2`） |
| `docs/P3_PREREG_ADDENDUM_02.md` §7 | 预注册的 Cursor 使用计划：窗口内开发在 Cursor（WSL remote 工作区）中进行；终端代理在 Cursor 内运行；使 6.4 可审计的三项措施（`.cursor/rules`、`DEV_WORKFLOW.md`、一个由 Cursor 原生 agent 实现的有界组件）；“此节对基准无影响” | `docs/P3_PREREG_ADDENDUM_02.md:127-137` |
| `HACKATHON_BASELINE.md` | 一句：V0 开发未使用 Cursor（V0 指 `v0-baseline`，赛前） | `HACKATHON_BASELINE.md:20` |
| `docs/HACKATHON_RULES.md` | 新版 Rule 5.1、Rule 6.4 的 Cursor 条文 | `docs/HACKATHON_RULES.md:19, 24, 152-153, 170-171` |
| `docs/submission/DRAFT_SUBMISSION_v4.md` 第 7 节 | 云会话草稿中对 Cursor 的处理：该节内容留 `[所有者填写]`，只指路到以上位置 | 本分支 |
| `decisions.md` | 其中“Claude 裁决”字样的条目（例：2026-10-22 `SECOND_DYNAMICS_CHANGE` 一条）记录了裁决来源标注；未包含 Cursor 使用说明 | `decisions.md:31` |
| 提交历史 | 窗口内提交的作者字段；`git log` 的作者、提交者信息本身不记录所用编辑器或代理 | `git log --format='%h %ci %an %s' pre-window-freeze..HEAD` |

仓库内未找到的材料：Cursor 的使用记录（会话导出、截图、日志等）。[UNKNOWN: 仓库中无依据]

---

## 2. [所有者裁决] Rule 5.1 新版原文与开发中使用的其他代理和执行器

本部分只陈述事实与出处。**如何如实披露、披露到何种细节，以及 2026-10-22 “Cursor 改为可选”公告的状态，由所有者决定。**

### 2.1 规则文本

- 新版 Rule 5.1 原文："Every submission must integrate Zetaris and Meterless, and teams must use Cursor for development." [来源: docs/HACKATHON_RULES.md:19, 153]
- 旧版 Rule 5.1 原文："Any language, framework, model or cloud, including closed-source APIs and sponsor credits." [来源: docs/HACKATHON_RULES.md:19]
- 2026-10-22 “Cursor 改为可选”公告：仓库中没有公告原文，其真实状态与适用范围 **[UNKNOWN]**。仓库内唯一的提及是所有者在任务说明中的记录（非仓库文件），以及 `DRAFT_SUBMISSION_v4.md` 第 1 节对该记录的转述。[来源: 本分支 DRAFT_SUBMISSION_v4.md 第 1 节；仓库全文检索无公告原文]
- 窗口：2026-10-22 00:00 UTC 至 2026-10-27 23:45 UTC。[来源: docs/HACKATHON_RULES.md:145; docs/P3_PREREG_ADDENDUM_03.md:11-19]

### 2.2 开发过程中出现过的代理与执行器（事实与出处）

| 工具 / 执行器 | 仓库内可见的记录 | 出处 |
|---|---|---|
| Cursor（含终端 agent、Cursor Agent） | `DEV_WORKFLOW.md` 作者工具列：“Luna/Codex（在 Cursor 终端）”“Cursor Agent 起草 + Gemini CLI 收尾”；Addendum 02 §7 的计划 | `docs/DEV_WORKFLOW.md:7-9`；`docs/P3_PREREG_ADDENDUM_02.md:127-137` |
| Codex | `DEV_WORKFLOW.md` 作者工具列（“Luna/Codex”）；本地执行器；issue #26 记载其用完额度后停止 | `docs/DEV_WORKFLOW.md:7-8`；issue #26 评论 2026-10-24T06:04:22Z |
| Gemini CLI | `DEV_WORKFLOW.md` 作者工具列（`cursor-rules` 一行“Gemini CLI 收尾”） | `docs/DEV_WORKFLOW.md:9` |
| Claude | `DEV_WORKFLOW.md` 审查者列；`decisions.md` 中“Claude 裁决”字样的条目；`.claude/settings.json`（赛前基础设施提交，仅工具设置） | `docs/DEV_WORKFLOW.md:7-9`；`decisions.md:31`；`HACKATHON_BASELINE.md`（Pre-window infrastructure 一节） |
| Claude Code 云会话 | 本任务所在的会话类型；issue #26 描述其角色为只读审计与文档起草，工作限于 `cloud/*` 分支，“Only the owner merges PRs”；该分支上的文件（T1–T7、本文档所在分支）即其产出 | issue #26 正文；各 `cloud/*` 分支 |
| Grok 4.7 | issue #26 记载：Codex 用完额度后，FRZ-2A v3 与 EVAL-PATH 改由 Grok 4.7 接手，两者尚未合并 | issue #26 评论 2026-10-24T06:25:11Z |

- 上表是**仓库与 issue #26 中可见的记录**，不是完整的开发工具清单；是否还有其他工具或执行器：**[所有者填写]**。
- 各工具 / 执行器各自对应哪些提交、哪些模块：仓库的提交作者字段不区分（`git log` 作者均为 Xifeng Ming）；按模块的对应关系仅见 `DEV_WORKFLOW.md` 三行，其余 **[UNKNOWN]**。

### 2.3 待所有者决定的事项（只列问题，不给措辞）

1. 提交材料中如何描述开发所用的全部代理和执行器：**[所有者裁决]**
2. 新版 Rule 5.1 与 2026-10-22 公告之间，提交材料按哪一版写，是否附公告原文或链接：**[所有者裁决]**
3. 是否需要在提交前向主办方确认上述两点：**[所有者裁决]**

---

## 3. Rule 4.2 / 赛前组件声明（Rule 5.4 新版；旧版 Rule 5.2）

### 3.1 规则原文

- Rule 4.2（两版相同）："Work committed before the window opens is not eligible, except for clearly declared pre-existing components." [来源: docs/HACKATHON_RULES.md:18, 146-147]
- 新版 Rule 5.4 / 旧版 Rule 5.2："Pre-existing open-source libraries are fine. Pre-existing product code must be declared in the submission form." [来源: docs/HACKATHON_RULES.md:20, 158-159]

### 3.2 界线（来自 `HACKATHON_BASELINE.md`）

- `v0-baseline` 为不可变的原始 V0 快照，提交 `546e82aefd4e07bf304d79c63dcffe6dd4b7c4ee`（标签对象 `11c45959397f029f5cb9eedfaa498514ec185b74`）。[来源: HACKATHON_BASELINE.md:5; `git rev-parse v0-baseline v0-baseline^{commit}`]
- `pre-window-freeze` 标签对象 `7dccc2532e3b248e2e93e274ace0fd659db1745f`，指向提交 `3b56637681551f21c6b4c253be6def59389d1051`（2026-10-19 22:38:27 +0800），是 `main` 的祖先。[来源: `git rev-parse pre-window-freeze pre-window-freeze^{commit}`; `git log -1 --format=%ci pre-window-freeze`]
- 基线文件声明：从 `pre-window-freeze` 可达的一切为赛前已有工作，不会被呈现为窗口内工作。[来源: HACKATHON_BASELINE.md:7]
- 基线文件同时写明：这不单独决定资格或主办方如何评判。主办方的判定方式 **[UNKNOWN]**。[来源: HACKATHON_BASELINE.md:7]

### 3.3 赛前组件清单（声明为 pre-existing）

内容为 `HACKATHON_BASELINE.md` 的转述；是否原样用于提交表单 **[所有者填写]**。

| 组 | 内容 | 提交 / 范围 | 出处 |
|---|---|---|---|
| V0 组件 | 种子化 2D 传送带世界（名义、bias、drift、moving-target、load-step、combo 场景）；名义抓取规划器；残差监视器与启发式扰动分类器；纠正器（±0.5 s 有界时间修正、可行性检查、固定 fail-closed 残差阈值）；确定性控制器；回合运行器（每对象一个终态，outcome escalation）；JSON 回执；同种子开/关基准；dev/eval 工具与盲评协议；CLI、Dockerfile、测试、文档与规则快照 | `v0-baseline` = `546e82a` | HACKATHON_BASELINE.md:9-18 |
| V0 的赞助方与 Cursor 状态 | V0 不含 LLM 集成，未使用 Zetaris、Meterless、NVIDIA；V0 开发未使用 Cursor | `v0-baseline` | HACKATHON_BASELINE.md:20 |
| 赛前基础设施 | CI 工作流 `.github/workflows/ci.yml`、仓库工具设置 `.claude/settings.json`；基线文件称仅为工具/配置，不提交评审 | `90821fc55d7581a156c68ec3cadc135738ff4ab6`、`a1287c3386044c4723a68378e870090eca87f032`、合并 `38f8ce139bf90de659a192f4456821dcff0db4a8` | HACKATHON_BASELINE.md:22-29 |
| 赛前 P3 预注册 | 4 个文档提交（`docs/P3_SYSTEM2_DESIGN.md`），只改文档 | `879dab82ab24344e0ece9a868f0a5466388203b9` 至 `024ea2e3e66b91f5a2157a66c073493e7107e109` | HACKATHON_BASELINE.md:35-37 |
| 赛前 H1 评估基础 | 18 个提交，改动 `src/rra/eval/*`、`src/rra/evidence/*`、`src/rra/sim/*`、`artifacts/h1/`、`config/v3_contracts.json` 及若干文档；基线文件写明 H1 改动了运行时/源码实现，不能被描述为仅工具配置 | `095ea10b3ad3b1a2d7b81c841c7cd7bacfed3f79` 至 `b0288da5cf7a924ce9b47b0ea9f7d6248f5f6bd0` | HACKATHON_BASELINE.md:39-64 |
| 赛前 Addendum 01–03、赞助方探针笔记 | 按其自述为赛前预注册 / 设计输入 | 见各文件头部 | docs/P3_PREREG_ADDENDUM_01.md:3-5；docs/P3_PREREG_ADDENDUM_02.md:3；docs/P3_PREREG_ADDENDUM_03.md:3；docs/SPIKE_NOTES_20261019.md:3 |

### 3.4 窗口内新工作清单（`pre-window-freeze..main`）

范围：`git rev-list --count pre-window-freeze..HEAD` = 66 个提交，最早 `b8d884a`（2026-10-22 21:11:38 +0800），最晚 `349d1e6`（2026-10-24 14:24:43 +0800）。以下按 `git log` 的提交主题分组，只列出处；各组是否对应“窗口内新工作”的最终声明 **[所有者核实]**。[来源: `git log --format='%h %ci %s' pre-window-freeze..HEAD`]

| 组 | 提交 / PR | 提交主题（节选） |
|---|---|---|
| System-2 确定性核心与升级交接 | `b8d884a`、`ccbefb3` | “add deterministic System-2 core”；“add isolated System-2 escalation handoff” |
| v3 上下文族、提议器、NIM 重放缓存 | `9ff81e1`、`bb8eb49`、`f65ba5b`、`9110cb3`、`b62691b` | context families；hypothesis proposer；NIM replay cache and smoke runner；disable Nemotron thinking；map second dynamics change text |
| Cursor 规则与开发流程记录 | `cf611a2`（PR #14，合并 `1ec5761`） | “add Cursor rules and development workflow record” |
| S2 核心、B3 dev 命令及其修复 | PR #12（合并 `cbc1f8a`）、#13（`345b6f9`）、#15（`198ab6a`）、#16（`2a3b52d`）；`7ea70ce`、`d11ce8b` 等 | B3 dev evaluation command；S2 授权、重放、receipt 相关修复（主题含 P3 章节号） |
| Meterless 持久化 / 重放桥 | `8eb7492`（PR #17，合并 `90054ca`） | “Meterless S2 run persistence and replay bridge (A02 §5)” |
| Zetaris 两源证据包路径 | `92dac5a`（PR #18，合并 `d54faa7`） | “add Zetaris two-source packet path (A02 §4)” |
| L5a 卫生 / 重放键 / 结构 ID | `ab509d3`（PR #19，合并 `2ff7a6b`） | “L5a: hygiene + replay key + structure IDs” |
| 预注册补遗 04 | `3319655`（PR #21，合并 `54f5006`） | “docs: add P3 preregistration addendum 04” |
| B4-strict / B4-tiebreak、`s2-b4-dev`、LLM 缓存 | `92e2b89`、`c852566`（PR #20，合并 `9fe1730`） | “Add B4 strict and tiebreak dev runner”；“Fix B4 artifact receipts and D4 fallback” |
| Python 3.12 运行时 | `745f8a8`（PR #22，合并 `612b06e`） | “ci: move runtime to Python 3.12” |
| 预注册补遗 05 | `a7dfa14`、`cabff0a`（PR #23，合并 `520b7cf`） | “docs: add P3 preregistration addendum 05”；“addendum 05 section 1 as re-observation hold” |
| FRZ-1（Addendum 05 实现） | `7ca3268`、`71ce80d`、`244b670`、`67bc419`、`154522b`、`56f36b0`、`afa2aa6`、`aa3dd1c`、`6d0b205`、`7e2c4a7`、`e942024`、`cb77107`（PR #24，合并 `5a05f6d`，2026-10-24 13:06:51 +0800） | 重观测保持、平局规则、replay 缺失传播、平台记录等 |
| 预注册补遗 06 | `83440e9`、`11bc637`（PR #25，合并 `349d1e6`） | “docs: add P3 preregistration addendum 06”；“register owner rulings R6-R9 and raise eval-v3 B4 cap in addendum 06” |
| 云会话产出（不在 main） | `cloud/t1-…` 至 `cloud/t7-…` 分支及本分支 | 只读审查、诊断、草稿；不属于 `pre-window-freeze..main` |
| 进行中（未合并） | FRZ-2A（issue #26 记为 PR #27）、EVAL-PATH、FRZ-2B | 状态“进行中”；不在 main |

### 3.5 窗口内修改过的赛前文件（逐个列出；新旧划分留 [所有者核实]）

范围：`git diff --name-status pre-window-freeze HEAD` 中状态为 `M` 的文件，共 13 个；“窗口内提交”列为 `git log --reverse pre-window-freeze..HEAD -- <文件>` 的结果。本文件没有做逐行的新旧划分。[来源: `git diff --name-status pre-window-freeze HEAD`; `git log --format=%h --reverse pre-window-freeze..HEAD -- <文件>`]

| 文件 | 窗口内提交（按时间） | 新旧划分 |
|---|---|---|
| `src/rra/evidence/episode.py` | `ccbefb3` `7c0f45f` `00385e2` `7f50fca` `5033f4f` `821846b` `9a2abf7` `1339fa3` `a832bd3` `408c852` `76c861f` `cdd6e59` `dbebe35` `ab509d3` `92e2b89` `c852566` `7ca3268` `71ce80d` `56f36b0` `6d0b205` `e942024` | [所有者核实] |
| `src/rra/eval/runner.py` | `ccbefb3` | [所有者核实] |
| `src/rra/eval/holdout.py` | `ab509d3` | [所有者核实] |
| `src/rra/eval/scenarios.py` | `ab509d3` | [所有者核实] |
| `src/rra/cli.py` | `7ea70ce` `92e2b89` | [所有者核实] |
| `tests/test_evidence.py` | `ab509d3` `154522b` | [所有者核实] |
| `requirements.txt` | `ab509d3` | [所有者核实] |
| `decisions.md` | `b8d884a` `9ff81e1` `b62691b` `9110cb3` `7ea70ce` `5661032` `745f8a8` | [所有者核实] |
| `README.md` | `745f8a8` | [所有者核实] |
| `README.en.md` | `745f8a8` | [所有者核实] |
| `Dockerfile` | `745f8a8` | [所有者核实] |
| `rra`（启动器） | `745f8a8` | [所有者核实] |
| `.github/workflows/ci.yml` | `745f8a8` | [所有者核实] |

补充事实：`HACKATHON_BASELINE.md:57, 60` 已把 `src/rra/evidence/episode.py` 与 `src/rra/sim/world.py` 列为 H1 阶段修改过的 `v0-baseline` 文件；`git diff --name-status pre-window-freeze HEAD` 中 `src/rra/sim/world.py` 不是 `M`（窗口内未再改动）。[来源: HACKATHON_BASELINE.md:57, 60；`git diff --name-status pre-window-freeze HEAD`]

### 3.6 需所有者回答的问题

1. 提交表单中的赛前组件声明写哪些条目、用什么粒度：**[所有者填写]**
2. 3.5 中每个文件的新旧划分，以及是否在表单中单独声明：**[所有者核实]**
3. 赛前 H1 评估基础（改动了 `src/rra/`）在声明中如何归类：**[所有者填写]**
4. 赛前 Addendum 01–03 与探针笔记是否作为赛前组件列出：**[所有者填写]**

---

## 4. Zetaris / Meterless / NVIDIA — "what was unique about your use of the sponsor technologies"

下列只列可引用的事实和出处。**“独特之处”的措辞、取舍与强调均为 [所有者填写]。** 本文件不对任何事实作“独特”与否的判断。

### 4.1 Zetaris

| 事实 | 出处 |
|---|---|
| 预注册角色：部署数据访问、治理、可审计的持久化与重放；不预先登记“Zetaris 或 Meterless 改善任何注册指标”的主张 | docs/P3_PREREG_ADDENDUM_02.md:50 |
| System-2 证据包由两个分离的数据源通过 Zetaris 联邦查询装配：S-TELEMETRY 与 S-OPS | docs/P3_PREREG_ADDENDUM_02.md:58-67 |
| 治理作为结构性泄漏控制：只有 C1 白名单字段与 P3 §12 上下文记录可写入 Zetaris 可达的数据源；静态检查枚举每个源的每一列 | docs/P3_PREREG_ADDENDUM_02.md:69-73 |
| 等价不变量：Zetaris 装配的证据包与本地参考加载器装配的证据包，规范 JSON 的 SHA-256 在 20 个 dev 回合的等价集上必须相等 | docs/P3_PREREG_ADDENDUM_02.md:75-81 |
| 已提交回执（记录值，本文件未重跑）：`T5: "PASS"`，20 个回合，`T3_anchor_mismatches: 0`，`T4_mismatches: 0`，`base_git_sha: 2a3b52dcf15cf352064f064e2a8b499c4fe06280`，Python 3.12.3 | artifacts/sponsor/zetaris-equivalence.json |
| 白名单回执 `extra_count: 0` | artifacts/sponsor/zetaris-whitelist.json |
| 标准库 REST 客户端；令牌取自环境变量；错误信息中令牌被替换为 `[REDACTED]` | src/rra/sponsor/zetaris.py:19-35 |
| 评估模式披露：注册评估（eval-v3）与基线 B1–B4 使用本地参考加载器；Zetaris 路径用于演示和等价回执，不用于注册评估；提交材料必须披露该评估模式 | docs/P3_PREREG_ADDENDUM_03.md:49-51, 59-61 |
| 访问路径：自管本地部署（Docker Compose 包），API 令牌到期日 2026-11-17 | docs/SPIKE_NOTES_20261019.md:6, 12 |
| 主办方对集成深度的期望、2026-10-21 onboarding 结论 | [UNKNOWN]，仓库中无记录（docs/SPIKE_NOTES_20261019.md:33） |

“独特之处”表述：[所有者填写]

### 4.2 Meterless

| 事实 | 出处 |
|---|---|
| 预注册角色：每次 System-2 决策运行持久化为 Meterless 管理的记录，用于检视推理轨迹、回放与演示证据链 | docs/P3_PREREG_ADDENDUM_02.md:95-101 |
| 记忆范围为回合内；注册运行中对其他回合只写不读，并有检查断言 | docs/P3_PREREG_ADDENDUM_02.md:103-107 |
| 决策不变性：持久化开/关在相同的录制 LLM 响应下须给出相同的 B4 决策 | docs/P3_PREREG_ADDENDUM_02.md:113-115 |
| 实现：Python 与 `bridge.ts` 通过 stdin/stdout JSON 行通信；固定 Meterless 提交 `1742dec56a66e58eef9dda2d2b865823758ca8cd`；映射 `source="rra.s2"`、`chatId=episode_id` | bridges/meterless/README.md:1-30 |
| 持久化是 `run_episode` 返回之后运行的包装，评估者真值键在存储前被剥除 | src/rra/sponsor/meterless.py:1-5, 21-24 |
| 已提交回执汇总（记录值，本文件未重跑）：20 个回合，`M1_roundtrip_mismatches: 0`，`M3_cross_episode_reads: 0`，`M4_replay_match: 20`，`M8_hidden_key_hits: 0`，`all_ok: true`；B4 一项为 "STALE: previous B4 section preserved; refresh deferred to FRZ-2 (requires NIM)." | artifacts/sponsor/meterless-persistence.json（`summary`，行 635 附近） |
| 赛前探针记录：开源路径 GO；参考实现为 TypeScript，RRA 为 Python，需要宿主侧适配器；检索看起来是词法 / 确定性的，不适合作为 RRA 的核心检索 | docs/SPIKE_NOTES_20261019.md:22-30 |
| 探针记录：参考实现的 dev 依赖 `npm audit` 报告 9 项（3 中、4 高、2 严重），按探针记录为仅 dev、未修复 | docs/SPIKE_NOTES_20261019.md:31 |
| 主办方是否将“参考实现 + 宿主侧桥”视为满足 Rule 5.1 | [UNKNOWN]，仓库中无依据 |

“独特之处”表述：[所有者填写]

### 4.3 NVIDIA

| 事实 | 出处 |
|---|---|
| 位置：NVIDIA NIM / Nemotron 是 B4 假设生成器的提供者，位于可替换适配器之后；不用于参数拟合、验证、歧义门或授权 | docs/P3_PREREG_ADDENDUM_02.md:121-125 |
| Rule 5.2（新版）使 NVIDIA 成为可选项；设计文档保留它是因为它是 B4 的 LLM | docs/P3_PREREG_ADDENDUM_02.md:123；docs/HACKATHON_RULES.md:154-155 |
| 兼容 OpenAI 接口的 NIM 客户端；端点 `https://integrate.api.nvidia.com/v1`；代码常量模型 `nvidia/nemotron-3.5-super-vl-120b-a12b`；密钥取自环境变量；请求按规范 JSON 的 SHA-256 做内容寻址缓存 | src/rra/llm/providers.py:13-14, 51-60, 76-84 |
| 默认关闭思考模式（`chat_template_kwargs={"enable_thinking": false}`）并纳入缓存键；决策记录写明服务端返回模型名为 `private/nvidia/nemotron-3.5-super-120b-a12b`，与代码常量不同；二者关系 | decisions.md:32；关系 [UNKNOWN] |
| B4 调用策略：仅当共享 B3 评估在该决策点无故障证据且歧义门结果为 AMBIGUOUS 时才调用生成器 | docs/P3_PREREG_ADDENDUM_04.md:13 |
| 注册 B4 结果必须由冻结响应缓存、禁用网络的代码生成；实时运行只用于填充缓存 | docs/P3_PREREG_ADDENDUM_04.md:43 |
| 请求格式、live 调用上限与时限的登记（eval-v3 至多 2,500 个不同 live 请求；格式模式选择规则） | docs/P3_PREREG_ADDENDUM_06.md §3.2–3.5 |
| 赛前探针：20 个并行请求均返回 HTTP 200；小 `max_tokens` 时可见内容可能为空 | docs/SPIKE_NOTES_20261019.md:17-18 |
| NVIDIA 对注册指标的贡献 | 待 eval-v3，尚无结果 |
| 速率限制 | [UNKNOWN]（docs/SPIKE_NOTES_20261019.md:20） |

“贡献在哪里”与“独特之处”表述：[所有者填写]

### 4.4 跨三者

- 三者组合使用方式中哪些点值得强调，以及是否提及 4.1 中的评估模式披露：[所有者填写]
- 演示视频（Rule 6.1）、幻灯片（Rule 6.2）中对应内容的位置：[所有者填写]（草稿见 `docs/submission/DECK_OUTLINE.md`、`VIDEO_SCRIPT.md`，位于 `cloud/t5-submission-refresh` @ `937188e14abb98e6743d759bd13982b8b919cf25`，不在 main）

---

## 5. 与其他清单的对应

- `DRAFT_SUBMISSION_v4.md` 第 10 节第 1、2、10、28、32 项指向本文件。
- 本文件中全部 `[所有者填写]` / `[所有者核实]` / `[所有者裁决]` 项在提交前须由所有者处理；本文件本身不是提交内容。
