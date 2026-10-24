# 任务卡 FRZ-1 — 冻结前 B3 核心修复（重观测、fail-closed、回放与确定性加固）（v2，替代 v1；v1 nogo 原因：F1 与"escalated 立即终态"冲突，见 `_reports/REPORT_D4_FRZ1_nogo.md`）
执行者：Luna（GPT-6 Luna，Codex CLI，WSL），新会话
仓库：pzy19-prog/reality-residual-agent；主库 ~/reality-residual-agent
工作区（由你创建）：~/reality-residual-agent-worktrees/frz1-b3core　分支 feat/frz1-b3core　基线 origin/main = 9fe1730（PR #20 合并提交）
git 身份："Xifeng Ming" <274782819+pzy19-prog@users.noreply.github.com>；提交与 PR 不加任何 Claude/AI 署名行
测试框架：pytest（pyproject：testpaths=["tests"]，pythonpath=["src"]）。预期基线：9fe1730 上 192 passed / 4 skipped
**本卡不调用 NIM、不需要也不得读取任何密钥**（不运行 pass，不 export NVIDIA_API_KEY）
派发已开放主库 .git 写权限（`--add-dir ~/reality-residual-agent/.git`），直接在主库执行 git 命令，不要另建克隆。
依据：`_reviews/PR19.md` N2、N4；`_reviews/PR20_R1.md` N2、N3；云端只读诊断 `origin/cloud/t1-pr20-review:docs/_review/T1_pr20_review.md`、`origin/cloud/t3-failure-funnel:docs/_diag/T3_failure_funnel.md`（只读参考，不要合并这些分支）；A04（docs/P3_PREREG_ADDENDUM_04.md）。

## §0.0 Bootstrap（v1 已建好 worktree、.venv 和基线输出，复用即可）
```
cd ~/reality-residual-agent && git fetch origin
test "$(git rev-parse --short=7 origin/main)" = "9fe1730" || 停（报告新 SHA；如果只多了 docs/ 下的附录合并提交，可以以新 SHA 为基线继续并注明）
git ls-remote --exit-code origin refs/heads/feat/frz1-b3core && 停
cd ~/reality-residual-agent-worktrees/frz1-b3core
test "$(git rev-parse --short=7 HEAD)" = "9fe1730" && test -z "$(git status --porcelain)" || 停
PY=$PWD/.venv/bin/python
PYTHONPATH=$PWD/src $PY -c "import sys,numpy,rra;print(sys.version.split()[0],numpy.__version__,rra.__file__)"   # 须 3.12.3 2.5.4 …/frz1-b3core/src/rra/__init__.py
test -f /tmp/frz1-base-b3/b3-dev.json || PYTHONPATH=$PWD/src $PY -m rra.cli s2-b3-dev --output-dir /tmp/frz1-base-b3
（v1 已测基线 pytest 192 passed / 4 skipped，不必重跑）
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
| Q9 | 目标级升级立即终态 | `episode.py:37` `TERMINAL_STATES` 含 `escalated`；`:835-842` S2 返回 PAUSE 的同一步，未授权的 `ESCALATE:` 目标被 `record_outcome(...,"escalated")` 并设 `safe_stop=True`；`record_outcome` 先写者为准（`:286-287`） | `sed -n 276,293p;832,842p` |
| Q10 | 已有的 episode 级重试模式 | `:430-446`：outcome_escalation 授权后清 `outcome_escalation_*`，未锁存时 `safe_stop=False`；否则 `outcome_retry_at_global = t+0.5`、`safe_stop=True`，最多 3 次（`outcome_escalation_attempts < 3`） | `sed -n 425,450p` |
| Q8 | 写死或运行时的 git sha | `scripts/l3_equivalence.py:154` 写死 `2a3b52d…`；`scripts/l6_b4_meterless_replay.py` 用运行时 `git rev-parse HEAD` 写入 manifest，`src/rra/sponsor/meterless.py:253-312` 的 manifest_sha256 覆盖了 base_git_sha | 同左 |

## §1 已裁决
- F1 **目标级"重观测保持"**（实现 P3 §8.3："PAUSE_AND_REOBSERVE, then human escalation if additional structured evidence does not resolve it"；模式照搬 Q10 的 episode 级重试）。**控制会话裁决：推迟写入 `escalated` 是策略行为的改变，不算评估器口径的改变，本卡授权这样做。** 评估器、TERMINAL_STATES、计分规则、分母一律不改。
  1. 进入保持：某目标 T 在某一步出现 `ESCALATE:`，且同一步 S2 对 T 的决策是 PAUSE_AND_REOBSERVE（无锁存、T 未被授权）时，**这一步不对 T 调用 `record_outcome(...,"escalated")`**；照常设 `safe_stop = True`（整线停止快速层发令，与现在相同的保守效果）；把 T 加入"保持集"，记录进入时的 escalate reason，`system2_next_retry[T] = t + 0.5`。
  2. 保持期间：T 不接受快速层命令。T 的第一个满足 `observation.time >= system2_next_retry[T]` 的观测点，不论有没有新的升级上升沿，都用当时累积的观测重新走同一条 S2 路径（run_b3 → 门控 → 授权；B4 变体照常经过 A04 的调用条件）。结果为 PAUSE → 再推后 0.5 s；结果为授权 → 走现有授权路径，T 移出保持集，并且仅当保持集为空且未锁存时才 `safe_stop = False`（照搬 `:441-442` 的条件）。
  3. 结束保持（转为升级）：出现以下任一情况，就在那一步对 T 写 `record_outcome(T, "escalated", <进入时的 reason> + ";REOBSERVE_EXHAUSTED", …)`，并把 T 移出保持集：硬故障锁存；T 已没有足够时间执行命令（用现有的 `window_remaining_time` 定义，`:748` 附近；剩余时间 ≤ 0 或不足以让授权命令按现有执行逻辑落在窗口内，二者取先到者，在报告里写明用的是哪个判断和代码行）；或 T 将因其他原因得到终态。`escalations` 列表在这一步追加，不在进入保持时追加。
  4. episode 结束时保持集里仍有目标的，按 3 写 `escalated`，不得留下无终态的目标。
  5. 只有 S2 返回 PAUSE 的目标进入保持；S2 返回 HUMAN_ESCALATION、锁存、或 S2 未运行（system2_enabled=False）时行为与现在完全相同。B1 的行为和 receipt 不变。B3、B4_STRICT、B4_TIEBREAK 用同一套逻辑。
  6. 补测试：(a) 保持中的目标在 +0.5 s 后被复查（不需要新的上升沿）；(b) 保持期间快速层不对该目标发令；(c) 窗口耗尽时写入 `escalated` 且 reason 以 `;REOBSERVE_EXHAUSTED` 结尾；(d) 锁存立即结束保持；(e) B1 的 receipt 不变（已有测试覆盖的话写明）。
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
- V3 B3 变化报告（**只报告，不设门槛，也不得为了改善这些数字去调参**）：基线 vs 新代码的 metrics 全字段对照表（recoverable_challenge_success_count、wrong_disposition、miss、unsafe_action 及 unsafe_action_by_source、preservation_regression_count、authorization_count、system2_calls）；S2 调用中 n<6 的占比；以及只被调用一次的对象数。另报 F1 的计数：进入保持的目标数、复查次数、保持后被授权的目标数、以 `;REOBSERVE_EXHAUSTED` 结束的目标数；以及 B3 终态计数（picked/escalated/skipped/attempt_failed）的基线对照。
- V4 安全不变量：`unsafe_action_by_source.s2_authorized` 的数值（基线是 0；如果新代码 >0，列出每个 seed/target、授权时刻、n_usable、所选结构，**不要修**，写进报告由审查端裁决）；锁存后 S2 授权数为 0。
- V5 确定性：新 b3-dev 连续生成两次，receipt 相同；`runtime_versions` 含 F6 的新字段；receipt 用代码规则复算一致。
- V6 F3/F4 的行为：`s2-b4-dev --subset --replay` 在新代码下以非 0 退出，并打印第一个未命中的请求 sha（预期如此，因为 F1 改变了调用点），写出退出码和 stderr 前 5 行。
- V7 F9 的数字表。
- V8 身份与密钥：作者和提交者为 Xifeng Ming noreply；没有署名行；`git log -p origin/main..HEAD | grep -cE 'nvapi-[A-Za-z0-9_-]{10,}'` = 0；`git diff --name-only origin/main...HEAD -- docs requirements.txt` 为空。
- V9 PR 的 CI：test 和 determinism 均为 pass（等 CI 跑完；超过 30 分钟就写当时状态）。

## §4 自主权
实现细节和环境问题自行处理（python 3.12.3、numpy 2.5.4 不变）。F1 推迟 `escalated` 的写入时机已获授权，不再构成硬停。硬停只限：Q1–Q10 不符；远端已有同名分支；需要改 F10 列出的范围；F1 需要修改评估器、TERMINAL_STATES、计分或分母的定义（写明冲突的代码行）；V2 B1 哈希出现变化。V4 出现 s2_authorized unsafe、或快速层 unsafe 增加，**都不是**硬停：照常完成并如实报告，列出每个对象。

## §5 失败报告
写 `~/reality-residual-agent-worktrees/_reports/REPORT_D4_FRZ1_nogo.md`：已完成步骤、失败命令原文、输出最后 50 行、判断；给出 sha256。

## §6 收尾
报告写 `~/reality-residual-agent-worktrees/_reports/REPORT_D4_FRZ1.md`：§0 复核值、F1–F9 改动说明（附代码行）、V1–V9 逐项结果和数字、PR 编号与 head SHA。**先定稿再算哈希**：末行写 `Report SHA-256 (body = content before this line, trailing whitespace stripped, plus one "\n"): <sha>`，并追加到 `ARCHIVE_D3.sha256`；写完哈希后不得再改正文。不合并，不删 worktree 或分支。
