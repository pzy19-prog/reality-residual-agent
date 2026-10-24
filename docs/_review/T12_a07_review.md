# T12 — Addendum 07 审查（冻结前，只读）

## 0. 范围与环境

- 审查对象：PR #29，分支 `docs/prereg-addendum-07`，**head `b65685914add8821d57fc10b6dfea8d3e4aef039`**（与任务卡一致；审查结束时 `git ls-remote` 仍为该 sha）。基于 main `349d1e68ebf196f9f3b25d5e2f6746b6029401fe`。
- 审查分支：`cloud/t12-a07-review`，从该 head 建立。本文件是相对该 head 唯一新增的文件。
- 对象文件：`docs/P3_PREREG_ADDENDUM_07.md`（下称 A07，88 行）。行号写作 `A07 §x.y:L行号`；其他文件写作 `P3:L`、`A04 §3:L`、`path@sha:L`。
- 对照材料（均为只读）：
  - main 上的 P3、A01–A06、`docs/EVAL_PROTOCOL.md`、`docs/H1_EVAL_FOUNDATION.md`；
  - `cloud/t9a-a06-review@e198916`、`cloud/t6-prefreeze-check@5369a90`；
  - PR #27 `feat/frz2-b4req@466bec6`、PR #28 `feat/eval-v3-path@52bdd47`（仅读代码）；
  - 公开 issue #26 的 28 条评论（截至 2026-10-24T08:48:59Z），只读。
- 未做的事：未打开 `config/eval_seeds*.json`，未运行种子生成、B3/B4 或任何 live 命令，未接触密钥，未在 issue 发评论。未运行任何代码，所以第 3 节与第 5 节里关于代码行为的说法都来自读源码，没有经过执行验证；第 5 节的检验设计只是设计，没有执行。
- 本文件只指出问题与影响，不提新的条文措辞，不下成败结论。
- 判定词：一致 / 部分 / 缺失 / 冲突。"冲突"指 A07 字面与 P3、A01–A06 的条文不同，或与任务卡列出的裁决相反；是否取代上位条文由所有者裁决（见第 6 节）。

---

## 1. 裁决覆盖表

| # | 裁决项 | A07 出处 | 判定 | 说明 |
|---|---|---|---|---|
| 1 | R9 (a)：模板 SHA 把 evidence_packet、s2_summary 换成固定占位符；写明占位符取值和 canonical JSON 函数 | §1.1:13 | 一致 | 占位符取值 `"<EVIDENCE_PACKET>"`、`"<S2_SUMMARY>"` 已写明，与 PR #27 `adapter.py:51,61,63` 逐字相同。canonical JSON 以参数形式写明（`sort_keys=True`、`separators=(",",":")`、`ensure_ascii=False`），没有写出函数名；代码 `providers.py:20-21` 的 `canonical_json` 另有 `allow_nan=False`，A07 未列（见 §5 Q-3）。"模型取请求常量而非返回名"已写（:13 末句）。 |
| 2 | R9 的"separate context-text 字段"如存在也替换 | §1.1:13 | 部分 | 这一句描述的是方案 (ii) 的残留分支。在方案 (i) 下该字段不存在（`adapter.py` 的 `propose(..., context_text="")` 参数不进入请求）。占位符取值对该字段未写。无实际影响，但留下一个未定义取值的分支（§5 Q-3）。 |
| 3 | R10 方案 (i)：context 放在 `evidence_packet.context = {text, content_sha256}`；写明四点 | §2 R10:27 | 一致 | 四点逐一出现：①同一冻结 P3 §12 文本、同一生成器、同一泄漏校验（"same text, from the same generator, with the same leakage validation"）；②只改位置（"from a separate channel to a sub-object of the packet"）；③"`context` is not a C1 field and adds no observable data"；④模板 SHA 排除文本。第④点的因果链在 :27 本身没有写出，只在 §1.1:13 里出现（"the evidence packet, which carries the context text (Section 2, R10), is replaced"），读者需要交叉阅读。另见 §4 对 H1 "separate channel"（H1:17）的关系。 |
| 4 | R11：请求去掉 `decision.episode_id` 和行级 `episode_id`；`command_id` 改写为 `"{target_id}:{step}"`；L3 导出和包哈希不变 | §2 R11:28 | 一致 | 三部分都写了，原形式 `"{seed}:{target_id}:{step}"` 也写了。代码 `packet.py:40-57` `generator_view` 的行为与此一致（T6 phase 3 的实测另见 §3）。 |
| 5 | R12：白名单外键逐项登记；写明都不含种子或隐藏参数 | §2 R12:29 | 一致 | 列出 `schema`、`decision.{target_id, step, time, seq}`、行级 `seq`、反馈行 `step`、`context.{text, content_sha256}`，以及 R6 的 System-2 摘要；末句写"None of them carries a seed value or a hidden simulator parameter"。与 T6 P3.3 实测的键集合一致。其中"行级 `seq`"没有区分观测、在场事件、反馈三组（均含 `seq`，T6 P3.3），影响小。 |
| 6 | R13：`served_models` 为 `{服务端模型名: 响应次数}` 汇总，作为 R9 的"按响应"记录 | §2 R13:30 | 一致 | 形式与所有者裁决相同。A07 未写该汇总计入哪些响应（含回放命中、不含错误记录），见 §3 C-5 与 §5 Q-6。 |
| 7 | 反馈先后规则：只含决策之前的条目，按 `seq < decision.seq` | §2:31 | 一致 | 写成"strictly less than"，`seq = target_id × episode_steps + step` 的公式也写明。代码 `packet.py:27` 为 `int(r["seq"]) < seq`。观测与在场事件的上界（代码为 `<=`，`packet.py:25-26`）A07 没有登记，见 §5 Q-8。 |
| 8 | T9a M-2：冻结 tag 名 `impl-freeze-v3` | §1.2:15 | 一致 | 指明 A06 §1.2 与 §2.3 中的 X。未写 tag 的类型（附注/轻量）与创建者，A06 同样没有。 |
| 9 | T9a M-4：B4 未完成时的运行与报告方式（"未完成则不报告指标"） | §4.5:61 | 部分 | "no B4 metrics and no Addendum 04 Section 6 counts are reported"，并列出应报告的字段（状态、原因、已完成 (seed, text condition) 对数、ledger 计数）。运行方式（cap 到达或截止后如何停止、是否可再续跑）散在 §4.4:59 与 §4.1:50。与 A04 §6.1 的字面关系见 §4 的 X-1。 |
| 10 | §4.1 服务端错误处理（本地新增） | §4.1:45-50 | 一致 | 四类规则与任务卡逐项相同：200 写缓存；400/404/413/422 写错误记录并在回放中复现 `PROVIDER_ERROR`；429、5xx、超时重试，仍失败则停止、不写缓存、可续跑；401/403 停止、修好凭据后可续跑。A07 另加"network errors"归入重试一类、错误记录"status code, no credentials"。未列出的状态码见 §5 Q-1。与 A04 §3 rule 1 的关系见 §4 的 X-2。 |
| 11 | §4.2 计数口径（本地新增） | §4.2:52 | 一致 | "至少一次 HTTP attempt"、ledger 在第一次尝试前追加、不重写、重试与续跑不增计数、2,500 上限按 ledger 不同条目数。"无论响应是什么"没有明写，只由"at least one HTTP attempt"隐含。ledger 追加与上限检查的先后、崩溃时的计数见 §5 Q-2。 |
| 12 | §5 S-8：结构 holdout 在 dev 种子 9、28、47、66、85、104、123 的 B3 运行与诊断中出现；B4/LLM dev 子集（diag-d1g，33 个种子）一个都没包含 | §5.1:75 | 部分 | A07 列出了七个 dev 种子，并说明"All System-2 development runs since the B3 development command (commit `7ea70ce`, 2026-10-22)"都按 `index mod 19` 分配。**关于 B4/LLM dev 子集不含这些种子的那句话在 head `b656859` 上不存在**（任务卡与 issue #26 评论 2026-10-24 08:39 / 08:48 都说它会作为后续提交补上；按要求照实记录）。现有措辞"All System-2 development runs"比已确认的事实宽：我读 `artifacts/s2/diag-d1g.json`（dev 子集文件）确认 33 个种子里没有这七个种子，但"所有 System-2 开发运行"是否都按此处理，A07 没有说明依据。2026-10-23 的历史 B4 开发运行（`92e2b89`，386 条缓存）所用种子范围，我没有查到，列为未核实。 |
| 13 | §5：eval-v3 的 case 9 单独报告为"开发中见过的 holdout"，不做组合泛化主张 | §5.2:77 | 一致 | "reported separately, labelled as the structural holdout seen during development, and no claim of composition generalization to an unseen structure is made from eval-v3"。"单独报告"的内容（哪些行、哪些指标）没有写；PR #28 里没有对应实现，见 §3 C-12。 |
| 14 | §5：V0 已知族不属于 eval-v3 | §5.3:79 | 部分 | 写了"not included"。"These were covered by the frozen eval v2 run"是一句事实陈述：`EVAL_PROTOCOL.md:7` 只说 eval v2 在实现 `c66b4bf` 上运行（早于 System-2、B3、B4），所以 v2 覆盖的是 V0 基线，B1-corrected/B2/B3/B4 没有在这些家族上运行过。见 §5 Q-9。 |
| 15 | R5/§3.4：探针与 dev B4 缓存在注册 runner 上生成（T9a A-9 的第二种读法） | §3.4:41 | 一致 | 采用了 A-9 的读法 2。 |

---

## 2. T9a 与 T6 遗留项在 A07 中的出处

### 2.1 T9a §5 必须项 M-1–M-4

| 项 | A07 出处 | 状态 |
|---|---|---|
| M-1 R9 `context_text` 勘误 | §1.1:13；§2 R10:27 | 已登记。方案由 (ii) 的"独立字段"改为 (i) 的"包内子对象"，占位符替换覆盖整个包。 |
| M-2 tag 名 | §1.2:15 | 已登记。 |
| M-3 请求中的种子标识 | §2 R11:28、R12:29；§6:85 | 已登记。种子标识从请求中移除（R11），其余键逐项登记（R12）；§6 把"请求含种子值或 `episode_id` 键"列为停止条件。T9a M-3 同时问到缓存是否提交：§4.7:69-71 登记缓存新文件随 Z 提交。 |
| M-4 未完成 B4 的运行与报告 | §4.4:59；§4.5:61 | 部分，见 §1 第 9 行。 |

### 2.2 T9a §5 建议项 S-1–S-10

| 项 | A07 出处 | 状态 |
|---|---|---|
| S-1 计数口径、错误是否入缓存、401/403 续跑、截止所覆盖阶段 | §4.1:45-50；§4.2:52；§4.4:59 | 已登记。截止"覆盖哪一阶段"：§4.4 写"the live fill must be complete by"，把截止限定在 live 填充。如何判定"填充已完成"见 §5 Q-5。 |
| S-2 指名冻结文本生成器 | §1.6:23 | 已登记：`src/rra/eval/context_v3.py`，变体顺序 `NO_TEXT_CONTEXT`、`HELPFUL_TEXT_CONTEXT`、`IRRELEVANT_TEXT_CONTEXT`、`MISLEADING_TEXT_CONTEXT`，与 `context_v3.py:16-18` 的 `VARIANTS` 一致。 |
| S-3 探针：去重口径、变体顺序、"valid"、探针后格式变更 | §3.1:35；§3.2:37；§3.3:39 | 已登记。去重键为 `json_object` 终稿负载的 SHA-256；"valid"含"未知 ID 去除后至少剩一项"，`finish_reason = length` 算无效；模板 SHA 不一致则探针作废并重做。**变体顺序**在 §3.1 里写为"then text-variant order"，没有指向 §1.6；顺序实际来自 §1.6，需读者自行关联。探针使用什么提议器来驱动 episode 以收集请求，A07 未写（§5 Q-4）。 |
| S-4 缓存键引用 | §1.3:17 | 已登记：A06 §3.3 的引用改为 A04 §1.3（A04 :17 是缓存键定义，核对一致）。 |
| S-5 R2 披露中的 dev 对象 | §1.4:19 | 部分。写明 dev seed 88、target 5；证据工件位置没有写。T6 phase 2 报告该对象行为与披露一致。 |
| S-6 产物位置 | §4.7:65-71 | 部分。结果文件、ledger、B4 新缓存文件已登记；探针工件（`artifacts/s2/b4-probe.json`，见 `b4_probe.py:147`）与探针缓存目录（`artifacts/llm_probe_cache/<mode>`，`b4_probe.py:104`）、dev B4 工件没有登记；第二次回放生成的回执写到哪里没有登记（§5 Q-7）。 |
| S-7 种子列表顺序 | §1.5:21 | 已登记（"in the order returned by `sample`, unsorted"）。#28 的 `gen_eval_v3_seeds.py:42` 直接用 `sample` 的返回，无排序调用。 |
| S-8 结构 holdout | §5:73-79 | 部分，见 §1 第 12、13、14 行。 |
| S-9 "exactly once"与续跑；种子值可见性 | §4.3:54-57；§4.6:63 | 已登记。B1/B1-legacy/B2/B3 允许"崩溃于写结果文件前"后重启；B4 为"live 填充（可续跑）+ 两次回放"。"All result artifacts are committed together"与 A06 §2.3(d) 的"one or more commits Z"的关系见 §5 Q-10。 |
| S-10 R9 占位符取值与 canonical JSON | §1.1:13 | 已登记，见 §1 第 1、2 行。 |

### 2.3 T6 第 2 阶段 P2.9 / P2.11（第 3 阶段补充）

| T6 项 | A07 出处 | 状态 |
|---|---|---|
| P2.9-1 白名单外键（`context.*`、`schema`、`decision.*`、行级键） | §2 R12:29 | 已登记。 |
| P2.9-2 context 放入包内与"separate channel"（H1:17）、A04 §1.2、A02 §4.2 的关系 | §2 R10:27 | 部分。R10 说明位置变化，没有引用 H1:17 或 A02 §4.2，也没有说是否取代 H1:17 的"separate channel"表述（见 §4 X-4）。 |
| P2.9-3 已提交的 `b4-dev.json` 与 `llm_cache/` 是旧版本，需在注册 runner 上重建 | §3.4:41 | 登记了"在注册 runner 上生成"，没有登记旧工件被替换或废弃的处理（旧 386 条缓存文件属于 `c852566` 格式，A07 §4.7:71 禁止修改或删除已有缓存文件，但那是针对 eval-v3 的 Z 提交；dev 缓存重建时旧文件如何处理未写）。 |
| P2.9-4 `served_models` 是否满足 R9"按响应" | §2 R13:30 | 已登记（所有者已接受）。 |
| P2.9-5 等价测试 2 只覆盖 index < 20 的 dev 种子 | 未登记 | 所有者在 issue #26（2026-10-24 07:53）裁定"Nothing to change"，属测试范围说明，不属协议条文。 |
| P2.9-6 / P2.11 B4 请求与缓存带种子值（`decision.episode_id`、行级 `episode_id`、`command_id` 前缀） | §2 R11:28；§6:85 | 已登记，处理方式为从请求中移除。 |
| P2.11 模板 SHA 占位符覆盖 `decision` | §1.1:13 | 已登记（整个 evidence_packet 被替换）。 |

---

## 3. A07 的描述与 PR #27、#28 代码是否一致

只读源码。#27 = `466bec6`，#28 = `52bdd47`。两个 PR 都基于 `5a05f6d`，互不包含对方；下面分别标注。

| # | A07 描述 | 出处 | 代码 | 判定 |
|---|---|---|---|---|
| C-1 | 模板 SHA 对替换后的终稿请求取 SHA；占位符字符串 | §1.1:13 | #27 `adapter.py:48-67`：`request_template_sha256` 把 user 消息中的 `evidence_packet` 换成 `"<EVIDENCE_PACKET>"`、`s2_summary` 换成 `"<S2_SUMMARY>"`，再走 `finalize_payload` 与 `canonical_json`。`request_body=None` 时用占位符骨架 `proposal_request("<EVIDENCE_PACKET>", "<S2_SUMMARY>")`。 | 一致。细节：骨架路径总会带 `s2_summary` 占位符；真实请求若没有该键（`proposal_request` 在 `s2_summary is None` 时省略键，`adapter.py:33`），则两条路径的哈希不同。B4 路径是否总带 `s2_summary` 我没有逐点核对。 |
| C-2 | context 在 `evidence_packet.context` | §2 R10:27 | #27 `packet.py:34`：`build_packet` 输出含 `"context": context`。T6 P2.10/P3 实测 350/350 请求中文本与哈希等于冻结值。 | 一致 |
| C-3 | R11 移除 `episode_id`、改写 `command_id` | §2 R11:28 | #27 `packet.py:40-57` `generator_view`；`episode.py:705` 调用 `generator_view(build_packet(...))`。改写用 `row['target_id']`、`row['step']` 拼出 `"{target_id}:{step}"`，而不是剥离前缀，结果相同。L3 的 `build_packet` 未改。 | 一致 |
| C-4 | 反馈 `seq < decision.seq` | §2:31 | #27 `packet.py:27`。反馈 `seq` 由 `episode.py:710-712` 用 `command_id` 末段的 step 与 `target_id` 计算，即**发令步**，不是执行时刻。 | 一致。读法问题见 §5 Q-8。 |
| C-5 | `served_models` 汇总 | §2 R13:30 | #27 `b4_dev.py:30-42,321-324,345`：`_ReadThroughProvider._record_model` 对每次**返回**的响应按 `response["model"]` 计数，缓存回放命中与 live 响应一起计；没有 `model` 字符串的响应静默不计；`served_models` 在 `hash_input`（`b4_dev.py:358`）内，计入 `receipt_sha256`。 | 部分。A07 没写这三点（回放命中计入、无 model 的响应不计、计入回执哈希）。见 §5 Q-6。 |
| C-6 | 缓存只写 200 响应 | §4.1:47 | #27 `providers.py:138-167`：仅在成功解析后 `write_text`；任何 HTTP 错误抛 `RuntimeError`（:156,158），无缓存写入。 | 部分：200 一致；400/404/413/422 的错误记录**未实现**——**待 EVAL-PATH-R1 实现**。 |
| C-7 | 429/5xx/超时/网络错误重试，仍失败则停止、不写缓存 | §4.1:49 | #27 `b4_dev.py:54-70`：最多 3 次；`if (status is not None and status < 500) or attempt == 2: raise`。(a) 429 属于 `< 500`，**不重试**，直接抛出；(b) 超时与网络错误在 `providers.py:157-158` 抛 `RuntimeError`，不更新 `last_http_status`，所以 `status` 保留上一次请求的值（初始为 `None`，成功一次后为 200）：初始为 `None` 时走重试，非首次请求则 `200 < 500` 成立而直接抛出；(c) 重试耗尽后抛 `RuntimeError`，被 `adapter.py:148` 捕获并转成 `Proposal(error=...)`，**运行继续**而不是停止。 | 不一致，**待 EVAL-PATH-R1 实现**。(a)(b)(c) 三处都与 A07 §4.1:49 不同。(b) 是我从代码读出的，未执行。 |
| C-8 | 401/403 停止、可续跑 | §4.1:50 | #27 `b4_dev.py:66-67`：`raise SystemExit("... stop Phase B")`。缓存目录在磁盘上保留，续跑走同一读通路径。 | 一致（停止与可续跑）。#28 的 eval 路径下续跑被其工作树守卫拒绝，见 C-10。 |
| C-9 | 计数：第一次 HTTP 尝试前登记 SHA、写 ledger | §4.2:52 | #28 `final_v3.py:45-71,96-100`：`LimitedProvider.complete` 在 `super().complete` 前调用 `budget.reserve(sha)`。该类包裹的是 `b4_dev.NvidiaNimProvider`（读通路径内部的 live 提供者），所以只在缓存未命中时调用；上限检查在加入集合之前（:65-67）。**没有 `live_ledger.jsonl`**：先前计数只从 `b4.json` 的 `distinct_live_requests` 读取（:301-313），该文件只在运行正常结束时写出。 | 部分。登记时机与"仅缓存未命中时计数"与 A07 一致；ledger 文件**未实现**，续跑时计数可能丢失或重复——**待 EVAL-PATH-R1 实现**（issue #26 的 X2 已列）。 |
| C-10 | 结果与缓存提交于 Z；回放两次；已有缓存文件不得修改或删除 | §4.3:57；§4.7:65-71；§6:86 | #28 `final_v3.py:123-135`：守卫要求工作树干净，且 `<tag>..HEAD` 改动只许在 `config/eval_seeds_v3.json` 与 `artifacts/eval_v3/` 内。`artifacts/llm_cache/` 不在白名单内，live 写入后工作树不干净、缓存提交后 `diff` 也含该路径，两种情形都被拒绝。没有"已有缓存文件被改动"的检测。 | 不一致，**待 EVAL-PATH-R1 实现**（issue #26 的 X1）。 |
| C-11 | 截止时间 2026-10-27 06:00 UTC | §4.4:59 | #28 `final_v3.py` 中没有截止时间或时钟检查（我对 `deadline`、`2026-10`、`utc` 做了 grep，无命中）。 | **待 EVAL-PATH-R1 实现**（或登记为人工执行的检查）。 |
| C-12 | 未完成 B4 行：报告状态、原因、已完成对数、ledger 计数，无指标 | §4.5:61 | #28 `final_v3.py:335-339`：cap 到达时返回 `status`、`reason: max_live_calls_reached`、`distinct_live_requests`、`completed_text_condition_pairs`，无 `metrics`。该"计数"来自内存集合，非 ledger。截止原因没有实现（无截止检查）。`.md` 输出在非完成状态下打印原因与计数（:397-403）。 | 部分：cap 路径一致；"ledger 计数"与"截止"路径**待 EVAL-PATH-R1 实现**。 |
| C-13 | case 9 单独报告 | §5.2:77 | #28 的回执含 `case_episode_counts`（:384）；B2 每行有 `case`（:231）；B4 的 `episodes` 记录来自 `b4_dev`，按种子而非按 case 键控。没有把 case 9 单列的代码。 | **待 EVAL-PATH-R1 实现**（或登记为后处理步骤；A07 §4.6:63 又禁止在行完成前打开种子字段，见 §5 Q-10）。 |
| C-14 | B4 回执含 `served_models`、模板 SHA、`format_mode` | §2 R13:30；§3.3:39 | #27 `b4_dev.py:195,335-345` 有；#28 的 `_run_b4`（`final_v3.py:316-343`）只返回 `metrics`、`episodes`、`llm_calls` 等，不含这些字段，且 `run_b4_dev` 在 #28 的基线上还没有 `format_mode` 参数。 | 待合并 #27 后由 EVAL-PATH-R1 传递；issue #26（08:05）已列。 |
| C-15 | 探针：前 10 个不同请求，种子顺序→变体顺序→决策顺序，按 `json_object` 终稿 SHA 去重 | §3.1:35 | #27 `scripts/b4_probe.py:47-71`：按 `diag-d1g.json` 种子顺序、`VARIANTS` 顺序，用 `_cache_key(entry, "json_object")` 去重，取满 10 个即停。请求由一个返回空 `items` 的 `_CaptureProposer` 驱动，且只跑 `B4_STRICT`。 | 一致（去重与顺序）。驱动方式（空提议器、仅 strict）A07 未写，见 §5 Q-4。 |
| C-16 | 探针"valid" = 无错误且去未知 ID 后至少一项；`finish_reason = length` 无效 | §3.2:37 | #27 `b4_probe.py:118`：`proposal.error is None and bool(proposal.items)`；`finish_reasons` 只做分布统计，不参与有效性判定（:117）。 | 部分：前半一致；"length 算无效"没有单独实现，只有当截断恰好导致解析错误时才间接无效。 |
| C-17 | 探针记录每种模式的模板 SHA | §3.3:39 | #27 `b4_probe.py:135-137`。 | 一致 |
| C-18 | 回放两次，第二次须与第一次一致；第一次是计分工件 | §4.3:57 | #28 的 `run_row` 把回执写到 `output_dir/{row}.json`（:394）；没有"两次回放并比较"的命令。第二次回放默认写同一路径，且工作树守卫要求干净。 | 未实现，A07 §4.7 也只登记了一个 `b4.{json,md}` 位置；见 §5 Q-7。 |
| C-19 | 停止条件检测（请求含种子值或 `episode_id` 键；缓存文件被改；ledger 缺失；缺响应/错误记录的缓存） | §6:85-88 | #27 有一个单元测试检查终稿负载不含 9 位种子子串与 `episode_id` 键（T6 P3.1）。其余三项无运行时检测；缓存缺失在回放里由 `ReplayCacheMiss` 终止（`providers.py:105`，A05 §3.1）。 | 部分 |
| C-20 | 种子顺序：列表索引 i 为 `sample` 返回顺序 | §1.5:21 | #28 `gen_eval_v3_seeds.py:42` 直接 `sample`；`final_v3.py:178-184` 按列表索引 `index % 19`。 | 一致 |

---

## 4. 与上位文件的一致性

### 4.1 已登记文件是否被编辑

- `git diff --stat origin/main HEAD`（A07 head 对 main）只显示 `decisions.md`（+1 行）和 `docs/P3_PREREG_ADDENDUM_07.md`（+88 行）。P3、A01–A06、`EVAL_PROTOCOL.md`、`H1_EVAL_FOUNDATION.md` 都未被改动。A07 用新补遗修订，符合"已登记文件不编辑、只能用新补遗修订"的项目规则。
- `decisions.md` 增加的一行是追加到末尾的表格行，格式与其前几行相同，没有改动已有行。该行列出 R10–R13、A06 勘误（R9(a)、tag 名、引用更正）、探针/live/计数/未完成/产物位置的澄清、holdout 披露，与 A07 内容对得上；没有提到 §4.1 的新错误处理规则是本地新增而非所有者裁决（该行只写"live 运行、计数、未完成处理的澄清"）。
- A07 未改动 `p3-prereg` tag（:9）。

### 4.2 A07 自称"不改变"的地方

A07 没有 A06 §4A 那样的"change no threshold, gate, scoring rule, or denominator"总声明。它的自我限定有两处：

- :9 "does not alter `docs/P3_SYSTEM2_DESIGN.md` or Addenda 01–06. Where this addendum and earlier documents differ, this addendum governs only the items listed below."
- :7 "No development or evaluation result figure is a ground for this addendum."

逐项对照：

| 编号 | A07 项 | 上位条文 | 判定与说明 |
|---|---|---|---|
| X-1 | §4.5:61 未完成 B4 不报告 "Addendum 04 Section 6 counts" | A04 §6.1:57："For each B4 variant report: LLM calls; counts of valid proposals, INVALID_PROPOSAL, PROVIDER_ERROR, and truncated outputs; and the gate_reason distribution" | **冲突（字面）**。A04 §6.1 是无条件的报告义务，且这些是诊断计数，不是 B4 收益或代价主张；A06 §3.5:43 只禁止"claim benefit or cost"，没有取消 §6.1 计数。A07 取消它们，但没有声明取代 A04 §6.1。任务卡的所有者裁决写的是"本地称未完成则不报告指标"，是否包含 §6.1 计数没有写明，列入需裁决。对 §6.2 的 50% 判定同理（未完成时它无法计算）。 |
| X-2 | §4.1:49 超时与持续失败 → 停止运行 | A04 §3 rule 1:33："The proposal is unusable (provider or HTTP error, timeout, replay-cache miss, ...)"，不可用 → fallback `PROVIDER_ERROR`；A04 §6.1 计数含 `PROVIDER_ERROR` | **冲突（字面）**。A04 rule 1 把"timeout/provider error"定为 fallback；A07 把持续的 429/5xx/超时改为停止运行，不产生 `PROVIDER_ERROR`，只有确定性 4xx 错误记录才会在回放中复现为 `PROVIDER_ERROR`。后果：在 eval-v3 中 `PROVIDER_ERROR` 只来自 4xx；A04 §6.2 的 50% 判定分子也只含这一类。A07 未声明取代 A04 rule 1。（回放行为与 A04 rule 1 一致，冲突只在 live 阶段。） |
| X-3 | §3.2:37 "truncated response counts as invalid" | A06 §3.2 "valid proposals (non-empty items and no error under the adapter rules)"；A04 §3 rule 1 / §6.1 把截断视为不可用/单独计数 | 一致于 A04；对 A06 是细化。可能改变选定的格式模式（仅限 dev、X 之前）。 |
| X-4 | R10：context 从独立通道改为包内子对象 | P3 §12 首句:496-498 "The System-2 evidence packet may include ... operational text"；A04 §1.2:15 "Free-form text context enters B4 requests only"；A04 §1.3:17 "deterministic function of the evidence packet and the text context"；H1:17 "Free-form operational text is a separate channel"；A02 §4.2:69-71（Zetaris 可达存储只写 C1 白名单与 P3 §12 context 记录） | P3 §12 与 A04 §1.2–1.3 字面不冲突。**H1:17 的"separate channel"字面与 R10 不同**：H1 不在 P3/A01–A06 之内，A07 没有引用它，也没有说明 H1:17 是否被取代。所有者已裁决方案 (i)，所以不列为与裁决相反；列入需裁决（是否需要另行说明 H1 的表述）。 |
| X-5 | §5.2:77 报告限制 | P3 §13.4:588-594 "Hold out at least one composition structure from all design/dev examples"；P3:305（修订后受影响结果不得作为 pristine holdout 证据）；P3:893 | 与 P3:305 的方向一致。A07 承认 P3 §13.4 在开发中未被遵守（:75 "Contrary to P3 Section 13.4"），但没有说明 P3 §19 中依赖 holdout 的成功判据（如有）如何处理，因为 A07 只禁止"组合泛化"主张。我没有查全 P3 §19 与 holdout 的对应关系，列入需裁决。 |
| X-6 | §5.3:79 V0 已知族不属于 eval-v3 | P3 §13.1:537-547；A06 §1.4:19 已把 case 限定为 14 个结构 + 5 个故障族 | 对 A06 §1.4 是明确化，不是新缩减。"v2 已覆盖"的事实依据见 §1 第 14 行。 |
| X-7 | §2:31 反馈先后规则 | A06 §4.7:61 "all command feedback in the episode that precedes the decision (no later feedback)" | 对 A06 是细化。是否改变 A06 的语义取决于"precedes"的读法，见 §5 Q-8。 |
| X-8 | §1.1:13 模板 SHA 定义 | A04 §5.4:53；A06 §4A R9:75 | 这是对 A06 R9 的更正；A07 :9 说"does not alter ... Addenda 01–06"，而 §1 标题为"Corrections to Addendum 06"。措辞上有张力，实际操作与项目规则（新补遗修订）一致。 |
| X-9 | §4.3:56 "A run that crashed before writing its result file may be restarted" | A06 §2.3(c) "every row run exactly once from the commands of X" | 对 A06 是细化，回应 T9a A-2。"写结果文件前崩溃"的边界见 §5 Q-11。 |
| X-10 | 阈值、门控、计分、分母 | P3 §18、§8.3、§9、§16；A05 §1–2 | **未发现 A07 改动已登记的阈值、门控、计分或分母**（verifier 阈值、common-action/ambiguity gate、authorization gate、B1-corrected 分母、平局规则、hold 规则均未在 A07 中出现）。A07 的改动面是请求内容（R10–R12）、live 运行/计数、报告规则。X-1、X-2 是报告与回退处理方式的字面差异，不涉及这些数值对象；是否把它们视为"计分规则"，由所有者判断。 |

---

## 5. 歧义与可检验性

每条：原句 → 读法 1 / 读法 2 → 对实现的影响 → 检验设计（只设计，未执行）。

**Q-1 未列出的 HTTP 状态（§4.1:47-50）**
- 原句：只列 200、400/404/413/422、429/5xx/超时/网络错误、401/403。
- 读法 1：未列状态码一律按"确定性错误"处理（写错误记录）。读法 2：未列状态码一律按"瞬时错误"处理（重试后停止）。读法 3：未登记。
- 影响：408、409、415、405、3xx、200 以外的 2xx 以及 200 但响应体不是 JSON 的情形各归哪类，决定缓存里是否有记录、回放是否缺失。代码（#27 `providers.py:149-158`）对 200 + 非 JSON 体会在 `json.loads` 抛 `ValueError`，被 `adapter.py:148` 吞掉，不写缓存，之后回放缺失。
- 检验：用 mock provider 对每个状态码各发一次，检查缓存内容、`PROVIDER_ERROR` 是否出现、回放是否缺失；对 200 + HTML 体、200 + 空 `choices`、200 + `finish_reason = length` 各一例。

**Q-2 ledger 先写与上限检查的先后（§4.2:52）**
- 原句："Each such SHA-256 is appended ... before its first attempt" 与 "the cap of 2,500 applies to the number of distinct entries in the ledger"，另有定义"for which at least one HTTP attempt was made"。
- 读法 1：先检查上限，未超限才追加并尝试；ledger 最多 2,500 项。读法 2：先追加，再检查；第 2,501 项可能已在 ledger 内但从未尝试，使"distinct entries"超过 2,500，从而触发 A06 §5:85"more than 2,500 distinct live eval-v3 requests"的停止条件。
- 另：追加后、HTTP 发出前进程被终止，则条目存在但无 HTTP 尝试——条目数与"至少一次 HTTP attempt"的定义不再相等（方向上偏大）。
- 影响：cap 附近的停止条件是否被触发；#28 现有 `reserve`（`final_v3.py:61-67`）是读法 1。
- 检验：mock provider，cap 设为 N；发 N+1 个不同请求，检查 ledger 行数是 N 还是 N+1、是否抛出、第 N+1 个请求是否发出过；在追加与发送之间注入崩溃，续跑后检查计数。

**Q-3 canonical JSON 与占位符的细节（§1.1:13）**
- 原句列出 `sort_keys`、`separators`、`ensure_ascii=False`，另写"applied after finalization (including the six-decimal rounding of Addendum 05 Section 3.4)"。
- 读法 1：先替换占位符再终稿化（代码顺序，`adapter.py:48-67`）。读法 2：先终稿化再替换（句子的字面顺序）。读法 1 与 2 在当前实现里得到相同结果，因为占位符字符串不含浮点数；但"rounding is applied after finalization"与"rounding is part of finalization"（`providers.py:54-71` 在 `finalize_payload` 内）措辞不一致。
- `allow_nan=False` 未写：对含 `NaN` 的输入，写法不同的实现会得到不同行为（抛错还是写出 `NaN`）。
- "separate context-text field ... likewise replaced"：占位符取值未写。
- 检验：对同一终稿请求分别按两种顺序求哈希，预期相同；改系统提示一个字符，预期不同；对两个不同 (seed, 文本条件) 的请求求模板哈希，预期相同；构造含 `NaN` 的字段，预期报错。

**Q-4 探针收集请求时由谁驱动 episode（§3.1:35）**
- 原句只写"requests are collected in the seed order ..., then text-variant order, then decision order within the episode"。
- 读法 1：用一个返回空列表的提议器驱动（代码如此，`b4_probe.py:27-34`，且只跑 `B4_STRICT`）。读法 2：用某个已有的缓存/真实提议结果驱动。后续决策点、因而后续请求依赖 episode 如何展开。
- 影响：探针集的第 2–10 个请求可能不同，进而可能影响被选格式模式。
- 检验：探针工件列出 10 个请求的 (seed, 变体, 决策点, 终稿 SHA)；独立脚本按空提议器重算并比较。

**Q-5 "live fill must be complete"（§4.4:59）**
- 读法 1：在 06:00 UTC 之前，最后一次需要 HTTP 的请求已经返回。读法 2：在 06:00 UTC 之前，已有一轮确认遍历显示缓存无缺失。
- 影响：全部请求集只能靠运行 episode 才能发现（请求依赖提议结果），所以"已完成"只有在一轮无缺失的遍历之后才能成立；若该遍历发生在 06:00 之后，读法 2 下运行被判为未完成。
- 检验：用 mock provider 构造一个运行，其 live 调用在截止前结束，确认遍历在截止后才跑完；检查脚本把该情形记成完成还是未完成，以及回执里记录的时刻。

**Q-6 `served_models` 计什么（§2 R13:30）**
- 读法 1：每个 live 响应一次。读法 2：每个被提议器消费的响应一次（代码，含回放命中，不含错误记录，`b4_dev.py:39-42`）。
- 影响：同一缓存在 live 与回放中得到的汇总不同（live 阶段的计数与回放阶段的计数口径不同）；错误记录、无 `model` 字段的响应不计，所以汇总总数不等于 `llm_calls`。因为 `served_models` 进入 `receipt_sha256`，回放两次必须一致，而 live 与回放的汇总可能不同。
- 检验：用含 200、400 错误记录、无 `model` 字段响应的 mock 缓存各回放两次，比较汇总与 `llm_calls`。

**Q-7 两次回放的回执放哪里、"match"比什么（§4.3:57；§4.7:65-71）**
- 原句："the first replay is the scored artifact, and the second must match it"。
- 读法 1：两个 `receipt_sha256` 相等（A06 §3.4:41 写的是"identical receipts"）。读法 2：整个结果文件逐字节相等。回执文件另含 `git_sha`、`runtime_versions`、`operational_cost`（#28 `final_v3.py:386-392`、`b4_dev.py:358-359`），后者不进入 `receipt_sha256`；若在第一次回放提交后再跑第二次，`git_sha` 就会不同。
- 位置：§4.7 只登记 `artifacts/eval_v3/b4.{json,md}`，第二次回放写到哪里没有登记，默认路径会覆盖第一份。
- 检验：在 mock 缓存上跑两次，比较 `receipt_sha256` 与文件字节；检查第二次是否覆盖第一次、工作树守卫是否放行。

**Q-8 "precedes the decision" 与观测上界（§2:31；A06 §4.7:61）**
- 原句：反馈行在 `seq` 严格小于决策 `seq` 时先于决策。
- 读法 1（按发令步）：`seq` 是 `target_id × episode_steps + step`，代码里全局时间正好是它乘以 `dt`（#27 `episode.py:517`），所以 `seq` 序等于发令时刻序。读法 2（按可见信息）：反馈行含 `execution_time`（C1 字段），带执行延迟的命令在发令步入包时，其 `execution_time` 可能晚于决策时刻。这是否算"决策之后的反馈"，A07 没有说。
- 观测与在场事件在代码里是 `seq <=`（含当前步，`packet.py:25-26`），A07 没有登记这个上界；A06 §4.7 只说"current target"。
- 检验：在 dev 种子上枚举满足 `seq < decision.seq` 且 `execution_time > decision.time` 的反馈行并计数；对 `seq == decision.seq` 的观测与在场事件是否入包做一个固定用例。

**Q-9 "covered by the frozen eval v2 run"（§5.3:79）**
- 读法 1：eval v2 覆盖的是 V0 基线在这些家族上的表现，B3/B4 在这些家族上未被评估。读法 2：这些家族不需要 System-2 评估。
- 影响：报告里是否可以引用 v2 作为 B3/B4 在已知族上的证据（`EVAL_PROTOCOL.md:7` 显示 v2 运行在 `c66b4bf`，早于 System-2）。
- 检验：核对 eval v2 工件中的行集合与基线名称。

**Q-10 "committed together" 与种子可见性（§4.6:63）**
- 读法 1：所有结果工件在同一个提交里。读法 2：在所有行完成之后提交，数量不限（A06 §2.3(d) 的"one or more commits Z"）。
- 影响：读法 1 下 Z 是单一提交；读法 2 下 Z 可以是多个。另外：每个行完成时 `artifacts/eval_v3/{row}.json` 已写在磁盘上且含种子字段，"seed fields ... are not opened"靠操作纪律，不靠代码。case 9 单列（§5.2）需要读种子字段所在文件，其时机受 §4.6 约束，A07 没写时机。
- 检验：运行脚本时抓取全部 stdout/stderr 与日志，检查不含种子值；用合成 9 位种子（不是真实种子）走完整个 eval 路径并检查。

**Q-11 "crashed before writing its result file"（§4.3:56）**
- 读法 1：`{row}.json` 未出现。读法 2：`{row}.json` 与 `{row}.md` 都未出现。#28 的 `run_row` 先写 `.json` 再写 `.md`（:394,412）；崩溃发生在两次写入之间时，哪一种算"崩溃于写结果文件前"不明。
- 检验：在两次写入之间注入崩溃，检查重启是否被允许、哪份算最终结果。

**Q-12 重试与后退的参数、"persist"的含义（§4.1:49）**
- 重试次数、后退时间、总时限、"persist"是单个请求还是持续的失败率，A07 没有给出。#28/#27 现有代码是每请求 3 次、`2**attempt` 秒（`b4_dev.py:68-70`）。
- 影响：不同实现在同一服务状况下停止的时刻不同；"stop the run"在多线程下对其他在飞请求的处理没有写。
- 检验：mock provider 注入连续 5xx，检查实际尝试次数、总等待时间、停止时其他线程的行为、ledger 内条目数。

**Q-13 R10 第一点"same leakage validation"（§2 R10:27）**
- 原句：同一泄漏校验。T6 P2.10 条件 3 记录 `run_b4_dev` 调用 `freeze_episode_contexts(str(seed), seed, cause)` 时没有传 `hidden_values`（默认空元组），所以 `validate_text_context` 的隐藏值检查在 B4 路径上实际针对空集合；数值泄漏检查（`_numeric_leak_check`）仍然运行。
- 读法 1：A07 的"same"是指与 `5a05f6d` 一致，没有新增也没有削弱。读法 2：A07 在声明这个校验满足 P3 §12.2:530-531 的"static leakage check must reject text containing serialized hidden parameter values"。
- 影响：这是读 A07 者可能赋予 R10 的含义差别；是否构成对 P3 §12.2 的符合性主张，所有者判断。
- 检验：用已知隐藏值作为 `hidden_values` 调用生成器，检查文本被拒绝；在 B4 路径上记录实际传入的 `hidden_values`。

---

## 6. 需所有者裁决的清单，以及合并前的修改项

### 6.1 需所有者裁决

1. **X-1**：A07 §4.5:61 在 B4 未完成时取消 A04 §6.1 的诊断计数（字面冲突）。需要决定：该例外是否是所有者的意图；若是，A07 是否应声明取代 A04 §6.1 的这一部分。
2. **X-2**：A07 §4.1:49 把持续的超时/429/5xx 改为停止运行，与 A04 §3 rule 1 的"timeout → `PROVIDER_ERROR` fallback"字面不同（本地新增项，任务卡不把它列为所有者裁决）。需要决定：是否接受，并是否需要声明取代。
3. **X-4**：R10 与 H1:17 "separate channel"的关系，是否需要在补遗里引用并说明。
4. **X-5**：§5.2 的报告限制与 P3 §19 中依赖 holdout 的判据的关系（我没有查全该对应关系）。
5. **§1 第 12 行**：§5.1 中关于 B4/LLM dev 子集不含 holdout 种子的那句话在 `b656859` 上缺失；"All System-2 development runs"措辞比已确认的事实宽；历史 386 条缓存对应的种子范围未核实。
6. **§1 第 14 行 / Q-9**：§5.3 "covered by the frozen eval v2 run" 的事实含义。
7. **Q-1、Q-12**：错误分类的穷尽性与重试参数是否属于需要预注册的内容，还是留给实现。
8. **Q-6**：`served_models` 的计数口径（含回放命中）是否即所有者接受的"按响应"记录。
9. **Q-2**：cap 附近 ledger 追加与检查的先后。

### 6.2 合并前必须修改（"必须"）

这里只列出问题，不提措辞。

- **A07 §5.1:75 缺少 B4/LLM dev 子集的说明**（任务卡与 issue #26 均说会作为后续提交补上）。在 head `b656859` 上不存在；合并前需要该提交，并且我建议审查指向新 head。
- **X-1**、**X-2**：两处与 A04 字面不同的地方需要所有者裁决后在 A07 中处理，否则 A07 与 A04 并存时有两种读法。
- **§4.1 与 §4.2 对应的实现**（C-6、C-7、C-9、C-10、C-11、C-12）：A07 描述的行为在 #27/#28 目前都没有实现；它们属于 EVAL-PATH-R1，应在 `impl-freeze-v3` 之前完成并经审查，这不是 A07 文本本身的修改项，但 A07 合并后这些条款即成为登记行为。

### 6.3 建议

- **Q-5**：登记"live 填充已完成"的判定方式（读法 1/2）。
- **Q-7**：登记第二次回放回执的位置与"match"的比较对象。
- **Q-8**：登记观测与在场事件的上界，并确认反馈"先于决策"是否包含执行时刻晚于决策的行。
- **Q-4**：登记探针收集请求时的提议器与跑的 B4 变体。
- **Q-10**：A07 §4.6 的"committed together"与 A06 §2.3(d) 的关系；case 9 单独报告的时机。
- **Q-11**：写结果文件前后崩溃的边界。
- **Q-3**：`allow_nan=False`，以及 `context-text` 残留分支的取值。
- **§2.3 P2.9-3**：dev 缓存与探针/dev B4 工件在注册 runner 上重建时，旧工件的处理。
- **§4.7:65-71**：探针工件与探针缓存的位置。
- **§1.4:19**：dev 对象 seed 88 / target 5 的证据工件位置。
- **§4.1:49 / Q-12**：重试次数、后退、"persist"的含义。
- **Q-13**：R10"same leakage validation"是否包含对 P3 §12.2 符合性的含义。
- **§4.3:56 / :54**：B1、B1-legacy、B2、B3 的表述与结果文件 `b1b3`（B1 与 B3 同一命令）之间的对应关系。

---

## 附录：本次审查执行的命令

均在 `/home/user/reality-residual-agent`，无 live 调用，无密钥。

- `git rev-parse HEAD` → `b65685914add8821d57fc10b6dfea8d3e4aef039`；`git checkout -b cloud/t12-a07-review`。
- `git fetch origin main cloud/t9a-a06-review cloud/t6-prefreeze-check feat/frz2-b4req feat/eval-v3-path`；`git rev-parse --short origin/<branch>` → `e198916`、`5369a90`、`466bec6`、`52bdd47`。
- `git diff --stat origin/main HEAD` → `decisions.md | 1 +`、`docs/P3_PREREG_ADDENDUM_07.md | 88 +`。
- `gh api repos/pzy19-prog/reality-residual-agent/issues/26/comments --paginate`（只读，28 条）。
- `git show` 读取 main 上的 P3、A01–A06、`EVAL_PROTOCOL.md`、`H1_EVAL_FOUNDATION.md`，以及 #27、#28 分支上的 `adapter.py`、`providers.py`、`packet.py`、`b4_dev.py`、`episode.py`（片段）、`scripts/b4_probe.py`、`final_v3.py`、`gen_eval_v3_seeds.py`。
- `git ls-remote origin docs/prereg-addendum-07 cloud/t12-a07-review main` → A07 head 仍为 `b656859`。
- 读取 `artifacts/s2/diag-d1g.json`（dev 子集，非 eval 种子）并检查是否含种子 9、28、47、66、85、104、123 → 33 个种子，无交集。
- 未打开 `config/eval_seeds*.json`。
