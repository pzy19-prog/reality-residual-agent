# 任务卡 FRZ-1-R1 — 修复重观测保持被提前结束（PR #24 BLOCK X1）（v1）
执行者：Luna（GPT-6 Luna，Codex CLI，WSL），新会话
仓库：pzy19-prog/reality-residual-agent；主库 ~/reality-residual-agent
工作区：~/reality-residual-agent-worktrees/frz1-b3core　分支 feat/frz1-b3core　基线 7e2c4a70b794df0223cd0c5e44d17997bfba7445（PR #24 head；**不要重建**）
git 身份："Xifeng Ming" <274782819+pzy19-prog@users.noreply.github.com>；提交与 PR 不加任何 Claude/AI 署名行
测试框架：pytest；基线：7e2c4a7 上 198 passed / 4 skipped
**本卡不调用 NIM、不读取任何密钥**。派发已开放主库 .git 写权限。
依据：`~/reality-residual-agent-worktrees/_control/_reviews/PR24.md`（X1）；A05（PR #23）§1；卡 `_cards/FRZ-1_v2.md` F1、F8、F9。

## §0.0 Bootstrap
```
cd ~/reality-residual-agent && git fetch origin
test "$(git rev-parse origin/feat/frz1-b3core)" = "7e2c4a70b794df0223cd0c5e44d17997bfba7445" || 停
cd ~/reality-residual-agent-worktrees/frz1-b3core
test "$(git rev-parse HEAD)" = "7e2c4a70b794df0223cd0c5e44d17997bfba7445" && test -z "$(git status --porcelain)" || 停
PY=$PWD/.venv/bin/python
PYTHONPATH=$PWD/src $PY -c "import rra;print(rra.__file__)"   # 须指向 frz1-b3core/src
test -f /tmp/frz1-base-b3/b3-dev.json || 停（基线 B3 输出缺失 → 用 9fe1730 代码重新生成；在报告中说明）
```

## §0 实测核对表（控制会话 2026-10-24 读 7e2c4a7 代码）
| # | 前提 | 实测值 |
|---|---|---|
| Q1 | 提前结束 1 | ESCALATE 分支中 `if (… s2_action is Action.PAUSE_AND_REOBSERVE): 进入保持` 之后的 `elif observation.target_id in system2_reobserve_holds: finish_reobserve_hold(...)`：S2 本步没运行时 `s2_action=None`，保持被立即结束 |
| Q2 | 提前结束 2 | S2 块之后的 `if (target in system2_reobserve_holds and s2_action is not Action.PAUSE_AND_REOBSERVE and target not in system2_authorized): finish_reobserve_hold(...)`：`s2_action=None` 时同样会触发 |
| Q3 | 现象 | REPORT_D4_FRZ1 V3：进入 195、复查 33、授权 0、耗尽 195；metrics 与终态计数和基线完全相同 |

## §1 已裁决
- R1 两处结束条件都只能在 **S2 本步实际运行过**（`s2_action is not None`）时判断。S2 没有运行的步骤，不论目标是否仍在升级，保持都继续，直到 A05 §1.4 的结束条件之一成立：锁存；窗口末端（沿用现有的 `base_plan.expected_arrival_time + dt/2 - t <= 0`）；目标切换或其他终态到期；episode 结束。S2 运行并返回非 PAUSE、且未授权时（例如 HUMAN_ESCALATION），按现有逻辑结束保持。
- R2 记录每次保持的结束原因，在 receipt 的 `system2_reobserve` 里增加 `end_reasons` 计数：`authorized`、`window_end`、`latch`、`target_switch`、`s2_non_pause`、`episode_end`。该字段进入 receipt（确定性）。
- R3 回归测试（至少 2 个）：
  - (a) 连续升级：构造或选取一个目标，进入保持后每一步都 `ESCALATE:`，断言它在 +0.5 s、+1.0 s… 都被复查，直到窗口末端，且结束原因为 `window_end`
  - (b) 不变量：在 diag 子集的若干 dev seed 上，对每个以 `window_end` 结束的保持，检查同一目标相邻两次 S2 决策的时间间隔 ≤ 0.5 + dt + 1e-9（容差写明）
- R4 重新生成 artifact（规则与 FRZ-1 v2 F8 相同）：`artifacts/s2/b3-dev.json`/`.md`，以及 meterless 的 B3 部分（`scripts/l6_persist_and_replay.py`）；B4 部分继续保持 stale。重测 F9（新代码；全 dev 130×4 和子集 33×4：调用点、去重请求、每 episode 最大值/中位数）。
- R5 提交方式：在 feat/frz1-b3core 上**新增提交**（代码和测试一个提交，artifact 一个提交），普通 push 更新 PR #24。禁止 force push、rebase、新建分支、合并。
- R6 不改：docs、requirements、adapter 的 prompt 和请求体、verifier 阈值、DSL、评估器、TERMINAL_STATES。

## §2 验收（数字写进报告）
- V1 pytest 全绿（≥ 200 passed，即 198 + 新增 ≥ 2）
- V2 B1 不变：新 b3-dev 的 `b1_receipt_sha256` 与 /tmp/frz1-base-b3 一致 130/130
- V3 F1 计数（全 dev 130 seed）：进入保持、复查次数、保持后授权、结束原因分布（R2 的 6 类）。diag 子集：n<6 调用占比、只调用一次的对象数。与 7e2c4a7 和基线 9fe1730 三方对照
- V4 B3 metrics 三方对照（基线 9fe1730 / 7e2c4a7 / 新代码）：recoverable_challenge_success_count、wrong_disposition、miss、unsafe_action（按来源）、preservation_regression_count、authorization_count、system2_calls、终态计数。**只报告，不设门槛，不得为改善数字调参**
- V5 安全：`unsafe_action_by_source.s2_authorized`。如果 >0，逐个列出 seed/target、授权时刻、n_usable、所选结构、common_action 时刻、执行误差，**不要修**；fast_layer_command 的 unsafe 如果增加，也逐个列出。锁存后的 S2 授权数为 0
- V6 确定性：b3-dev 连续生成两次 receipt 相同，且用代码规则复算一致
- V7 F9 新数字表（附 7e2c4a7 的旧数字对照）
- V8 身份、密钥、范围：作者 Xifeng Ming noreply；`nvapi-` 计数 0；`git diff --name-only origin/main...HEAD -- docs requirements.txt` 为空
- V9 PR #24 新 head 的 CI：test 和 determinism 均 pass

## §4 自主权
实现细节自行处理。硬停只限：§0 不符；需要改 R6 范围；B1 哈希变化；修好后保持语义与 A05 §1 冲突（写明原文和代码行）。V5 出现 unsafe 不是硬停。

## §5 失败报告
`~/reality-residual-agent-worktrees/_reports/REPORT_D4_FRZ1R1_nogo.md`，给出 sha256。

## §6 收尾
报告写 `~/reality-residual-agent-worktrees/_reports/REPORT_D4_FRZ1R1.md`（§0、R1–R4 改动及代码行、V1–V9、PR #24 新 head）。**先定稿再算哈希**：末行写 `Report SHA-256 (body = content before this line, trailing whitespace stripped, plus one "\n"): <sha>`，并追加到 `ARCHIVE_D3.sha256`。不合并。
