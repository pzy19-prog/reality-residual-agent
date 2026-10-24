# T9a — Addendum 06 审查（冻结前）

- 审查对象：`docs/P3_PREREG_ADDENDUM_06.md`（下称 A06），main 头 `349d1e68ebf196f9f3b25d5e2f6746b6029401fe`（PR #25 合并；PR head `11bc637`）。实际 sha 与任务卡一致。
- 对照文件：`docs/P3_SYSTEM2_DESIGN.md`（P3）、Addendum 01–05（A01–A05）、`docs/EVAL_PROTOCOL.md`、§0 所有者裁决 R1–R9 及"其他已定"。
- 行号格式：`A06 §x.y:L` 表示 A06 的节号与文件行号；其他文件写作 `P3:L`、`A05 §x:L` 等。
- 范围说明：本文件只指出问题与影响，不提出预注册条文措辞，不做成败判定。`config/eval_seeds*.json` 未打开；`config/eval_seeds_v3.json` 仅做存在性检查（`test -e` → 不存在）。未运行任何种子生成脚本或 live 命令，未接触密钥。
- 为说明可检验性，审查时读了 main 上少量实现代码（只读）；这些代码位置只作为"后续审查应检查何处"的线索，不代表冻结候选 X 的状态。

---

## 1. 裁决覆盖表

| 裁决 | A06 出处 | 判定 | 说明 |
|---|---|---|---|
| R1 保持入口仅限快速层 ESCALATE 路径上的 PAUSE | §4.4:55；§4A R1:67 | 一致 | §4.4 明写 infeasible correction 与 episode 级结果升级触发的 `PAUSE_AND_REOBSERVE` 不进入 hold。§4.4 另外登记了三条细节（已终态目标不进入 hold；到期判定容差 1e-9 s；pick 窗口终点 = 名义到达时间 + dt/2，仅在重评采样点检查），这些是对 A05 §1.2/§1.4:15,19 的实现解读，不在 R1 原文内，见 §3 A-4。 |
| R2 维持 FRZ-1 现状（无保持且无 latch 时解除 safe_stop），88/5 行为披露 | §4.5:57；§4A R2:68 | 部分 | 行为登记与 R2 一致（包括清除"此前因其他原因设置的 safe stop"）。披露只写"one development object"，未写出所指对象（seed 88 / target 5）或其证据工件，读者无法据 A06 定位该对象。 |
| R3 episode 级 safe_stop 不在本次冻结范围，作为失败模式披露 | §4.6:59；§4A R3:69 | 一致 | §4.6 说明行为未变；R3 条写明"disclosed as a failure mode"。§4.6 正文本身未出现"failure mode"字样，披露落在 §4A，属表述位置问题，不影响判定。结果报告中如何呈现该失败模式未登记（见 §2 第 13 项）。 |
| R4 注册 runner：i7-10750H / Python 3.12.3 / NumPy 2.5.4 / scipy-openblas 0.3.34 | §2.1:25；§4A R4:70 | 一致 | 另含 x86_64 架构。A05 §4.1:41 要求的 receipt 平台字段（Python、NumPy、架构、CPU、BLAS）与此一一对应。 |
| R5 A05 §3.4 在注册 runner 上实现，B4 缓存在那里 live 重建 | §4A R5:71；相关 §3.3:39 | 部分 | 仅在 §4A 以一句话登记，正文无对应节。"rebuilt live"是指 eval-v3 缓存在注册 runner 上从空开始填充，还是也包括 dev 缓存（含 §3.2 探针工件）在注册 runner 上重建，未写明，见 §3 A-9。 |
| R6 B4 请求保留 passing[]（structure_id/rmse/n_usable）、current_time、horizon | §4.7:61（末段）；§4A R6:72 | 一致 | §4.7 写"exactly the items of owner ruling R6"。 |
| R7 观测/在场事件只含当前目标且字段完整（C1：8/4）；命令反馈为整个 episode（决策之前）；known_config 截取为 C1 5 字段 | §4.7:61；§4A R7:73 | 部分 | 三个范围与 R7 一致；known_config 5 字段逐一列出。观测 8 字段与在场事件 4 字段只写"all C1 fields"，未列名或计数（列表在 A01 item 4:73）。另 §4.7 登记保留 L3 簿记键 `episode_id`、`seq`（反馈另保留 `step`），这些非 C1 键随请求发送；main 上 `src/rra/evidence/sources.py:69` 把 `episode_id` 设为 `str(seed)`，若 eval 路径沿用，eval-v3 种子值会出现在请求体与缓存中，与 §1.3:17 的"不检视种子值"存在交互，见 §3 A-7 与 §5 M-3。"precedes the decision"对同一仿真时刻的反馈是否计入未定，见 §3 A-8。 |
| R8 A05 §2 二维平局按 (tau, delay) 字典序取最小 | §4.3:53；§4A R8:74 | 一致 | "tau"在 A05 §2:27 中对应 speed-step time。A06 未写明 tau 即 speed-step time，属术语对应问题，影响小。 |
| R9 请求模板 SHA-256：evidence_packet、s2_summary、context_text 三者替换为固定占位符后 canonical_json 取 SHA-256；模型标识记录服务端返回名 | §4A R9:75；§3.1:35 | 缺失，勘误待合并 | A06 R9 只将 evidence packet 与 System-2 summary 替换为占位符，缺 `context_text`。按合并版读法，模板哈希随每个文本变体变化，不再是"模板"哈希。所有者已要求另出带日期的勘误 PR，在冻结 tag 前合并。模型标识部分（服务端返回名；请求常量另记）与 R9 一致。另：R9 未写占位符的具体取值，也未写"canonical JSON"指哪一个函数，见 §3 A-10。 |
| 冻结 tag 名 `impl-freeze-v3` | 未登记 | 缺失 | A06 全文以"implementation-candidate freeze tag X"（§2.3:29）指代，未出现 tag 名。§1.2:15 的脚本以"HEAD 是否为 freeze-tag commit"为前置条件，tag 名未登记则该条件无可检验的具体对象。 |
| eval-v3 = 100 个 seed | §1.1:13 | 一致 | |
| B4 eval-v3 不同 live 请求上限 2,500 | §3.3:39；§5:85 | 一致 | 计数口径（重试、401/403 后续跑、错误响应）见 §3 A-12。 |
| NIM 预算已批准 | 未登记 | 缺失（非协议要素） | 预算属运营事项，A06 无需登记；列出仅为覆盖完整。§3.5:43 的"incomplete"判据只有上限与截止时间两种，预算耗尽是否同样按 incomplete 处理未写。 |

---

## 2. eval-v3 协议要素清单

| # | 要素 | A06 出处 | 状态与说明 |
|---|---|---|---|
| 1 | seed 数量 | §1.1:13 | 100。 |
| 2 | 生成方法（CSPRNG、范围） | §1.1:13 | `secrets.SystemRandom().sample`，无放回，`[10000, 2147483647)`；与 dev / v1 / v2 范围不重叠（与 `EVAL_PROTOCOL.md:5-7` 一致）。"sample" 的总体写法（`range(10000, 2147483647)`）未写出，但区间已唯一确定。输出列表顺序即 §1.4 的 index 顺序，A06 未明说"按生成顺序写入、不排序"，见 §3 A-1。 |
| 3 | 生成脚本与前置检查 | §1.2:15 | `scripts/gen_eval_v3_seeds.py`，三项拒绝条件（文件已存在、工作树不干净、HEAD 不是 freeze-tag commit）；只打印数量与 SHA-256。main 上该脚本尚不存在（`ls scripts` 无此文件），须在 X 中出现。 |
| 4 | 生成时机与隔离（P3 §18.1:838-850；A01 item 9:78） | §1.2:15；§1.3:17；§2.3:29 | 冻结 tag 之后、单进程、注册 runner。P3/A01 的"isolated context/process"由"single process"与"只打印数量与哈希"体现；生成该进程的执行者（所有者本人或 agent 会话）及其上下文是否与开发会话隔离，未登记。 |
| 5 | 种子文件单独提交、父提交为冻结 tag | §1.3:17；§2.3:29 (b)；§5:81 | 已登记，并列为停止条件。 |
| 6 | 场景分配规则 | §1.4:19 | `i mod 19`：14 个组合结构，然后 5 个故障族；case 0–4 各 6 个、5–18 各 5 个（100 = 5×19 + 5，计算一致）。结构与故障族的具体顺序以"follows the development runs"引用实现（main 上 `src/rra/eval/b3_dev.py:104`、`b4_dev.py:80`、`evidence/sources.py:50` 均为 `index % 19`，故障族顺序见 `src/rra/eval/scenarios.py:12-14`），A06 未逐项列出。P3 §13.4 结构 holdout（`AND(SPEED_STEP,ACTUATOR_DELAY)`，`artifacts/h1/structural-holdout.json`）在 eval-v3 中属于哪个 case、是否单独报告，未登记。P3 §13.1:537-548 的 V0 已知族场景是否属于 eval-v3，未说明。 |
| 7 | 文本条件 | §1.5:21 | 每个物理 episode 跑 P3 §12.2 的四个配对条件，使用"dev 所用的冻结 context generator"。main 上同时存在 `src/rra/eval/context_v3.py` 与 `src/rra/eval/text_context.py`，A06 未指名，见 §3 A-6。P3 §12.2:515 写"every eligible physical eval episode"，A06 未说明 eligible 的判定（读作全部 100 个）。 |
| 8 | 各基线的运行方式与次数 | §1.5:21；§2.2:27；§2.3:29 (c)；§3.3-3.4:39-41 | 行：B1(corrected)、B2、B3、B4-strict、B4-tiebreak、B1-legacy（诊断）。B1/B1-legacy/B2/B3 每物理 episode 一次；B4 每 (seed, 文本条件)。B2 = (T 1.15, R 2.15)，与 `artifacts/h1/b2-grid.json` 的 `selected` 一致（该工件 `eligible: false`，即按 P3:670 的无可行对规则选出；A06 未提，属已有工件事实）。"run exactly once from the commands of X"：具体命令未在 A06 中列出，只引用 X；B4 的"一次"与 live 续跑及两次 replay 的关系见 §3 A-2。 |
| 9 | 产物位置 | 未登记 | A06 只写"result artifacts committed in one or more commits Z after Y"（§2.3:29 (d)）；结果工件路径、缓存目录（dev 缓存在 `artifacts/llm_cache/`，A04 §5.1:101）是否与 eval-v3 缓存分开、缓存是否提交，未登记。 |
| 10 | 续跑规则 | §3.3:39 | "may be resumed after an interruption"。续跑是否允许跨进程/跨日、续跑前后 X 是否须一致、已缓存的错误响应是否重发，未登记，见 §3 A-12。 |
| 11 | 401/403 停止 | §3.3:39 | "HTTP 401 or 403 stops the run"。停止后是否可在修复凭据后续跑、或直接按 §3.5 incomplete 处理，未登记，见 §3 A-13。 |
| 12 | 2,500 上限与"未完成"判定 | §3.3:39；§3.5:43；§5:85 | 已登记上限、incomplete 报告方式（完成的 (seed, 文本条件) 对数量）、"不主张 B4 收益或代价"。超过 2,500 列为停止条件。incomplete 时如何生成被报告的数值（A05 §3.1:31 要求 replay 遇缓存未命中即中止）未登记，见 §3 A-14。 |
| 13 | 10-27 06:00 UTC 截止 | §3.5:43 | 已登记。截止只针对 live 填充还是包括两次 replay 与结果提交，未写；见 §3 A-15。该时刻早于 A03 §1:13 的 build window 结束（10-27 23:45 UTC），无冲突。 |
| 14 | 格式选择规则：探针集定义 | §3.2:37 | "33-seed development subset 上按 seed 顺序与文本变体顺序收集的前 10 个不同 B4 请求"。"不同"的判定口径（含/不含 response-format 字段）未写，见 §3 A-16。 |
| 15 | 格式选择规则：比较指标 | §3.2:37 | "most valid proposals (non-empty items and no error under the adapter rules)"。"non-empty items"是过滤未知 ID 之前还是之后计数，未写；与 A04 §3 rule 1 的"usable"定义不同（A04 中空列表可用，走 rule 4），见 §3 A-17。 |
| 16 | 格式选择规则：平局规则 | §3.2:37 | `json_object` > `json_schema` > `nvext_guided_json`。 |
| 17 | 格式选择规则：选定后写入冻结代码 | §3.2:37 | "selected mode becomes the default in X, and the probe artifact is committed before X"。探针后若请求格式另有改动（A04 §5.4:107 允许冻结前改动），探针结果是否须重做，未登记，见 §3 A-18。 |
| 18 | 模型 | §3.1:35；§4A R9:75 | 请求模型 = X 中的 `NIM_MODEL`（main：`src/rra/llm/providers.py:14`）；逐响应记录服务端返回名。 |
| 19 | 结果报告规则（与 A04 §6 的关系） | §3.2:37（只引 A04 §6.2）；§3.5:43 | A04 §6.1:111 的逐变体计数与 §6.2:113 的 50% 规则对 eval-v3 继续适用（A06 未改动）。A06 只在 §3.2 提及 §6.2；B4 incomplete 时 §6.1/§6.2 是否仍按已完成部分计算，未登记。A05 §3.3:35 的 `llm_calls` 计数、A05 §4.3:45 的平台报告、A03 §3:51 的评估模式披露，A06 未重复，按上位文件继续有效。R2/R3 披露在结果报告中的呈现方式未登记。 |
| 20 | 不因结果修改的承诺 | §2.4:31；§5:82 | 已登记（实现、阈值、提示词、格式模式、种子均不因结果改动）；与 P3 §18.1 item 7:850、EVAL_PROTOCOL rule 3:13 一致。 |
| 21 | 种子值不可检视的时段 | §1.3:17；§5:83 | "所有已登记基线运行完之前"不检视；之后在结果 receipt 中出现。B1 等行的结果先于 B4 提交时，其 receipt 是否已含种子值，见 §3 A-3。 |
| 22 | replay 生成与一致性 | §3.4:41；§5:84 | 两次 replay、receipt 相同；含 replay-cache-miss fallback 无效。与 A04 §4:97、A05 §3.1:31 一致。A04 §4 的"network disabled"A06 未重复，按引用继续有效。 |

---

## 3. 歧义与可检验性

每条：原句 → 读法 1 / 读法 2 → 对实现的影响 → 检验设计（只设计，不执行）。

**A-1 种子列表顺序（§1.1:13 + §1.4:19）**
- 读法 1：`sample()` 的返回顺序原样写入文件，index i 即该顺序。读法 2：写入前可排序（如升序），index i 按排序后顺序。
- 影响：同一组种子在两种读法下 case 分配不同；若脚本排序，§1.4 的"follows the development runs"与 dev 种子（升序）一致但与 sample 顺序不一致。
- 检验（FRZ-2A）：读 `scripts/gen_eval_v3_seeds.py` 源码，确认写入前是否有 `sort`；用替身输出路径和固定 `random.Random(0)` 打桩做单元测试，核对 JSON 列表顺序与 sample 返回顺序。不在真实路径运行。

**A-2 "every row run exactly once"（§2.3:29 (c)）与 B4 续跑、两次 replay（§3.3:39，§3.4:41）**
- 读法 1："一次"指一次完整的注册流程（live 填充可多次续跑 + 两次 replay 都算同一次运行）。读法 2：每行恰好一次进程执行；续跑或第二次 replay 违反。
- 影响：读法 2 下 §3.3/§3.4 与 §2.3 自相矛盾；读法 1 下需要界定"一次"在 B1/B2/B3 是否也允许中断后续跑。
- 检验（EVAL-PATH）：核对 B1/B2/B3 的命令是否有续跑开关；若有，对照 A06 判断是否被允许；B4 路径确认 live 与 replay 是两个不同命令且 replay 输出只来自缓存。

**A-3 "no person or agent inspects the seed values before all registered baselines have been run"（§1.3:17）与结果提交 Z（§2.3:29 (d)）**
- 读法 1：只要不"查看"即可；B1 等行的结果文件（含种子值）可在 B4 完成前提交。读法 2：任何含种子值的工件在全部行完成前都不得写入可被读到的位置（包括提交、日志、终端输出）。
- 影响：读法 2 下运行脚本的日志、进度输出、B1 结果 receipt 都不能打印种子；读法 1 下需要另有措施防止 agent 会话读到。
- 检验（EVAL-PATH）：静态检查所有 eval 命令的 stdout/stderr 输出路径与日志字段，是否打印 seed 或 episode_id；在 dev 种子上用替身运行时抓取输出，grep 种子值。

**A-4 §4.4:55 三项细节相对 A05 §1:13-21**
- "A target that already has a terminal outcome does not enter a hold"、"due test uses a 1e-9 s tolerance"、"pick-window end … nominal plan arrival time plus dt/2 and is checked at re-evaluation samples"。
- 读法 1：这些是 A05 §1.2/§1.4 的实现细化，A05 本身未变。读法 2：其中"只在重评采样点检查窗口终点"改变了 A05 §1.4:19"the point after which an authorized command could no longer execute"的触发时刻（A05 读作连续时间点，A06 读作离散检查）。
- 影响：读法 2 下 hold 结束可能比 A05 字面晚至多一个重评间隔（0.5 s 级），影响 `REOBSERVE_EXHAUSTED` 的时刻与理由后缀统计。
- 检验（FRZ-2A）：构造窗口终点落在两次重评之间的合成用例，检查 hold 在何时以何种理由结束；对照 A06 §4.4 与 A05 §1.4 两种读法各自的预期。

**A-5 §4.5:57 "including a safe stop set earlier for another reason (one development object)"**
- 读法 1：仅对 hold 期间被 S2 授权的路径清除 safe stop。读法 2：任何 hold 结束（含 `REOBSERVE_EXHAUSTED`）后也清除。
- 影响：读法 2 会扩大"其他原因 safe stop 被清除"的范围。
- 检验（FRZ-2A）：对 dev 对象 seed 88 / target 5（任务卡所称）和一个以 `REOBSERVE_EXHAUSTED` 结束的合成用例，检查 safe stop 标志的变化点。

**A-6 "the frozen context generator used in development"（§1.5:21）**
- 读法 1：`src/rra/eval/context_v3.py`（main 上 `b4_dev.py:17` 引用）。读法 2：`src/rra/eval/text_context.py`（main 上仍存在，选择函数不同）。
- 影响：两个模块的变体选择规则不同（`context_v3.py:138,143` 与 `text_context.py:55,57`），会产生不同文本。
- 检验（EVAL-PATH）：确认 eval-v3 路径只 import 一个生成器；对 dev 种子比较 eval 路径与 dev 路径产生的 `content_sha256` 一致（A03 §2 item 7:47）。

**A-7 L3 簿记键随请求发送（§4.7:61 "Rows keep the L3 bookkeeping keys `episode_id` and `seq`"）**
- 读法 1：保留在 L3 存储的行中，但发送给生成器前剔除。读法 2：随请求一并发送给生成器（"Rows keep"出现在描述请求内容的段落中）。
- 影响：读法 2 下，若 `episode_id = str(seed)`（main 上 `src/rra/evidence/sources.py:69`），eval-v3 种子值进入外部服务请求、缓存文件和缓存键；与 §1.3 的不检视要求、P3 §12.2:529 的泄漏限制（种子本身不是隐藏参数，但属 eval 标识）均有交互。另外 `known_config` 的 `episode_id` 在 `sources.py:107` 被剔除，而观测/事件/反馈行未剔除，二者不对称。
- 检验（EVAL-PATH）：对一个 dev 种子生成最终请求体（不发送），列出所有键，确认 `episode_id` 的值来源（种子 / 其他标识）以及是否出现在 `messages[].content` 中。

**A-8 "all command feedback in the episode that precedes the decision (no later feedback)"（§4.7:61）**
- 读法 1：`execution_time`（或 `issued_time`）严格小于决策时刻。读法 2：小于等于决策时刻（同一仿真步内已产生的反馈计入）。另：以 `issued_time`、`execution_time` 还是 `step` 判断先后未写。
- 影响：同步内的反馈是否进入请求，改变请求体与缓存键。
- 检验（FRZ-2A/EVAL-PATH）：构造同一步内先有反馈后有决策的用例，检查反馈是否在包内；读过滤条件的比较运算符与字段。

**A-9 R5 "the B4 cache is rebuilt live there"（§4A R5:71）**
- 读法 1：只指 eval-v3 缓存。读法 2：dev 缓存与 §3.2 探针也要在注册 runner 上重建。
- 影响：读法 2 下 dev 侧 B4 工件与探针工件须在 X 之前于注册 runner 上重新生成。
- 检验（FRZ-2A）：检查 X 之前提交的探针工件与 dev B4 工件的 receipt 平台字段是否为 §2.1 的 runner。

**A-10 R9 模板哈希（§4A R9:75）**
- 除 context_text 缺失（§5 M-1）外：占位符取值未写；"canonical JSON"未指明函数（键排序、分隔符、`ensure_ascii`）；A05 §3.4 的浮点 6 位舍入是在替换前还是替换后施加未写（替换后不影响，但若 summary 之外还有浮点字段则相关）。
- 影响：不同实现产生不同模板哈希；两种合理实现均"符合"条文。
- 检验（FRZ-2A）：同一 X、同一配置下，对两个不同 (seed, 文本条件) 的最终请求计算模板哈希，预期相同；改动系统提示词一个字符，预期不同。

**A-11 §3.1:35 与 R9 的"model name"**
- 读法 1：模板哈希覆盖请求中的 `NIM_MODEL`（请求常量）。读法 2：覆盖服务端返回名。
- 影响：读法 2 会使模板哈希依赖响应，失去"请求模板"含义。R9 后半句已分开记录两者，读法 1 更贴合，但正文未明说。
- 检验（FRZ-2A）：确认模板哈希函数输入只来自请求体。

**A-12 "At most 2,500 distinct live requests"（§3.3:39；§5:85）**
- 读法 1：按缓存键（最终请求体 SHA-256）去重计数，重试与续跑不增加计数。读法 2：按实际 HTTP 调用次数计数（含重试，main 上 `b4_dev.py` 有指数退避重试）。
- 另：错误响应（5xx、超时）是否写入缓存。main 上 `adapter.py:110` 将 `OSError` 等转为 `Proposal(error=…)`；若错误不入缓存，replay 时会缓存未命中并按 A05 §3.1 中止；若入缓存，续跑时不会重发。
- 影响：计数口径决定何时触发 §3.5 incomplete 与 §5 停止条件；错误是否入缓存决定 replay 能否完成。
- 检验（EVAL-PATH）：读计数器实现，确认计数对象；用 mock provider 注入一次 500 再成功，检查计数与缓存内容。

**A-13 "HTTP 401 or 403 stops the run"（§3.3:39）**
- 读法 1：停止后可在修复凭据后续跑（属"interruption"）。读法 2：停止即终止，B4 按 §3.5 incomplete 报告。
- 影响：两种读法下 B4 行是否可能完整。
- 检验（EVAL-PATH）：mock provider 返回 401，确认进程非零退出、缓存未写入该响应、续跑命令的行为符合所有者选定读法。

**A-14 incomplete B4 行的数值来源（§3.5:43 与 §3.4:41、A05 §3.1:31）**
- 读法 1：incomplete 时只报告完成对数，不生成 B4 指标。读法 2：对已完成的 (seed, 文本条件) 子集做 replay 并报告指标（但"no benefit or cost is claimed"）。
- 影响：读法 2 需要一个只遍历已完成对的 replay 入口，否则 A05 §3.1 的缓存未命中中止会使 replay 无法完成；该入口本身是 A06 未登记的新运行方式。A04 §6.1 的计数在读法 1 下无从报告。
- 检验（EVAL-PATH）：确认 replay 命令是否有子集参数；若有，确认子集由缓存内容决定还是由显式列表决定，以及 receipt 是否记录子集。

**A-15 "cannot be completed by 2026-10-27 06:00 UTC"（§3.5:43）**
- 读法 1：截止时刻 live 填充未完成即 incomplete。读法 2：截止前预估无法完成即可提前判 incomplete；或截止包括两次 replay 与结果提交。
- 影响：决定何时停止 live 调用、是否允许截止后做 replay。
- 检验（EVAL-PATH）：确认运行脚本是否内置截止检查，以及检查的对象（live 阶段 / 全流程）；receipt 是否记录 live 填充结束时间。

**A-16 探针集"first 10 distinct B4 requests"（§3.2:37）**
- 读法 1：按去除 response-format 字段后的请求去重（同一请求在三种模式下各发一次）。读法 2：按最终 provider 负载去重（三种模式的负载本就不同，"distinct"按某一模式定义）。另外"seed order and text-variant order"中变体顺序未指明（`context_v3.VARIANTS` 的元组顺序是一种可能）。
- 影响：探针集成员不同。
- 检验（FRZ-2A）：探针工件应列出 10 个请求的 (seed, 变体, 决策点) 与去重键；独立脚本按条文重算该列表并比较。

**A-17 "valid proposals (non-empty items and no error under the adapter rules)"（§3.2:37）**
- 读法 1：adapter 过滤未知 ID 之后 `items` 非空。读法 2：原始响应 `items` 非空。另：A04 §3 rule 1 的"usable"把空列表视为可用（由 rule 4 处理），§3.2 的"valid"与之不同；`finish_reason=length` 是否算 error 未写（A04 §3 rule 1 视为 truncated → 不可用）。
- 影响：模式得分与平局情况可能随读法变化，从而改变选定模式。
- 检验（FRZ-2A）：探针工件按两种读法各给一个分数；若两种读法选出的模式相同，歧义对结果无影响；若不同，提交所有者裁决。

**A-18 探针后的请求格式变更（§3.2:37 与 A04 §5.4:107）**
- 读法 1：探针后到 X 之间不得再改请求格式。读法 2：可改，探针结果仍有效。
- 影响：读法 2 下选定模式所依据的探针可能与 X 中的请求不对应。
- 检验（FRZ-2A）：比较探针工件记录的模板哈希（按勘误后 R9）与 X 中的模板哈希。

**A-19 §2.3:29 对 EVAL_PROTOCOL rule 1 的读法**
- `EVAL_PROTOCOL.md:11` 字面为"Eval seeds are frozen in their own commit before the implementation they measure"；A06 将其与 P3 §18.1 合读为"种子先于任何运行冻结，实现先冻结"。字面读法下种子应先于实现提交。
- 影响：顺序不同。A06 的读法与 P3 §18.1:844-848 的顺序一致；EVAL_PROTOCOL 不属于 P3/A01–05，此处列为歧义而非冲突。
- 检验（EVAL-PATH）：核对 git 历史 X → Y → Z 的父子关系与 `git diff X..Z -- src/` 为空。

---

## 4. 与上位文件的一致性

A06 自称"does not alter P3 or Addenda 01–05"（:9），§4A 自称"change no threshold, gate, scoring rule, or denominator"（:65）。逐项对照：

| 对象 | 上位条文 | A06 相关条文 | 结论 |
|---|---|---|---|
| verifier 阈值（≥6 可用观测、RMSE ≤ 0.030） | P3 §18:830 | 无 | 未改动。 |
| common-action / ambiguity gate、authorization gate | P3 §8.3、§9；A05 §1.6:23 | §4.4:55 | 未改动门控本身；§4.4 改变的是 hold 入口与结束时刻的实现解读（§3 A-4）。 |
| B4 调用条件 | A04 §1.1:67 | 无 | 未改动。 |
| B4 请求内容 | A03 §2 item 4:35（"full whitelisted evidence packet for the episode"）；A04 §1.2:69（"This addendum does not narrow it"） | §4.7:61；R7 | 观测与在场事件限于当前目标、known_config 限于 C1 字段，相对 A03 字面"for the episode"是收窄。A06 以所有者解读裁决 R7 登记，并声明"does not remove evidence in the sense of Addendum 03 Section 2 item 4"。该声明是解读而非条文对照可证的事实；按 §0 规则，因与 R7 一致，不列为冲突，但"不改变"的说法依赖 R7 的解读成立。另外 §4.7 相对 A04 §5.3:105 的缩减包是扩充，与 A04 §5.3 要求的修正一致。 |
| 请求中的非 C1 字段 | A01 item 4:73（C1 白名单）；P3 §5 输入隔离 | §4.7:61（保留 `episode_id`、`seq`、`step`；附加 R6 summary） | R6 summary 属 System-2 派生量，非 C1 观测字段；`episode_id`/`seq`/`step` 为非 C1 键。A01 item 4 限定的是"policy-visible structured information"，这些键是否属于该范围未在任何文件中定义。列为需所有者确认（§5 M-3），不判为冲突。 |
| 计分与分母 | P3 §16:714-734 | 无 | 未改动；B1-corrected 每物理 episode 一次（§1.5:21）与 P3 §16:716 一致。 |
| 平局规则 | A05 §2:27 | §4.3:53 | 二维平局的补充；A05 §2 原文按单一 grid value 写，未定义二维情形，A06 填补而非改写。 |
| safe stop 解除 | A05 §1.3:17 | §4.5:57 | A05 字面"The safe stop is cleared only when no target remains in a hold and no fault latch is set"是必要条件；A06 读作"满足该条件即清除，包括其他原因设置的 safe stop"。这是对"only when"的一种读法，所有者 R2 已定，不列为冲突。 |
| replay 与缓存 | A04 §4:97；A05 §3.1:31、§3.4:37 | §3.3:39、§3.4:41 | 一致。§3.3 将缓存键出处写为"Addendum 04 Section 4"，缓存键实际在 A04 §1.3:71（§4 为工件完整性），属引用偏差（§5 S-4）。 |
| B4 报告规则 | A04 §6:109-113 | §3.2:37、§3.5:43 | 未改动 §6；§3.5 新增 incomplete 情形下"不主张收益或代价"，与 §6.2 的方向一致，是新增的报告限制而非放宽。 |
| 文本条件 | P3 §12.2:513-533；A03 §2 item 7:47 | §1.5:21 | 一致；生成器所指见 §3 A-6。 |
| B2 参数 | P3 §15 B2 tuning:649-672 | §2.2:27 | 与工件一致，未改动。 |
| 种子处理顺序 | P3 §18.1:838-850；A01 items 8-9:77-78 | §1.2-1.3、§2.3 | 一致，并比上位文件更具体。 |
| 停止条件 | P3 §25:976-990；A03–A05 各 §stop | §5:79-85 | 均为新增；"replay-cache-miss fallback"一条与 A05 §5:53 重复，无矛盾。A06 §5 的效果写作"invalidates the affected eval-v3 rows until corrected under P3 Section 18.2"，而 A03–A05 写作"implementation defect, not a result"；两种表述的处置路径不同（前者指向 18.2 修正并可能重生成 eval 集），属表述差异，非冲突。 |
| 截止时间 | A03 §1:13（build window 至 10-27 23:45 UTC） | §3.5:43 | 06:00 早于窗口结束，无冲突。 |

结论性说明：按条文对照，未发现 A06 改动 P3 或 A01–A05 已登记的阈值、门控、计分或分母。A06 中相对上位字面有实质变化的两处（§4.7 请求范围、§4.5 safe stop 解读）都对应已定裁决 R7、R2。**未发现需列为"冲突"的条目。**

---

## 5. 冻结前待办

### 必须

- **M-1（R9 勘误）** §4A R9:75 缺 `context_text` 占位符替换。所有者已定方案 (a)，勘误 PR 须在 `impl-freeze-v3` 之前合并。状态：缺失，勘误待合并。
- **M-2（冻结 tag 名）** A06 未登记 tag 名 `impl-freeze-v3`；§1.2 的 HEAD 检查与 §2.3 的 X 依赖它。可与 M-1 同一勘误处理，由所有者决定。
- **M-3（请求中的种子标识）** §4.7:61 保留 `episode_id` 等键；若其值为种子（main 上 `sources.py:69`），eval-v3 种子将进入外部请求与缓存，并与 §1.3 不检视规则交互。需要所有者澄清：这些键是否发送给生成器，以及 `episode_id` 在 eval 路径中的取值。
- **M-4（incomplete 情形的运行与报告方式）** §3.5:43 与 A05 §3.1:31 合读时，incomplete B4 行无已登记的生成方式（§3 A-14），A04 §6.1 计数在该情形下是否报告亦未定。需在冻结前澄清，否则截止或上限触发时执行者需要临场决定。

### 建议

- **S-1** 写明 2,500 的计数口径与错误响应是否入缓存（§3 A-12），以及 401/403 后能否续跑（A-13）、截止时间所覆盖的阶段（A-15）。
- **S-2** 指名 §1.5 的冻结文本生成器模块（A-6）。
- **S-3** §3.2 探针：去重口径、变体顺序、"valid"定义与 A04 "usable"的关系、探针后格式变更的处理（A-16、A-17、A-18）。
- **S-4** §3.3:39 缓存键引用应指向 A04 §1.3 而非 §4（引用偏差）。
- **S-5** R2 披露中写明 development object 的标识（seed 88 / target 5）与证据工件位置。
- **S-6** 产物位置（结果工件、eval-v3 缓存目录、是否提交缓存）未登记（§2 第 9 项）。
- **S-7** 种子列表顺序是否保持 sample 返回顺序（A-1）。
- **S-8** P3 §13.4 结构 holdout 在 eval-v3 中的 case 位置与报告方式；P3 §13.1 V0 已知族是否属于 eval-v3（§2 第 6 项）。
- **S-9** "exactly once"与续跑、两次 replay 的关系（A-2）；种子值在 B1 等结果提交时是否已可见（A-3）。
- **S-10** R9 的占位符取值与 canonical JSON 函数（A-10）。

### 需所有者裁决

本次审查未发现与 P3 / A01–A05 的条文冲突，也未发现与 §0 裁决相反的登记。上列 M-3、M-4 需要所有者给出澄清（属歧义，不属冲突）。

---

## 6. 给 T9b（EVAL-PATH）与 T6 第 2 阶段（FRZ-2A）的核验要点

### T9b — EVAL-PATH 审查

| # | 要点 | A06 节 |
|---|---|---|
| E-1 | eval 路径的 case 分配为 `index % 19`，结构顺序与故障族顺序同 dev 路径；100 个种子下 case 计数 6×5 + 5×14 | §1.4 |
| E-2 | 每物理 episode 四个文本条件；只 import 一个文本生成器；`content_sha256` 校验失败即中止（A03 §2 item 7） | §1.5 |
| E-3 | B1、B1-legacy、B2、B3 每物理 episode 一次且不读文本；B2 从 `b2-grid.json` 读取 (1.15, 2.15) 而非硬编码另一值 | §1.5、§2.2 |
| E-4 | 运行命令全部来自 X；结果提交后 `git diff X..Z -- src/` 为空 | §2.3、§5 |
| E-5 | stdout、日志、进度输出不含种子值或 `str(seed)` 形式的 `episode_id`（A-3、A-7） | §1.3、§4.7 |
| E-6 | 请求模型取 `NIM_MODEL`；receipt 逐响应记录服务端返回名并另记请求常量 | §3.1、R9 |
| E-7 | live 路径经 read-through 缓存，键为最终请求体 SHA-256（A04 §1.3），浮点 6 位舍入（A05 §3.4） | §3.3 |
| E-8 | 401/403 非零退出；续跑行为与所有者澄清一致（A-13） | §3.3 |
| E-9 | 2,500 计数器的计数对象与超限时的行为（A-12）；超过即停止 | §3.3、§5 |
| E-10 | replay 生成两次、receipt 一致；缓存未命中非零退出且无 fallback（A05 §3.1） | §3.4、§5 |
| E-11 | 截止检查与 incomplete 报告路径（完成对计数）存在且与澄清一致（A-14、A-15） | §3.5 |
| E-12 | `llm_calls` 按 (seed, 文本条件) 跨两个 B4 变体计数，另分别报告两个变体的调用（A05 §3.3） | §3（引用） |
| E-13 | A04 §6.1 各计数与 §6.2 50% 判定在结果生成代码中实现 | §3.2（引用 A04 §6） |
| E-14 | receipt 记录 §2.1 平台字段（A05 §4.1） | §2.1 |

### T6 第 2 阶段 — FRZ-2A 审查

| # | 要点 | A06 节 |
|---|---|---|
| F-1 | `scripts/gen_eval_v3_seeds.py` 存在于 X；三项拒绝条件；只打印数量与 SHA-256；使用 `secrets.SystemRandom().sample`、区间 `[10000, 2147483647)`、100 个；写入顺序（A-1）。只读源码与打桩测试，不在真实路径运行 | §1.1、§1.2 |
| F-2 | 冻结 tag 名为 `impl-freeze-v3` 且 M-1 勘误已在 tag 之前合并 | R9、§2.3 |
| F-3 | 模板哈希：三者（evidence_packet、s2_summary、context_text）替换为占位符；不同 (seed, 文本条件) 得到同一哈希（A-10、A-11） | §4A R9 |
| F-4 | §3.2 探针工件在 X 之前提交；探针集成员可按条文重算；选定模式为 X 中默认值；探针后无请求格式变更或已重做（A-16 至 A-18） | §3.2 |
| F-5 | 硬故障 latch 在证据窗口为空时也设置（commit `71ce80d`） | §4.1 |
| F-6 | L3 equivalence receipt 运行时解析 `base_git_sha`（commit `afa2aa6`） | §4.2 |
| F-7 | 二维平局取 (tau, delay) 字典序最小；容差 1e-12 × max(1, \|min\|)（A05 §2） | §4.3 |
| F-8 | hold 只在快速层 ESCALATE 路径进入；已终态目标不进入；1e-9 s 容差；窗口终点检查时刻（A-4） | §4.4 |
| F-9 | safe stop 解除条件与 R2 一致；seed 88 / target 5 行为与披露一致（A-5） | §4.5 |
| F-10 | episode 级 safe stop 行为未变 | §4.6 |
| F-11 | B4 请求：观测 8 字段、在场事件 4 字段（仅当前目标）；反馈为决策之前的全 episode（A-8）；known_config 5 字段；R6 summary 恰为 passing[]（structure_id、rmse、n_usable）、current_time、horizon；非 C1 键处理与 M-3 澄清一致 | §4.7、R6、R7 |
| F-12 | 未经配置生成器运行 B4 即中止（A05 §3.2）；该检查在 X 中仍有效 | §5（引用 A05） |
