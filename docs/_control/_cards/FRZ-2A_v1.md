# 任务卡 FRZ-2A — B4 请求按登记规范重做（canonical 证据包、6 位小数、格式模式、receipt 字段、测试、探针脚本）（v1，不调用 NIM）
执行者：Luna（GPT-6 Luna，Codex CLI，WSL），新会话
仓库：pzy19-prog/reality-residual-agent；主库 ~/reality-residual-agent
工作区（由你创建）：~/reality-residual-agent-worktrees/frz2-b4req　分支 feat/frz2-b4req　基线：origin/main，且必须包含 PR #24 的 head cb771079c1c119d73d0ebd0e24704a1935731cea
git 身份："Xifeng Ming" <274782819+pzy19-prog@users.noreply.github.com>；提交与 PR 不加任何 Claude/AI 署名行
测试框架：pytest；预期基线：200 passed / 4 skipped（以 §0.0 实测为准）
**本卡不调用 NIM、不需要也不得读取任何密钥**（不运行 pass，不 export NVIDIA_API_KEY）。实际调用 NIM 的部分在 FRZ-2B。派发已开放主库 .git 写权限。
依据：A03 §2 第 3、4 条；A04 §1.2、§1.3、§1.5、§3、§5.4、§6.1；A05 §3.3、§3.4；`_reviews/PR20_R1.md`；云端 T1 审查 `origin/cloud/t1-pr20-review:docs/_review/T1_pr20_review.md` §2、§5、§6（只读参考，不要合并该分支）。

## §0.0 Bootstrap
```
cd ~/reality-residual-agent && git fetch origin
git merge-base --is-ancestor cb771079c1c119d73d0ebd0e24704a1935731cea origin/main || 停（PR #24 尚未合并）
git ls-remote --exit-code origin refs/heads/feat/frz2-b4req && 停
git worktree add -b feat/frz2-b4req ~/reality-residual-agent-worktrees/frz2-b4req origin/main
cd ~/reality-residual-agent-worktrees/frz2-b4req
git config user.name "Xifeng Ming"; git config user.email "274782819+pzy19-prog@users.noreply.github.com"
/usr/bin/python3.12 -m venv .venv && .venv/bin/pip install -q -r requirements.txt pytest
PY=$PWD/.venv/bin/python
PYTHONPATH=$PWD/src $PY -c "import sys,numpy,rra;print(sys.version.split()[0],numpy.__version__,rra.__file__)"   # 3.12.3 2.5.4 …/frz2-b4req/src/rra/__init__.py
PYTHONPATH=$PWD/src $PY -m pytest -q -p no:cacheprovider    # 记录基线计数（预期 200 passed / 4 skipped）
```

## §0 实测核对表（控制会话 2026-10-24 读 origin/main 与 PR #24 代码）
| # | 前提 | 实测值 | 复核命令 |
|---|---|---|---|
| Q1 | canonical 证据包 | `src/rra/evidence/packet.py:9-29` `build_packet`：本目标 seq ≤ 决策 seq 的 observations、presence_events；全部 seq < 决策 seq 的 command_feedback；known_config；context；decision 段。L3 用它在 24,000 个决策点上做过 Zetaris/参考加载器等价校验 | `cat src/rra/evidence/packet.py` |
| Q2 | 参考导出路径 | `src/rra/evidence/sources.py:80-110`：从 run_episode receipt 导出各表（observations 带 seq = target_id*episode_steps+step；feedback 的 step 从 command_id 解析；known 含 dt,tolerance,x_pick,y_pick,belt_speed,episode_steps,object_count；context = {text, content_sha256}），再调用 build_packet | `sed -n 60,135p src/rra/evidence/sources.py` |
| Q3 | B4 当前请求 | `src/rra/evidence/episode.py` B4 块：手工拼的缩减包（observations 只有 time/observed_x/nominal_x 等），`text_context` 另传；`src/rra/llm/adapter.py:66-82` 系统提示 + `{"evidence_packet","context_text"}`，`response_format={"type":"json_object"}` | `grep -n "evidence_packet = {" -A16 src/rra/evidence/episode.py`；`sed -n 60,90p src/rra/llm/adapter.py` |
| Q4 | 格式失败形态 | 92e2b89 的 386 个缓存响应：71 个可解析；310 个能 json.loads 但键名缺失（如 `{": [{": "SENSOR_BIAS", …`）；5 个 finish_reason=length | `_reviews/tools/n1_cache_count.py` 的结论（A04 §5.1） |
| Q5 | receipt 缺字段 | b4_dev 的 body 里没有模型 ID、请求模板 sha（T1 §6）；strict/tiebreak 的调用数没有分开（T1 §1） | `grep -n "NIM_MODEL\|body = {" -A3 src/rra/eval/b4_dev.py` |
| Q6 | 未覆盖的规则 | T1 §2：rule 1（episode 级 provider error / invalid proposal）、rule 4、rule 5 回落分支、rule 2 与 3 同时出现时的顺序，都没有单元测试 | `grep -n "def test" tests/test_b4_episode.py` |

## §1 已裁决
- G1 **B4 请求的证据 = canonical 证据包**：在每个 B4 调用点，用 `build_packet` 构造证据包，输入与参考导出路径（Q2）对该决策点会给出的完全相同：本目标观测与在场事件（seq ≤ 决策 seq）、全部更早的指令反馈、known_config（7 个字段）、context = {text, content_sha256}（冻结文本；B3 不发请求，所以 B3 不涉及）、decision 段。另加一个派生段 `s2_summary = {passing: [{structure_id, rmse, n_usable}…], current_time, horizon}`。请求体 = 系统提示 + `{"evidence_packet": <canonical 包>, "s2_summary": …}`；文本不再单独以 `context_text` 重复发送（它已在 packet.context 里）。
  - 必须补一个等价测试：在至少 3 个 dev seed（含一个带指令反馈的 seed）上，run_episode 内部构造的包与"导出各表 → `load_packets`"得到的同一决策点的包，`packet_sha256` 完全相同（参照 `sources.py` 现有导出逻辑；如果需要把导出逻辑抽成函数复用，可以重构，但不得改变导出表内容和 L3 的包哈希）。
- G2 **浮点 6 位小数**（A05 §3.4）：在 `finalize_payload` 或请求序列化处，对请求 messages 里 JSON 内容的所有浮点值统一 `round(x, 6)`；只作用于发给 provider 的请求，不改 receipt 和证据包本身的哈希口径（canonical 包的 L3 哈希不变）。补测试：仅最后一位不同的两个浮点值，得到相同的缓存键。
- G3 **提示词与格式模式**：
  - 系统提示改为 v2：明确给出 JSON schema 和一个字面示例，例如 `{"items":[{"hypothesis_id":"SENSOR_BIAS","rationale":"…","evidence_refs":["obs:0:1.200"]}]}`；保留"只能用登记 ID""只选结构、不估数值参数"；ID 列表照旧来自 dsl。
  - 新增 provider 设置 `format_mode`，取值 `json_object`（现状）、`json_schema`（OpenAI 风格 `response_format={"type":"json_schema","json_schema":{"name":"proposal","schema":<schema>,"strict":true}}`）、`nvext_guided_json`（`nvext={"guided_json":<schema>}`）。format_mode 进入 finalize 后的 payload，因此进入缓存键。**默认值暂时保持 `json_object`**，最终取值由 FRZ-2B 的探针按登记规则决定。
  - schema：`items` 为数组，每项必须有 `hypothesis_id`（枚举 = 14 个结构 ID + 6 个故障 ID）、`rationale`（字符串）、`evidence_refs`（字符串数组），不允许额外字段。
- G4 **receipt 字段**（A04 §5.4）：b4_dev 的 body 写入 `llm_request_spec = {model, format_mode, max_tokens, chat_template_kwargs, request_template_sha256}`，**进入哈希**。`request_template_sha256` = 把 evidence_packet 和 s2_summary 换成字面占位符 `"<EVIDENCE_PACKET>"`、`"<S2_SUMMARY>"` 之后，finalize 后 payload 的 canonical JSON（sort_keys，紧凑分隔符）的 sha256。补测试：模板 sha 与具体包内容无关，但随提示词或 format_mode 变化。
- G5 **调用数分开报告**（A05 §3.3）：每个 (seed, 文本变体) 记录 `strict_proposer_invocations`、`tiebreak_proposer_invocations`（未去重），和现有的 `llm_requests_served`（去重后的服务数）一起进入哈希；metrics 中两个变体各自给出 invocations。
- G6 **补测试**（Q6）：rule 1 两种情况（provider error、invalid proposal）在 episode 层面得到相应的 `TIEBREAK_FALLBACK:*` 且动作为 PAUSE；rule 4（空列表、无 passing 结构）；rule 5 回落（common_action 非 UPDATE → `TIEBREAK_FALLBACK:NO_SAFE_ACTION`）；同一 proposal 里既有排在前面的 fault ID 又有未知 ID 时，结果为 FAULT_ID。
- G7 **探针脚本** `scripts/b4_probe.py`（本卡只写不跑）：
  - 在 diag 子集（artifacts/s2/diag-d1g.json 的 seed）上，按 seed 顺序、文本变体顺序收集 B4 调用点，取前 K 个（默认 K=10）不同的请求作为探针集；全过程只用 dev seed
  - 对每个 format_mode 各发一次（K×3 次 live 调用），响应写入单独目录 `artifacts/llm_probe_cache/`（不混进 llm_cache）
  - 输出 `artifacts/s2/b4-probe.json`：每个模式的有效解析数（按 adapter 规则得到非空 items 且无 error）、finish_reason 分布、HTTP 错误数、平均延迟；receipt 规则同其他 artifact
  - `--dry-run`：不联网，只打印将要发送的请求数和它们的缓存键，exit 0；`--live`：需要 NVIDIA_API_KEY（由 FRZ-2B 运行）
  - 调用总数硬上限参数 `--max-calls`（默认 30），超过就中止
- G8 不重生成 b4-dev.json 和 meterless 的 B4 段（请求变了，旧缓存全部失效，需要 FRZ-2B 实际调用 NIM），在报告和 PR 正文中标为 stale。B3 不受影响：b3-dev 的 receipt 必须与 main 上的完全相同（B3 不发请求）。
- G9 不改：docs、requirements（如果 json_schema 需要新依赖就停）、verifier/门控/授权、DSL、评估器、FRZ-1 的保持逻辑。
- G10 交付：分若干提交；push；`gh pr create --base main --head feat/frz2-b4req --title "FRZ-2A: canonical B4 evidence packet, request format modes, receipt spec"`，正文写改动清单和 stale 清单。不合并。

## §2 验收
- V1 pytest 全绿，计数 = 基线 + 新增测试（列出测试名）
- V2 等价：G1 等价测试通过；另在 diag 子集全部 33 seed × 4 变体的 B4 调用点上，统计 run_episode 内部包与导出路径包的 `packet_sha256` 相同数 x/x（只用假 proposer，不联网）
- V3 B3 不变：在新代码上生成 b3-dev 到临时目录，receipt 与 main 上 `artifacts/s2/b3-dev.json` 相同；B1 130/130 相同
- V4 请求体量：子集上 B4 请求（finalize 后，json_object 模式）的字节数分布（最小/中位/最大），并按每 4 字符约 1 token 粗估输入 token
- V5 `scripts/b4_probe.py --dry-run` 的输出：探针集大小、三种模式的请求数、缓存键示例；exit 0
- V6 `llm_request_spec` 在三种 format_mode 下的 request_template_sha256（三个不同的值）
- V7 身份、密钥、范围：作者 Xifeng Ming noreply；`nvapi-` 计数 0；docs、requirements 没有改动
- V8 PR 的 CI：test 和 determinism 均 pass

## §4 自主权
实现细节自行处理。硬停只限：§0 不符；PR #24 未合并；需要新依赖；需要改 G9 范围；G1 的等价测试无法通过且原因在 L3 导出逻辑本身（写明差异字段）；B3 receipt 发生变化。

## §5 失败报告
`~/reality-residual-agent-worktrees/_reports/REPORT_D4_FRZ2A_nogo.md`，给出 sha256。

## §6 收尾
报告写 `~/reality-residual-agent-worktrees/_reports/REPORT_D4_FRZ2A.md`（§0、G1–G8 改动及代码行、V1–V8、PR 编号与 head）。**先定稿再算哈希**：末行写 `Report SHA-256 (body = content before this line, trailing whitespace stripped, plus one "\n"): <sha>`，并追加到 `ARCHIVE_D3.sha256`。不合并，不删 worktree 或分支。
