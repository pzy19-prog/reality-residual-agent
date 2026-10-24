# 任务卡 L5-B-R1 — PR #20 修复（v1）
执行者：Luna（GPT-6 Luna，Codex CLI，WSL），**新会话**
仓库：pzy19-prog/reality-residual-agent；主库 ~/reality-residual-agent
工作区：~/reality-residual-agent-worktrees/l5b-b4　分支 feat/l5b-b4　基线 92e2b89a545753a831c8ca0c3fd7aaf22fc89d49（PR #20 head；**不要重建**）
git 身份："Xifeng Ming" <274782819+pzy19-prog@users.noreply.github.com>；提交与 PR 不加任何 Claude/AI 署名行
测试框架：pytest（pyproject：testpaths=["tests"]，pythonpath=["src"]）。基线：92e2b89 上 190 passed / 4 skipped
依据：审查结论 `~/reality-residual-agent-worktrees/_control/_reviews/PR20.md`（BLOCK：X1；同修 X2；顺修 N2、N3）
**本卡不调用 NIM、不需要也不得读取任何密钥**（不运行 pass，不 export NVIDIA_API_KEY）

## §0.0 Bootstrap
1. 校验并通读（sha256 不符 → 停）：
   ```
   cd ~/reality-residual-agent-worktrees/_control
   echo "0118bcaf6f9ef4803557abc4191593c55888d2fa6e8e226e1046e10db61ca923  _cards/L5-B_v1.md" | sha256sum -c
   sha256sum _reviews/PR20.md   # 记录到报告；正文以文件为准
   ```
   读 `_cards/L5-B_v1.md`、`_reviews/PR20.md`、`_reports/REPORT_D3_L5B.md`。
2. 工作区：
   ```
   cd ~/reality-residual-agent-worktrees/l5b-b4
   test "$(git rev-parse HEAD)" = "92e2b89a545753a831c8ca0c3fd7aaf22fc89d49"
   test -z "$(git status --porcelain)"
   test "$(git -C ~/reality-residual-agent ls-remote origin refs/heads/feat/l5b-b4 | cut -c1-40)" = "92e2b89a545753a831c8ca0c3fd7aaf22fc89d49"
   PY=$PWD/.venv/bin/python
   $PY -c "import sys,numpy,rra;print(sys.version.split()[0],numpy.__version__,rra.__file__)"   # 须 3.12.3 2.5.4 …/l5b-b4/src/rra/__init__.py
   $PY -m pytest -q   # 须 190 passed / 4 skipped
   ```
   任一不符 → 停。

## §0 实测核对表（控制会话 2026-10-23 实测）
| # | 前提 | 实测值 |
|---|---|---|
| Q1 | l5b-b4 HEAD / 干净 | 92e2b89…，porcelain 0 行 |
| Q2 | 远端 feat/l5b-b4 | 92e2b89…（即 PR #20 head） |
| Q3 | pytest | 190 passed / 4 skipped（审查复跑 286s） |
| Q4 | 断网回放可行 | `unshare -rn` 可用，内部连外网报 `Errno 101`；`$PY -m rra.cli s2-b4-dev --subset --replay` exit 0，llm_calls=0 |
| Q5 | 回放 = 提交 artifact（llm_calls 清零后） | 回放 receipt `b49a6c0cc8ad15c25866b89f5eea04956e615afca8ae753fcab8df4f9017e971`；per-episode receipt/decisions/proposal_rank 132/132 一致 |
| Q6 | 提交 artifact receipt `ad473c0f…f238` | 按代码规则不可复算；含代码中不存在的键 `canonical_replay_live_llm_calls` |
| Q7 | D4 偏差影响 | 27 个 TEXT_TIEBREAK 中：fault ID 排在被选结构前 0 次、含未知 ID 0 次、被选不是第一名 0 次 |
| Q8 | 回放 PROVIDER_ERROR | 5 次（与在线一致） |

## §1 已裁决
- R1（X1）**artifact 只能由代码一次生成**：
  - 每个 (seed, 变体) 记录 `llm_requests_served`（该任务里 provider 成功返回的请求数，replay 命中 + live 调用之和；确定性，**进入**哈希）。
  - 运行相关的数字（`live_llm_calls`、耗时、nproc、serial/parallel 计时）放进 `operational_cost`，**不进入** receipt 哈希，做法同 b3_dev。
  - metrics 中 `llm_calls` 改为基于 `llm_requests_served` 的确定性计数；live 调用数只出现在 `operational_cost`。
  - 删除任何手工后处理；不得出现代码之外写入的键。最终 `artifacts/s2/b4-dev.json` 由下面这条命令直接生成，之后不再手动改动：
    `unshare -rn env PYTHONPATH=$PWD/src $PY -m rra.cli s2-b4-dev --subset --replay`
  - 在 `operational_cost` 中另写 `historical_live_run`：`{"source_commit": "92e2b89", "live_llm_calls": 376, "note": "transcribed from REPORT_D3_L5B.md"}`。这是唯一允许的抄录值，不进入哈希。
- R2（X2）**D4 回落按顺序判断**：按 proposal 顺序扫描，第一个命中的是 fault ID → `TIEBREAK_FALLBACK:FAULT_ID`；proposal 含任何未知 ID（`receipt.unknown_ids` 非空）→ `TIEBREAK_FALLBACK:UNKNOWN_ID`；其余规则不变。补两个单元测试（假 proposer）。
- R3（N2）删除 `scripts/l6_b4_meterless_replay.py` 中回退到 `l5a-hygiene` 的路径；vendored Meterless 缺失时用 `git submodule update --init`（如该路径是 submodule）补齐，否则明确报错退出。不得引用其他 worktree 的路径。
- R4（N3）报告中对 TEXT_TIEBREAK 授权数给出统计口径；审查端按 decisions 计为 25。
- R5 不改 adapter、prompt、请求体（会改变缓存键）；不处理 N1、N4、N5。
- R6 提交方式：在 feat/l5b-b4 上**新增提交**并普通 push（更新 PR #20）。禁止 force push、禁止 rebase 已推送提交、禁止新建分支、不合并。

## §2 验收（数字写进报告）
- V1 新 artifact 的 `receipt_sha256` 能用代码规则从文件正文复算（给出复算命令和结果）；**连续生成两次**，receipt 逐字相同。
- V2 与 92e2b89 的 artifact 逐 (seed, 变体) 对比：所有 B4_STRICT / B4_TIEBREAK 的 **actions 和 authorizations** 132/132 相同；decisions 中只允许 `gate_reason` 在 `TIEBREAK_FALLBACK:*` 之间变化（列出变化计数）。出现其他差异 → 停，写 nogo。
- V3 B-1 strict 与 B3 decisions 132/132 一致；B3 子集 receipt 33/33 与 `b3-dev.json` 一致。
- V4 `sum(llm_requests_served)` 与 376 对比，写出差值和原因（例如 probes、失败请求）。
- V5 B-4：重跑 `scripts/l6_b4_meterless_replay.py`，decisions 20/20、receipt 20/20 一致，更新 `meterless-persistence.json`；不依赖其他 worktree。
- V6 `$PY -m pytest -q` 全绿（≥ 192 passed，即新增 2 个测试）；`git grep -n "l5a-hygiene" -- src scripts tests` 为空；`git log -p 92e2b89..HEAD | grep -cE 'nvapi-[A-Za-z0-9_-]{10,}'` 为 0。

## §4 自主权
环境与实现细节自行处理（python 3.12.3、numpy 2.5.4 不变）。硬停只限：版本钉死无法满足；与 §1 冲突；任何需要密钥或 NIM 的情况；需要改注册文件；基线不符；V2 出现非允许差异。

## §5 失败报告
写 `~/reality-residual-agent-worktrees/_reports/REPORT_D3_L5B_R1_nogo.md`（已完成步骤、失败命令原文、输出最后 50 行、判断），给出 sha256。

## §6 收尾
报告写 `~/reality-residual-agent-worktrees/_reports/REPORT_D3_L5B_R1.md`：§0 复核值、R1–R4 改动说明、V1–V6 逐项数字、新旧 receipt 对照、PR #20 新 head。末尾附自身 sha256 并追加到 `ARCHIVE_D3.sha256`。不合并，不删 worktree 或分支。
