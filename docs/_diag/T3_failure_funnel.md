# T3 — B3 dev 失败漏斗与 unsafe_action 成因（只读诊断）

- 基线：`main` = `54f5006923b5b08f11a94b5610f26c4342a402cf`（与任务书核对值一致）；分支 `cloud/t3-failure-funnel`
- 执行者：任务书指定的云会话（只读诊断；本文件是分支上唯一新增文件）
- 数据范围：只用 `config/dev_seeds.json`（0–129）和已提交的 `artifacts/s2/*.json`，以及这些文件在 git 历史中的已提交版本。`config/eval_seeds*.json` 未打开。未运行任何 live 命令，也未使用密钥。
- 完成情况：任务书第 1–5 项均已完成，没有因预算中止的项。
- 本文不判定成败。所有计数变化只陈述“从 a 变为 b”。

## 0. 记号与证据规则

- **出处写法**：`文件 → 字段路径`。`artifacts/s2/` 前缀省略。`[]` 表示对列表逐项求和或计数。
- **派生数**（不是文件里直接存的字段，而是对字段做计数或分组）标为 `Rk`（附录 A 脚本里的函数 `rk_*`）或 `Bk`（附录 B 脚本的输出行）。脚本只读已提交 JSON，在仓库根目录用 `python3 -I` 运行即可复现。
- **历史版本**写作 `<sha>:b3-dev.json → 字段`，即 `git show <sha>:artifacts/s2/b3-dev.json` 里的字段。
- **FACT**：可以直接从文件字段或代码行读到。**INFERENCE**：由 FACT 推出的机制性解释，需要“确认还缺的证据”才能坐实。
- 阈值来源（FACT）：verifier 要求 n≥6 且 RMSE≤0.030（`src/rra/s2/verifier.py:26-27`，`src/rra/s2/fitter.py:36` 的 `min_observations=6`）。common-action 容差 = `tolerance` = 0.20（`src/rra/sim/world.py:21`；`src/rra/s2/verifier.py:33-44`）。unsafe 判据之一是 `position_error > 2×tolerance`（`src/rra/eval/scoring.py:97-98`）。evaluator 的 `position_error` 取 `max(空间误差, |实际时刻−命令时刻|×速度)`（`src/rra/controller/control.py:57-60`）。

## 1. 漏斗

### 1.1 全 dev 对象层（130 seeds，`b3-dev.json`）

| 量 | 值 | 出处 |
|---|---:|---|
| episode 数 | 130 | `b3-dev.json → episode_count` |
| 对象总数 | 1560 | R2/R3 附带：`b3-dev.json → episodes[].score.dispositions` 键数之和（12×130） |
| 处置标签 RECOVER / REFUSE / PAUSE_THEN_RECOVER | 1357 / 124 / 79 | B1：`episodes[].score.dispositions[]` 值计数 |
| challenge（B1 未 picked） | 899 | B1：`episodes[].score.challenge_count` 求和 |
| recoverable challenge | 775 | `metrics.recoverable_challenge_count` |
| recoverable challenge success | 84 | `metrics.recoverable_challenge_success_count` |
| wrong_disposition | 589 | `metrics.wrong_disposition` |
| ordinary miss（0.2<e≤0.4） | 96 | `metrics.miss` |
| unsafe_action | 7 | `metrics.unsafe_action` |
| 其中 fast_layer_command / s2_authorized | 7 / 0 | `metrics.unsafe_action_by_source` |
| 同 episode 的 B1-corrected unsafe | 43 | `metrics.b1_corrected_unsafe_action` |
| preservation / regression | 582 / 0 | `metrics.preservation_count` / `metrics.preservation_regression_count` |
| S2 调用次数 | 1961 | `operational_cost.system2_calls` |
| verifier 调用 | 27454 | `operational_cost.verifier_calls`（=1961×14） |
| `authorization_count` | 209 | `metrics.authorization_count`（口径见 §1.5） |
| `pause_refusal` | 1522 | `metrics.pause_refusal`（口径见 §1.5） |
| B3 终态 picked / skipped / escalated / attempt_failed / rejected | 712 / 492 / 253 / 103 / 0 | `episodes[].b3_terminal_counts` 求和 |
| B1 终态 picked / escalated / skipped / attempt_failed / rejected | 661 / 443 / 372 / 84 / 0 | `episodes[].b1_terminal_counts` 求和 |

`b3-dev.json` 只给前 20 个 seed（index<20）保留了逐决策记录 `episodes[].system2_decisions`（`src/rra/eval/b3_dev.py:165-167`）。所以全 dev 的**调用层**阶段只能看到这 20 个 seed（§1.2b）。完整的调用层漏斗来自 diag 子集（§1.2a）。

### 1.2 调用层阶段漏斗（升级 → 拟合 → verifier → common-action → authorization）

阶段定义取自代码：升级 = 进入 `run_b3`（`src/rra/evidence/episode.py:619-621`）；拟合 = `n_usable_total ≥ 6`；verifier = `passing` 非空；common-action = `gate == COMMON_ACTION`；authorization = 决策记录中带 `authorization`（条件见 `episode.py:690-696`：`chosen` 非空、无 fault、`exception` 非空）。

#### 1.2a diag-d1g（33 个 dev seed，396 对象；与 d1f 底层数据逐字段相同，见 §3.1）

| 阶段 | 进入 | 留下 | 流失 | 出处 |
|---|---:|---:|---:|---|
| 对象 | 396 | — | — | R4：`diag-d1g.json → episodes[].score.dispositions` |
| 升级（≥1 次 S2 调用） | 396 对象 | 396 对象 / 498 次调用 | 0 | R4：`episodes[].system2_diagnostic_trace[]` |
| 拟合（n_usable≥6） | 498 调用 | 146 | 352（全部 gate=`NO_VERIFIED_HYPOTHESIS`） | R4：`system2_diagnostic_trace[].n_usable_total`、`.gate` |
| verifier（\|V\|≥1） | 146 | 146 | 0 | R4：`system2_diagnostic_trace[].passing` |
| common-action | 146 | 30（`COMMON_ACTION`） | 116（`AMBIGUOUS`）；`NO_SAFE_ACTION` 0 | R4：`system2_diagnostic_trace[].gate` |
| authorization | 30 个 UPDATE 决策 | 19 个带 authorization 记录 | 11 个没有（全部在 t=0.5） | R4/R6：`episodes[].system2_decisions[].authorization` |
| 授权后对象结局 | 18 个对象 | 14 个不在 wrong_disposition | 4 个在 wrong_disposition；0 个 unsafe | R5：交叉 `system2_decisions[]`、`wrong_disposition_objects[]`、`unsafe_target_ids` |

补充（R5，`diag-d1g.json → episodes[].system2_diagnostic_trace[]`）：
- 每对象调用次数：1 次的 323 个，2 次 59 个，3 次 2 个，4 次 9 个，5 次 3 个。
- 首次调用的 `n_usable_total` <6 的 339 个，≥6 的 57 个。首次调用 `sim_time` 中位数 0.2 s。
- **所有调用都 n<6 的对象有 272 个**。这 272 个对象末次调用时的 `window_remaining_time` 最小 2.208 s，中位数 5.831 s，最大 8.154 s。
- AMBIGUOUS 调用的 \|V\| 分布：3:7，4:1，5:20，6:5，7:29，9:18，11:2，13:1，14:33。在非 fault episode 的 114 次 AMBIGUOUS 中，真实结构在 V 里的有 111 次，不在的 3 次（真实结构来自 `episodes[].structure`，这是 dev 实现值）。

对象级交叉表（R5，`disposition × 是否授权 × 是否 wrong × 是否 unsafe`）：

| disposition | 授权 | wrong | unsafe | 对象数 |
|---|---|---|---|---:|
| RECOVER | 否 | 否 | 否 | 211 |
| RECOVER | 否 | 是 | 否 | 153 |
| RECOVER | 是 | 否 | 否 | 14 |
| RECOVER | 否 | 否 | **是** | 7 |
| REFUSE | 否 | 否 | 否 | 7 |
| RECOVER | 是 | 是 | 否 | 4 |

#### 1.2b 全 dev 前 20 个 seed（`b3-dev.json` 中唯一保留决策记录的部分）

| 记录类型（trigger, action, gate, 有无 authorization） | 数 | 出处 |
|---|---:|---|
| fast, PAUSE, NO_VERIFIED_HYPOTHESIS, 无 | 201 | R1：`b3-dev.json → episodes[0..19].system2_decisions[]` |
| fast, PAUSE, AMBIGUOUS, 无 | 41 | R1 |
| fast, UPDATE, COMMON_ACTION, 有 | 21 | R1 |
| fast, UPDATE, COMMON_ACTION, **无** | 4 | R1 |
| hard_fault_latch, HUMAN_ESCALATION, HARD_FAULT_LATCH, 无 | 20 | R1 |
| outcome_escalation, PAUSE, NO_VERIFIED_HYPOTHESIS, 无 | 9 | R1 |
| outcome_escalation, PAUSE, AMBIGUOUS, 无 | 6 | R1 |
| outcome_escalation, UPDATE, COMMON_ACTION, 有 | 3 | R1 |
| 合计记录 / 这 20 个 seed 的 `system2_calls` 之和 | 305 / 285 | R1；差值 20 = HARD_FAULT_LATCH 记录，这些记录不走 `run_b3` |

- 201 条 fast NO_VERIFIED 记录中，14 个假设全部带 `n_usable < 6` 违例。另外 9 条 outcome_escalation 记录的 verification 没有 `n_usable` 字段，`rmse` 全为 inf（R1，`system2_decisions[].verifications[].violated_invariants`）。
- 这 20 个 seed 共 240 个对象，全部至少有 1 条 S2 记录（R1）。

### 1.3 wrong_disposition 的归因漏斗（diag 脚本自带的分类）

`diag-d1g.json → diagnostic_funnel`（按**末次** S2 调用归类，见 `scripts/d1g_diag.py:27-44`），合计 157，等于 `episodes[].score.wrong_disposition_count` 之和（R4）：

| 类别 | 计数 |
|---|---:|
| n_usable<6 | 87 |
| AMBIGUOUS | 64 |
| 已授权但 miss/未执行 | 4 |
| 门控时刻已在拾取窗口外 | 2 |

同一组对象按**首次**调用归类（`diag-d1f.json → diagnostic_funnel`）：n_usable<6 141，AMBIGUOUS 14，已授权但 miss/未执行 2。逐对象迁移（R6）：(n<6 → n<6) 87，(n<6 → AMBIGUOUS) 50，(AMBIGUOUS → AMBIGUOUS) 14，(n<6 → 窗口外) 2，(n<6 → 已授权但…) 2，(已授权但… → 已授权但…) 2。

口径注意（FACT，`scripts/d1g_diag.py:27-44`）：“已授权但 miss/未执行”是**兜底类**。只要循环没有在前面的 gate 返回，就会落到这里，不要求真的存在授权。另外脚本没有单独的 common-action/authorization 拒绝类别：UPDATE 但没有授权的决策（§1.2a 的 11 个）不会被单独计数。

### 1.4 按 dev 结构分组（R2，`b3-dev.json → episodes[]`）

| case | eps | rec. challenge | success | wrong | miss | unsafe | B1 unsafe | `authorizations` | S2 calls |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ACTUATOR_DELAY | 7 | 29 | 0 | 18 | 11 | 0 | 0 | 0 | 90 |
| SENSOR_BIAS | 7 | 1 | 0 | 1 | 0 | 0 | 0 | 5 | 84 |
| SENSOR_BIAS+ACTUATOR_DELAY | 7 | 45 | 0 | 28 | 17 | 0 | 0 | 7 | 95 |
| SENSOR_BIAS+SPEED_STEP | 7 | 62 | 26 | 29 | 7 | 0 | 0 | 28 | 117 |
| SENSOR_BIAS+SPEED_STEP+ACTUATOR_DELAY | 7 | 74 | 0 | 60 | 13 | 1 | 0 | 15 | 131 |
| SENSOR_BIAS+VELOCITY_OFFSET | 7 | 59 | 9 | 49 | 1 | 0 | 0 | 17 | 121 |
| SENSOR_BIAS+VELOCITY_OFFSET+ACTUATOR_DELAY | 7 | 84 | 8 | 67 | 6 | 3 | 3 | 12 | 111 |
| SENSOR_BIAS+VELOCITY_OFFSET+SPEED_STEP | 7 | 49 | 15 | 29 | 5 | 0 | 0 | 26 | 125 |
| SPEED_STEP | 7 | 29 | 1 | 27 | 1 | 0 | 0 | 10 | 93 |
| SPEED_STEP+ACTUATOR_DELAY | 7 | 60 | 0 | 48 | 12 | 0 | 0 | 6 | 115 |
| VELOCITY_OFFSET | 7 | 57 | 2 | 54 | 1 | 0 | 0 | 3 | 124 |
| VELOCITY_OFFSET+ACTUATOR_DELAY | 7 | 71 | 0 | 56 | 13 | 2 | 2 | 5 | 121 |
| VELOCITY_OFFSET+SPEED_STEP | 7 | 62 | 11 | 51 | 0 | 0 | 0 | 24 | 132 |
| VELOCITY_OFFSET+SPEED_STEP+ACTUATOR_DELAY | 7 | 71 | 4 | 58 | 8 | 1 | 1 | 25 | 139 |
| FAULT:BELT_STOP | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 48 |
| FAULT:OBJECT_MISSING | 6 | 0 | 0 | 0 | 0 | 0 | 37 | 1 | 35 |
| FAULT:SECOND_DYNAMICS_CHANGE | 6 | 0 | 0 | 0 | 1 | 0 | 0 | 10 | 96 |
| FAULT:SENSOR_SPIKE_BURST | 7 | 22 | 8 | 14 | 0 | 0 | 0 | 9 | 93 |
| FAULT:SENSOR_STUCK | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 91 |

FACT：7 个含 ACTUATOR_DELAY 的 case 的 success 合计 12（0+0+0+8+0+0+4）。全部 7 个 unsafe 都在含 ACTUATOR_DELAY 的 case 里。B1 的 43 个 unsafe 中有 37 个在 FAULT:OBJECT_MISSING。

### 1.5 计数口径（读漏斗前需知道的）

- **`authorization_count` ≠ 实际签发的授权数**（FACT）。`src/rra/eval/b3_dev.py:115-118` 统计的是 `action == UPDATE_MODEL_AND_REPLAN` 的决策数，再加上 episode 级授权数。前 20 个 seed：`episodes[].authorizations` 之和 = 31 = 28 个 UPDATE 决策 + 3 个 episode 级授权。28 个 UPDATE 中只有 24 个带 `authorization` 记录，4 个没有（R1）。全 dev 的 209 里有多少个是“UPDATE 但未授权”，无法从已提交数据得到。
- **`pause_refusal` = 至少出现过一次 PAUSE/HUMAN_ESCALATION 决策的对象数**（`b3_dev.py:153-154`）。这些对象之后仍可能被命令或 picked。例如 seed 0：`episodes[0].pause_target_ids` 有 11 个，`b3_terminal_counts.picked` = 12（B4）。
- **diag 子集几乎不含 fault family**。`scripts/d1*_diag.py` 选的是 `i % 19 ∈ {1,2,3}` 的 seed，再加上手工补充的 seed。33 个 seed 里只有 seed 52（SENSOR_STUCK）是 fault episode（R6 输出）。所以子集看不到 fault 相关的计数变化（见 §3.2 中 dbebe35 那一行）。

## 2. unsafe_action 来源拆分

### 2.1 当前 `b3-dev.json` 的 7 个（全部 `fast_layer_command`）

出处：R3（`b3-dev.json → episodes[].score.unsafe_target_ids`、`.unsafe_by_source`、`.b1_unsafe_action_count`、`.b1_terminal_counts`、`.b3_terminal_counts`）。逐对象轨迹取自 R8（`diag-d1g.json → episodes[].failure_trace[]`、`.system2_diagnostic_trace[]`），与 `diag-d1-before.json → episodes[].failure_trace[]` 比对。

| seed/target | case | S2 调用（t, n_usable, gate） | cmd−true_eta (s) | exec−cmd (s) | 空间误差 | time_error | max | 与 d1-before 轨迹相同 | B1 同 episode unsafe |
|---|---|---|---:|---:|---:|---:|---:|---|---:|
| 46/0 | VO+AD | (0.2, 3, NO_VERIFIED) | 0.197 | 0.170 | 0.435 | 0.193 | 0.435 | 是（d1-before 中 S2 调用 0 次） | 1 |
| 51/1 | VO+SS+AD | (0.3, 4, NO_VERIFIED) | 0.100 | 0.389 | 0.491 | 0.491 | 0.491 | 是（0 次） | 1 |
| 88/1 | SB+SS+AD | (0.2, 3, NO_VERIFIED) | 0.091 | 0.266 | 0.449 | 0.310 | 0.449 | 是（0 次） | **0** |
| 103/1 | VO+AD | (0.2, 3, NO_VERIFIED) | 0.164 | 0.214 | 0.423 | 0.218 | 0.423 | 是（0 次） | 1 |
| 106/0 | SB+VO+AD | (0.3, 4, NO_VERIFIED) | 0.031 | 0.400 | 0.409 | 0.476 | 0.476 | 是（0 次） | 3（整个 episode） |
| 106/1 | 同上 | (0.2, 3, NO_VERIFIED) | −0.013 | 0.400 | 0.365 | 0.444 | 0.444 | 是（0 次） | 同上 |
| 106/2 | 同上 | (0.2, 3, NO_VERIFIED) | 0.041 | 0.400 | 0.412 | 0.543 | 0.543 | 是（0 次） | 同上 |

列定义：`cmd−true_eta` = `failure_trace.command_time − failure_trace.true_eta`；`exec−cmd` = `failure_trace.execution_time − failure_trace.command_time`；“空间误差”/“time_error” = `failure_trace.position_error` / `.time_error`；`max` = 两者较大值，对应 evaluator 判据（`control.py:57-60`）。evaluator 行本身没有提交，所以 max 列是 INFERENCE，见 §4 C1。

拆成两组：
- **6 个（46/0、51/1、103/1、106/0-2）**：B3 与 B1 在这些 episode 的终态计数完全相同（R3：`b1_terminal_counts == b3_terminal_counts`），每个 episode 的 B1 unsafe 数与 B3 相同。轨迹字段（命令时刻、执行时刻、误差）与 d1-before 中 S2 从未触及这些目标时完全相同（R8）。S2 只在 t≈0.2–0.3、n=3–4 时调用过一次，结论 PAUSE，之后再没有调用。
- **1 个（88/1）**：B1 在 seed 88 上 12 个对象全部 escalated，没有发出命令（`episodes[seed=88].b1_terminal_counts`）。B3 的终态是 attempt_failed 3、escalated 7、skipped 2。`diag-d1g.json` 的 seed 88 显示：target 0 在 t=5.0 由 S2 授权（COMMON_ACTION，执行时刻 6.0），结局 attempt_failed，空间误差 0.338、time_error 0.266，不在 unsafe 中；随后 target 1 和 target 2 由快速层命令，target 1 的误差 0.449 被计为 unsafe。`authorization_source` 记为 `fast_layer_command`，因为执行时 target 1 不在 `system2_authorized` 中（`episode.py:866-869`）。

### 2.2 `unsafe-traces-d1d.json` 的 8 个（全部 `s2_authorized`，提交于 1cc7d07）

条数与 `1cc7d07:b3-dev.json → metrics.unsafe_action` = 8、`unsafe_action_by_source.s2_authorized` = 8 一致。出处：R7（`unsafe-traces-d1d.json → unsafe_objects[].authorization_decisions[]`、`.evaluator`、`.failure_trace`）。

| 组 | seed/target | 授权时刻 | n_usable | 被选结构（hypothesis） | 拟合参数 | evaluator position_error | 当前 b3-dev 中 |
|---|---|---:|---:|---|---|---:|---|
| A | 24/1 | 0.5 | 6 | SENSOR_BIAS (h00) | bias −0.189 | 0.431 | 不在 unsafe |
| A | 26/2 | 0.5 | 6 | SENSOR_BIAS (h00) | bias −0.001 | 0.753 | 不在 |
| A | 30/2 | 0.5 | 6 | SENSOR_BIAS (h00) | bias 0.254 | 0.799 | 不在 |
| A | 116/1 | 0.5 | 6 | SENSOR_BIAS (h00) | bias −0.005 | 0.446 | 不在 |
| A | 119/1 | 0.5 | 6 | SENSOR_BIAS (h00) | bias 0.354 | 1.127 | 不在 |
| B | 48/0 | 5.1 | 52 | SB+SS (h05) | bias 0.450，τ 2.35，Δ 0.295 | 0.401 | 不在 |
| B | 48/1 | 5.2 | 53 | SB+SS (h05) | bias 0.449，τ 2.25，Δ 0.280 | 0.460 | 不在 |
| B | 88/0 | 5.0 | 51 | SB+SS (h05) | bias 0.343，τ 1.30，Δ 0.253 | 0.713 | 不在（target 0 现为 miss，见 §2.1） |

- A 组（FACT）：只有一次 S2 调用，发生在 t=0.5，样本数恰好 6（下限）。passing 集有 4–7 个结构，被选中的是枚举顺序里的第一个结构 h00 = SENSOR_BIAS（`episode.py:690` 用 `next(...)` 取第一个满足容差的假设）。命令时刻 = `common_action_time`，执行误差 0.43–1.13。
- B 组（FACT）：授权较晚，样本 51–53 个，被选结构是 SB+SS。`diag-d1d.json → unsafe_diagnostics[]` 记录了 48/0 和 88/0 的 `step_after_decision = false`（真实阶跃 2.529/1.320 早于决策时刻 5.1/5.0）。88/0 另有 `execution_time − command_time` = 0.266（R7），这个 episode 的真实结构含 ACTUATOR_DELAY。
- 在之后各阶段的去向见 §3。

### 2.3 B1 → B3 的 unsafe 差（全 dev）

`metrics.b1_corrected_unsafe_action` 43 → `metrics.unsafe_action` 7。按 R2 分组：B1 的 43 = FAULT:OBJECT_MISSING 37 + 含 ACTUATOR_DELAY 的组合 6（SB+VO+AD 3、VO+AD 2、VO+SS+AD 1）。B3 的 7 = 这 6 个（§2.1 第一组）+ 88/1（SB+SS+AD，B1 为 0）。“B3 的 6 个与 B1 的 6 个是同一批 target”只在 episode 计数层面一致；`b3-dev.json` 没有存 B1 的逐目标 unsafe id（见 §4 C1 缺失证据）。

## 3. 阶段间变化（只陈述）

### 3.1 diag 子集（27→33 个 dev seed）

阶段与提交对应（FACT，`git log -- artifacts/s2/<file>`）：d1-before/after 由 d11ce8b 提交（d1-before 最早在 7f50fca）；d1d 和 unsafe-traces-d1d 由 1cc7d07 提交；d1e 由 48116ad；d1f 由 cdd6e59；d1g 由 dbebe35。

| 量 | d1-before | d1-after | d1d | d1e | d1f | d1g | 出处 |
|---|---:|---:|---:|---:|---:|---:|---|
| seeds | 27 | 27 | 27 | 27 | 33 | 33 | `seeds` |
| 有 S2 调用的对象 / 对象 | 67/324 | 67/324 | 324/324 | 324/324 | 396/396 | 396/396 | R4 |
| S2 调用 | 326 | 344 | 826 | 422 | 498 | 498 | R4 |
| n<6 调用 | 0 | 0 | 309 | 294 | 352 | 352 | R4 |
| AMBIGUOUS 调用 | 307 | 327 | 471 | 107 | 116 | 116 | R4 |
| COMMON_ACTION 调用 | 19 | 17 | 46 | 21 | 30 | 30 | R4 |
| UPDATE 且有授权 / 无授权 | 19/0 | 17/0 | 46/0 | 21/0 | 19/11 | 19/11 | R4 |
| wrong_disposition | 159 | 159 | 319 | 150 | 157 | 157 | `episodes[].score.wrong_disposition_count` |
| unsafe | 9 | 9 | 4 | 10 | 7 | 7 | `episodes[].score.unsafe_action_count` |
| ordinary miss | 19 | 19 | 1 | 20 | 27 | 27 | `episodes[].score.ordinary_miss_count` |
| recoverable challenge / success | 187/0 | 187/0 | 187/0 | 187/10 | 213/22 | 213/22 | `episodes[].score.*` |
| preservation regression | 0 | 0 | 137 | 3 | 0 | 0 | `episodes[].score.preservation_regression_count` |
| `diagnostic_funnel`：从未升级到 S2 | 95 | 95 | 0 | 0 | 0 | 0 | `diagnostic_funnel` |
| 〃 n_usable<6 | 0 | 0 | 280 | 135 | 141 | 87 | 〃 |
| 〃 AMBIGUOUS | 48 | 50 | 31 | 13 | 14 | 64 | 〃 |
| 〃 已授权但 miss/未执行 | 12 | 10 | 6 | 2 | 2 | 4 | 〃 |
| 〃 门控时刻已在拾取窗口外 | 4 | 4 | 2 | 0 | 0 | 2 | 〃 |

unsafe 对象集合（R4，`episodes[].unsafe_target_ids`）：
- d1-before = d1-after：46/0，48/0，51/1，88/0，88/1，103/1，106/0-2
- d1d：48/0，48/1，88/0，116/1
- d1e：40/6，46/0，51/1，88/1，97/7，103/1，106/0-2，116/1
- d1f = d1g：46/0，51/1，88/1，103/1，106/0-2（与当前 `b3-dev.json` 的 7 个相同）

逐步陈述：
1. **d1-before → d1-after**：seed 集、score 各项和 unsafe 集合都相同。COMMON_ACTION 调用 19→17，AMBIGUOUS 307→327，`diagnostic_funnel` 中“已授权但…”12→10、AMBIGUOUS 48→50。7f50fca..d11ce8b 之间唯一改动决策逻辑的提交（按提交标题和 diff）是 5033f4f：把 ACTUATOR_DELAY 从命令时刻里移出，改为对每个假设各自加到执行时刻上（`git show 5033f4f -- src`）。INFERENCE：before 对应 5033f4f 之前、after 对应之后。文件本身没有 git_sha 字段，所以这一对应无法直接核对（§6）。
2. **d1-after → d1d**（1cc7d07，前序 9a2abf7 / 1339fa3 / a832bd3 / 408c852）：有 S2 调用的对象 67→324，“从未升级到 S2”95→0，出现了 309 次 n<6 调用。9a2abf7 让 correction-infeasible 事件也进入 S2（`git show 9a2abf7`）。preservation regression 0→137，wrong 159→319，miss 19→1，unsafe 9→4。原来的快速层 unsafe 对象（46/0、51/1、103/1、106/0-2、88/1）在 d1d 中都不在 unsafe 集里，新增的 48/1、116/1 是 S2 授权产生的。
3. **d1d → d1e**（48116ad，前序 668fe22、76c861f）：preservation regression 137→3，wrong 319→150，miss 1→20，unsafe 4→10。668fe22 从预测的物理位置中去掉了 `− sensor_bias`。76c861f 把 S2 的 pause 改为不构成 veto（提交标题）。B 组 48/0、48/1、88/0 离开 unsafe 集；快速层的 46/0、51/1、88/1、103/1、106/0-2 回到 unsafe 集；新增 40/6、97/7（与 116/1 同样在 t=0.5 由 S2 授权，R6）。
4. **d1e → d1f**（cdd6e59）：seed 集 27→33（新增 24、26、30、52、67、119；`scripts/d1f_diag.py:23` 还列了 97 和 116，但它们已在集中）。在共同的 27 个 seed 上：unsafe 10→7，wrong 150→147，success 10→13，preservation regression 3→0（R6）。cdd6e59 要求授权必须带非空的 `temporary_policy_exception`（`git show cdd6e59 -- src/rra/s2/authorization.py`）。d1f 中出现 11 个“UPDATE 但没有授权”的决策，全部在 t=0.5，包含 d1e 中曾授权并成为 unsafe 的 40/6、97/7、116/1（R6）。
5. **d1f → d1g**（dbebe35）：底层数据（`system2_diagnostic_trace`、`system2_decisions`、`failure_trace`、`score`）逐字段相同（R6）。`diagnostic_funnel` 的变化（n<6 141→87、AMBIGUOUS 14→64 等）**只来自归类规则从“首次调用”改为“末次调用”**（`diff scripts/d1f_diag.py scripts/d1g_diag.py`）。dbebe35 的代码改动（hard-fault latch）在这 33 个 seed 上没有改变任何收据字段。它在全 dev 上的影响见 §3.2。
6. 记录问题（FACT）：`diag-d1f.json → phase` 的值是 `"diag-d1e"`（`scripts/d1f_diag.py` 沿用了 d1e 的字符串），但文件内容确实是 d1f（33 个 seed）。

### 3.2 全 dev（`b3-dev.json` 各提交版本，`<sha>:b3-dev.json → metrics.*`、`operational_cost.system2_calls`）

| 提交 | success | wrong | miss | unsafe（fast/s2） | correct_refuse_rate | pres. regr. | authorization_count | S2 calls |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| 7ea70ce | 62 | 602 | 103 | 9（无分来源） | 1.0 | 0 | 132 | 字段缺 |
| d11ce8b | 60 | 603 | 104 | 9（无分来源） | 1.0 | 0 | 126 | 5998 |
| 1cc7d07 | 29 | 1299 | 16 | 8（0/8） | 1.0 | 577 | 353 | 10465 |
| 48116ad | 72 | 607 | 91 | 16（7/9） | 0.99194 | 8 | 215 | 2051 |
| cdd6e59 | 84 | 603 | 96 | 21（17/4） | 0.88710 | 0 | 220 | 2045 |
| dbebe35 | 84 | 589 | 96 | 7（7/0） | 1.0 | 0 | 209 | 1961 |
| ab509d3（当前） | 84 | 589 | 96 | 7（7/0） | 1.0 | 0 | 209 | 1961 |

陈述：
- cdd6e59 → dbebe35：unsafe 21→7（fast 17→7，s2 4→0），correct_refuse_rate 0.88710→1.0，wrong 603→589。按 `refuse_total` = 124 换算，0.88710×124 = 110，即 cdd6e59 版本中有 14 个 REFUSE 对象被发出命令，dbebe35 版本中为 0。这个差额 14 与 unsafe 减少的 14 相等。REFUSE 对象只出现在 fault family episode，而 diag 子集几乎不含这类 episode，这与 §3.1 第 5 条（子集上无变化）相符。
- 48116ad → cdd6e59：s2 来源 unsafe 9→4，fast 来源 7→17，correct_refuse_rate 0.99194→0.88710（被命令的 REFUSE 对象 1→14）。
- ab509d3 与 dbebe35 的 metrics 相同；receipt sha 不同（2bcf3aa… → 6eb3c6f…），ab509d3 新增了 `runtime_versions`。

## 4. 候选成因（按证据强度排序）

### C1 当前 7 个 unsafe 中的 6 个：沿袭 B1 的快速层命令；执行延迟和命令偏晚共同造成超过 2×tolerance 的误差；S2 只做过一次 n<6 的早期调用

- FACT
  - 6 个对象（46/0、51/1、103/1、106/0-2）的 case 都含 ACTUATOR_DELAY，`authorization_source = fast_layer_command`（`metrics.unsafe_action_by_source`）。
  - 所在 episode 的 B1/B3 终态计数相同，B1 unsafe 数相同（R3）。
  - 轨迹字段与 S2 从未调用时（d1-before）逐值相同（R8）。
  - 每个对象只有一次 S2 调用：t=0.2–0.3，n=3–4，NO_VERIFIED_HYPOTHESIS → PAUSE（R8）。
  - S2 再次进入的条件只有两个：新的 escalation 上升沿，或尚未尝试过的 infeasible 事件。`system2_next_retry` 只限制最早时刻，不会主动安排复查（`episode.py:616-621, 744-746`）。PAUSE 不构成 veto（76c861f）。
  - `exec−cmd` 为 0.170–0.400 s，`cmd−true_eta` 为 −0.013–0.197 s（R8）。
- INFERENCE
  - (a) 这 6 个对象的 unsafe 由快速层产生，B3 没有改变它们的命令。
  - (b) 误差由两部分组成，比重因对象而异：未建模的执行延迟（51/1、106/*、88/1 主要是这一项），以及命令时刻相对真实到达时刻偏晚（46/0、103/1 两项相当）。两种成分都与数据相容，这里并列给出，不强行取舍。
  - (c) 106/1 的空间误差 0.365 < 0.4，它被计为 unsafe 应当来自 time_error 0.444（evaluator 取 max）。
- 确认还缺的证据
  - B1 逐目标的 `unsafe_target_ids` 和 evaluator 行（`b3-dev.json` 只存了计数）。
  - B3 这 7 个对象的 evaluator 行（`position_error`、`target_exists_at_execution`、`stale_authorization`），用于确认 unsafe 判据走的是 `e > 2×tol` 这一支，以及 106/1 的 max 来自 time_error。
  - 快速层 correction 的逐步记录（`correction.reason`、`clamped`、`infeasible`），用于说明 PAUSE 之后为什么没有新的 escalation 上升沿。
- 离线检验设计（dev seeds 46、51、103、106；只写设计，未执行）：在临时目录对每个 seed 调用 `run_episode(..., terminal_monitoring="corrected", realization=realize_episode(seed, structure))` 两次（`system2_enabled=False/True`，`include_trace=True, include_s2_diagnostics=True`），把两次的 `evaluator_objects` 和 `failure_trace` 写到临时 JSON 后逐目标比对。预期可证伪的点：如果 B1 和 B3 的 unsafe 目标 id 不同，或 evaluator 的 `position_error` 不等于 `max(空间, time_error)`，则 (a) 或 (c) 不成立。误差分解可以用同一份 trace 在两种对照下计算：令 `actuator_delay=0`（只在 realization 副本上改，不改仓库），或把命令时刻替换为 `true_eta`。

### C2 88/1：S2 对同 episode 另一目标的授权解除了 B1 里的 episode 级 escalation，使快速层得以命令后续目标

- FACT
  - B1 在 seed 88 上全部 12 个对象 escalated，没有命令（`episodes[seed=88].b1_terminal_counts`）。
  - B3 在 t=5.0 授权了 88/0（`diag-d1g.json` seed 88 `system2_decisions`），之后 88/1 和 88/2 由快速层命令。
  - escalation 记录及 `safe_stop` 只在目标不在 `system2_authorized` 时才会写入（`episode.py:747-754`）。命令发出需要 `not safe_stop`（`episode.py:832`）。
- INFERENCE：B1 中 88/0 的 escalation 把 `safe_stop` 置位，挡住了后续目标。B3 中 88/0 被 S2 授权，没有走 escalation，`safe_stop` 没有置位，于是 88/1 由快速层命令并超过 2×tol。按现行归因规则（`authorization_source` 只看执行目标本身），这个对象计入 fast_layer_command。
- 并列的另一解释：88/1 在 B1 中可能并非因为 `safe_stop` 被挡，而是自身 escalation（逐目标的 B1 原因没有提交）。两种解释都与已提交数据相容。
- 确认还缺的证据：B1 seed 88 的逐目标 `outcomes[].reason`（例如 `safe_stop_before_command` 或 `ESCALATE:`），以及 B3 seed 88 中 `safe_stop` 随时间的取值。
- 离线检验设计（dev seed 88）：两次 `run_episode`（S2 关/开，include_trace），比较 target 0 的 escalation 时刻、target 1 的 `outcomes[].reason` 和 receipt 中的 `safe_stop`。反事实检验：在 S2 开启时，只对 target 0 屏蔽授权（例如用 monkeypatch 让 `authorize` 对 `scope == "target:0"` 抛错，只在测试进程内生效，不改仓库），观察 88/1 是否重新变为 escalated。

### C3 wrong_disposition 的主要流失点之一：S2 调用发生在样本不足 6 个时，且之后多数对象没有再次调用

- FACT（d1g 子集）
  - 352/498 次调用 n<6（R4）。
  - 323/396 个对象只被调用一次，272 个对象的所有调用都 n<6，而这些对象末次调用时 `window_remaining_time` 的中位数为 5.831 s（R5）。
  - 按末次调用归类，wrong 的 87/157 属于 n<6（`diagnostic_funnel`）。
  - 全 dev 前 20 个 seed：210/285 次调用为 NO_VERIFIED_HYPOTHESIS（R1）。
  - 再次进入条件见 C1。
- INFERENCE：触发发生得早（infeasible 事件在 t≈0.2 就出现），而 PAUSE 之后没有定时重观测，所以对象在还有数秒窗口时就停留在“样本不足”的状态。decisions.md:33 描述的“按目标重观测时步进复查”与上述代码路径（`episode.py:619-621` 只在新的触发上进入）之间的关系，需要所有者确认（§5）。
- 并列解释：也可能是快速层在 PAUSE 之后自行命令或跳过了目标，使得没有机会再调用 S2，也就是终态先于复查到来。d1g 中 153 个 RECOVER/未授权/wrong 对象的 `failure_trace.skip_reason` 分布可以区分这两种情况，但本文没有逐对象核对，属于未完成的细分，不是缺数据。
- 确认还缺的证据：逐对象“PAUSE 时刻 → 终态时刻 → 期间是否出现过 escalation 上升沿”的时间线（需要 correction 的逐步 reason，目前没有提交）。
- 离线检验设计（dev，diag 子集的 33 个 seed）：在临时进程里给 `run_episode` 加一个只在测试里生效的包装，在 `system2_next_retry` 到期时强制再进入 `run_b3`，并记录第二次调用的 `n_usable_total` 和 gate。度量 n<6 → ≥6 的迁移数，以及迁移后的 gate 分布。这只是对机制的检验，不是提议修改实现。

### C4 wrong_disposition 的另一主要流失点：样本充足后 AMBIGUOUS（多个嵌套结构的 verifier 结果都是 passed=True，common-action 找不到共同时刻）

- FACT
  - n≥6 的 146 次调用全部 \|V\|≥1，其中 116 次为 AMBIGUOUS（R4）。
  - AMBIGUOUS 时 \|V\| 为 3–14，33 次是全部 14 个结构都 passed=True（R5）。
  - 真实结构在 V 中 111/114（R5）。
  - 按末次调用归类，AMBIGUOUS 占 wrong 的 64/157。其中 50 个对象首次调用时是 n<6，样本增加后转为 AMBIGUOUS（R6）。
  - common-action 要求所有 passing 假设在同一时刻的预测误差都 ≤0.20（`verifier.py:37-43`）。
  - d1-before/after 的 `ambiguous_cases[].all_passing_models_are_supersets` 中，True 的分别只有 30/307 和 30/327（B3：`diag-d1-before.json`/`diag-d1-after.json → ambiguous_cases[]`）。
- INFERENCE：短时段观测下，含 SPEED_STEP 或 VELOCITY_OFFSET 的超集模型和不含它们的模型残差都在 0.030 以内，但外推到拾取时刻时分歧超过 0.20，于是 gate 停在 AMBIGUOUS。
- 并列解释：(i) 识别性不足（数据太短，任何阈值都无法区分）；(ii) RMSE 阈值 0.030 相对噪声偏宽，使非超集模型的 verifier 结果也为 passed=True。已提交数据无法区分这两者。
- 补充 FACT：`ambiguous_cases[].predicted_position_spread_world_units` 由 `scripts/analyze_d1.py:10-23` 计算，其公式含 `− sensor_bias`，与 668fe22 之后的 `prediction.py` 不一致。因此这一列的数值不能代表当前预测口径。
- 确认还缺的证据：AMBIGUOUS 调用时各 passing 假设在候选时刻网格上的逐一误差 `error(h,t)`（当前没有记录），以及噪声水平（dev realization 的噪声参数）。
- 离线检验设计（dev，d1g 子集）：对已提交的 AMBIGUOUS 调用记录（`system2_diagnostic_trace[].fits[].parameters` + `decision_observation`），离线重算 `pick_error_at_command_time` 的逐假设误差曲线，统计 `min_t max_h error` 的分布及其离 0.20 的距离。另用同一批 dev seed 在临时进程里把 RMSE 阈值换成几档，只观测 \|V\| 的变化，不改仓库。

### C5（历史，已不在当前 unsafe 中）早期授权：t=0.5、n=6，选中枚举顺序第一个结构

- FACT
  - D1d 版本有 5 个 s2_authorized unsafe（24/1、26/2、30/2、116/1、119/1），都在 t=0.5、n=6 时授权，被选结构都是 h00 = SENSOR_BIAS（R7）。
  - d1e 中另有 40/6、97/7 同型（R6）。
  - cdd6e59 引入非空 exception 要求之后，t=0.5 的 UPDATE 决策全部没有授权（d1f/d1g 中 11 个；全 dev 前 20 个 seed 中有 4 个：3 个在 t=0.5，1 个在 t=1.9，B2），这几个对象从 unsafe 集中消失。
  - 当前 `chosen` 仍是 `next(...)`，即枚举顺序里第一个满足容差的假设（`episode.py:690`）。
- INFERENCE：这些对象离开 unsafe 集，是因为“这次授权不需要 policy exception”这一条件挡住了它们，而不是预测本身被纠正。也就是说，只要出现需要 exception 的早期 UPDATE，同样的“只凭 6 个样本、选第一个结构”路径仍然可达。
- 并列解释：也可能 A 组的误差主要来自 t=0.5 之后才发生的 SPEED_STEP 或速度偏移（`step_after_decision` 只对 48/0、88/0 计算过，A 组没有算）。
- 确认还缺的证据：A 组 5 个对象的真实 `speed_step_time` 等 realization 值（dev 数据，可离线取得）与授权时刻的比较；以及当前代码下“需要 exception 的早期 UPDATE”在全 dev 上的出现次数（目前只存了前 20 个 seed 的决策）。
- 离线检验设计（dev seeds 24、26、30、116、119、40、97）：读取 `realize_episode(seed, structure).recoverable`，比较阶跃时刻与 0.5。用当前代码 `include_s2_diagnostics=True` 跑全 130 个 dev seed，输出写到临时目录（不用 s2-b3-dev 的默认目录），统计 `action == UPDATE` 且 `n_usable_total ≤ 8` 的决策数，以及其中有授权的数目。

### C6（历史）预测中重复扣除 sensor_bias

- FACT
  - B 组 48/0、48/1、88/0 在 D1d 被 S2 授权，误差分别为 0.401、0.460、0.713，所选模型的 bias 拟合值分别为 0.450、0.449、0.343（R7）。
  - 668fe22 删除了 `prediction.py` 中的 `− sensor_bias`。d1e 中这三个对象不在 unsafe 集里。
  - 88/0 另有 0.266 s 的执行延迟（R7）。
- INFERENCE：对 48/0 和 48/1，误差的量级与 bias 相当，与“bias 被当成物理位移扣除”相符。对 88/0，误差大于 bias，余量与执行延迟同号同量级。
- 并列解释：88/0 的误差也可能主要来自所选 SB+SS 模型没有包含 ACTUATOR_DELAY。
- 确认还缺的证据：在 1cc7d07 和 668fe22 两个版本下，对这三个对象逐项分解预测误差（bias 项、延迟项、τ 误差项）。
- 离线检验设计（dev seeds 48、88）：用 `git worktree` 在临时目录检出 1cc7d07 与 668fe22（不改当前分支），分别以 `include_s2_diagnostics=True` 跑这两个 seed，比较授权时刻的 `action_time`、`chosen` 和执行误差。

### C7（口径，非成因但影响漏斗读数）

FACT：`authorization_count` 包含未授权的 UPDATE（§1.5）；`pause_refusal` 是“出现过一次 pause 的对象数”；diag 的“已授权但 miss/未执行”是兜底类；diag 子集几乎不含 fault episode；`diag-d1f.json → phase` 标错；d1-before/after 没有 git sha。确认这些不需要新证据，只需要所有者决定口径（§5）。

## 5. 需所有者裁决（只列出，不提出对预注册文件或补遗的修改）

1. **88/1 的来源归属**：执行目标本身没有 S2 授权，但它之所以被命令，可能源于同 episode 另一目标的 S2 授权（C2）。现行 `authorization_source` 规则把它计为 `fast_layer_command`。是否需要另一种归属口径，由所有者决定。
2. **`authorization_count` 的口径**：现在统计的是 UPDATE 决策数加 episode 级授权数，包含 exception 为空、未实际签发的 UPDATE。
3. **PAUSE 之后是否应该按时复查**：decisions.md:33 的描述与 `episode.py:619-621` 的进入条件之间的关系（C3）。
4. **diag 子集的代表性**：子集几乎不含 fault family。dbebe35 在全 dev 上让 unsafe 21→7，但子集上没有变化。
5. **记录问题**：`diag-d1f.json → phase` 写成 `diag-d1e`；d1-before/after 没有生成时的 git sha；decisions.md:32 引用的 `REPORT_D1.md` 不在仓库中（任务书已核对；本文再次确认工作树中 `find -iname 'REPORT_D1*'` 无结果，已抓取的 main 前 300 个提交的历史中也没有这个路径）。
6. **启动器版本**：`rra` 启动器要求 Python 3.11（`rra:7-8`），而已提交的 `b3-dev.json → runtime_versions.python` 为 3.12.3。§6 的复跑因此改用 `python -m rra.cli`。
7. **跨机器的 receipt 哈希**：见 §6。聚合 metrics 一致，但逐 seed 的 B3 receipt sha 有 115/130 个不同。是否把它作为确定性要求的一部分，由所有者决定。

## 6. 复跑对照（第 5 项，可选）

- 环境：Python 3.12.3 venv（会话 scratchpad），numpy 2.5.4，pydantic 2.14.1（`pip install -r requirements.txt`）。
- 命令：`PYTHONPATH=src <venv>/bin/python -m rra.cli s2-b3-dev --output-dir <scratchpad>/b3rerun`。没有用 `./rra`，因为它会拒绝 3.12（见 §5 第 6 条）。输出目录在仓库之外，运行后 `git status --porcelain` 为空。
- 耗时：墙钟 54.8 s，nproc=4（文件中记录 `parallel_full_dev_wall_seconds` = 51.200）。

对比结果（复跑文件对比已提交的 `b3-dev.json`）：

| 项 | 结果 |
|---|---|
| `metrics`（全部字段） | 完全相同 |
| 逐 seed `b1_receipt_sha256` | 130/130 相同 |
| 逐 seed `b3_receipt_sha256` | 115/130 不同 |
| `receipt_sha256` | 6eb3c6fb… → 48d6dafd… |
| 前 20 个 seed 的决策 action / gate_reason / common_action_time | 0 处不同 |
| 前 20 个 seed 中拟合参数、rmse、residual 的最后一位浮点差 | 5441 处 residual 分量、176 处 rmse 等（量级 1e-17） |
| 拟合的 `speed_step_time` 在 0.05 s 网格上取到相邻格 | 8 处：seed 0/t7、10/t6（3 个结构）、13/t9（2 个）、18/t2（2 个）。全部在 AMBIGUOUS 调用中，n=7–10，两侧的 `passed` 都为 True |
| `operational_cost` | 只有计时类字段不同（`production_pause_seconds` 367.107 → 152.812，wall 时间，nproc 8→4） |
| 文件 sha256 | 已提交 74ccf39a… / 复跑 193f1117… |

INFERENCE：B3 receipt 的差异来自最小二乘在不同机器上最后一位浮点的差别，以及由此引起的网格 argmin 平局翻转。在这次复跑中，这些差别没有传到任何决策或 metrics。对 index ≥ 20 的 seed，`b3-dev.json` 没有保留决策记录，所以无法逐决策核对。不过这 110 个 seed 的 metrics 与 `b1_receipt_sha256` 都相同。

## 附录 A：派生脚本（R1–R8）

在仓库根目录运行：`python3 -I <path>/t3_derive.py`。脚本只读 `artifacts/s2/*.json`，不写文件。

```python
"""T3 derivations over committed artifacts only (read-only; dev data only)."""
import json
from collections import Counter

A = "artifacts/s2/"
L = lambda name: json.load(open(A + name))


def r1_b3dev_first20():
    """R1: b3-dev.json episodes[0..19].system2_decisions by (trigger, action, gate_reason, has authorization)."""
    d = L("b3-dev.json")
    eps = [e for e in d["episodes"] if "system2_decisions" in e]
    c = Counter((r.get("trigger", "fast_escalation"), r["action"], r.get("gate_reason"),
                 r.get("authorization") is not None) for e in eps for r in e["system2_decisions"])
    print("R1 seeds", [e["seed"] for e in eps], "records", sum(c.values()),
          "system2_calls", sum(e["system2_calls"] for e in eps),
          "authorizations field", sum(e["authorizations"] for e in eps))
    for k, v in c.most_common():
        print("  ", v, k)
    nv = Counter("all-n<6" if all("n_usable < 6" in v.get("violated_invariants", []) for v in r["verifications"])
                 else "no-n_usable-field" for e in eps for r in e["system2_decisions"]
                 if r.get("gate_reason") == "NO_VERIFIED_HYPOTHESIS")
    objs = sum(len(e["score"]["dispositions"]) for e in eps)
    with_dec = len({(e["seed"], r["target_id"]) for e in eps for r in e["system2_decisions"]})
    print("   NO_VERIFIED split", dict(nv), "objects", objs, "objects with >=1 record", with_dec)


def r2_b3dev_by_case():
    """R2: b3-dev.json episodes[] grouped by case/fault_family; score.* summed."""
    d = L("b3-dev.json")
    rows = {}
    for e in d["episodes"]:
        key = "+".join(e["case"]) or "FAULT:" + str(e["fault_family"])
        c = rows.setdefault(key, Counter())
        c["eps"] += 1
        for k in ("recoverable_challenge_count", "challenge_success_count", "wrong_disposition_count",
                  "ordinary_miss_count", "unsafe_action_count"):
            c[k] += e["score"][k]
        c["b1_unsafe"] += e["b1_unsafe_action_count"]
        c["authorizations"] += e["authorizations"]
        c["system2_calls"] += e["system2_calls"]
    for k, c in sorted(rows.items()):
        print("R2", k, dict(c))


def r3_b3dev_unsafe():
    """R3: b3-dev.json episodes[] with score.unsafe_action_count > 0."""
    for e in L("b3-dev.json")["episodes"]:
        if e["score"]["unsafe_action_count"]:
            ids = e["score"]["unsafe_target_ids"]
            print("R3", e["seed"], e["case"], ids, [e["score"]["dispositions"][str(i)] for i in ids],
                  e["unsafe_by_source"], "b1_unsafe", e["b1_unsafe_action_count"],
                  "b1_terminal", e["b1_terminal_counts"], "b3_terminal", e["b3_terminal_counts"])


def r4_diag_stages(name):
    """R4: diag-*.json call-level stages over episodes[].system2_diagnostic_trace[]."""
    d = L(name)
    calls = [c for e in d["episodes"] for c in e["system2_diagnostic_trace"]]
    small = sum(c["n_usable_total"] < 6 for c in calls)
    big = [c for c in calls if c["n_usable_total"] >= 6]
    empty = sum(not c["passing"] for c in big)
    gates = Counter(c["gate"] for c in big if c["passing"])
    objs = sum(len(e["score"]["dispositions"]) for e in d["episodes"])
    called = len({(e["seed"], c["target_id"]) for e in d["episodes"] for c in e["system2_diagnostic_trace"]})
    dec = Counter((r["action"], r.get("gate_reason"), r.get("authorization") is not None)
                  for e in d["episodes"] for r in e["system2_decisions"])
    unsafe = [(e["seed"], e["unsafe_target_ids"]) for e in d["episodes"] if e["unsafe_target_ids"]]
    print(f"R4 {name} phase={d['phase']} seeds={len(d['seeds'])} objects={objs} called={called} "
          f"calls={len(calls)} n<6={small} n>=6={len(big)} |V|=0&n>=6={empty} gates={dict(gates)}")
    print("   decisions", dict(dec))
    print("   unsafe", unsafe, "score sums",
          {k: sum(e["score"][k] for e in d["episodes"]) for k in
           ("wrong_disposition_count", "unsafe_action_count", "ordinary_miss_count",
            "recoverable_challenge_count", "challenge_success_count", "preservation_regression_count")})


def r5_d1g_objects():
    """R5: diag-d1g.json per-object call counts, first-call n_usable, AMBIGUOUS |V| and true-structure membership."""
    d = L("diag-d1g.json")
    per, nfirst, only_small, amb, true_in, auth_objs = Counter(), Counter(), 0, Counter(), Counter(), Counter()
    wr, xt = [], Counter()
    for e in d["episodes"]:
        by = {}
        for c in e["system2_diagnostic_trace"]:
            by.setdefault(c["target_id"], []).append(c)
        auth = {r["target_id"] for r in e["system2_decisions"] if r.get("authorization")}
        wrong = {o["target_id"] for o in e["wrong_disposition_objects"]}
        for t, cs in by.items():
            per[len(cs)] += 1
            nfirst["<6" if cs[0]["n_usable_total"] < 6 else ">=6"] += 1
            if all(c["n_usable_total"] < 6 for c in cs):
                only_small += 1
                wr.append(cs[-1]["window_remaining_time"])
            for c in cs:
                if c["gate"] == "AMBIGUOUS":
                    amb[len(c["passing"])] += 1
                    if e["fault_family"] is None:
                        true_in[sorted(e["structure"]) in [sorted(p) for p in c["passing"]]] += 1
        for t in auth:
            auth_objs["wrong" if t in wrong else "not_wrong"] += 1
        for t, disp in e["score"]["dispositions"].items():
            t = int(t)
            xt[(disp, "auth" if t in auth else "noauth", "wrong" if t in wrong else "-",
                "unsafe" if t in e["unsafe_target_ids"] else "-")] += 1
    wr.sort()
    print("R5 calls/object", dict(per), "first-call n_usable", dict(nfirst), "objects all-calls n<6", only_small,
          "window_remaining_time(last call) min/median/max", round(wr[0], 3), round(wr[len(wr) // 2], 3),
          round(wr[-1], 3))
    print("   AMBIGUOUS |V| sizes", dict(sorted(amb.items())), "true structure in V", dict(true_in),
          "authorized objects", dict(auth_objs))
    print("   disposition x auth x wrong x unsafe", dict(xt.most_common()))


def r6_f_vs_g_and_e_vs_f():
    """R6: d1f vs d1g underlying equality; first->last label transitions; d1e vs d1f on common seeds."""
    f, g, e = L("diag-d1f.json"), L("diag-d1g.json"), L("diag-d1e.json")
    keys = ("system2_diagnostic_trace", "system2_decisions", "failure_trace", "score")
    print("R6 d1f==d1g on", keys, all(a[k] == b[k] for a, b in zip(f["episodes"], g["episodes"]) for k in keys))
    tr = Counter((x["first_failure"], y["last_s2_call"]) for a, b in zip(f["episodes"], g["episodes"])
                 for x, y in zip(a["wrong_disposition_objects"], b["wrong_disposition_objects"]))
    print("   first->last", dict(tr))
    es = {x["seed"]: x for x in e["episodes"]}
    common = [x for x in f["episodes"] if x["seed"] in es]
    s = lambda eps, k: sum(x["score"][k] for x in eps)
    for k in ("unsafe_action_count", "wrong_disposition_count", "challenge_success_count",
              "preservation_regression_count"):
        print(f"   {k}: d1e={s(es.values(), k)} d1f(common {len(common)})={s(common, k)}")
    noauth = [(x["seed"], r["target_id"], r["time"]) for x in f["episodes"] for r in x["system2_decisions"]
              if r["action"] == "UPDATE_MODEL_AND_REPLAN" and not r.get("authorization")]
    print("   d1f UPDATE without authorization", len(noauth), noauth)
    for seed, t in ((40, 6), (97, 7), (116, 1)):
        rr = [(r["time"], r["action"], r.get("authorization") is not None) for r in es[seed]["system2_decisions"]
              if r["target_id"] == t]
        print(f"   d1e {seed}/{t} decisions {rr} unsafe={t in es[seed]['unsafe_target_ids']}")


def r7_unsafe_traces_d1d():
    """R7: unsafe-traces-d1d.json unsafe_objects[]."""
    for o in L("unsafe-traces-d1d.json")["unsafe_objects"]:
        a = [x for x in o["authorization_decisions"] if x["action"] == "UPDATE_MODEL_AND_REPLAN"][-1]
        print("R7", o["seed"], o["target_id"], o["authorization_source"], "auth t", round(a["time"], 2),
              "n", a["n_usable"], a["structure"], {k: round(v, 3) for k, v in a["fitted_parameters"].items()},
              "pos_err", round(o["evaluator"]["position_error"], 3), "cmd", o["failure_trace"]["command_time"],
              "exec", o["failure_trace"]["execution_time"], "true_eta", o["failure_trace"]["true_eta"])


def r8_fast_layer_unsafe():
    """R8: diag-d1g.json and diag-d1-before.json failure_trace[] for the 7 b3-dev unsafe objects."""
    g = {e["seed"]: e for e in L("diag-d1g.json")["episodes"]}
    b = {e["seed"]: e for e in L("diag-d1-before.json")["episodes"]}
    for seed, t in ((46, 0), (51, 1), (88, 1), (103, 1), (106, 0), (106, 1), (106, 2)):
        x = next(r for r in g[seed]["failure_trace"] if r["target_id"] == t)
        y = next(r for r in b[seed]["failure_trace"] if r["target_id"] == t)
        cs = [(c["sim_time"], c["n_usable_total"], c["gate"]) for c in g[seed]["system2_diagnostic_trace"]
              if c["target_id"] == t]
        same = all(x[k] == y[k] for k in ("command_time", "execution_time", "position_error", "time_error"))
        print(f"R8 {seed}/{t} cmd={x['command_time']} exec={x['execution_time']} true_eta={x['true_eta']} "
              f"cmd-true_eta={x['command_time'] - x['true_eta']:.3f} exec-cmd={x['execution_time'] - x['command_time']:.3f} "
              f"pos={x['position_error']} time={x['time_error']} max={max(x['position_error'], x['time_error'])} "
              f"calls={cs} same_as_d1-before={same} "
              f"d1-before_calls={sum(c['target_id'] == t for c in b[seed]['system2_diagnostic_trace'])}")


if __name__ == "__main__":
    r1_b3dev_first20(); r2_b3dev_by_case(); r3_b3dev_unsafe()
    for n in ("diag-d1-before.json", "diag-d1-after.json", "diag-d1d.json", "diag-d1e.json",
              "diag-d1f.json", "diag-d1g.json"):
        r4_diag_stages(n)
    r5_d1g_objects(); r6_f_vs_g_and_e_vs_f(); r7_unsafe_traces_d1d(); r8_fast_layer_unsafe()
```

## 附录 B：补充计数（B1–B4）

同样在仓库根目录用 `python3 -I` 运行。已核对的输出：B1 = RECOVER 1357 / REFUSE 124 / PAUSE_THEN_RECOVER 79，challenge 合计 899；B2 = (0,6,0.5)、(10,0,0.5)、(14,3,0.5)、(19,9,1.9)；B3 = d1-before 307 条（True 30 / False 277），d1-after 327 条（True 30 / False 297）；B4 = seed 0 pause 11、picked 12。

```python
"""T3 supplementary counts (B1–B4) over committed artifacts only."""
import json
from collections import Counter

A = "artifacts/s2/"
d = json.load(open(A + "b3-dev.json"))
print("B1 dispositions", dict(Counter(v for e in d["episodes"] for v in e["score"]["dispositions"].values())),
      "challenge_count sum", sum(e["score"]["challenge_count"] for e in d["episodes"]))
print("B2 first-20 UPDATE without authorization",
      [(e["seed"], r["target_id"], round(r["time"], 2)) for e in d["episodes"] for r in e.get("system2_decisions", [])
       if r["action"] == "UPDATE_MODEL_AND_REPLAN" and not r.get("authorization")])
for n in ("diag-d1-before.json", "diag-d1-after.json"):
    x = json.load(open(A + n))
    print("B3", n, "ambiguous_cases", len(x["ambiguous_cases"]),
          dict(Counter(c["all_passing_models_are_supersets"] for c in x["ambiguous_cases"])))
print("B4 seed 0 pause_target_ids", len(d["episodes"][0]["pause_target_ids"]),
      "picked", d["episodes"][0]["b3_terminal_counts"]["picked"])
```

## 附录 C：复现说明

附录 A 脚本在 `54f5006` 上运行的完整输出共 80 行；正文里每个 `Rk` 数字都直接来自这份输出。复现方法是重新运行脚本，没有另外提交输出文件，因为本任务只允许新增这一个文件。
