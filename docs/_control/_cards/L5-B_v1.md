# 任务卡 L5-B — Phase B：B4-strict / B4-tiebreak + dev 运行（v1）
执行者：Luna（GPT-6 Luna，Codex CLI，WSL），**新会话**
仓库：pzy19-prog/reality-residual-agent；主库 ~/reality-residual-agent
工作区：~/reality-residual-agent-worktrees/l5b-b4　分支 feat/l5b-b4　基线 ab509d38e2ce8e045603e4b0fa4c8e225e04f79f（已由上一 Luna 会话建好，**不要重建**）
git 身份："Xifeng Ming" <274782819+pzy19-prog@users.noreply.github.com>；提交与 PR 不加任何 Claude/AI 署名行
测试框架：pytest（pyproject：testpaths=["tests"]，pythonpath=["src"]）。基线：ab509d3 上 187 passed / 4 skipped
上游：PR #19（Phase A，head ab509d3）已审查：PASS，无阻断项，见 `_control/_reviews/PR19.md`。本卡**不处理** PR19 的非阻断项 N1–N6

## §0.0 Bootstrap（按顺序执行）
1. 读卡并校验（sha256 不符 → 停）：
   ```
   cd ~/reality-residual-agent-worktrees/_control/_cards
   echo "df45416fa2ffa8c764ce1ec51470bad3bf206f7267cbef37f3f4a44c7bc0f5cc  L5_v2.md" | sha256sum -c
   echo "3954e664249fa90b58135ec7d9c41a5824c994869d8184241bd5900323df6006  L5_v2_P-1.md" | sha256sum -c
   ```
   通读 L5_v2.md（尤其 §1 D2–D5 和 §3）以及 P-1。
2. 读 `~/reality-residual-agent-worktrees/_reports/REPORT_D3_L5.md`（Phase A 已完成，**不重做** A1–A8）和 `REPORT_D3_L5_nogo3.md`。
3. 核对工作区：
   ```
   cd ~/reality-residual-agent-worktrees/l5b-b4
   test "$(git rev-parse --abbrev-ref HEAD)" = "feat/l5b-b4"
   test "$(git rev-parse HEAD)" = "ab509d38e2ce8e045603e4b0fa4c8e225e04f79f"
   test -z "$(git status --porcelain)"
   git -C ~/reality-residual-agent ls-remote --exit-code origin refs/heads/feat/l5b-b4 && 停止并报告（远端已有同名分支）
   git config user.name "Xifeng Ming"; git config user.email "274782819+pzy19-prog@users.noreply.github.com"
   ```
4. 建本 worktree 自己的解释器（**不要沿用** l5a-hygiene/.venv：它是 editable 安装，`import rra` 会落到 l5a-hygiene/src）：
   ```
   python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt -e .
   echo ".venv/" >> "$(git rev-parse --git-path info/exclude)"
   PY=$PWD/.venv/bin/python
   $PY -c "import sys,numpy,rra;print(sys.version.split()[0],numpy.__version__,rra.__file__)"
   ```
   必须输出 `3.12.3 2.5.4 /home/mxfclaw/reality-residual-agent-worktrees/l5b-b4/src/rra/__init__.py`。版本不符且无法修复 → 停。
5. 基线测试：`$PY -m pytest -q` 必须为 **187 passed / 4 skipped**，否则停。

## §0 实测核对表（控制会话 2026-10-23 实测；Luna 逐项复核，任一不符 → 停，P12 除外）
| # | 前提 | 控制会话实测值 | 复核命令 |
|---|---|---|---|
| Q1 | 分支和 HEAD | feat/l5b-b4 @ ab509d38e2ce… | `git rev-parse --abbrev-ref HEAD; git rev-parse HEAD` |
| Q2 | 工作区干净 | porcelain 0 行；尚无 .venv | `git status --porcelain \| wc -l` |
| Q3 | 远端无同名分支 | `ls-remote origin refs/heads/feat/l5b-b4` 0 行 | 同 §0.0-3 |
| Q4 | 解释器 | 系统 python3 3.12.3；l5a venv 3.12.3/2.5.4/pytest 8.4.2/pydantic 2.14.1，但 editable 安装指向 l5a-hygiene/src | §0.0-4 |
| Q5 | PR #19 | OPEN，base main，head ab509d3，MERGEABLE；审查 PASS | `gh pr view 19 --json state,headRefOid` |
| Q6 | NIM provider 读的环境变量 | `NVIDIA_API_KEY`（`src/rra/llm/providers.py:82`），模型 `NIM_MODEL`（:14），超时 90s | `grep -n "NVIDIA_API_KEY\|NIM_MODEL =" src/rra/llm/providers.py` |
| Q7 | 密钥审计脚本存在 | `scripts/l3_secret_audit.py` | `ls scripts/l3_secret_audit.py` |
| Q8 | SUBSET 定义 | L1g 33-seed 子集在 `artifacts/s2/diag-d1g.json` | `ls artifacts/s2/diag-d1g.json` |
| Q9 | B3 基准 artifact | `artifacts/s2/b3-dev.json` receipt `6eb3c6fb986bcbfea2c0fa87fd280be6b23935d9c3d795d187eefbe88052df3d`（Phase A 已重生成，审查端已复现） | `python3 -c "import json;print(json.load(open('artifacts/s2/b3-dev.json'))['receipt_sha256'])"` |
| P12 | L3 容器 | `rra-l3-pg` Exited (0)、`rra-l3-ops` Exited (255)；ops 的挂载源 worktree 已不存在。**不是 Phase B 前提**，见 §1 R7 | `docker ps -a --format '{{.Names}} {{.Status}}'` |
| P13 | NVIDIA key 条目 | 使用 **`ai/nvidia-nim`**（用户在 nogo3 之后指定）。控制会话**未运行** pass，可读性 UNKNOWN | 由 Luna 执行：`timeout 10 pass show ai/nvidia-nim \| wc -c` 必须 > 0；失败（含超时或 GPG 未解锁）→ 停，等用户在交互终端解锁 GPG |

## §1 已裁决（直接执行，不再讨论）
- R0 L5_v2 §1 的 D2–D5 原样生效（B4-strict、调用策略、B4-tiebreak、episode 入口）；D1、D6–D10 已在 Phase A 完成，不再改动。
- R1 **密钥条目只用 `ai/nvidia-nim`**。禁止使用 `ai/nvidia/api-key.REJECTED-403-20261021` 或其他任何条目，也不 `pass ls` 另找。
- R2 **key 只在运行 B0/B2 的那个 shell 里 export**：`export NVIDIA_API_KEY="$(pass show ai/nvidia-nim | head -n1)"`。不写入任何文件、`.env`、日志、报告或提交；不 echo，不 `set -x`，不打印请求头。跑完执行 `unset NVIDIA_API_KEY`。
- R3 **B0 试探调用返回 401 或 403 → 立即停止**，不换条目，不重试别的 key，写 nogo4。其他网络错误或 5xx 允许按 §4 自行重试，但退避后合计不超过 3 次。
- R4 执行顺序：从 L5_v2 §3 开始，**B0 → B1 → B2 → B-1…B-6**；B0 门规则（≈4×N_amb×1.3 > 2000，或推算全量 > 4h → SUBSET）不变，SUBSET 的 seed 取自 `artifacts/s2/diag-d1g.json`。
- R5 B1/B3 沿用 ab509d3 上的现有 artifact（B1 哈希未变；B3 已在 Phase A 重生成，Q9），不重跑；B2 artifact 若因 Phase A 改变哈希，按 v2 §3 B2 重跑。
- R6 NIM 缓存写入 `artifacts/llm_cache/`，缓存记录只含 request 和 response body；B-6 的密钥扫描范围必须覆盖 `artifacts/llm_cache/` 和本次全部新增产物。
- R7 P12 不阻断 Phase B（B-1…B-6 都不依赖 Zetaris/PG）。可以尝试 `docker start rra-l3-pg rra-l3-ops`，结果写入报告；失败不停，**不删除、不重建容器**。
- R8 交付：`git push -u origin feat/l5b-b4`；开 PR，标题 "L5b: B4-strict/tiebreak + dev run"，**base=feat/l5a-hygiene**，不合并。
- R9 禁止修改预注册和登记文件（`docs/P3_*`、`docs/H1_EVAL_FOUNDATION.md`、A01–A03）；任何策略路径都不读取 `kind:manifest`。

## §2 验收（数字写进报告）
- B0：N_amb、估算调用量、10 次试探调用的速率与推算时长、是否 SUBSET（附原因）
- B1：D2–D5 实现与测试；`src/rra/eval/b4_dev.py`（含 nproc 和 serial/parallel 一致性检查）及 cli 子命令
- B2：dev 运行完成（全量或 SUBSET），每个 episode × 4 变体 × {B4_STRICT, B4_TIEBREAK}
- B-1 B4_STRICT 的 system2_decisions 与 B3 逐条相同（所有 episode×变体）；不一致即视为 bug → 停
- B-2 B4_TIEBREAK：按变体报告 s2_authorized 的 unsafe_action；所有 TEXT_TIEBREAK 授权都经过 authorize()（有测试）
- B-3 断网后用 ReplayProvider 重跑整个 B4 dev，decisions 和 receipt 哈希 100% 相同（写明断网方式，并在 shell 中 unset key 后运行）
- B-4 Meterless 开/关：同一回放缓存下，B4_TIEBREAK 的 decisions 20/20 相同；把 `meterless-persistence.json` 的 B4 栏从 DEFERRED 更新为实测结果
- B-5 五行结果表 B1/B2/B3/B4-strict/B4-tiebreak × 各文本变体（字段同 v2 §3 B-5）；MISLEADING 变体另外单列 §17 的 5 项
- B-6 `$PY -m pytest -q` 全绿（≥187 passed）；`$PY scripts/l3_secret_audit.py`（或等价扫描）覆盖 `artifacts/llm_cache/`，0 命中；`git log -p ab509d3..HEAD | grep -c 'nvapi-'` 为 0

## §4 自主权
- 环境问题（venv、pip、PATH、缓存目录、网络重试、docker start）由你自行解决，前提是 python 3.12.3 和 numpy 2.5.4 不变。
- 实现细节、测试组织、并行策略、顺手修的小 bug：自行处理，在报告中列出。
- 硬停只限：版本钉死无法满足；与 §1 裁决冲突；密钥（P13 失败、401/403、任何疑似泄露）；需要改注册文件；远端已有同名分支；基线测试不是 187/4；B-1 不一致。

## §5 失败报告
任何停止：写 `~/reality-residual-agent-worktrees/_reports/REPORT_D3_L5_nogo4.md`，内容包括已完成步骤、失败命令原文（含 key 的命令只写变量名，不写值）、输出最后 50 行、你的判断，并给出 sha256。已有的 nogo、nogo2、nogo3 保留，不要覆盖。

## §6 收尾
- 报告写 `~/reality-residual-agent-worktrees/_reports/REPORT_D3_L5B.md`（**不要覆盖**已有的 REPORT_D3_L5.md）：§0 复核表实测值、P13 条目名、B0–B-6 逐项 PASS/FAIL 及数字、N_amb 与实际 llm_calls、是否 SUBSET、新旧哈希、环境版本、PR 链接。末尾附自身 sha256，并追加到 `ARCHIVE_D3.sha256`。
- 确认 shell 中已 `unset NVIDIA_API_KEY`。
- 不合并 PR，不删 worktree 或分支，不删容器。等控制会话审查后由合并卡统一收尾。
