# 任务卡 FRZ-1 — 冻结前 B3 核心修复（重观测、fail-closed、回放与确定性加固）（v1）
执行者：Luna（GPT-6 Luna，Codex CLI，WSL），新会话
仓库：pzy19-prog/reality-residual-agent；主库 ~/reality-residual-agent
工作区（由你创建）：~/reality-residual-agent-worktrees/frz1-b3core　分支 feat/frz1-b3core　基线 origin/main = 9fe1730（PR #20 合并提交）
git 身份："Xifeng Ming" <274782819+pzy19-prog@users.noreply.github.com>；提交与 PR 不加任何 Claude/AI 署名行
测试框架：pytest（pyproject：testpaths=["tests"]，pythonpath=["src"]）。预期基线：9fe1730 上 192 passed / 4 skipped
**本卡不调用 NIM、不需要也不得读取任何密钥**（不运行 pass，不 export NVIDIA_API_KEY）
派发已开放主库 .git 写权限（`--add-dir ~/reality-residual-agent/.git`），直接在主库执行 git 命令，不要另建克隆。
依据：`_reviews/PR19.md` N2、N4；`_reviews/PR20_R1.md` N2、N3；云端只读诊断 `origin/cloud/t1-pr20-review:docs/_review/T1_pr20_review.md`、`origin/cloud/t3-failure-funnel:docs/_diag/T3_failure_funnel.md`（只读参考，不要合并这些分支）；A04（docs/P3_PREREG_ADDENDUM_04.md）。

## §0.0 Bootstrap
```
cd ~/reality-residual-agent && git fetch origin
test "$(git rev-parse --short=7 origin/main)" = "9fe1730" || 停（报告新 SHA；如果只多了 docs/ 下的附录合并提交，可以以新 SHA 为基线继续并注明）
git ls-remote --exit-code origin refs/heads/feat/frz1-b3core && 停
git worktree add -b feat/frz1-b3core ~/reality-residual-agent-worktrees/frz1-b3core origin/main
cd ~/reality-residual-agent-worktrees/frz1-b3core
git config user.name "Xifeng Ming"; git config user.email "274782819+pzy19-prog@users.noreply.github.com"
/usr/bin/python3.12 -m venv .venv && .venv/bin/pip install -q -r requirements.txt pytest
PY=$PWD/.venv/bin/python
PYTHONPATH=$PWD/src $PY -c "import sys,numpy,rra;print(sys.version.split()[0],numpy.__version__,rra.__file__)"   # 须 3.12.3 2.5.4 …/frz1-b3core/src/rra/__init__.py
PYTHONPATH=$PWD/src $PY -m pytest -q -p no:cacheprovider    # 须 192 passed / 4 skipped
PYTHONPATH=$PWD/src $PY -m rra.cli s2-b3-dev --output-dir /tmp/frz1-base-b3   # 基线 B3 dev，留作对照（不要写进仓库）
```
（`.venv` 不要提交；如果 .gitignore 没有覆盖它，在报告里说明，不要改 .gitignore 以外的文件来处理。）

## §0 实测核对表（控制会话 2026-10-24 实测，任一不符 → 停并报告）
| # | 前提 | 实测值 | 复核命令 |
|---|---|---|---|
| Q1 | PAUSE 后不会主动复查 | `src/rra/evidence/episode.py:626-628`：只有 `escalation_event`（新的升级上升沿）或"未尝试过的 infeasible"才会进入 S2；`:832-834` PAUSE 时只设置 `system2_next_retry = t+0.5`，它只是下限 | `sed -n 618,640p;826,836p` |
| Q2 | 影响规模（T3，diag 33 seed） | 498 次调用中 352 次 n<6；323/396 个对象只被调用一次；272 个对象的所有调用都 n<6，末次调用时剩余窗口中位 5.831 s | T3 §4 C3（只读参考） |
| Q3 | 锁存证据为空时跳过 | `episode.py:269-271` 附近：`if not supporting_ids and fault in {SENSOR_STUCK, BELT_STOP…}: continue` | `grep -n "not supporting_ids" src/rra/evidence/episode.py` |
| Q4 | 回放缓存未命中被悄悄回落 | `src/rra/llm/adapter.py` 在 `except (… RuntimeError, OSError)` 里把异常转成 `Proposal.error`；`ReplayCacheMiss` 是 `FileNotFoundError` 的子类（`providers.py`）→ 标为 PROVIDER_ERROR，运行 exit 0（T1 §4：云端 VM 回放只命中 62 个请求） | `grep -n "except\|class ReplayCacheMiss" src/rra/llm/adapter.py src/rra/llm/providers.py` |
| Q5 | 无 proposer 时会悄悄回落 | `episode.py:667-669`：`proposer is None` → `NO_PROPOSER` → `TIEBREAK_FALLBACK:NO_PROPOSER` | `grep -n NO_PROPOSER src/rra/evidence/episode.py` |
| Q6 | 拟合网格 | `src/rra/s2/fitter.py:47-48`：tau 网格 `np.arange(0.5,5.001,0.05)`，delay 网格 `np.arange(0.0,0.501,0.01)`；T3 §6：跨机器有 8 处 speed_step_time 取到相邻格（最后一位浮点差引起的平局翻转） | `sed -n 36,80p src/rra/s2/fitter.py` |
| Q7 | runtime_versions 只有 python/numpy | `src/rra/eval/b3_dev.py:262`（b4_dev.py 同理） | `grep -rn runtime_versions src/rra` |
| Q8 | 写死或运行时的 git sha | `scripts/l3_equivalence.py:154` 写死 `2a3b52d…`；`scripts/l6_b4_meterless_replay.py` 用运行时 `git rev-parse HEAD` 写入 manifest，`src/rra/sponsor/meterless.py:253-312` 的 manifest_sha256 覆盖了 base_git_sha | 同左 |

## §1 已裁决
- F1 **PAUSE 后定时重观测**（实现 P3 §8.3 和 "n<6 必须 re-observe"，以及 decisions.md 写的"按目标重观测时步进复查"）：某目标的 S2 决策为 PAUSE_AND_REOBSERVE 之后，只要它还没有被 S2 授权、没有锁存、仍在拾取窗口内、也还没有终态，就在仿真时间到达 `system2_next_retry`（= 该次决策时间 + 0.5 s，沿用现有常量）后的第一个观测点，以当时累积的观测重新走同一条 S2 路径（run_b3 → 现有门控 → 授权）。即使没有新的升级上升沿也照样复查。复查结果仍为 PAUSE 的，再往后推 0.5 s。B3、B4_STRICT、B4_TIEBREAK 完全一致；B1（system2_enabled=False）行为与 receipt 不变。"终态"按现有 outcome 定义判断；如果你认为 `escalated` 记录是否算终态存在歧义，在报告中写明你的判断依据和代码行。
- F2 **锁存 fail-closed**（PR19 N4）：证据为空时照样锁存（证据 id 用该目标已有的 evidence_ids，仍为空就记录空列表），不得 `continue`。补测试。
- F3 **回放缓存未命中即中止**：在 replay-only 模式下，`ReplayCacheMiss` 不得被 adapter 转为 proposal error，必须向上抛出，让 `s2-b4-dev --replay` 以非 0 退出，并在 stderr 打印未命中的请求 sha。live 模式行为不变（未命中就走 live 调用）。补测试（假 provider）。
- F4 **B4 变体缺少 proposer 是配置错误**：`run_episode(s2_variant in {B4_STRICT, B4_TIEBREAK}, proposer=None)` 在入口抛 ValueError，删除 `NO_PROPOSER` 回落路径。补测试。
- F5 **拟合网格平局规则**：tau 和 delay 网格选 argmin 时，目标值与最小值之差 ≤ `1e-12 * max(1, |最小值|)` 的都算平局，取网格值最小的一个。只改选取规则，不改网格、阈值和目标函数。补一个构造平局的单元测试。
- F6 **运行平台记录**：所有写 `runtime_versions` 的地方（b3_dev、b4_dev、episode receipt，有的话）增加 `machine`（platform.machine()）、`cpu_model`（/proc/cpuinfo 第一条 `model name`，读不到就写 null）、`blas`（`numpy.show_config(mode="dicts")` 里 Build Dependencies 的 blas 名称和版本）。仍然不进入任何哈希。
- F7 **git sha 不进哈希**（PR19 N2、PR20_R1 N2）：`scripts/l3_equivalence.py` 改为运行时 `git rev-parse HEAD`；meterless 的 manifest 保留 `base_git_sha` 字段，但 `manifest_sha256` 改为在排除 `base_git_sha` 后计算（如果 manifest 哈希由 Meterless 引擎计算、仓库这一侧无法排除，就停在这一步，在报告中说明原因，其余继续）。
- F8 **重生成 artifact**（只在本卡代码上生成，生成后不再手改）：
  - `artifacts/s2/b3-dev.json`/`.md`：`$PY -m rra.cli s2-b3-dev`（默认输出目录）
  - meterless：只重跑 B3 部分 `scripts/l6_persist_and_replay.py`（先 `scripts/setup_meterless.sh`）。B4 部分 `scripts/l6_b4_meterless_replay.py` 依赖 NIM 缓存，会因为 F1 产生新的请求而未命中，所以**不重跑**；如果 B3 部分重跑会覆盖或删除 `meterless-persistence.json` 里的 B4 段，保留原有的 B4 段并标记 stale，在报告中说明做法
  - `artifacts/s2/b4-dev.json` 和 meterless 的 B4 部分**本卡不重生成**，报告中标为"stale，待 FRZ-2（需要 NIM）"
  - L3 equivalence 需要 ops 容器，本卡不跑
- F9 **测算 B4 调用量**（为 NIM 预算服务，不调用 NIM）：用一个计数用的假 proposer（每次返回合法的空 proposal），跑 B4_STRICT（strict 的动作恒等于 B3，所以计数就是调用点个数）：
  - 全 dev 130 seed × 4 文本变体，以及 diag 子集 33 seed × 4 变体：调用点总数、去重后的请求数（按 evidence_packet+context_text 去重，与 `_MemoizedProposer` 的做法一致）、每个 episode 的最大值和中位数
  - 同样口径算一遍基线（9fe1730）的数，作对照
  - eval-v3 的 episode 规模：只从 P3 / config/v3_contracts.json / 代码里读出规定的数量（**不得生成或查看 eval-v3 seed 值**），给出计算依据
- F10 不改：`docs/`（预注册文件一律不动）、`requirements.txt`、adapter 的 prompt 和请求体（证据包和格式修复留给 FRZ-2）、B2 相关代码、verifier 阈值、DSL。
- F11 交付：按 F1–F7 分成若干提交（每个提交只做一件事），最后一个提交放 F8 的 artifact；`git push -u origin feat/frz1-b3core`；`gh pr create --base main --head feat/frz1-b3core --title "FRZ-1: S2 re-observation, fail-closed latch, replay/determinism hardening"`，正文写改动清单、F8 的 stale 清单、F9 的数字。不合并。

## §2 验收（数字写进报告）
- V1 pytest 全绿，≥ 192 + 新增测试数（列出新增测试名）；`git grep -n NO_PROPOSER -- src` 为空。
- V2 B1 不变：新代码重生成的 b3-dev.json 中逐 seed `b1_receipt_sha256` 与基线 /tmp/frz1-base-b3 的结果 130/130 相同。
- V3 B3 变化报告（**只报告，不设门槛，也不得为了改善这些数字去调参**）：基线 vs 新代码的 metrics 全字段对照表（recoverable_challenge_success_count、wrong_disposition、miss、unsafe_action 及 unsafe_action_by_source、preservation_regression_count、authorization_count、system2_calls）；S2 调用中 n<6 的占比；以及只被调用一次的对象数。
- V4 安全不变量：`unsafe_action_by_source.s2_authorized` 的数值（基线是 0；如果新代码 >0，列出每个 seed/target、授权时刻、n_usable、所选结构，**不要修**，写进报告由审查端裁决）；锁存后 S2 授权数为 0。
- V5 确定性：新 b3-dev 连续生成两次，receipt 相同；`runtime_versions` 含 F6 的新字段；receipt 用代码规则复算一致。
- V6 F3/F4 的行为：`s2-b4-dev --subset --replay` 在新代码下以非 0 退出，并打印第一个未命中的请求 sha（预期如此，因为 F1 改变了调用点），写出退出码和 stderr 前 5 行。
- V7 F9 的数字表。
- V8 身份与密钥：作者和提交者为 Xifeng Ming noreply；没有署名行；`git log -p origin/main..HEAD | grep -cE 'nvapi-[A-Za-z0-9_-]{10,}'` = 0；`git diff --name-only origin/main...HEAD -- docs requirements.txt` 为空。
- V9 PR 的 CI：test 和 determinism 均为 pass（等 CI 跑完；超过 30 分钟就写当时状态）。

## §4 自主权
实现细节和环境问题自行处理（python 3.12.3、numpy 2.5.4 不变）。硬停只限：Q1–Q8 不符；远端已有同名分支；基线测试不符；需要改 F10 列出的范围；F1 与现有 outcome 机制无法在不改评估器口径的前提下实现（写明冲突的代码行）；V2 B1 哈希出现变化。V4 出现 s2_authorized unsafe **不是**硬停：照常完成并如实报告。

## §5 失败报告
写 `~/reality-residual-agent-worktrees/_reports/REPORT_D4_FRZ1_nogo.md`：已完成步骤、失败命令原文、输出最后 50 行、判断；给出 sha256。

## §6 收尾
报告写 `~/reality-residual-agent-worktrees/_reports/REPORT_D4_FRZ1.md`：§0 复核值、F1–F9 改动说明（附代码行）、V1–V9 逐项结果和数字、PR 编号与 head SHA。**先定稿再算哈希**：末行写 `Report SHA-256 (body = content before this line, trailing whitespace stripped, plus one "\n"): <sha>`，并追加到 `ARCHIVE_D3.sha256`；写完哈希后不得再改正文。不合并，不删 worktree 或分支。
