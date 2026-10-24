# 任务卡 FRZ-2A — 保持逻辑按 A05 对齐 + B4 请求按登记规范重做（canonical 证据包、6 位小数、格式模式、receipt 字段、测试、探针脚本）（v3，不调用 NIM）
执行者：Luna（GPT-6 Luna，Codex CLI，WSL），新会话（接续 v2 的 no-go，在已有 worktree 和两个本地提交上继续）
仓库：pzy19-prog/reality-residual-agent；主库 ~/reality-residual-agent
工作区（已存在）：~/reality-residual-agent-worktrees/frz2-b4req　分支 feat/frz2-b4req（本地，未推送）　HEAD = 2eccd65（G0 代码 a63523d + G0 artifact 2eccd65，均为 v2 执行结果，保留）　基线 origin/main = 5a05f6d
git 身份："Xifeng Ming" <274782819+pzy19-prog@users.noreply.github.com>；提交与 PR 不加任何 Claude/AI 署名行
测试框架：pytest；预期基线：200 passed / 4 skipped（以 §0.0 实测为准）
**本卡不调用 NIM、不需要也不得读取任何密钥**（不运行 pass，不 export NVIDIA_API_KEY）。实际调用 NIM 的部分在 FRZ-2B。派发已开放主库 .git 写权限。
**v3 相对 v2 的改动**：v2 在 G1 硬停（`_reports/REPORT_D4_FRZ2A_nogo.md`，sha c2323a93…4945）。原因是 v2 的 Q2 写错：origin/main 上 L3 导出的 known_config 是 7 个字段（多 episode_steps、object_count），v2 误写为 5 个（控制会话读了主库未更新的本地 checkout）。v3 裁决：L3 不动，B4 包的 known_config 投影为 C1 的 5 个字段，等价测试按投影比较（G1）。另吸收所有者裁决 R6–R9（G1、G4、G11）。G0 已完成，不重做。
**v2 的改动（保留）**：新增 G0；G6 采用 T6 测试草案；V3 分段核对 B3 receipt。
依据：A03 §2 第 3、4 条；A04 §1.2、§1.3、§1.5、§3、§5.4、§6.1；A05 §1.1–§1.4、§3.3、§3.4；`_reviews/PR20_R1.md`、`_reviews/PR24_R1.md`；云端只读文档（不要合并这些分支）：`origin/cloud/t1-pr20-review:docs/_review/T1_pr20_review.md` §2、§5、§6；`origin/cloud/t4-frz1-review:docs/_review/T4_frz1_review.md` §1、§4、§7；`origin/cloud/t6-prefreeze-check:docs/_review/T6_prefreeze_check.md` §1、§2、附录 A.2、附录 B.1。

## §0.0 Bootstrap
```
cd ~/reality-residual-agent && git fetch origin
test "$(git rev-parse origin/main)" = "5a05f6d56f2f08d1d9a985ee17912bcec02a23bc" || 停（main 有新提交，报告 SHA）
git ls-remote --exit-code origin refs/heads/feat/frz2-b4req && 停
cd ~/reality-residual-agent-worktrees/frz2-b4req
test "$(git rev-parse --short=7 HEAD)" = "2eccd65" && test -z "$(git status --porcelain)" || 停
PY=$PWD/.venv/bin/python
PYTHONPATH=$PWD/src $PY -c "import sys,numpy,rra;print(sys.version.split()[0],numpy.__version__,rra.__file__)"   # 3.12.3 2.5.4 …/frz2-b4req/src/rra/__init__.py
PYTHONPATH=$PWD/src $PY -m pytest -q -p no:cacheprovider    # 记录计数（G0 之后）
test -f /tmp/frz2-base-b3/b3-dev.json || 停（基线 B3 缺失 → 用 5a05f6d 代码重新生成到该路径，在报告中说明）
```

## §0 实测核对表（控制会话 2026-10-24 读 origin/main 与 PR #24 head cb77107 代码）
| # | 前提 | 实测值 | 复核命令 |
|---|---|---|---|
| Q1 | canonical 证据包 | `src/rra/evidence/packet.py:9-29` `build_packet`：本目标 seq ≤ 决策 seq 的 observations、presence_events；全部 seq < 决策 seq 的 command_feedback；known_config；context；decision 段。L3 用它在 24,000 个决策点上做过 Zetaris/参考加载器等价校验 | `cat src/rra/evidence/packet.py` |
| Q2 | 参考导出路径 | `src/rra/evidence/sources.py:94`（origin/main）：known 表 = episode_id + dt、tolerance、x_pick、y_pick、belt_speed、episode_steps、object_count；`export_sources` 与 `load_packets`（`:123-131`）进包时只去掉 episode_id，所以 L3 包内 known_config 是 **7 个字段**；`load_packets` 还用 `episode_steps` 算 seq。行内另带记账键 episode_id、seq（反馈行另有 step）。v2 硬停已实测：唯一差异是 known_config | `git show origin/main:src/rra/evidence/sources.py \| sed -n 86,131p` |
| Q3 | B4 当前请求 | `episode.py` B4 块手工拼缩减包：observations 只有 time/observed_x/nominal_x，feedback 4 个字段，没有在场事件和 x_pick/y_pick/belt_speed；`adapter.py:79-82` 原样 json.dumps，`text_context` 另传 | `grep -n "evidence_packet = {" -A16 src/rra/evidence/episode.py`；T6 §1.4 |
| Q4 | 格式失败形态 | 92e2b89 的 386 个缓存响应：71 个可解析；310 个能 json.loads 但键名缺失；5 个 finish_reason=length | `_reviews/tools/n1_cache_count.py`（A04 §5.1） |
| Q5 | receipt 缺字段 | b4_dev 的 body 没有模型 ID、请求模板 sha；strict/tiebreak 调用数没有分开 | `grep -n "NIM_MODEL\|body = {" -A3 src/rra/eval/b4_dev.py`；T6 C-13 |
| Q6 | 未覆盖的规则 | rule 1、rule 4、rule 5 回落、rule 2 与 3 顺序没有单元测试（T1 §2）；B4 下的保持、actuator-delay 一维/二维平局、`s2-b4-dev --replay` 缺失时退出码没有测试（T4 §1.1 第 5–7 项） | `grep -n "def test" tests/test_b4_episode.py tests/test_s2.py` |
| Q7 | §1.3 safe_stop 解除（**不改**，所有者 2026-10-24 裁决 R2：维持现状，88/5 在提交材料中披露） | cb77107 `episode.py:880-885`：保持目标被授权后，只要保持集为空且无锁存就 `safe_stop = False`，不管 safe_stop 是谁设的。main 上 S2 单目标授权从不解除 safe_stop（main 只有 :442 的 episode 级 outcome escalation 授权会解除）。dev 上的唯一一例是 88/5：t=0.2 已被别的原因设为 safe_stop，t=5.9 授权后被解除并发出命令（T4 §4.5、§4.6 S1）。A05 §1.1 "existing safe stop applies"、§1.3 "cleared only when" 是必要条件 | `sed -n 875,886p src/rra/evidence/episode.py`；`git show 9fe1730:src/rra/evidence/episode.py \| grep -n "safe_stop = False"` |
| Q8 | 保持偏差 b：已有终态的目标再次进入保持 | `:886-893`：同一步内 window_end 先结束保持并记 escalated，随后新的 ESCALATE 上升沿再调 S2，PAUSE 后 `setdefault` 再次进入。dev 上 6 次（17/9、21/8、39/4、61/11、69/7、83/7），hold_entries 183 对应 177 个对象，escalations 追加重复项（T4 §4.1 H1） | `sed -n 886,905p src/rra/evidence/episode.py` |
| Q9 | 保持偏差 c：浮点比较跳过 +0.5 s 那一帧 | `:652-653` hold_due 与 `:668` S2 门都用 `observation.time >= system2_next_retry`，`next_retry = t + 0.5`；dev 上 11 个保持区间为 0.6 s（例如 7/1：3.8→4.4）。A05 §1.2 要求 "first observation at or after 0.5 s" | `sed -n 650,670p src/rra/evidence/episode.py`；T4 §1 表 §1.2 |

## §1 已裁决
- **G0 保持逻辑按 A05 §1.2、§1.4 对齐（第一个提交，只含 G0 代码与测试；之后一个提交重新生成 artifact）**。这是条款符合性修复（A05 §5 第 1 条把"保持中目标未按 §1.2 重评估"列为缺陷），不是按 dev 结果调参。§1.3 的 safe_stop 解除（Q7）按所有者裁决 R2 保持现状，不得改动。
  - G0-b（Q8）：已在 `outcomes_by_target` 中有终态的目标不得进入保持，走原有的 ESCALATE 处理路径（record_outcome 先写者为准，行为同 main）。`hold_entries` 与 `end_reasons` 合计应等于进入保持的不同对象数。
  - G0-c（Q9）：重试到期判定统一用 `observation.time >= next_retry - 1e-9`（容差常量写在一处并注释引用 A05 §1.2），同时用于 hold_due 和 S2 门里的 next_retry 比较。
  - 测试（每项至少 1 个）：(b) 同一步 window_end 结束后再出现 ESCALATE 上升沿，不再进入保持，`hold_entries` 不增加；(c) 复查间隔：沿用 `test_diag_dev_seed_reobservations_stay_within_retry_interval`，把容差收紧为 `0.5 + 1e-9`（不再加 dt），并扩到 diag 子集全部 seed。
  - G0 之后重新生成 `artifacts/s2/b3-dev.json`/`.md` 和 meterless 的 B3 段（规则同 FRZ-1 v2 F8）。B4 段继续 stale（G8）。
- G1 **B4 请求的证据 = canonical 证据包**：在每个 B4 调用点，用 `build_packet` 构造证据包，输入与参考导出路径（Q2）对该决策点会给出的完全相同：本目标观测与在场事件（seq ≤ 决策 seq）、全部更早的指令反馈、known_config **投影为 C1 的 5 个字段**（dt、tolerance、x_pick、y_pick、belt_speed；所有者裁决 R7，A01 §4）、context = {text, content_sha256}（冻结文本；B3 不发请求，所以 B3 不涉及）、decision 段。另加一个派生段 `s2_summary = {passing: [{structure_id, rmse, n_usable}…], current_time, horizon}`（保留；它来自 B3 verifier，不是白名单外的世界状态）。请求体 = 系统提示 + `{"evidence_packet": <canonical 包>, "s2_summary": …}`；文本不再单独以 `context_text` 重复发送（它已在 packet.context 里）。
  - **L3 不动**：不改 `export_sources`、`load_packets`、导出表内容和 L3 包哈希。episode_steps、object_count 是 L3 存储与 seq 计算用的记账字段，不属于 C1，也不发给 LLM；去掉它们不算 A03 §2 第 4 项所说的"移除证据"。
  - 投影只用一个函数（例如 `rra.evidence.packet.project_c1_known_config`），B4 构造包和等价测试共用。
  - 等价测试：在至少 3 个 dev seed（含一个带指令反馈的 seed）上，run_episode 内部构造的包，与"`export_sources` → `load_packets` → 对 known_config 做同一投影"得到的同一决策点的包，`packet_sha256` 完全相同。另断言投影前后只有 known_config 的 episode_steps、object_count 两个键不同。
  - 反馈范围：build_packet 只放 seq < 决策 seq 的反馈（episode 内决策之前的全部反馈；R7 的"整个 episode"按此实现，不含未来反馈）。
  - `s2_summary` 的内容就是 R6 批准的 passing[]（structure_id、rmse、n_usable）、current_time、horizon，不得再加字段。
  - 可用 T6 附录 A.2 `check_packet_whitelist.py` 的思路自查，但以 build_packet 为准。
- G2 **浮点 6 位小数**（A05 §3.4）：在 `finalize_payload` 或请求序列化处，对请求 messages 里 JSON 内容的所有浮点值统一 `round(x, 6)`；只作用于发给 provider 的请求，不改 receipt 和证据包本身的哈希口径（canonical 包的 L3 哈希不变）。补测试：仅最后一位不同的两个浮点值，得到相同的缓存键。
- G3 **提示词与格式模式**：
  - 系统提示改为 v2：明确给出 JSON schema 和一个字面示例，例如 `{"items":[{"hypothesis_id":"SENSOR_BIAS","rationale":"…","evidence_refs":["obs:0:1.200"]}]}`；保留"只能用登记 ID""只选结构、不估数值参数"；ID 列表照旧来自 dsl。
  - 新增 provider 设置 `format_mode`，取值 `json_object`（现状）、`json_schema`（OpenAI 风格 `response_format={"type":"json_schema","json_schema":{"name":"proposal","schema":<schema>,"strict":true}}`）、`nvext_guided_json`（`nvext={"guided_json":<schema>}`）。format_mode 进入 finalize 后的 payload，因此进入缓存键。**默认值暂时保持 `json_object`**，最终取值由 FRZ-2B 的探针按登记规则决定。
  - schema：`items` 为数组，每项必须有 `hypothesis_id`（枚举 = 14 个结构 ID + 6 个故障 ID）、`rationale`（字符串）、`evidence_refs`（字符串数组），不允许额外字段。
- G4 **receipt 字段**（A04 §5.4）：b4_dev 的 body 写入 `llm_request_spec = {model, format_mode, max_tokens, chat_template_kwargs, request_template_sha256}`，**进入哈希**；另把各响应中服务端返回的 `model` 名按出现次数汇总为 `served_models` 写进 receipt（进入哈希；R9）。`request_template_sha256`（R9：去掉证据后的请求骨架）= 把 evidence_packet 和 s2_summary 换成字面占位符 `"<EVIDENCE_PACKET>"`、`"<S2_SUMMARY>"` 之后，finalize 后 payload 的 canonical JSON（sort_keys，紧凑分隔符）的 sha256。补测试：模板 sha 与具体包内容无关，但随提示词或 format_mode 变化。
- G5 **调用数分开报告**（A05 §3.3）：每个 (seed, 文本变体) 记录 `strict_proposer_invocations`、`tiebreak_proposer_invocations`（未去重），和现有的 `llm_requests_served`（去重后的服务数）一起进入哈希；metrics 中两个变体各自给出 invocations。
- G6 **补测试**：
  - (Q6 前半) rule 1 两种情况（provider error、invalid proposal）在 episode 层面得到相应的 `TIEBREAK_FALLBACK:*` 且动作为 PAUSE；rule 4（空列表、无 passing 结构）；rule 5 回落（common_action 非 UPDATE → `TIEBREAK_FALLBACK:NO_SAFE_ACTION`）；同一 proposal 里既有排在前面的 fault ID 又有未知 ID 时，结果为 FAULT_ID。
  - (Q6 后半) 采用 T6 附录 B.1 `test_t6_drafts.py` 中的草案，放进 `tests/`（文件名自定，`REPO` 由文件位置解析）：B4-strict/B4-tiebreak 下的保持；actuator-delay 一维平局与 (tau, delay) 二维平局（字典序，即 FRZ-1 现有实现，裁决保留）；`s2-b4-dev --replay` 缓存缺失时非零退出且不写 b4-dev.json；§3.4 的三个草案按 G2 的实现形式调整。草案若与 G0/G1 的新行为冲突，按新行为改断言并在报告中写明。
- G7 **探针脚本** `scripts/b4_probe.py`（本卡只写不跑 live）：
  - 在 diag 子集（artifacts/s2/diag-d1g.json 的 seed）上，按 seed 顺序、文本变体顺序收集 B4 调用点，取前 K 个（默认 K=10）不同的请求作为探针集；全过程只用 dev seed
  - 对每个 format_mode 各发一次（K×3 次 live 调用），响应写入单独目录 `artifacts/llm_probe_cache/`（不混进 llm_cache）
  - 输出 `artifacts/s2/b4-probe.json`：每个模式的有效解析数（按 adapter 规则得到非空 items 且无 error）、finish_reason 分布、HTTP 错误数、平均延迟；receipt 规则同其他 artifact
  - `--dry-run`：不联网，只打印将要发送的请求数和它们的缓存键，exit 0；`--live`：需要 NVIDIA_API_KEY（由 FRZ-2B 运行）
  - 调用总数硬上限参数 `--max-calls`（默认 30），超过就中止
- G8 不重生成 b4-dev.json 和 meterless 的 B4 段（请求变了，旧缓存全部失效，需要 FRZ-2B 实际调用 NIM），在报告和 PR 正文中标为 stale。
- G9 不改：docs（decisions.md 只按 G11 加一行）、requirements（如果 json_schema 需要新依赖就停）、verifier/门控/授权门、DSL、评估器、TERMINAL_STATES、保持逻辑中 G0 以外的部分（§1.3 safe_stop 解除按 R2 不动；保持入口仍只限 ESCALATE 路径，infeasible 和 outcome escalation 的 PAUSE 不进入保持；窗口终点仍用 `base_plan.expected_arrival_time + dt/2`）。
- G11 `decisions.md`（仓库根目录，非登记文件）表格加一行：日期 2026-10-24，内容为所有者裁决 R1–R9（R1 A05 §1.1 保持入口取窄读法，只限快速层 ESCALATE 路径；R2 §1.3 维持现状不改代码，88/5 在提交材料中披露；R3 episode 级 safe_stop 主导 84/775 不在冻结范围，作为失败模式披露；R4 登记 runner = 本机 i7-10750H、Python 3.12.3、NumPy 2.5.4、scipy-openblas 0.3.34；R5 A05 §3.4 在本机实现，B4 缓存在本机 live 重建；R6 B4 请求保留 passing[]、current_time、horizon；R7 证据包范围：本目标的观测与在场事件、episode 内决策之前的全部指令反馈、known_config 取 C1 的 5 个字段；R8 二维网格平局按 (tau, delay) 字典序；R9 请求模板 SHA-256 = 去掉证据后的请求骨架的哈希，模型标识记录服务端返回的名字），依据写"T4 审查 §7 第 1、2、9、10 条；T6 冻结前核对 §5 第 1–4 条；Addendum 05；登记见 Addendum 06"。单独一个提交。
- G10 交付：分若干提交（G0 代码+测试 → G0 artifact → B4 部分若干提交）；push；`gh pr create --base main --head feat/frz2-b4req --title "FRZ-2A: A05 hold conformance and canonical B4 request"`，正文写改动清单和 stale 清单，并逐条写明对应关系：G0-b ↔ T4 §7 第 4 条，G0-c ↔ T4 §7 第 3 条 (a)，§1.3（T4 §7 第 2 条）按 R2 未改，G1 ↔ R6/R7，G4 ↔ R9。不合并。

## §2 验收
- V1 pytest 全绿，计数 = 基线 + 新增测试（列出测试名）
- V2 等价：G1 等价测试通过；另在 diag 子集全部 33 seed × 4 变体的 B4 调用点上，统计 run_episode 内部包与导出路径包（投影后）的 `packet_sha256` 相同数 x/x（只用假 proposer，不联网）；L3 包哈希（未投影）与 5a05f6d 相同
- V3 B3 / B1（分段）：
  - G0 artifact 提交上：B1 `b1_receipt_sha256` 与 /tmp/frz2-base-b3 一致 130/130；B3 metrics 与基线对照表（recoverable success、wrong、miss、unsafe 按来源、preservation_regression、authorization_count、system2_calls、终态计数、`system2_reobserve` 全部字段含 end_reasons、复查间隔最大值），**只报告，不设门槛，不得为改善数字调参**；`unsafe_action_by_source.s2_authorized` 若 >0，逐个列出，不要修
  - 最终 head 上：重新生成 b3-dev 到临时目录，receipt 与 G0 artifact 提交里的 `artifacts/s2/b3-dev.json` 相同（B4 部分不得影响 B3）；连续生成两次 receipt 相同
- V4 请求体量：子集上 B4 请求（finalize 后，json_object 模式）的字节数分布（最小/中位/最大），并按每 4 字符约 1 token 粗估输入 token
- V5 `scripts/b4_probe.py --dry-run` 的输出：探针集大小、三种模式的请求数、缓存键示例；exit 0。另给出 G2 实施后 diag 子集与全 dev 的去重请求数（假 proposer、不联网；作为 FRZ-2B 预算依据）
- V6 `llm_request_spec` 在三种 format_mode 下的 request_template_sha256（三个不同的值）
- V7 身份、密钥、范围：作者 Xifeng Ming noreply；`nvapi-` 计数 0；docs、requirements 没有改动
- V8 PR 的 CI：test 和 determinism 均 pass

## §4 自主权
实现细节自行处理。硬停只限：§0 不符；需要新依赖；需要改 G9 范围；G1 的等价测试在投影之后仍不通过（写明差异字段）；B1 哈希变化；G0 之后的 B4 提交改变了 B3 receipt。G0 让 B3 metrics 变好或变坏都不是硬停。

## §5 失败报告
`~/reality-residual-agent-worktrees/_reports/REPORT_D4_FRZ2A_nogo.md`，给出 sha256。

## §6 收尾
报告写 `~/reality-residual-agent-worktrees/_reports/REPORT_D4_FRZ2A.md`（引用 v2 no-go 报告中的 G0 结果，§0、G0–G11 改动及代码行、V1–V8、PR 编号与 head）。**先定稿再算哈希**：末行写 `Report SHA-256 (body = content before this line, trailing whitespace stripped, plus one "\n"): <sha>`，并追加到 `ARCHIVE_D3.sha256`。不合并，不删 worktree 或分支。
