# 任务卡 EVAL-PATH-R1 — PR #28 返工：merge main、守卫与账本（X1/X2）、失败响应处理（A07 R14）、format_mode 透传（v1，不调用 NIM）
执行者：Grok 4.7（Grok CLI，WSL；沙箱 profile `rra-exec`），新会话
仓库：pzy19-prog/reality-residual-agent；主库 ~/reality-residual-agent
工作区（已存在）：~/reality-residual-agent-worktrees/eval-v3-path　分支 feat/eval-v3-path　HEAD = 52bdd47ad2a2df5a4399cf3b9ced1e9ea20b8753（PR #28 head）
git 身份："Xifeng Ming" <274782819+pzy19-prog@users.noreply.github.com>（作者和提交者）；提交信息和 PR 正文不得出现任何 AI 署名行
测试框架：pytest
**本卡不调用 NIM，不读取任何密钥（不运行 pass，不设置 NVIDIA_API_KEY），绝不在真实路径运行 seed 生成器，不创建也不打开 `config/eval_seeds*.json`。** 网络只用于 git/gh。live 路径一律用假 HTTP 测试（monkeypatch `urlopen` 或 provider），不得真的连 NIM。不读写其他 worktree；不修改 `~/reality-residual-agent-worktrees/_control`。长时间命令在前台等它跑完；进程池可以正常使用，不要用信号量垫片或 LD_PRELOAD。
依据：`_reviews/PR28.md`（X1、X2、合并冲突）；A07（PR #29，即将合并）§4.1–§4.7 与所有者裁决 R14、R15（17:11 / 17:30）；A06 §2.3、§3.3–§3.5；A04 §3 rule 1、§6.1。

## §0.0 Bootstrap
```
cd ~/reality-residual-agent && git fetch origin
test "$(git rev-parse origin/feat/eval-v3-path)" = "52bdd47ad2a2df5a4399cf3b9ced1e9ea20b8753" || 停
git merge-base --is-ancestor 466bec6613f3950b12c00c789ed81c4c36aa3e39 origin/main || 停（PR #27 未合并）
cd ~/reality-residual-agent-worktrees/eval-v3-path
test "$(git rev-parse HEAD)" = "52bdd47ad2a2df5a4399cf3b9ced1e9ea20b8753" && test -z "$(git status --porcelain)" || 停
test "$(git config user.email)" = "274782819+pzy19-prog@users.noreply.github.com" || 停
test ! -e config/eval_seeds_v3.json || 停
PY=$PWD/.venv/bin/python
```

## §0 实测核对表（控制会话 2026-10-24 读 origin/main edd54c0 与 52bdd47）
| # | 前提 | 实测值 |
|---|---|---|
| Q1 | 合并冲突 | `git merge-tree origin/main origin/feat/eval-v3-path`：`src/rra/cli.py`、`src/rra/eval/b4_dev.py` 两个文件冲突 |
| Q2 | 守卫 | `final_v3.py:123-135` 要求工作区干净，且 `<tag>..HEAD` 中只允许 seed 文件和 `artifacts/eval_v3/` 有改动；B4 live 写 `artifacts/llm_cache/`（`b4_dev.py` 中的 `cache_dir`）。这就是 PR28 X1 |
| Q3 | live 计数 | `_prior_distinct_live_requests` 只读取 `b4.json`，该文件只在正常结束时写出。这就是 PR28 X2 |
| Q4 | 当前失败处理 | main `b4_dev.py` `_ReadThroughProvider.complete`：最多 3 次；status < 500 立即抛出；401/403 → SystemExit；失败一律不写缓存。`providers.py` `NvidiaNimProvider.complete` 只在 HTTP 200 时写缓存；200 但正文不是 JSON 时，`json.loads` 抛 JSONDecodeError（会被 adapter 归为 INVALID_PROPOSAL，也不写缓存） |
| Q5 | 错误分类 | `episode.py:737-741`：proposal.error 的类型名属于 {ValueError, TypeError, ValidationError, JSONDecodeError} → INVALID_PROPOSAL；其他（含 RuntimeError）→ PROVIDER_ERROR |
| Q6 | replay 读取缓存 | `ReplayProvider.complete`：文件不存在 → ReplayCacheMiss；`record["response"]` 不是 dict → ValueError |

## §1 已裁决
- M0 **先 merge**：`git merge origin/main`（merge 提交，不 rebase），解决 `cli.py`、`b4_dev.py` 冲突。原则是两边的功能都保留：#27 的 format_mode、served_models、llm_request_spec、strict/tiebreak 调用数；#28 的 seeds_path。merge 提交单独一个。
- M1 **守卫（X1）**：eval_v3 角色下，下列三项都只能落在白名单 {`config/eval_seeds_v3.json`、`artifacts/eval_v3/**`、`artifacts/llm_cache/**`} 内：
  - `git diff --name-status <tag> HEAD` 的已跟踪改动；
  - 工作区的已跟踪改动；
  - 未跟踪文件。

  此外，`artifacts/llm_cache/**` 中只允许新增文件，状态 M、D、R 都拒绝。不再要求工作区完全干净。测试覆盖四种情况：缓存目录有未跟踪文件时可以续跑；`<tag>` 之后已提交缓存时可以 replay；`src/` 有改动（已提交或未提交）时拒绝；修改或删除已有缓存文件时拒绝。
- M2 **账本（X2，A07 §4.2）**：
  - 只用于 eval_v3 角色的 live：在对某个请求做第一次 HTTP 尝试**之前**，把它的 finalize 后 request_sha256 作为一行 JSON（`{"request_sha256": …}`，不写请求内容）追加写入 `artifacts/eval_v3/live_ledger.jsonl`，写后 flush 并 fsync。
  - 已经在账本中的 sha 不再追加。`already` = 账本中不同 sha 的个数。
  - 追加之前先检查上限：已有 2,500 个不同条目时，不再尝试新请求，run 以 incomplete 结束（Q-2）。
  - 错误记录也计数。
  - 测试：模拟中途异常后续跑时，计数从账本接上；在上限处停下，且第 2,501 个请求没有发出任何 HTTP 尝试；账本只追加，从不改写。
- M3 **失败响应处理（A07 §4.1，R14）**：在 `NvidiaNimProvider` 与 `_ReadThroughProvider`（或你认为合适的集中位置）实现以下规则。dev 和 eval 的 live 都适用。
  - HTTP 200 且正文是 JSON：照旧写缓存。
  - **确定性错误**：3xx、400、404、409、413、422，以及除下面列出的码以外的其他 4xx。立即写一条错误记录到缓存，文件名就是该请求的 cache key：`{"request": payload, "error": {"http_status": <int 或 null>, "class": "deterministic"}}`。不写响应正文，不写凭据，也不写时间。
  - **暂时性错误**：408、429、5xx、超时、网络错误，以及 HTTP 200 但正文不是 JSON。总共最多尝试 5 次，指数退避，有 Retry-After 时遵守它（上限可设 60 s）。仍然失败就写错误记录，`"class": "transient_exhausted"`。
  - 错误记录是最终结果。live 路径中，它和 replay 路径一样以 RuntimeError 子类（例如 `CachedProviderError`）交给 adapter，所以两条路径都得到 `PROVIDER_ERROR`（Q5），proposal.error 中不含响应正文。
  - `ReplayProvider` 读到错误记录时抛出同一个 RuntimeError 子类（不是 ReplayCacheMiss，也不是 ValueError）。
  - **连续 10 个请求以错误记录结束**时，抛出专门的异常（例如 `LiveOutageStop`）停止 run，非零退出，可以续跑；这 10 条记录保留。计数按完成顺序、跨线程共享，任何一个成功响应都把计数清零。
  - 401/403：停止，不写缓存（沿用 SystemExit 或专门的异常），修正凭证后可以续跑。
  - 测试（假 HTTP）：500×5 → 写错误记录，PROVIDER_ERROR，replay 后结果相同；400 → 立即写记录，没有重试；429 带 Retry-After → 被遵守（可以 monkeypatch sleep 来断言等待时长）；200 非 JSON ×5 → 写错误记录；401 → 停止且不写记录；连续 10 个错误记录 → 停止；live 与 replay 的 receipt 对同一错误给出相同的决策记录。
- M4 **未完成时的计数（A07 §4.5，R15）**：incomplete 的 b4 receipt 增加 `a04_counts`：
  - 来源：从账本 + 缓存计算；
  - 内容：`llm_calls` = 账本中不同 sha 的个数；`valid`、`INVALID_PROPOSAL`、`PROVIDER_ERROR`、`truncated` 是对账本中每个 sha 的缓存记录，用 adapter 规则分类的结果；
  - 另记 `gate_reason_distribution: "not available (incomplete)"`。

  补一个测试。
- M5 **截止时刻（A07 §4.4）**：
  - live 命令开始时，把 `live_fill_started_utc` 写进 receipt 的不进哈希部分（与 runtime_versions 同一类排除）。完成时写 `live_fill_completed_utc`。
  - 增加 `--deadline-utc`，默认 `2026-10-27T06:00:00Z`。到点后不再发起新的 HTTP 尝试，run 以 incomplete 结束，reason 为 `deadline`。
  - 测试：用假时钟验证。
- M6 **format_mode 与字段透传**：`rra eval-v3 b4` 增加 `--format-mode`，默认值取 `rra.llm.providers` 中的默认常量。A06 §3.2：FRZ-2B 会改这个常量；本卡不改它的值，只保证 eval 路径从同一个常量读取。eval b4 receipt 要带上 run_b4_dev 结果中的 `llm_request_spec`、`served_models`、strict/tiebreak 调用数。
- M7 **不打印 seed（A07 §4.6）**：检查 eval 路径所有 stdout、stderr 和异常信息。用一个 9 位 seed 的临时 seed 文件做测试（dev 角色、临时目录），抓取 CLI 的输出，断言其中没有该 seed 的字符串。
- M8 不改：docs、requirements、`episode.py`、`packet.py`、adapter 的提示词和请求体、verifier/门控/授权、DSL、评估器、已提交的 artifacts。`providers.py`、`b4_dev.py`、`final_v3.py`、`cli.py`、tests 可以改。
- M9 提交：merge 提交 → 若干功能提交（M1/M2、M3、M4–M7 可分开）；普通推送更新 PR #28；PR 正文末尾追加一段改动说明（对应 PR28 X1/X2、A07 §4.1/§4.2/§4.4/§4.5/§4.6、R14/R15）。禁止强制推送、rebase、新建分支、合并。

## §2 验收
- V1 全量 pytest 全绿，计数 ≥ main（edd54c0）的计数 + 本 PR 的测试（列出新增测试名）
- V2 merge 后在 dev 上重跑等价：`rra eval-v3 b1b3 --role dev --seeds-file config/dev_seeds.json` 与 `rra s2-b3-dev` 的 B1/B3 逐 seed receipt 130/130 相同；B3 receipt = bfda4d101bd79f8d62738807402b33e24aba29028f5f4bc550a9b13304cb1132（main 上提交的 b3-dev）
- V3 `rra eval-v3 b4 --estimate --role dev --seeds-file config/dev_seeds.json` 的输出 = 1400；diag 子集 = 444
- V4 M1–M7 测试名逐条列出，并写明各自覆盖的规则
- V5 `config/eval_seeds_v3.json` 不存在，`git log --all -- config/eval_seeds_v3.json` 为空；`nvapi-` 0；身份正确；`git diff --name-only origin/main...HEAD` 符合 M8
- V6 PR #28 新 head 的 CI：test、determinism 均 pass

## §4 自主权
实现细节自行处理。硬停只限：§0 不符；需要改 M8 范围；V2 不成立且原因不在本卡改动内；任何步骤需要真实 seed 或真实 NIM。

## §5 失败报告
`~/reality-residual-agent-worktrees/_reports/REPORT_D4_EVALPATHR1_nogo.md`，给出 sha256。

## §6 收尾
报告写 `~/reality-residual-agent-worktrees/_reports/REPORT_D4_EVALPATHR1.md`（§0、M0–M7 改动及代码行、V1–V6、PR #28 新 head）。**先定稿再算哈希**：末行写 `Report SHA-256 (body = content before this line, trailing whitespace stripped, plus one "\n"): <sha>`，并追加到 `ARCHIVE_D3.sha256`。不合并。
