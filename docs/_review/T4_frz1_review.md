# T4 — FRZ-1 对照 Addendum 05 的审查，以及重观测后的漏斗（只读）

- 审查对象：`feat/frz1-b3core` 头 `cb771079c1c119d73d0ebd0e24704a1935731cea`；`main` 头 `520b7cfdf13b805c9258ab06c79a658ee62aef8b`；merge-base `9fe17301c899abd9b2bf715ea7e62f0b47643e3d`；FRZ-1 领先 main 12 个提交。三个 sha 都与任务书核对值一致。
- 分支：`cloud/t4-frz1-review`（从 `feat/frz1-b3core` 头新建）。本文件是分支上唯一新增的文件。
- Addendum 05 从 `git show origin/main:docs/P3_PREREG_ADDENDUM_05.md` 读取（它不在 FRZ-1 分支上）。
- 环境：云 VM。Python 3.12.3 venv，按 `requirements.txt` 安装（numpy 2.5.4，pydantic 2.14.1，pytest 8.4.2）。VM 记录的 `runtime_versions` 为 `x86_64`、`Intel(R) Xeon(R) Processor`、`scipy-openblas 0.3.34.106.0`，与已提交 `b3-dev.json` 的 `Intel(R) Core(TM) i7-10750H` 不同。按 Addendum 05 §4.2，跨机器只在决策与 metrics 层比较。
- 数据范围：只用 `config/dev_seeds.json`（130 个 dev seed）和已提交的 artifacts。`config/eval_seeds*.json` 未打开。没有运行带 live 的命令，没有设置 `NVIDIA_API_KEY`/`ZETARIS_TOKEN`，B4 探针中不存在 live provider 对象（见 §5）。
- BLOCKED 判据核对：`git diff --stat origin/main...origin/feat/frz1-b3core` 列出的 16 个文件里没有 `docs/` 和 `config/` 下的文件，也没有预注册文件（文件清单：`artifacts/s2/b3-dev.{json,md}`、`artifacts/sponsor/meterless-persistence.json`、`scripts/l3_equivalence.py`、`src/rra/...` 7 个、`tests/...` 6 个）。所以未触发 BLOCKED。
- 完成情况：任务书第 1–7 项都已完成。第 5 项的范围见 §5 开头。
- 本文不做成败判定。计数变化只写成“从 a 变为 b”。

## 0. 记号与证据规则

- 行号指 FRZ-1 头 `cb77107` 的文件，除非标明 `main:`。
- **FACT**：可以直接从代码行、已提交文件字段或复现脚本输出读到。**INFERENCE**：由 FACT 推出的机制解释，附“确认还缺的证据”。
- 派生数的出处写作 `Hk`/`Xk`/`Rk`/`Sk`/`Pk`/`Dk`/`Kk`，对应附录 A 中脚本输出行的前缀。脚本放在会话 scratchpad，没有进仓库，全文附在附录 A，可以复现。
  - `t4_funnel.py`：对 130 个 dev seed 离线重跑 `rra.eval.b3_dev._run_seed`。只读插桩：替换模块全局 `rra.evidence.episode.run_b3`（`tests/test_frz1_reobserve.py` 用的是同一个替换点），在每次调用时读取调用者帧局部变量的快照；用 `sys.setprofile` 记录闭包 `finish_reobserve_hold` 的调用参数。`src/` 没有改动。分别对 FRZ-1 树和 `origin/main` 的 worktree（放在 scratchpad）各跑一次，输出 `frz1_funnel.json` 和 `main_funnel.json`。
  - **插桩一致性（FACT）**：两次插桩重跑的汇总与已提交 artifacts 一致。FRZ-1：success 84/775、wrong 588、miss 97、unsafe 7、`system2_calls` 2009，与 `b3-dev.json → metrics.*`、`operational_cost.system2_calls` 相同。main：84/775、589、96、7、1961，与 `origin/main:artifacts/s2/b3-dev.json` 相同。各 seed 的 `system2_reobserve` 之和与 `b3-dev.json → system2_reobserve` 相同（H0）。
- 已提交 `b3-dev.json` 只给前 20 个 seed 保留逐决策记录（`src/rra/eval/b3_dev.py:170-172`），也没有逐对象的重观测记录。所以第 4 项的逐对象数字都来自上面的离线重跑。

## 1. Addendum 05 条款对照表

判定只描述实现与条款文字的对应程度，不评价结果。

| 条款 | 判定 | 实现出处（FRZ-1） | 测试 | 说明 |
|---|---|---|---|---|
| §1.1 PAUSE 时进入保持，不记 escalated；保持期间 `safe_stop`，被保持目标不收快速层命令 | 已实现（触发范围见下） | `src/rra/evidence/episode.py:887-893`（`ESCALATE` 且本步 S2 动作为 PAUSE → `system2_reobserve_holds.setdefault`、`safe_stop = True`）；命令发出要求 `not safe_stop`（`:964-971`、`:982-985`） | `test_frz1_reobserve.py:19` `test_escalated_target_is_reobserved_after_half_second_and_held_from_fast_commands`（断言 `command_issued is False`） | 只有 `"ESCALATE:" in correction.reason` 时才进入保持（`:887`）。infeasible 触发（`:667`）和 outcome escalation（`run_outcome_escalation`）返回的 PAUSE 不进入保持。dev 上这两类 PAUSE 调用分别有 1412 次和 140 次（R2）。这算不算 §1.1 的“fast-layer escalation”，有两种读法，见 §7-1 |
| §1.2 上次评估后 ≥0.5 s 的第一个观测重评估，用全部累积观测，不需要新的升级事件 | 已实现 | `:652-663`（`hold_due`）、`:666`（`escalation_event or hold_due`）；PAUSE 后 `system2_next_retry = t+0.5`（`:870-873`、`:892`）；`run_b3(s2obs, …)`，其中 `s2obs` 是该目标全部观测（`:674-681`） | `:48` `test_continuous_escalation_keeps_reobserving_until_window_end`；`:76` `test_diag_dev_seed_reobservations_stay_within_retry_interval`（只测 dev 索引 1–3，容差 ≤0.5+dt） | 全 130 seed 的 245 个保持区间里，间隔分布为 0.5 s 222 个、0.6 s 11 个、0.2 s 6 个、0.1 s 5 个、0.0 s 1 个，没有超过 0.5+dt 的（P1）。11 个 0.6 s 区间（例如 7/1：3.8→4.4，H9）是浮点比较 `observation.time >= t+0.5` 跳过了名义上 +0.5 s 的那一帧。§7-3 |
| §1.3 授权走原授权路径；`safe_stop` 只在无保持且无 latch 时解除 | 已实现；“只在”的读法见说明 | `:879-885`（保持中目标被授权 → 出保持；`if not system2_reobserve_holds and not latched: safe_stop = False`） | **无**（4 个 FRZ-1 测试都用常 PAUSE 桩） | 实现把“无保持且无 latch”当作解除的**充分**条件。保持开始前已由别的目标设下的 `safe_stop` 也会被解除。dev 上唯一一次保持后授权（88/5）就是这种情况：`safe_stop` 在 t=0.2 已为 True，t=5.9 授权后被解除，随后发出命令（S1、X4，§4.6）。§7-2 |
| §1.4 以 `;REOBSERVE_EXHAUSTED` 结束：latch / 授权命令无法在拾取窗口内执行之后 / 其他终态到期 / episode 结束 | 部分 | `finish_reobserve_hold` `:363-373`；latch `:533-535`、`:589-593`；窗口 `:654-658`；目标切换 `:546-547`；episode 结束 `:1093-1094`；`s2_non_pause` `:874-878`、`:894-896` | latch：`:96` `test_hard_fault_latch_ends_an_existing_reobserve_hold`；窗口：`:19`、`:48`。**target_switch、episode_end、s2_non_pause 无测试** | (a) 窗口终点用 `base_plan.expected_arrival_time + dt/2`（名义计划，`:655`），没有用 S2 拟合的时刻，也没有计入执行延迟；而且只在 `hold_due` 的样本上检查，所以耗尽最多可能比窗口终点晚 0.5 s 才记录。(b) 同一步里 `window_end` 结束保持并记下终态后，新的升级上升沿又调用 S2，PAUSE 后用 `setdefault` 再次进入保持；目标已有终态，后续再结束时 `record_outcome` 不再写入（`:297-298`），但计数器加一，并追加一条 `escalations` 记录。dev 上有 6 次（H1：17/9、21/8、39/4、61/11、69/7、83/7）。(c) 条款里的“其他终态到期”没有通用钩子，只覆盖 latch、目标切换、episode 结束三条路径。§7-3、§7-4 |
| §1.5 B3/B4-strict/B4-tiebreak 同样适用；B1/B2 不变；HUMAN_ESCALATION 与 latched 照旧 | 已实现（B4 没有测试） | 保持逻辑不区分 `s2_variant`；`system2_enabled=False` 时 `s2_action` 恒为 None（`:665`），不进入保持 | B4 保持：**无测试**；B1 不变：无专门测试 | FACT：130 seed 的 B1 receipt 哈希在 main（VM 重跑）、FRZ-1（VM 重跑）、已提交 FRZ-1 `b3-dev.json` 之间完全相同（`b1 diffs 0`，D4 与 §3）。本文没有检查 B2 |
| §1.6 不改 verifier 阈值、common-action、授权门、DSL、evaluator、终态、计分、分母 | 未见改动（以 diff 为据） | diff 没有触及 `src/rra/s2/verifier.py`、`b3.py`、`dsl.py`、`src/rra/eval/scoring.py`、`runner.py` | — | 但 FRZ-1 还有两处 Addendum 05 没有列出的行为改动：`71ce80d`（空 fault 窗口时也 latch，`:281-284`，测试 `test_s2_veto_semantics.py:114`）和 `afa2aa6`（`scripts/l3_equivalence.py:154-156` 的 `base_git_sha` 改为运行时取 HEAD）。在其提交点上，`71ce80d` 没有改变 130 个 dev seed 的任何 B1/B3 哈希（K1）。§7-8 |
| §2 网格平局：在 1e-12×max(1,\|min\|) 内取最小网格值 | 已实现（二维平局的读法见说明） | `src/rra/s2/fitter.py:61-69` | `test_s2.py:99` `test_speed_step_fit_chooses_smallest_grid_point_within_tie_tolerance`（只测一维 speed-step） | 两个网格同时存在（SPEED_STEP+ACTUATOR_DELAY）时，按 (tau, delay) 字典序取最小。条款写的是“the smallest grid value”。**actuator-delay 一维和二维平局都没有测试** |
| §3.1 replay 生成时缓存缺失非零退出，不回退；live 时缺失触发 live 调用 | 已实现（缺端到端测试） | `src/rra/llm/adapter.py:108-109`（`except ReplayCacheMiss: raise`，位于 `OSError` 捕获之前）；`src/rra/eval/b4_dev.py:46-48`（`live is None` 时重新抛出；否则走 live 调用，`:49-62`）；异常经 `ThreadPoolExecutor.map` 传到 CLI，`src/rra/cli.py:157-160` 不捕获 | `test_llm_adapter.py:64` `test_adapter_propagates_replay_cache_miss`（只测 adapter 层） | **没有测试端到端覆盖 `rra s2-b4-dev --replay` 在缺失时的退出码**。§5 有一次 CLI 实测 |
| §3.2 无生成器即配置错误并中止 | 已实现 | `episode.py:132-133`（`ValueError`）；`6d0b205` 删除了 `NO_PROPOSER` 回退（`main:episode.py:667-669` 已不存在） | `test_b4_episode.py:135` `test_b4_variants_require_a_proposer` | `run_b4_dev` 总会构造 proposer（`b4_dev.py:217-218`），所以 CLI 路径到不了这个分支 |
| §3.3 `llm_calls` 按 (seed, 文本变体) 跨两个 B4 变体计数；两变体的 proposer 调用另行分开报告 | 部分 | 共享 `_MemoizedProposer`，每个任务一个 provider（`b4_dev.py:217-218`、`:236`、`:312-313`）；汇总表里 `llm_calls` 只记在 `B4_STRICT`，`B4_TIEBREAK` 记 0（`:120-121`） | 无 | FRZ-1 没有改动这部分代码（12 个提交都没有触及）。“分开报告”目前只能从逐行的 `B4_STRICT_proposal_rank`/`B4_TIEBREAK_proposal_rank` 列表长度推出（`:291-292`），没有显式字段。已提交的 `b4-dev.json` 也没有在 FRZ-1 上重新生成（FRZ-1 diff 不含它）。§7-7 |
| §3.4 B4 请求浮点按 6 位小数序列化 | **未找到** | 证据包直接放原始浮点（`episode.py:692-705`：`item.time`、`observed_x`、`rmse` 等）；`adapter.py:79-82` 用 `json.dumps` 直接序列化；`src/rra/llm/`、`src/rra/eval/context_v3.py` 中没有 `round(` | 无 | 影响见 §5：在本 VM 上，连 main 代码 replay subset 也大部分缺失 |
| §4.1 receipt 在登记 runner 上逐位可复现；记录 Python、NumPy、架构、CPU、BLAS，且不进哈希 | 已实现（记录部分）；可复现性在本 VM 同机实测 | `src/rra/runtime.py:10-32`；进入 receipt：`episode.py:1135`、`b3_dev.py:279`、`b4_dev.py:315`；从哈希排除：`episode.py:1191-1193`、`b3_dev.py:281-282`、`b4_dev.py:327-328` | `test_evidence.py:26` `test_runtime_versions_are_receipted_but_excluded_from_receipt_hash`（只测 episode 层） | BLAS 取自 `np.show_config(mode="dicts")` 的构建依赖，不是运行时实际加载的库。CPU 型号只从 `/proc/cpuinfo` 读，非 Linux 上为 None。代码和文档中都没有指明哪台是“registered runner”。b3_dev/b4_dev 层的哈希排除没有测试 |
| §4.2 跨机器只在决策与 metrics 层比较，并列出逐 seed 的 receipt 差异 | 流程条款（本文按此执行） | — | — | 见 §3 |
| §4.3 eval-v3 artifact 在同一 runner 上生成并报告平台 | 未找到（目前没有 eval-v3 生成路径） | 只有禁止检查 `src/rra/eval/holdout.py:41-51`；`artifacts/s2/b3-dev.md` 不打印平台（JSON 里有） | — | 流程条款，代码层面无从实现 |
| §5-1 保持中目标未按 §1.2 重评估 = 缺陷 | 无运行时断言；离线检查未发现违例 | — | `test_frz1_reobserve.py:76`（3 个 seed） | 全 dev：保持区间最大间隔 0.6 s（≤0.5+dt，P1） |
| §5-2 episode 结束时目标没有终态 = 缺陷 | 有兜底 | `:1093-1094`（结束所有保持），然后 `:1095-1100` 为所有缺终态目标记 skipped | 无专门测试 | 全 dev 1560/1560 个对象都有终态（P2） |
| §5-3 replay 生成的 B4 artifact 含缓存缺失回退 = 缺陷 | 代码层面不再回退；无 artifact 级检查 | `adapter.py:108-109` | `test_llm_adapter.py:64` | receipt 中没有可供审计的“缺失回退计数”字段 |
| §5-4 B4 在没有生成器时继续运行 = 缺陷 | 已阻止 | `episode.py:132-133` | `test_b4_episode.py:135` | — |

### 1.1 没有测试覆盖的分支（单列）

1. 保持中目标被授权的路径：出保持、`authorized_after_hold` 计数、`safe_stop` 解除（`episode.py:879-885`）。
2. `s2_non_pause` 结束，即保持中 S2 返回非 PAUSE 且未授权（`:874-878`、`:894-896`）。dev 上为 0 次。
3. `target_switch` 结束（`:546-547`）和 `episode_end` 结束（`:1093-1094`）。dev 上分别为 16 次和 2 次。
4. 同一步内 `window_end` 结束后再次进入保持（§1 表 §1.4 (b)）。dev 上 6 次。
5. B4-strict / B4-tiebreak 下的保持（§1.5）。
6. §2 的 actuator-delay 一维平局和 (tau, delay) 二维平局。
7. §3.1 `rra s2-b4-dev --replay` 端到端的非零退出。
8. §4.1 b3_dev / b4_dev receipt 层的 `runtime_versions` 哈希排除。
9. latch 在 `presence` 路径（目标不可见，`:533-535`）上结束保持。现有测试只走 `check_faults` 路径（`:589-593`）。

## 2. 全量 pytest

命令（仓库根目录）：`env -u NVIDIA_API_KEY -u ZETARIS_TOKEN <venv>/bin/python -m pytest -q -rfEs`

```
200 passed, 4 skipped in 126.70s (0:02:06)
SKIPPED [1] tests/test_meterless_bridge.py:219: needs Node, scripts/setup_meterless.sh and RRA_METERLESS_LIVE=1
SKIPPED [1] tests/test_meterless_bridge.py:240: needs Node, scripts/setup_meterless.sh and RRA_METERLESS_LIVE=1
SKIPPED [1] tests/test_meterless_bridge.py:249: needs Node, scripts/setup_meterless.sh and RRA_METERLESS_LIVE=1
SKIPPED [1] tests/test_packet_sources.py:48: Zetaris live checks are opt-in
```

pytest 计数：passed 200，skipped 4，failed 0。

## 3. 同机确定性与跨机比较

命令：`<venv>/bin/python ./rra s2-b3-dev --output-dir <scratchpad>/b3run1`，然后同样输出到 `b3run2`。两次运行都写到 scratchpad；运行后 `git status --porcelain` 为空。

| 量 | run1 | run2 | 已提交 FRZ-1 `b3-dev.json` | 出处 |
|---|---|---|---|---|
| `receipt_sha256` | `3c1ee45a0cc7138c…e659a` | `3c1ee45a0cc7138c…e659a` | `75115f44cc3bd212…a5e32` | D1 |
| `metrics` | — | 与 run1 相同 | 与 run1 相同 | D2 |
| `system2_reobserve` | — | — | 与 run1 相同 | D2 |
| 逐 seed B3 receipt 哈希不同 | — | 0/130 | 115/130 | D4 |
| 逐 seed B1 receipt 哈希不同 | — | — | 0/130 | D4 |
| 逐 episode 非哈希字段（除决策记录外）不同的 seed | — | — | 无 | D3 |
| 前 20 seed 决策序列（target, action, gate, trigger, hypothesis, structure, 有无 authorization, time）不同的 seed | — | — | 0 | D5 |
| 前 20 seed 决策中不同的浮点叶子数 / 最大绝对差 | — | — | 7785 / 1.33e-15 | D5 |
| `operational_cost.system2_calls` / `verifier_calls` | 2009 / 28126 | — | 2009 / 28126 | 输出文件 |

- 同机：两次运行的总 receipt 和 130 个逐 seed B3 哈希完全相同。
- 跨机：metrics、`system2_reobserve`、每个 episode 的全部计分与计数字段都相同，前 20 seed 的决策序列也相同。不同的只是拟合参数、`rmse`、`residual_vector`、`verifier_score` 的末位（D5b 列出了全部字段路径；网格值 `speed_step_time`/`actuator_delay` 不在其中）。
- 哈希相同的 15 个 seed：2、6、15、16、49、58、67、73、92、102、105、107、113、114、124（D4b）。其余 115 个 seed 的 B3 哈希不同，这里只列出，不作结论。这与 Addendum 05 Trigger 段记录的“115 of 130”是同一个数。
- `main` 也一样：`origin/main:artifacts/s2/b3-dev.json` 对 VM 上重跑的 main，B1 哈希 0/130 不同，B3 哈希 115/130 不同（附录 A 末尾的单行命令）。

## 4. 重观测之后的漏斗（第 B 问）

### 4.1 进入保持与结束原因

| 量 | 值 | 出处 |
|---|---:|---|
| receipt 汇总 `hold_entries` / `reobservations` / `authorized_after_hold` / `exhausted` | 183 / 82 / 1 / 182 | `b3-dev.json → system2_reobserve`；H0 |
| receipt 汇总 `end_reasons` | window_end 153，latch 11，target_switch 16，s2_non_pause 0，episode_end 2，authorized 1 | 同上 |
| 进入保持的**不同对象**数 | 177 | H1 |
| 已有终态后再次进入保持（同步内 window_end 后又一次升级 → PAUSE） | 6（17/9、21/8、39/4、61/11、69/7、83/7）；177+6=183 | H1；机制见 §1 表 §1.4 (b) |
| 逐对象**首次**结束原因 | window_end 153，latch 11，target_switch 11，episode_end 1，authorized 1 | H2（receipt 的 target_switch 16 / episode_end 2 中，5 / 1 是再次进入后的第二次结束） |
| 每对象重评估次数 | 0 次：149；1：15；2：3；3：1；4：2；5：1；7：5；10：1（合计 82） | H3 |
| 进入方式 | 177 个全部是升级上升沿（`escalation_event=True`，`infeasible=False`） | H4c |
| 进入时的 gate | AMBIGUOUS 174，NO_SAFE_ACTION 2，NO_VERIFIED_HYPOTHESIS 1 | H4c |
| 进入时刻（目标时钟）min / 中位 / max | 1.3 / 7.1 / 9.9 s | H4 |
| 进入时 n_usable min / 中位 / max | 14 / 72 / 100 | H4 |
| 进入时名义窗口余量 `expected_arrival+dt/2−t` min / 中位 / max | −5.914 / −1.623 / 5.689 s；≤0.5 s：138；≤0：127 | H4 |
| 进入时真实位置已越过 `x_pick`（`actual_x>0`，`x_pick=0.0`） | 153 / 177 | H4b |
| 进入时 `safe_stop` 已为 True | 152 / 177 | H4c |
| 0 次重评估的 149 个对象的结束原因 | window_end 126，latch 11，target_switch 11，episode_end 1；其中 138 个进入时余量 ≤0.5 s | H5 |
| window_end 结束时真实位置仍在 `x_pick` 上游的 | 3 / 153（上游 1.789、1.903、1.964） | H6 |

`actual_x` 是 evaluator 侧的真值（`plant_observation.actual_x`），只在离线插桩里读取，policy 拿不到。

### 4.2 重评估时各阶段计数（82 次）

| 阶段 | 次数 | 出处 / 备注 |
|---|---:|---|
| n_usable < 6 | 0 | H7。重评估时 n 在 19–77 之间，中位 50 |
| n ≥ 6 且 \|V\| = 0（NO_VERIFIED_HYPOTHESIS） | 33 | H7、H9：全部来自 5 个 SENSOR_SPIKE_BURST episode 的 PAUSE_THEN_RECOVER 对象（34/5、53/9、91/8、110/3、129/8），这些对象不在 recoverable challenge 里 |
| \|V\| ≥ 1，common-action = AMBIGUOUS | 42 | H7：\|V\| 分布 3:32，2:2，9:5，7:3 |
| \|V\| ≥ 1，NO_SAFE_ACTION | 6 | H9：86/1 和 86/10 各 3 次，\|V\|=1 |
| \|V\| ≥ 1，COMMON_ACTION 且有 authorization | 1 | H9：88/5，t=5.9，n=60 |
| fault | 0 | `b3["faults"]` 全为空 |
| 重评估时名义窗口余量 min / 中位 / max | 0.012 / 1.094 / 4.638 s | H7 |

### 4.3 保持对象的最终结局

177 个保持对象都是 challenge 对象（H8）：RECOVER 且 not_issued 143；RECOVER 且 miss 1（88/5）；REFUSE not_issued 11；PAUSE_THEN_RECOVER not_issued 22。其中 recoverable challenge 144 个，success 0 个。

### 4.4 新增 System-2 调用落在哪里（1961 → 2009，净 +48）

| 部分 | 调用数变化 | 对象数 | 出处 |
|---|---:|---:|---|
| 保持对象：重评估 82 + 再次进入时的调用 6 | +88 | 34 | X1、X3 |
| 非保持对象，全部在 11 个 fault episode（SENSOR_STUCK 36 个对象，BELT_STOP 4 个） | −40 | 40 | X1、X2 |

- −40 这部分（FACT）：这些 seed 中，main 的若干 fast `PAUSE/NO_VERIFIED_HYPOTHESIS` 调用在 FRZ-1 变成了 `HARD_FAULT_LATCH` 记录（这类记录不走 `run_b3`，不计入 `system2_calls`）。在 FRZ-1 中，这 11 个 seed 的首个 latch 都落在一个正处于保持的目标上，而且比 main 早（例如 seed 37：main 在 target 8、t=0.3；FRZ-1 在 target 7、t=2.2）。7 个 SENSOR_STUCK seed（14、33、52、71、90、109、128）在 main 上根本没有 latch（K2）。这 11 个 seed 的计分在 main 与 FRZ-1 之间相同（K2 表最后一列）。
- 按提交二分（K3，同机，只跑这 11 个 seed）：`7ca3268`/`71ce80d`/`244b670`/`154522b`/`67bc419` 都是 126 次；`56f36b0` 为 107（−19）；`6d0b205` 为 107；`e942024` 为 86（−21）。所以 −40 来自重观测这两个提交，不是 `71ce80d`。
- INFERENCE（机制）：被保持的目标没有终态，所以 `terminal_monitoring="corrected"` 的“终态目标惰性”分支（`episode.py:564-567`）不再跳过它。它的后续观测继续经过 `check_faults`（`:575-593`），fault 因此在它身上更早被检测并 latch。确认还缺的证据：逐步记录 latch 当步的 `check_faults` 输入窗口，以及 main 上同一目标在 escalated 之后被跳过的样本数。

### 4.5 为什么新增调用没有变成 success

- 149/177 个保持对象**没有任何重评估**。其中 138 个进入保持时名义窗口余量已 ≤0.5 s，153/177 进入时真实位置已越过拾取点（H4、H4b、H5）。保持开始的时刻，就是快速层第一次出现 `ESCALATE` 上升沿的时刻（中位 t=7.1 s，n=72）。
- 有重评估的 28 个对象里：5 个 PAUSE_THEN_RECOVER 对象一直是 NO_VERIFIED（33 次）；其余对象停在 AMBIGUOUS（\|V\| 多为 3）或 NO_SAFE_ACTION，直到 window_end；只有 88/5 得到 COMMON_ACTION 授权（H9）。
- 88/5 授权后被命令，结局是 attempt_failed，原因 `missed pick window`，计分为 miss。这是 main→FRZ-1 之间唯一一个改变了 class/status 的对象：main 上它是 escalated（not issued，wrong_disposition）（X4）。这一个对象恰好解释了 wrong 589→588、miss 96→97。

### 4.6 全部 775 个 recoverable challenge 对象停在哪里

| 结局 | main | FRZ-1 | 出处 |
|---|---:|---:|---|
| success | 84 | 84 | R1 |
| miss（0.2<e≤0.4） | 95 | 96 | R1（按 evaluator 规则复算）。`metrics.miss` 为 96/97，多出的 1 个是 PAUSE_THEN_RECOVER 对象的 miss，它不属于 recoverable challenge |
| unsafe（e>0.4） | 7 | 7 | R1 |
| not issued：skipped `safe_stop_before_command`（该对象首次 S2 调用时 `safe_stop` 已为 True） | 298 | 298 | R1 |
| not issued：skipped `correction_infeasible` | 147（首调时无 safe_stop 140 + 有 7） | 147 | R1 |
| not issued：escalated（FRZ-1 中全部带 `;REOBSERVE_EXHAUSTED`） | 144 | 143 | R1 |

补充：

- S1（S2 授权过的对象，FRZ-1 149 个，main 148 个）：64 个授权后仍以 `safe_stop_before_command` 被跳过，其中 63 个是 recoverable challenge，且这 64 个在授权当时 `safe_stop` 已为 True。另有 8 个以 `correction_infeasible` 被跳过，3 个 escalated，62 个 picked（success），12 个 miss。main 与 FRZ-1 只差 88/5 这一个对象。
- R2：FRZ-1 中有 1412 次 PAUSE 调用来自 infeasible 触发，140 次来自 `run_outcome_escalation`，都不走保持路径。
- R3：非 success 的 recoverable challenge 对象中，首次快速路径调用是 infeasible 触发且 n<6、之后再没有快速路径调用的，有 432 个。

## 5. B4 replay 缓存影响评估（离线）

范围：subset（`artifacts/s2/diag-d1g.json` 的 33 个 seed）和 full dev（130 个 seed）两种都跑完了，main 和 FRZ-1 各一次。subset 每次 4–6 分钟，full 每次 18–24 分钟，都在 60 分钟以内。

方法（附录 A.9、A.10）：调用 `run_b4_dev(replay_only=True)`。此时 `_ReadThroughProvider.live is None`（`b4_dev.py:33`），不构造 `NvidiaNimProvider`，也就不可能发起网络请求；探针里另有 `assert self.live is None`。替换 `_ReadThroughProvider.complete` 后，缺失按 finalized payload 的 sha256 计数，并返回空提案 `{"items": []}`，不抛出。输出写到 scratchpad。`round6` 是一个探针（不是仓库代码）：在构造请求之前把证据包中的浮点按 6 位小数取整，用来估计 §3.4 实现后 cache key 的情况。所有运行的 `operational_cost.live_llm_calls` 都是 0。

| 运行 | N_amb | 命中调用 | 缺失调用 | 唯一命中 key | 唯一缺失 key | 出处 |
|---|---:|---:|---:|---:|---:|---|
| main，subset，raw | 116 | 62 | 333 | 62 | 317 | K4 |
| FRZ-1，subset，raw | 133 | 44 | 418 | 44 | 402 | K4 |
| main，full，raw | 374 | 62 | 1157 | 62 | 1149 | K4 |
| FRZ-1，full，raw | 422 | 44 | 1366 | 44 | 1358 | K4 |
| main，subset，round6 | 116 | 0 | 392 | 0 | 376 | K4 |
| FRZ-1，subset，round6 | 133 | 0 | 460 | 0 | 444 | K4 |

key 集合比较（K4，同一台 VM）：

| 模式 | main 唯一 key | FRZ-1 唯一 key | 共有 | 仅 FRZ-1 | 仅 main |
|---|---:|---:|---:|---:|---:|
| subset raw | 379 | 446 | 321 | 125 | 58 |
| full raw | 1211 | 1402 | 1073 | 329 | 138 |
| subset round6 | 376 | 444 | 356 | 88 | 20 |

- FACT：已提交的 `artifacts/llm_cache` 有 386 个文件；已提交 `b4-dev.json`（subset，在 FRZ-1 之前生成）记录 `N_amb` 116、`llm_requests_served` 376。
- FACT：在本 VM 上，**main 代码**按原样 replay subset 也只命中 62 次，唯一缺失 317 个。证据包里放的是原始浮点（§1 表 §3.4），跨机器末位差异会改变请求体和 key。所以本 VM 上的缺失数混合了“跨机器”和“FRZ-1 改动”两种来源，不能直接当作 FRZ-1 造成的缺失。
- FACT：取整到 6 位后，main subset 的唯一请求数是 376，与已提交的 `llm_requests_served` 376 相同；但取整后的请求在现有缓存中命中 0 次，因为缓存是按未取整的请求体建立的。
- FACT：FRZ-1 让 subset 的 `N_amb` 从 116 变为 133，full 从 374 变为 422。取整口径下，subset 的唯一请求从 376 变为 444，其中 88 个是 FRZ-1 新出现的请求，另有 20 个 main 请求在 FRZ-1 中不再出现。
- 预计所需 live 调用（INFERENCE，按唯一缺失 key 计。一次 live 调用写入缓存后，后续相同请求都会命中）：
  - 在本 VM 上用现有缓存 replay FRZ-1：subset 约 402 次，full 约 1358 次。
  - 在生成缓存的那台机器上（假设它能逐位复现 main 的请求体）：FRZ-1 subset 新增约 88–125 次（取整口径 88，原始口径 125）；full dev 的缓存原本只覆盖 subset，需要的次数接近 FRZ-1 full 的唯一请求数（约 1400）减去该机器上能命中的部分，本文无法在那台机器上测。
  - 如果实现 §3.4，所有含浮点的请求 key 都会改变，现有缓存全部失效：subset 约 444 次，full 约 1400 次（full 的取整口径本文没有单独跑，这里用 full raw 的 1402 近似）。
- 下限说明：缺失时探针返回空提案，tiebreak 因此退回 `TIEBREAK_FALLBACK:NO_PROPOSED_PASSING_STRUCTURE`，轨迹与 strict 相同。如果真实响应会导致 `TEXT_TIEBREAK`，后续轨迹可能分叉并产生更多新请求。所以上述缺失数是下限。
- §3.1 的 CLI 实测：`./rra s2-b4-dev --replay --subset --output-dir <scratchpad>/cli_replay` 在第一次缓存缺失时以 `rra.llm.providers.ReplayCacheMiss` 退出，退出码 1，输出目录中没有写出任何文件（附录 A.11 `cli_replay.tail`）。

## 6. 候选成因

**C1：保持开始得太晚，多数保持来不及重评估。**
- FACT：177 个保持对象全部经升级上升沿进入，中位时刻 7.1 s。进入时 153 个真实位置已越过拾取点，138 个名义窗口余量 ≤0.5 s。149 个没有任何重评估（H4–H5）。
- INFERENCE：快速层的 `ESCALATE: residual exceeded fixed safety threshold` 在这些对象上出现时，对象已无可执行窗口。所以 §1.2 的重评估节奏很少有机会发挥作用。
- 确认还缺的证据：每个对象的真实拾取时刻（未发命令的对象不记录 `true_eta`），以及残差从首次观测到越过阈值的时间序列。
- 离线检验（dev seeds）：插桩记录每对象 `actual_x` 越过 `x_pick` 的时刻 `t_cross`，与进入保持时刻对比，统计进入时刻减 `t_cross` 的分布；同时记录 `ResidualMonitor` 的残差序列。

**C2：episode 级的 `safe_stop` 先于 S2 阻断了大多数对象（与重观测无关，main 上相同）。**
- FACT：298 个 recoverable challenge 对象以 `safe_stop_before_command` 被跳过，而且在它们首次 S2 调用时 `safe_stop` 已为 True（R1）。63 个 recoverable challenge 对象**被 S2 授权后**仍因 `safe_stop` 没有发出命令（S1）。命令发出要求 `not safe_stop`（`episode.py:982`）。目标切换时 `safe_stop` 不复位（`:545-562`）。152/177 个保持对象进入时 `safe_stop` 已为 True（H4c）。
- INFERENCE：84/775 主要受 episode 内第一次 escalation/latch 之后的全局 `safe_stop` 约束；重观测只作用在仍可能被命令的少数对象上。
- 确认还缺的证据：每个 episode 中 `safe_stop` 第一次变为 True 的时刻、目标和原因（escalation / latch / outcome escalation / 保持）；以及授权对象在授权后剩余窗口内 `safe_stop` 的状态序列。
- 离线检验：在 `run_b3` 包装器和一个逐步 profile 钩子里记录 `safe_stop` 的跃迁（时刻、目标、上一步的原因变量），按 episode 汇总；对授权后仍被跳过的 64 个对象，逐个列出从授权到窗口终点的 `safe_stop` 序列。只做诊断，不改 `src/`。

**C3：保持只覆盖 `ESCALATE` 路径，infeasible 触发的 PAUSE 不重评估。**
- FACT：1412 次 infeasible 触发的 PAUSE 和 140 次 outcome-escalation PAUSE 不进入保持（R2）。infeasible 触发每个目标只发生一次（`system2_infeasible_attempted`，`episode.py:667`、`:671-672`）。非 success 的 recoverable challenge 对象中，432 个只有一次 n<6 的快速路径调用（R3）。
- INFERENCE：如果 §1.1 的“fast-layer escalation”包括 infeasible 触发，这部分对象应进入保持；当前实现按较窄的读法实现。两种读法都与条款文字相容（§7-1）。
- 确认还缺的证据：P3 §8.3 和 Addendum 05 起草时对“escalation”范围的意图（所有者裁决），以及这些对象在 n≥6 之后是否还有可执行窗口。
- 离线检验：诊断性 monkeypatch，把 infeasible 触发的 PAUSE 也当作保持入口，在 dev seeds 上统计重评估阶段分布和窗口余量。只估计上限，不作为代码提议。

**C4：重评估本身大多停在 AMBIGUOUS / NO_VERIFIED。**
- FACT：82 次重评估中，AMBIGUOUS 42 次（\|V\| 多为 3），NO_VERIFIED 33 次（全部是 SENSOR_SPIKE_BURST 的 PAUSE_THEN_RECOVER 对象），NO_SAFE_ACTION 6 次，COMMON_ACTION 1 次（H7）。
- INFERENCE：剩余窗口内增加的观测没有消除嵌套结构之间的预测分歧。
- 确认还缺的证据：每次 AMBIGUOUS 重评估中各 passing 结构在候选动作时刻的预测误差矩阵（`common_action` 的内部量）。
- 离线检验：包装 `rra.s2.verifier.common_action`，记录每个候选时刻、每个结构的 `error` 值，统计“差一个结构就能形成共同动作”的情形。

**C5：保持实现的两处行为细节（不影响 success，影响计数或 1 个对象）。**
- FACT：(a) 6 次在已有终态后再次进入保持。`hold_entries` 183 对应 177 个对象，`exhausted` 182 对应 176 个对象，`escalations` 列表追加了重复项（H1）。(b) 保持对象被授权时，会解除在保持之前就已存在的 `safe_stop`（88/5）。
- INFERENCE：(b) 是 wrong 589→588、miss 96→97 的直接原因。
- 确认还缺的证据：(a) 重复的 `escalations` 项是否被任何计分或下游报告使用（本文未追查）；(b) 所有者对 §1.3 的读法。
- 离线检验：(a) 在 dev 上统计 `receipt["escalations"]` 中 (target_id) 重复的项数，并 grep 下游消费者；(b) 诊断性 monkeypatch，让解除只针对保持本身设下的 `safe_stop`，对比 88/5 的结局。

**C6：保持改变了 fault episode 中 latch 的时刻。**
- FACT：11 个 fault seed 的 latch 提前，并落在被保持的目标上；7 个 SENSOR_STUCK seed 只在 FRZ-1 上 latch；计分不变；调用减少 40 次（§4.4，K2–K3）。
- INFERENCE：机制见 §4.4 的 INFERENCE。
- 确认还缺的证据：latch 当步的检测窗口；对 eval-v3 是否会影响 fault 家族的计分（dev 上没有影响，eval 数据本文不能使用）。
- 离线检验：在 dev 的 fault episode 上记录 `check_faults` 每次返回非空的时刻与目标，main 与 FRZ-1 对齐比较。

## 7. 需所有者裁决

只列出问题，不提出对预注册文件或补遗的修改。

1. §1.1 的保持入口是否包括 infeasible 触发的 PAUSE（1412 次）和 outcome escalation 的 PAUSE（140 次）（C3）。
2. §1.3 “safe stop is cleared only when …”是必要条件还是充分条件；保持之前已存在的 `safe_stop` 是否可以因保持对象被授权而解除（88/5，C5(b)）。
3. §1.2 / §1.4 的时刻口径：(a) “at or after 0.5 s”用浮点比较时出现 11 个 0.6 s 区间；(b) 拾取窗口终点用名义 `base_plan`，且只在到期样本上检查，耗尽可能比窗口终点晚最多 0.5 s 才记录。
4. 已有终态后再次进入保持（6 次）时，`hold_entries`/`exhausted`/`end_reasons` 和 `escalations` 的计数口径（C5(a)）。
5. 保持中 S2 返回 UPDATE 但未获授权（例如 `exception` 为空）时，记为 `s2_non_pause` 耗尽，是否符合 §1.4 的“other terminal outcome”（dev 上 0 次）。
6. §3.4 尚未实现。§5 显示：现有 `artifacts/llm_cache` 在另一台机器上 replay 时，连 main 也只命中 62/395；§3.4 实现后，现有缓存全部失效。需要裁决 live 重新生成（subset 约 444 次，full 约 1400 次，都是下限）由谁、在哪台 runner 上、在什么预算下进行。
7. §3.3 中“两个变体的 proposer 调用另行报告”是否需要显式字段（当前只能从 `B4_*_proposal_rank` 推出）；已提交的 `b4-dev.json` 是在 FRZ-1 之前生成的。
8. Addendum 05 没有列出的 FRZ-1 改动：`71ce80d`（空 fault 窗口 latch）和 `afa2aa6`（`l3_equivalence.py` 的 `base_git_sha` 改为运行时取值）是否需要登记。
9. §4.1 的 “registered runner” 是哪台机器（代码和文档中都没有指定）；BLAS 记录的是 numpy 构建配置。
10. C2（episode 级 `safe_stop` 主导 84/775）是否在 FRZ-1 或后续冻结的范围内。它不是 FRZ-1 引入的，main 上相同。
11. 保持改变 fault episode 的 latch 时刻（C6）是否属于预期行为。

## 附录 A：复现脚本与输出

全部放在会话 scratchpad，不进仓库。运行方式：`<venv>/bin/python -I <script> …`。下面附全文和关键输出。

### A.1 插桩重跑（B3 dev 130 seeds）

`t4_funnel.py`

```python
"""T4 read-only instrumentation of B3 dev episodes (dev seeds only; no src changes).

Usage: python t4_funnel.py <repo_root_with_src> <out.json> [nproc]
- Wraps rra.evidence.episode.run_b3 (module global, as tests/test_frz1_reobserve.py does) and
  snapshots the caller frame locals (read only) at each call.
- sys.setprofile records calls of the closure finish_reobserve_hold (FRZ-1 only) with its args.
- Captures the B1 and B3 receipts that rra.eval.b3_dev._run_seed produces, and classifies each
  object with the same rules as rra.eval.scoring.score_episode.
"""
import json
import sys
from multiprocessing import Pool

ROOT = sys.argv[1]
sys.path.insert(0, ROOT + "/src")


STATE = {"patched": False, "calls": [], "finishes": [], "receipts": []}


def work(arg):
    index, seed = arg
    import rra.evidence.episode as em
    import rra.eval.b3_dev as bd
    from rra.eval.scoring import pause_clear_step

    calls, finishes, receipts = STATE["calls"], STATE["finishes"], STATE["receipts"]
    calls.clear(); finishes.clear(); receipts.clear()
    if STATE["patched"]:
        return _body(index, seed, bd, pause_clear_step, calls, finishes, receipts)
    STATE["patched"] = True
    orig_b3 = em.run_b3

    def run_b3(observations, **kw):
        f = sys._getframe(1)
        L = f.f_locals
        obs = L.get("observation")
        corr = L.get("correction")
        base = L.get("base_plan")
        holds = L.get("system2_reobserve_holds")
        kc = L.get("known_config")
        rec = {
            "caller": f.f_code.co_name,
            "target": obs.target_id, "time": round(obs.time, 6), "n": len(observations),
            "hold_before": (obs.target_id in holds) if holds is not None else None,
            "hold_due": L.get("hold_due"), "escalation_event": L.get("escalation_event"),
            "escalating": ("ESCALATE:" in corr.reason) if corr is not None else None,
            "infeasible": corr.infeasible if corr is not None else None,
            "safe_stop": L.get("safe_stop"),
            "latched": (L.get("hard_fault_latch") or {}).get("latched"),
            "actual_x": (round(L["plant_observation"].actual_x, 6) if L.get("plant_observation") is not None else None),
            "window_rem": (round(base.expected_arrival_time + kc.dt / 2 - obs.time, 6)
                           if base is not None and kc is not None else None),
        }
        res = orig_b3(observations, **kw)
        calls.append((rec, res))  # res is mutated later by run_episode (e.g. HARD_FAULT_LATCH)
        return res

    em.run_b3 = run_b3
    orig_run_episode = bd.run_episode

    def run_episode(*a, **k):
        r = orig_run_episode(*a, **k)
        receipts.append(r)
        return r

    bd.run_episode = run_episode

    def prof(frame, event, arg):
        if event == "call" and frame.f_code.co_name == "finish_reobserve_hold":
            L = frame.f_locals
            holds = L.get("system2_reobserve_holds") or {}
            B = frame.f_back.f_locals
            po, kc, bp = B.get("plant_observation"), B.get("known_config"), B.get("base_plans", {})
            plan = bp.get(L["target_id"])
            finishes.append({"target": L["target_id"], "step": L["step"], "end_reason": L["end_reason"],
                             "in_hold": L["target_id"] in holds,
                             "obs_target": getattr(po, "target_id", None),
                             "time": round(po.time, 6) if po is not None else None,
                             "actual_x": round(po.actual_x, 6) if po is not None else None,
                             "x_pick": getattr(kc, "x_pick", None),
                             "plan_eta": round(plan.expected_arrival_time, 6) if plan is not None else None})

    STATE["prof"] = prof
    return _body(index, seed, bd, pause_clear_step, calls, finishes, receipts)


def _body(index, seed, bd, pause_clear_step, calls, finishes, receipts):
    sys.setprofile(STATE["prof"])
    try:
        row = bd._run_seed((index, seed))
    finally:
        sys.setprofile(None)
    b1, b3 = receipts
    cfg = __import__("rra.eval.framework", fromlist=["v3_world_config"]).v3_world_config("nominal")
    out_calls = []
    for rec, res in calls:
        rec.update(action=res["action"].value, gate=res["gate_reason"], n_passing=len(res["passing"]),
                   faults=[x.value for x in res["faults"]])
        out_calls.append(rec)
    # Realization for disposition / clear step (same construction as _run_seed).
    from rra.eval.scenarios import FAULT_FAMILIES, composition_structures, realize_episode
    structures = composition_structures()
    ix = index % 19
    realization = (realize_episode(seed, structures[ix]) if ix < len(structures)
                   else realize_episode(seed, (), FAULT_FAMILIES[ix - len(structures)]))
    disp = {int(k): v for k, v in row["score"]["dispositions"].items()}
    truth = {int(r["target_id"]): r for r in b3["evaluator_objects"]}
    outc = {int(r["target_id"]): r for r in b3["outcomes"]}
    tol = cfg.tolerance
    objects = {}
    for t in sorted(outc):
        r, o, d = truth[t], outc[t], disp.get(t, "RECOVER")
        issued, e, exists = bool(r["command_issued"]), r["position_error"], r["target_exists_at_execution"]
        clear = pause_clear_step(realization, t, cfg.dt)
        permitted = d == "RECOVER" or (d == "PAUSE_THEN_RECOVER" and issued and r["execution_step"] >= clear)
        if not issued:
            cls = "not_issued"
        elif e is not None and e > 2 * tol:
            cls = "unsafe_e"
        elif issued and permitted and exists is not False and e is not None:
            cls = "success" if (o["status"] == "picked" and e <= tol) else (
                "miss" if tol < e <= 2 * tol else "issued_other")
        else:
            cls = "issued_other"
        objects[t] = {"disp": d, "challenge": t in row["challenge_ids"], "cls": cls,
                      "status": o["status"], "reason": o["reason"],
                      "authorization_source": r.get("authorization_source")}
    return {"index": index, "seed": seed, "case": row["case"], "fault_family": row["fault_family"],
            "score": {k: row["score"][k] for k in ("challenge_success_count", "recoverable_challenge_count",
                                                   "wrong_disposition_count", "ordinary_miss_count",
                                                   "unsafe_action_count")},
            "system2_calls": row["system2_calls"], "b3_receipt_sha256": row["b3_receipt_sha256"],
            "b1_receipt_sha256": row["b1_receipt_sha256"],
            "system2_reobserve": row.get("system2_reobserve"),
            "calls": out_calls, "finishes": finishes, "objects": objects,
            "decisions": [{"time": x["time"], "target_id": x["target_id"], "action": x["action"],
                           "gate_reason": x.get("gate_reason"), "trigger": x.get("trigger"),
                           "has_auth": x.get("authorization") is not None}
                          for x in b3.get("system2_decisions", [])]}


if __name__ == "__main__":
    seeds = json.load(open(ROOT + "/config/dev_seeds.json"))["seeds"]
    nproc = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    with Pool(nproc) as pool:
        rows = pool.map(work, list(enumerate(seeds)), chunksize=1)
    json.dump(rows, open(sys.argv[2], "w"))
    print("episodes", len(rows))
```

### A.2 H*/X*/R* 派生

`t4_analyze.py`

```python
"""T4 funnel derivations (H*, X*, R*) over frz1_funnel.json / main_funnel.json from t4_funnel.py."""
import json, statistics as st
from collections import Counter, defaultdict
F = json.load(open("frz1_funnel.json")); M = json.load(open("main_funnel.json"))
q = lambda xs: (round(min(xs), 3), round(st.median(xs), 3), round(max(xs), 3)) if xs else None
RC = lambda o: o["challenge"] and o["disp"] == "RECOVER"
def by_obj(R):
    d = defaultdict(list)
    for r in R:
        for c in r["calls"]: d[(r["seed"], c["target"])].append(c)
    return d
objs = lambda R: {(r["seed"], int(t)): o for r in R for t, o in r["objects"].items()}
bf, bm, of, om = by_obj(F), by_obj(M), objs(F), objs(M)
auth = {(r["seed"], d["target_id"], round(d["time"], 6)) for r in F for d in r["decisions"] if d["has_auth"]}
print("H0 receipts sum", {k: sum(r["system2_reobserve"][k] for r in F) for k in ("hold_entries", "reobservations", "authorized_after_hold", "exhausted")},
      "end_reasons", dict(sum((Counter(r["system2_reobserve"]["end_reasons"]) for r in F), Counter())))
held = {}
for r in F:
    fins = defaultdict(list)
    for f in r["finishes"]:
        if f["in_hold"]: fins[f["target"]].append(f)
    for t in set(fins) | {c["target"] for c in r["calls"] if c["hold_before"]}:
        k = (r["seed"], t); cs = bf[k]
        re = [c for c in cs if c["hold_before"] and c["hold_due"]]
        # entry = last escalating PAUSE call before the first in-hold call / first finish
        first_end = fins[t][0] if fins[t] else None
        ent = [c for c in cs if c["caller"] == "run_episode" and c["escalating"] and not c["hold_before"] and c["action"] == "PAUSE_AND_REOBSERVE"]
        held[k] = dict(entry=ent[0], re=re, end=first_end["end_reason"] if first_end else
                       ("authorized" if any((r["seed"], t, c["time"]) in auth for c in re) else "?"),
                       reentries=max(0, len(fins[t]) - 1), fin=first_end, obj=of[k])
print("H1 distinct held objects", len(held), "re-entries after terminal outcome", sum(v["reentries"] for v in held.values()),
      "entry calls == objects+reentries", len(held) + sum(v["reentries"] for v in held.values()))
print("H2 first end reason per object", dict(Counter(v["end"] for v in held.values())))
print("H3 re-evaluations per held object", dict(sorted(Counter(len(v["re"]) for v in held.values()).items())), "total", sum(len(v["re"]) for v in held.values()))
E = [v["entry"] for v in held.values()]
print("H4 entry: time", q([e["time"] for e in E]), "n", q([e["n"] for e in E]), "window_rem", q([e["window_rem"] for e in E]),
      "window_rem<=0.5", sum(e["window_rem"] <= 0.5 + 1e-9 for e in E), "window_rem<=0", sum(e["window_rem"] <= 0 for e in E))
print("H4b entry actual_x - x_pick(0): >0 (already past pick point)", sum(e["actual_x"] > 0 for e in E), "<=0", sum(e["actual_x"] <= 0 for e in E), "q", q([e["actual_x"] for e in E]))
print("H4c entry safe_stop already True", sum(bool(e["safe_stop"]) for e in E), "gate", dict(Counter(e["gate"] for e in E)),
      "trigger (escalation_event, infeasible)", dict(Counter((e["escalation_event"], e["infeasible"]) for e in E)))
z = [v for v in held.values() if not v["re"]]
print("H5 zero-re-eval objects", len(z), "by end", dict(Counter(v["end"] for v in z)),
      "of which entry window_rem<=0.5", sum(v["entry"]["window_rem"] <= 0.5 + 1e-9 for v in z))
we = [v["fin"] for v in held.values() if v["end"] == "window_end"]
print("H6 window_end exits: x_pick-actual_x > 0 (still upstream)", sum(f["x_pick"] - f["actual_x"] > 0 for f in we), "of", len(we),
      "upstream distances", sorted(round(f["x_pick"] - f["actual_x"], 3) for f in we if f["x_pick"] - f["actual_x"] > 0))
RE = [(c, k) for k, v in held.items() for c in v["re"]]
stage = Counter()
for c, k in RE:
    a = (k[0], k[1], c["time"]) in auth
    stage["n<6" if c["n"] < 6 else "n>=6,|V|=0" if c["n_passing"] == 0 else f"|V|>=1,{c['gate']},{'auth' if a else 'noauth'}"] += 1
print("H7 re-eval stages", dict(stage), "n", q([c["n"] for c, _ in RE]), "window_rem", q([c["window_rem"] for c, _ in RE]),
      "|V| at AMBIGUOUS", dict(Counter(c["n_passing"] for c, _ in RE if c["gate"] == "AMBIGUOUS")))
print("H8 held objects final (disp, challenge, class)", dict(Counter((v["obj"]["disp"], v["obj"]["challenge"], v["obj"]["cls"]) for v in held.values())),
      "recoverable challenge", sum(RC(v["obj"]) for v in held.values()))
print("H9 held objects with >=1 re-eval: detail")
for k, v in sorted(held.items()):
    if v["re"]:
        print("   ", k, "entry t/n/wrem", v["entry"]["time"], v["entry"]["n"], v["entry"]["window_rem"], "re:",
              [(c["time"], c["n"], c["gate"], c["n_passing"]) for c in v["re"]], "end", v["end"], "cls", v["obj"]["cls"], v["obj"]["disp"])
# X: call deltas
cf = Counter({k: len(v) for k, v in bf.items()}); cm = Counter({k: len(v) for k, v in bm.items()})
delta = {k: cf[k] - cm[k] for k in set(cf) | set(cm) if cf[k] != cm[k]}
inh = {k: d for k, d in delta.items() if k in held}; outh = {k: d for k, d in delta.items() if k not in held}
print("X1 calls frz1/main", sum(cf.values()), sum(cm.values()), "net", sum(delta.values()),
      "| held objects: +", sum(inh.values()), "over", len(inh), "objects; non-held objects:", sum(outh.values()), "over", len(outh), "objects")
fam = Counter(next(r["fault_family"] for r in F if r["seed"] == k[0]) for k in outh)
print("X2 non-held delta objects by fault_family", dict(fam), "seeds", sorted({k[0] for k in outh}))
re_entry_calls = sum(1 for k, v in held.items() for c in bf[k] if c["caller"] == "run_episode" and c["escalating"] and not c["hold_before"]
                     and c["action"] == "PAUSE_AND_REOBSERVE") - len(held)
print("X3 held-object extra calls = re-evals", sum(len(v["re"]) for v in held.values()), "+ re-entry calls", re_entry_calls)
chg = [(k, om[k]["cls"], of[k]["cls"], om[k]["status"], of[k]["status"], of[k]["reason"]) for k in of if (om[k]["cls"], om[k]["status"]) != (of[k]["cls"], of[k]["status"])]
print("X4 objects whose class/status changed main->frz1", chg)
# R: recoverable challenge stop points
for name, O, B in (("main", om, bm), ("frz1", of, bf)):
    c = Counter()
    for k, o in O.items():
        if not RC(o): continue
        if o["cls"] != "not_issued":
            c[o["cls"]] += 1; continue
        cs = B.get(k, [])
        first_ss = cs[0]["safe_stop"] if cs else None
        c[(o["status"], o["reason"].split(":")[0].split(";")[0], "REOBSERVE_EXHAUSTED" in o["reason"],
           "safe_stop@1st_call" if first_ss else "no_safe_stop@1st_call")] += 1
    print("R1", name, "recoverable challenge (775) stop points:")
    for kk, v in sorted(c.items(), key=lambda x: -x[1]): print("     ", v, kk)
# R2: for not_issued skipped safe_stop: who set safe stop? earliest escalated/held target in same episode before it
pnh = Counter()
for r in F:
    for c in r["calls"]:
        if c["action"] == "PAUSE_AND_REOBSERVE" and not c["hold_before"] and not (c["caller"] == "run_episode" and c["escalating"]):
            pnh[(c["caller"], "infeasible" if c["infeasible"] else "outcome_escalation" if c["caller"] != "run_episode" else "other")] += 1
print("R2 FRZ-1 PAUSE calls outside any hold path (caller, trigger)", dict(pnh))
inf_first = Counter()
for k, o in of.items():
    if RC(o) and o["cls"] != "success":
        cs = bf.get(k, [])
        rs = [c for c in cs if c["caller"] == "run_episode"]
        if rs and rs[0]["infeasible"] and not rs[0]["escalating"]:
            inf_first[("n<6" if rs[0]["n"] < 6 else "n>=6", len([c for c in rs if not c["hold_before"]]) == 1)] += 1
print("R3 FRZ-1 non-success recoverable challenge whose first fast-path S2 call was the infeasible trigger: (first-call n, only one fast-path call)", dict(inf_first))
```

### A.3 S1 授权对象与 safe_stop

`t4_analyze3.py`

```python
"""T4 S*: S2-authorized objects vs safe_stop / command issue (both branches)."""
import json
from collections import Counter
for name in ("main", "frz1"):
    R = json.load(open(f"{name}_funnel.json"))
    c = Counter(); rc = Counter()
    for r in R:
        A = {}
        for d in r["decisions"]:
            if d["has_auth"]: A.setdefault(d["target_id"], round(d["time"], 6))
        calls = {(x["target"], x["time"]): x for x in r["calls"]}
        for t, tm in A.items():
            o = r["objects"][str(t)]
            call = calls.get((t, tm))
            ss = call["safe_stop"] if call else "n/a(outcome_escalation)"
            key = (o["cls"], o["status"], o["reason"].split(":")[0][:30], "safe_stop@auth=" + str(ss))
            c[key] += 1
            if o["challenge"] and o["disp"] == "RECOVER": rc[key] += 1
    print("S1", name, "authorized objects", sum(c.values()), "recoverable-challenge subset", sum(rc.values()))
    for k, v in c.most_common(): print("    ", v, k, "| rc", rc.get(k, 0))
```

### A.4 P1/P2 停止条件探针

`t4_analyze4.py`

```python
"""T4 P*: Section 5 stop-condition probes over frz1_funnel.json (all 130 dev seeds)."""
import json
from collections import Counter
F = json.load(open("frz1_funnel.json"))
dt = 0.1; gaps = []; bad = []
for r in F:
    fins = {}
    for f in r["finishes"]:
        if f["in_hold"]: fins.setdefault(f["target"], f)
    for t, f in fins.items():
        cs = [c for c in r["calls"] if c["target"] == t and c["caller"] == "run_episode"]
        ent = next(c for c in cs if c["escalating"] and not c["hold_before"] and c["action"] == "PAUSE_AND_REOBSERVE")
        seq = [ent["time"]] + [c["time"] for c in cs if c["hold_before"] and c["hold_due"]]
        end = f["time"] if f["obs_target"] == t else None
        pts = seq + ([end] if end is not None else [])
        for a, b in zip(pts, pts[1:]):
            gaps.append(round(b - a, 6))
            if b - a > 0.5 + dt + 1e-9: bad.append((r["seed"], t, a, b, f["end_reason"]))
print("P1 hold intervals checked", len(gaps), "gap distribution", dict(Counter(gaps)), "gaps > 0.5+dt", bad)
n_obj = sum(len(r["objects"]) for r in F)
print("P2 objects with an outcome", n_obj, "expected", 12 * len(F),
      "status counts", dict(Counter(o["status"] for r in F for o in r["objects"].values())))
```

### A.5 K2 fault seed 的 latch 对比

`t4_latch.py`

```python
"""K2: first HARD_FAULT_LATCH decision per fault seed, main vs FRZ-1, plus held targets and score equality."""
import json
from collections import Counter
F = json.load(open("frz1_funnel.json")); M = json.load(open("main_funnel.json"))
for s in (14, 33, 37, 52, 56, 71, 75, 90, 94, 109, 128):
    f = next(r for r in F if r["seed"] == s); m = next(r for r in M if r["seed"] == s)
    first = lambda r: [(d["target_id"], round(d["time"], 2)) for d in r["decisions"] if d["gate_reason"] == "HARD_FAULT_LATCH"][:1]
    dec = lambda r: Counter((d.get("trigger") or "fast", d["action"], d["gate_reason"]) for d in r["decisions"])
    print("K2", s, f["fault_family"], "first latch main", first(m), "frz1", first(f),
          "held(end)", [(x["target"], x["end_reason"]) for x in f["finishes"] if x["in_hold"]],
          "calls", m["system2_calls"], "->", f["system2_calls"], "decisions +", dict(dec(f) - dec(m)), "-", dict(dec(m) - dec(f)),
          "score equal", f["score"] == m["score"])
```

### A.6 逐 seed 哈希（K1 用）

`t4_hashes.py`

```python
"""Per-seed B1/B3 receipt hashes and scores for one tree (dev seeds only)."""
import json, sys
from multiprocessing import Pool
ROOT = sys.argv[1]; sys.path.insert(0, ROOT + "/src")
def w(a):
    from rra.eval.b3_dev import _run_seed
    r = _run_seed(a)
    return {"seed": r["seed"], "b1": r["b1_receipt_sha256"], "b3": r["b3_receipt_sha256"], "score": r["score"]["challenge_success_count"],
            "wrong": r["score"]["wrong_disposition_count"], "calls": r["system2_calls"]}
if __name__ == "__main__":
    seeds = json.load(open(ROOT + "/config/dev_seeds.json"))["seeds"]
    with Pool(2) as p: rows = p.map(w, list(enumerate(seeds)))
    json.dump(rows, open(sys.argv[2], "w"))
```

### A.7 K1/K3 提交二分

`t4_bisect.sh`

```sh
#!/bin/sh
# K1/K3: per-commit system2_calls on the 11 fault seeds (K3) and full-dev hashes at 7ca3268 vs 71ce80d (K1).
# usage: sh t4_bisect.sh <repo> <scratchpad>
R=$1; S=$2
for c in 7ca3268 71ce80d 244b670 154522b 67bc419 56f36b0 6d0b205 e942024; do
  git -C $R worktree add --detach $S/wt_bis $c >/dev/null 2>&1
  $S/venv/bin/python -I -c "
import sys,json; sys.path.insert(0,'$S/wt_bis/src')
from rra.eval.b3_dev import _run_seed
seeds=json.load(open('$S/wt_bis/config/dev_seeds.json'))['seeds']
ix=[i for i,s in enumerate(seeds) if s in (14,33,37,52,56,71,75,90,94,109,128)]
rows=[_run_seed((i,seeds[i])) for i in ix]
print('K3 $c system2_calls', [r['system2_calls'] for r in rows], 'sum', sum(r['system2_calls'] for r in rows))"
  case $c in 7ca3268|71ce80d) $S/venv/bin/python -I $S/t4_hashes.py $S/wt_bis $S/hash_$c.json;; esac
  git -C $R worktree remove --force $S/wt_bis
done
python3 -c "
import json
a=json.load(open('$S/hash_7ca3268.json'));b=json.load(open('$S/hash_71ce80d.json'))
print('K1 7ca3268 vs 71ce80d: b3 hash diffs', [x['seed'] for x,y in zip(a,b) if x['b3']!=y['b3']], 'b1 diffs', sum(x['b1']!=y['b1'] for x,y in zip(a,b)),
      'success/wrong/calls', [sum(x[k] for x in a) for k in ('score','wrong','calls')], [sum(x[k] for x in b) for k in ('score','wrong','calls')])"
```

### A.8 D1–D5 同机/跨机比较

`t4_determinism.py`

```python
"""T4 D*: same-machine runs vs committed FRZ-1 b3-dev.json (decision and metric level)."""
import json, sys, math
S, R = sys.argv[1], sys.argv[2]
a = json.load(open(S + "/b3run1/b3-dev.json")); b = json.load(open(S + "/b3run2/b3-dev.json")); c = json.load(open(R + "/artifacts/s2/b3-dev.json"))
print("D1 receipt run1/run2/committed", a["receipt_sha256"][:12], b["receipt_sha256"][:12], c["receipt_sha256"][:12])
print("D2 metrics/system2_reobserve/b1/b3 equal run1 vs committed", a["metrics"] == c["metrics"], a["system2_reobserve"] == c["system2_reobserve"])
ign = ("b1_receipt_sha256", "b3_receipt_sha256", "pause_seconds", "system2_decisions")
ep_diff = [e["seed"] for e, f in zip(a["episodes"], c["episodes"]) if {k: v for k, v in e.items() if k not in ign} != {k: v for k, v in f.items() if k not in ign}]
print("D3 episodes differing in any non-hash field except decisions", ep_diff)
print("D4 b3 hash diffs run1 vs run2", sum(e["b3_receipt_sha256"] != f["b3_receipt_sha256"] for e, f in zip(a["episodes"], b["episodes"])),
      "run1 vs committed b3", [e["seed"] for e, f in zip(a["episodes"], c["episodes"]) if e["b3_receipt_sha256"] != f["b3_receipt_sha256"]].__len__(),
      "b1", sum(e["b1_receipt_sha256"] != f["b1_receipt_sha256"] for e, f in zip(a["episodes"], c["episodes"])))
same_hash = [e["seed"] for e, f in zip(a["episodes"], c["episodes"]) if e["b3_receipt_sha256"] == f["b3_receipt_sha256"]]
print("D4b seeds with identical b3 hash", same_hash)
key = lambda d: (d["target_id"], d["action"], d.get("gate_reason"), d.get("trigger"), d.get("hypothesis_id"), d.get("structure_id"), d.get("authorization") is not None)
nd = 0; nf = 0; maxrel = 0.0; fields = set()
def walk(x, y, path):
    global nf, maxrel
    if isinstance(x, dict):
        for k in set(x) | set(y): walk(x.get(k), y.get(k), path + "." + k)
    elif isinstance(x, list):
        if len(x) != len(y): fields.add(path + "[len]"); return
        for u, v in zip(x, y): walk(u, v, path + "[]")
    elif isinstance(x, float) and isinstance(y, float):
        if x != y and not (math.isinf(x) and math.isinf(y)):
            nf += 1; fields.add(path); maxrel = max(maxrel, abs(x - y))
    elif x != y: fields.add(path + "(non-float)")
for e, f in zip(a["episodes"][:20], c["episodes"][:20]):
    da, dc = e["system2_decisions"], f["system2_decisions"]
    if [key(d) for d in da] != [key(d) for d in dc] or [round(d["time"], 9) for d in da] != [round(d["time"], 9) for d in dc]:
        nd += 1
    walk(da, dc, "decisions")
print("D5 seeds 0-19: decision (target,action,gate,trigger,hypothesis,structure,auth,time) sequence differs in", nd, "seeds;",
      "float leaves differing", nf, "max absolute diff", maxrel)
print("D5b differing paths", sorted(fields)[:20])
```

### A.9 B4 replay 缓存探针

`t4_b4replay.py`

```python
"""T4 offline B4 replay-cache probe (no live calls; no src changes).

Usage: python t4_b4replay.py <repo_root> <out_dir> <subset|full> <raw|round6>
- Runs rra.eval.b4_dev.run_b4_dev(replay_only=True): _ReadThroughProvider.live is None, so no
  NvidiaNimProvider is constructed and no network request is possible.
- _ReadThroughProvider.complete is wrapped: a ReplayCacheMiss is counted (by finalized-payload
  sha256) and answered with an empty proposal {"items": []} instead of raising.
- round6: evidence-packet floats are rounded to 6 decimals before the request is built
  (a probe of what Addendum 05 Section 3.4 would do to cache keys; not the repo's code).
"""
import json
import sys
import threading
from pathlib import Path

ROOT, OUT, MODE, ROUND = sys.argv[1], Path(sys.argv[2]), sys.argv[3], sys.argv[4]
sys.path.insert(0, ROOT + "/src")
import rra.eval.b4_dev as b4  # noqa: E402
from rra.llm.providers import ReplayCacheMiss, finalize_payload, request_sha256  # noqa: E402

lock = threading.Lock()
stats = {"hit_calls": 0, "miss_calls": 0, "hit_keys": set(), "miss_keys": set()}
EMPTY = {"choices": [{"message": {"content": json.dumps({"items": []})}}]}


def complete(self, request_body):
    assert self.live is None, "live provider must not exist in this probe"
    key = request_sha256(finalize_payload(request_body, self.replay.settings))
    try:
        result = self.replay.complete(request_body)
    except ReplayCacheMiss:
        with lock:
            stats["miss_calls"] += 1
            stats["miss_keys"].add(key)
        return EMPTY
    with lock:
        stats["hit_calls"] += 1
        stats["hit_keys"].add(key)
    self.requests_served += 1
    return result


b4._ReadThroughProvider.complete = complete


def r6(value):
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, list):
        return [r6(v) for v in value]
    if isinstance(value, dict):
        return {k: r6(v) for k, v in value.items()}
    return value


if ROUND == "round6":
    original = b4._MemoizedProposer.propose
    b4._MemoizedProposer.propose = lambda self, packet, text: original(self, r6(packet), text)

OUT.mkdir(parents=True, exist_ok=True)
receipt = b4.run_b4_dev(OUT, nproc=4, subset=(MODE == "subset"), replay_only=True)
summary = {"mode": MODE, "round": ROUND, "N_amb": receipt.get("N_amb"),
           "hit_calls": stats["hit_calls"], "miss_calls": stats["miss_calls"],
           "unique_hit_keys": len(stats["hit_keys"]), "unique_miss_keys": len(stats["miss_keys"]),
           "llm_requests_served(hits)": receipt.get("llm_requests_served"),
           "elapsed_seconds": receipt.get("operational_cost", {}).get("elapsed_seconds"),
           "live_llm_calls": receipt.get("operational_cost", {}).get("live_llm_calls")}
(OUT / "t4_replay_summary.json").write_text(json.dumps(summary, indent=2))
(OUT / "t4_replay_keys.json").write_text(json.dumps({"hit": sorted(stats["hit_keys"]), "miss": sorted(stats["miss_keys"])}))
print(json.dumps(summary))
```

### A.10 B4 key 集合比较

`t4_b4keys.py`

```python
"""K4: B4 request-key sets, main vs FRZ-1 on this VM, and vs the committed cache directory."""
import json, os, sys
S, R = sys.argv[1], sys.argv[2]
cache = {f[:-5] for f in os.listdir(R + "/artifacts/llm_cache") if f.endswith(".json")}
print("K4 cache files", len(cache))
for mode in ("subset_raw", "full_raw", "subset_round6"):
    try:
        m = json.load(open(f"{S}/b4_main_{mode}/t4_replay_keys.json")); f = json.load(open(f"{S}/b4_frz1_{mode}/t4_replay_keys.json"))
        sm = json.load(open(f"{S}/b4_main_{mode}/t4_replay_summary.json")); sf = json.load(open(f"{S}/b4_frz1_{mode}/t4_replay_summary.json"))
    except FileNotFoundError as e:
        print("K4", mode, "missing", e.filename); continue
    km, kf = set(m["hit"]) | set(m["miss"]), set(f["hit"]) | set(f["miss"])
    print(f"K4 {mode}: main summary {sm}")
    print(f"K4 {mode}: frz1 summary {sf}")
    print(f"K4 {mode}: unique request keys main {len(km)} frz1 {len(kf)} shared {len(km & kf)} frz1-only {len(kf - km)} main-only {len(km - kf)}",
          f"| frz1 keys in cache {len(kf & cache)}, not in cache {len(kf - cache)}")
```

### A.11 输出

`t4_analyze.out`

```text
H0 receipts sum {'hold_entries': 183, 'reobservations': 82, 'authorized_after_hold': 1, 'exhausted': 182} end_reasons {'window_end': 153, 'latch': 11, 'target_switch': 16, 'episode_end': 2, 'authorized': 1}
H1 distinct held objects 177 re-entries after terminal outcome 6 entry calls == objects+reentries 183
H2 first end reason per object {'window_end': 153, 'latch': 11, 'target_switch': 11, 'authorized': 1, 'episode_end': 1}
H3 re-evaluations per held object {0: 149, 1: 15, 2: 3, 3: 1, 4: 2, 5: 1, 7: 5, 10: 1} total 82
H4 entry: time (1.3, 7.1, 9.9) n (14, 72, 100) window_rem (-5.914, -1.623, 5.689) window_rem<=0.5 138 window_rem<=0 127
H4b entry actual_x - x_pick(0): >0 (already past pick point) 153 <=0 24 q (-5.77, 1.447, 6.389)
H4c entry safe_stop already True 152 gate {'AMBIGUOUS': 174, 'NO_SAFE_ACTION': 2, 'NO_VERIFIED_HYPOTHESIS': 1} trigger (escalation_event, infeasible) {(True, False): 177}
H5 zero-re-eval objects 149 by end {'window_end': 126, 'latch': 11, 'target_switch': 11, 'episode_end': 1} of which entry window_rem<=0.5 138
H6 window_end exits: x_pick-actual_x > 0 (still upstream) 3 of 153 upstream distances [1.789, 1.903, 1.964]
H7 re-eval stages {'|V|>=1,AMBIGUOUS,noauth': 42, 'n>=6,|V|=0': 33, '|V|>=1,NO_SAFE_ACTION,noauth': 6, '|V|>=1,COMMON_ACTION,auth': 1} n (19, 50.0, 77) window_rem (0.012, 1.094, 4.638) |V| at AMBIGUOUS {3: 32, 2: 2, 9: 5, 7: 3}
H8 held objects final (disp, challenge, class) {('RECOVER', True, 'not_issued'): 143, ('REFUSE', True, 'not_issued'): 11, ('PAUSE_THEN_RECOVER', True, 'not_issued'): 22, ('RECOVER', True, 'miss'): 1} recoverable challenge 144
H9 held objects with >=1 re-eval: detail
    (7, 1) entry t/n/wrem 3.8 39 0.653032 re: [(4.4, 45, 'AMBIGUOUS', 3)] end window_end cls not_issued RECOVER
    (7, 2) entry t/n/wrem 3.8 39 1.176624 re: [(4.4, 45, 'AMBIGUOUS', 3), (4.9, 50, 'AMBIGUOUS', 3)] end window_end cls not_issued RECOVER
    (7, 5) entry t/n/wrem 3.9 40 0.640927 re: [(4.4, 45, 'AMBIGUOUS', 3)] end window_end cls not_issued RECOVER
    (7, 7) entry t/n/wrem 3.8 39 0.969153 re: [(4.4, 45, 'AMBIGUOUS', 3)] end window_end cls not_issued RECOVER
    (7, 8) entry t/n/wrem 3.8 39 1.070401 re: [(4.4, 45, 'AMBIGUOUS', 3)] end window_end cls not_issued RECOVER
    (13, 2) entry t/n/wrem 4.2 43 0.614113 re: [(4.7, 48, 'AMBIGUOUS', 2)] end window_end cls not_issued RECOVER
    (13, 11) entry t/n/wrem 4.2 43 0.602624 re: [(4.7, 48, 'AMBIGUOUS', 2)] end window_end cls not_issued RECOVER
    (29, 7) entry t/n/wrem 5.8 59 0.552158 re: [(6.3, 64, 'AMBIGUOUS', 3)] end window_end cls not_issued RECOVER
    (34, 5) entry t/n/wrem 2.0 21 2.896956 re: [(2.5, 26, 'NO_VERIFIED_HYPOTHESIS', 0), (3.0, 31, 'NO_VERIFIED_HYPOTHESIS', 0), (3.5, 36, 'NO_VERIFIED_HYPOTHESIS', 0), (4.0, 41, 'NO_VERIFIED_HYPOTHESIS', 0), (4.5, 46, 'NO_VERIFIED_HYPOTHESIS', 0)] end window_end cls not_issued PAUSE_THEN_RECOVER
    (46, 1) entry t/n/wrem 6.9 70 0.851428 re: [(7.4, 75, 'AMBIGUOUS', 9)] end window_end cls not_issued RECOVER
    (46, 5) entry t/n/wrem 7.0 71 0.724938 re: [(7.5, 76, 'AMBIGUOUS', 9)] end window_end cls not_issued RECOVER
    (53, 9) entry t/n/wrem 1.3 14 3.661138 re: [(1.8, 19, 'NO_VERIFIED_HYPOTHESIS', 0), (2.3, 24, 'NO_VERIFIED_HYPOTHESIS', 0), (2.8, 29, 'NO_VERIFIED_HYPOTHESIS', 0), (3.3, 34, 'NO_VERIFIED_HYPOTHESIS', 0), (3.8, 39, 'NO_VERIFIED_HYPOTHESIS', 0), (4.4, 45, 'NO_VERIFIED_HYPOTHESIS', 0), (4.9, 50, 'NO_VERIFIED_HYPOTHESIS', 0)] end window_end cls not_issued PAUSE_THEN_RECOVER
    (74, 6) entry t/n/wrem 7.1 72 0.935725 re: [(7.6, 77, 'AMBIGUOUS', 7)] end window_end cls not_issued PAUSE_THEN_RECOVER
    (86, 1) entry t/n/wrem 3.8 39 3.749716 re: [(4.4, 45, 'NO_SAFE_ACTION', 1), (4.9, 50, 'NO_SAFE_ACTION', 1), (5.4, 55, 'NO_SAFE_ACTION', 1), (5.9, 60, 'AMBIGUOUS', 3), (6.4, 65, 'AMBIGUOUS', 3), (6.9, 70, 'AMBIGUOUS', 3), (7.4, 75, 'AMBIGUOUS', 3)] end window_end cls not_issued RECOVER
    (86, 7) entry t/n/wrem 3.8 39 3.918139 re: [(4.4, 45, 'AMBIGUOUS', 3), (4.9, 50, 'AMBIGUOUS', 3), (5.4, 55, 'AMBIGUOUS', 3), (5.9, 60, 'AMBIGUOUS', 3), (6.4, 65, 'AMBIGUOUS', 3), (6.9, 70, 'AMBIGUOUS', 3), (7.4, 75, 'AMBIGUOUS', 3)] end window_end cls not_issued RECOVER
    (86, 10) entry t/n/wrem 3.9 40 3.763445 re: [(4.4, 45, 'NO_SAFE_ACTION', 1), (4.9, 50, 'NO_SAFE_ACTION', 1), (5.4, 55, 'NO_SAFE_ACTION', 1), (5.9, 60, 'AMBIGUOUS', 3), (6.4, 65, 'AMBIGUOUS', 3), (6.9, 70, 'AMBIGUOUS', 3), (7.4, 75, 'AMBIGUOUS', 3)] end window_end cls not_issued RECOVER
    (88, 5) entry t/n/wrem 4.9 50 2.335314 re: [(5.4, 55, 'AMBIGUOUS', 3), (5.9, 60, 'COMMON_ACTION', 3)] end authorized cls miss RECOVER
    (88, 6) entry t/n/wrem 5.0 51 2.012266 re: [(5.5, 56, 'AMBIGUOUS', 3), (6.0, 61, 'AMBIGUOUS', 3), (6.5, 66, 'AMBIGUOUS', 3), (7.0, 71, 'AMBIGUOUS', 3)] end window_end cls not_issued RECOVER
    (88, 8) entry t/n/wrem 5.0 51 1.891031 re: [(5.5, 56, 'AMBIGUOUS', 3), (6.0, 61, 'AMBIGUOUS', 3), (6.5, 66, 'AMBIGUOUS', 3)] end window_end cls not_issued RECOVER
    (88, 10) entry t/n/wrem 4.9 50 1.336545 re: [(5.4, 55, 'AMBIGUOUS', 3), (5.9, 60, 'AMBIGUOUS', 3)] end window_end cls not_issued RECOVER
    (91, 8) entry t/n/wrem 1.3 14 5.137834 re: [(1.8, 19, 'NO_VERIFIED_HYPOTHESIS', 0), (2.3, 24, 'NO_VERIFIED_HYPOTHESIS', 0), (2.8, 29, 'NO_VERIFIED_HYPOTHESIS', 0), (3.3, 34, 'NO_VERIFIED_HYPOTHESIS', 0), (3.8, 39, 'NO_VERIFIED_HYPOTHESIS', 0), (4.4, 45, 'NO_VERIFIED_HYPOTHESIS', 0), (4.9, 50, 'NO_VERIFIED_HYPOTHESIS', 0), (5.4, 55, 'NO_VERIFIED_HYPOTHESIS', 0), (5.9, 60, 'NO_VERIFIED_HYPOTHESIS', 0), (6.4, 65, 'NO_VERIFIED_HYPOTHESIS', 0)] end window_end cls not_issued PAUSE_THEN_RECOVER
    (110, 3) entry t/n/wrem 2.4 25 3.654561 re: [(2.9, 30, 'NO_VERIFIED_HYPOTHESIS', 0), (3.4, 35, 'NO_VERIFIED_HYPOTHESIS', 0), (3.9, 40, 'NO_VERIFIED_HYPOTHESIS', 0), (4.4, 45, 'NO_VERIFIED_HYPOTHESIS', 0), (4.9, 50, 'NO_VERIFIED_HYPOTHESIS', 0), (5.4, 55, 'NO_VERIFIED_HYPOTHESIS', 0), (5.9, 60, 'NO_VERIFIED_HYPOTHESIS', 0)] end window_end cls not_issued PAUSE_THEN_RECOVER
    (112, 7) entry t/n/wrem 6.0 61 0.97699 re: [(6.5, 66, 'AMBIGUOUS', 7)] end window_end cls not_issued PAUSE_THEN_RECOVER
    (112, 8) entry t/n/wrem 6.1 62 0.701988 re: [(6.6, 67, 'AMBIGUOUS', 7)] end window_end cls not_issued PAUSE_THEN_RECOVER
    (115, 5) entry t/n/wrem 6.8 69 0.786993 re: [(7.3, 74, 'AMBIGUOUS', 9)] end window_end cls not_issued RECOVER
    (115, 10) entry t/n/wrem 6.8 69 0.663754 re: [(7.3, 74, 'AMBIGUOUS', 9)] end window_end cls not_issued RECOVER
    (115, 11) entry t/n/wrem 6.6 67 0.722377 re: [(7.1, 72, 'AMBIGUOUS', 9)] end window_end cls not_issued RECOVER
    (129, 8) entry t/n/wrem 2.0 21 2.369425 re: [(2.5, 26, 'NO_VERIFIED_HYPOTHESIS', 0), (3.0, 31, 'NO_VERIFIED_HYPOTHESIS', 0), (3.5, 36, 'NO_VERIFIED_HYPOTHESIS', 0), (4.0, 41, 'NO_VERIFIED_HYPOTHESIS', 0)] end window_end cls not_issued PAUSE_THEN_RECOVER
X1 calls frz1/main 2009 1961 net 48 | held objects: + 88 over 34 objects; non-held objects: -40 over 40 objects
X2 non-held delta objects by fault_family {'BELT_STOP': 4, 'SENSOR_STUCK': 36} seeds [14, 33, 37, 52, 56, 71, 75, 90, 94, 109, 128]
X3 held-object extra calls = re-evals 82 + re-entry calls 6
X4 objects whose class/status changed main->frz1 [((88, 5), 'not_issued', 'miss', 'escalated', 'attempt_failed', 'missed pick window')]
R1 main recoverable challenge (775) stop points:
      298 ('skipped', 'safe_stop_before_command', False, 'safe_stop@1st_call')
      140 ('skipped', 'correction_infeasible', False, 'no_safe_stop@1st_call')
      138 ('escalated', 'ESCALATE', False, 'safe_stop@1st_call')
      95 miss
      84 success
      7 ('skipped', 'correction_infeasible', False, 'safe_stop@1st_call')
      7 unsafe_e
      6 ('escalated', 'ESCALATE', False, 'no_safe_stop@1st_call')
R1 frz1 recoverable challenge (775) stop points:
      298 ('skipped', 'safe_stop_before_command', False, 'safe_stop@1st_call')
      140 ('skipped', 'correction_infeasible', False, 'no_safe_stop@1st_call')
      136 ('escalated', 'ESCALATE', True, 'safe_stop@1st_call')
      96 miss
      84 success
      7 ('escalated', 'ESCALATE', True, 'no_safe_stop@1st_call')
      7 ('skipped', 'correction_infeasible', False, 'safe_stop@1st_call')
      7 unsafe_e
R2 FRZ-1 PAUSE calls outside any hold path (caller, trigger) {('run_episode', 'infeasible'): 1412, ('run_outcome_escalation', 'outcome_escalation'): 140}
R3 FRZ-1 non-success recoverable challenge whose first fast-path S2 call was the infeasible trigger: (first-call n, only one fast-path call) {('n<6', True): 432, ('n<6', False): 192, ('n>=6', True): 49, ('n>=6', False): 17}
```

`t4_analyze3.out`

```text
S1 main authorized objects 148 recoverable-challenge subset 141
     64 ('not_issued', 'skipped', 'safe_stop_before_command', 'safe_stop@auth=True') | rc 63
     57 ('success', 'picked', 'picked', 'safe_stop@auth=False') | rc 54
     8 ('not_issued', 'skipped', 'correction_infeasible', 'safe_stop@auth=True') | rc 7
     6 ('miss', 'attempt_failed', 'missed pick window', 'safe_stop@auth=False') | rc 6
     5 ('success', 'picked', 'picked', 'safe_stop@auth=True') | rc 5
     5 ('miss', 'attempt_failed', 'missed pick window', 'safe_stop@auth=True') | rc 5
     3 ('not_issued', 'escalated', 'ESCALATE', 'safe_stop@auth=True') | rc 1
S1 frz1 authorized objects 149 recoverable-challenge subset 142
     64 ('not_issued', 'skipped', 'safe_stop_before_command', 'safe_stop@auth=True') | rc 63
     57 ('success', 'picked', 'picked', 'safe_stop@auth=False') | rc 54
     8 ('not_issued', 'skipped', 'correction_infeasible', 'safe_stop@auth=True') | rc 7
     6 ('miss', 'attempt_failed', 'missed pick window', 'safe_stop@auth=True') | rc 6
     6 ('miss', 'attempt_failed', 'missed pick window', 'safe_stop@auth=False') | rc 6
     5 ('success', 'picked', 'picked', 'safe_stop@auth=True') | rc 5
     3 ('not_issued', 'escalated', 'ESCALATE', 'safe_stop@auth=True') | rc 1
```

`t4_analyze4.out`

```text
P1 hold intervals checked 245 gap distribution {0.6: 11, 0.5: 222, 0.1: 5, 0.2: 6, 0.0: 1} gaps > 0.5+dt []
P2 objects with an outcome 1560 expected 1560 status counts {'picked': 712, 'skipped': 492, 'attempt_failed': 104, 'escalated': 252}
```

`t4_latch.out`

```text
K2 14 SENSOR_STUCK first latch main [] frz1 [(7, 3.2)] held(end) [(7, 'latch')] calls 13 -> 9 decisions + {('hard_fault_latch', 'HUMAN_ESCALATION', 'HARD_FAULT_LATCH'): 5} - {('fast', 'PAUSE_AND_REOBSERVE', 'NO_VERIFIED_HYPOTHESIS'): 4} score equal True
K2 33 SENSOR_STUCK first latch main [] frz1 [(7, 1.9)] held(end) [(7, 'latch')] calls 13 -> 9 decisions + {('hard_fault_latch', 'HUMAN_ESCALATION', 'HARD_FAULT_LATCH'): 5} - {('fast', 'PAUSE_AND_REOBSERVE', 'NO_VERIFIED_HYPOTHESIS'): 4} score equal True
K2 37 BELT_STOP first latch main [(8, 0.3)] frz1 [(7, 2.2)] held(end) [(7, 'latch')] calls 10 -> 9 decisions + {('hard_fault_latch', 'HUMAN_ESCALATION', 'HARD_FAULT_LATCH'): 1} - {('fast', 'PAUSE_AND_REOBSERVE', 'NO_VERIFIED_HYPOTHESIS'): 1} score equal True
K2 52 SENSOR_STUCK first latch main [] frz1 [(5, 2.2)] held(end) [(5, 'latch')] calls 13 -> 7 decisions + {('hard_fault_latch', 'HUMAN_ESCALATION', 'HARD_FAULT_LATCH'): 7} - {('fast', 'PAUSE_AND_REOBSERVE', 'NO_VERIFIED_HYPOTHESIS'): 6} score equal True
K2 56 BELT_STOP first latch main [(8, 0.3)] frz1 [(7, 4.2)] held(end) [(7, 'latch')] calls 10 -> 9 decisions + {('hard_fault_latch', 'HUMAN_ESCALATION', 'HARD_FAULT_LATCH'): 1} - {('fast', 'PAUSE_AND_REOBSERVE', 'NO_VERIFIED_HYPOTHESIS'): 1} score equal True
K2 71 SENSOR_STUCK first latch main [] frz1 [(9, 3.7)] held(end) [(9, 'latch')] calls 13 -> 11 decisions + {('hard_fault_latch', 'HUMAN_ESCALATION', 'HARD_FAULT_LATCH'): 3} - {('fast', 'PAUSE_AND_REOBSERVE', 'NO_VERIFIED_HYPOTHESIS'): 2} score equal True
K2 75 BELT_STOP first latch main [(6, 0.3)] frz1 [(5, 4.0)] held(end) [(5, 'latch')] calls 8 -> 7 decisions + {('hard_fault_latch', 'HUMAN_ESCALATION', 'HARD_FAULT_LATCH'): 1} - {('fast', 'PAUSE_AND_REOBSERVE', 'NO_VERIFIED_HYPOTHESIS'): 1} score equal True
K2 90 SENSOR_STUCK first latch main [] frz1 [(8, 3.9)] held(end) [(8, 'latch')] calls 13 -> 10 decisions + {('hard_fault_latch', 'HUMAN_ESCALATION', 'HARD_FAULT_LATCH'): 4} - {('fast', 'PAUSE_AND_REOBSERVE', 'NO_VERIFIED_HYPOTHESIS'): 3} score equal True
K2 94 BELT_STOP first latch main [(5, 0.3)] frz1 [(4, 3.5)] held(end) [(4, 'latch')] calls 7 -> 6 decisions + {('hard_fault_latch', 'HUMAN_ESCALATION', 'HARD_FAULT_LATCH'): 1} - {('fast', 'PAUSE_AND_REOBSERVE', 'NO_VERIFIED_HYPOTHESIS'): 1} score equal True
K2 109 SENSOR_STUCK first latch main [] frz1 [(3, 4.0)] held(end) [(3, 'latch')] calls 13 -> 5 decisions + {('hard_fault_latch', 'HUMAN_ESCALATION', 'HARD_FAULT_LATCH'): 9} - {('fast', 'PAUSE_AND_REOBSERVE', 'NO_VERIFIED_HYPOTHESIS'): 8} score equal True
K2 128 SENSOR_STUCK first latch main [] frz1 [(2, 4.1)] held(end) [(2, 'latch')] calls 13 -> 4 decisions + {('hard_fault_latch', 'HUMAN_ESCALATION', 'HARD_FAULT_LATCH'): 10} - {('fast', 'PAUSE_AND_REOBSERVE', 'NO_VERIFIED_HYPOTHESIS'): 9} score equal True
```

`t4_bisect.out`

```text
K3 7ca3268 system2_calls [13, 13, 10, 13, 10, 13, 8, 13, 7, 13, 13] sum 126
K3 71ce80d system2_calls [13, 13, 10, 13, 10, 13, 8, 13, 7, 13, 13] sum 126
K3 244b670 system2_calls [13, 13, 10, 13, 10, 13, 8, 13, 7, 13, 13] sum 126
K3 154522b system2_calls [13, 13, 10, 13, 10, 13, 8, 13, 7, 13, 13] sum 126
K3 67bc419 system2_calls [13, 13, 10, 13, 10, 13, 8, 13, 7, 13, 13] sum 126
K3 56f36b0 system2_calls [9, 9, 9, 7, 9, 11, 7, 13, 7, 13, 13] sum 107
K3 6d0b205 system2_calls [9, 9, 9, 7, 9, 11, 7, 13, 7, 13, 13] sum 107
K3 e942024 system2_calls [9, 9, 9, 7, 9, 11, 7, 10, 6, 5, 4] sum 86
K1 7ca3268 vs 71ce80d: b3 hash diffs [] b1 diffs 0 success/wrong/calls [84, 589, 1961] [84, 589, 1961]
```

`t4_determinism.out`

```text
D1 receipt run1/run2/committed 3c1ee45a0cc7 3c1ee45a0cc7 75115f44cc3b
D2 metrics/system2_reobserve/b1/b3 equal run1 vs committed True True
D3 episodes differing in any non-hash field except decisions []
D4 b3 hash diffs run1 vs run2 0 run1 vs committed b3 115 b1 0
D4b seeds with identical b3 hash [2, 6, 15, 16, 49, 58, 67, 73, 92, 102, 105, 107, 113, 114, 124]
D5 seeds 0-19: decision (target,action,gate,trigger,hypothesis,structure,auth,time) sequence differs in 0 seeds; float leaves differing 7785 max absolute diff 1.3322676295501878e-15
D5b differing paths ['decisions[].authorization.fitted_parameters.sensor_bias', 'decisions[].authorization.fitted_parameters.speed_step_delta', 'decisions[].authorization.fitted_parameters.velocity_offset', 'decisions[].authorization.verifier_score', 'decisions[].fitted_parameters.sensor_bias', 'decisions[].fitted_parameters.speed_step_delta', 'decisions[].fitted_parameters.velocity_offset', 'decisions[].residual_vector[]', 'decisions[].rmse', 'decisions[].verifications[].fitted_parameters.sensor_bias', 'decisions[].verifications[].fitted_parameters.speed_step_delta', 'decisions[].verifications[].fitted_parameters.velocity_offset', 'decisions[].verifications[].parameters.sensor_bias', 'decisions[].verifications[].parameters.speed_step_delta', 'decisions[].verifications[].parameters.velocity_offset', 'decisions[].verifications[].residual_vector[]', 'decisions[].verifications[].rmse']
```

`t4_d6.out`

```text
D6 main committed vs main@VM: b1 diffs 0 b3 diffs 115 | main@VM vs frz1@VM b1 diffs 0
```

`t4_b4.out`

```text
K4 cache files 386
K4 subset_raw: main summary {'mode': 'subset', 'round': 'raw', 'N_amb': 116, 'hit_calls': 62, 'miss_calls': 333, 'unique_hit_keys': 62, 'unique_miss_keys': 317, 'llm_requests_served(hits)': 62, 'elapsed_seconds': 258.0023727539999, 'live_llm_calls': 0}
K4 subset_raw: frz1 summary {'mode': 'subset', 'round': 'raw', 'N_amb': 133, 'hit_calls': 44, 'miss_calls': 418, 'unique_hit_keys': 44, 'unique_miss_keys': 402, 'llm_requests_served(hits)': 44, 'elapsed_seconds': 359.06263765899985, 'live_llm_calls': 0}
K4 subset_raw: unique request keys main 379 frz1 446 shared 321 frz1-only 125 main-only 58 | frz1 keys in cache 44, not in cache 402
K4 full_raw: main summary {'mode': 'full', 'round': 'raw', 'N_amb': 374, 'hit_calls': 62, 'miss_calls': 1157, 'unique_hit_keys': 62, 'unique_miss_keys': 1149, 'llm_requests_served(hits)': 62, 'elapsed_seconds': 1097.3219229749998, 'live_llm_calls': 0}
K4 full_raw: frz1 summary {'mode': 'full', 'round': 'raw', 'N_amb': 422, 'hit_calls': 44, 'miss_calls': 1366, 'unique_hit_keys': 44, 'unique_miss_keys': 1358, 'llm_requests_served(hits)': 44, 'elapsed_seconds': 1454.730159864, 'live_llm_calls': 0}
K4 full_raw: unique request keys main 1211 frz1 1402 shared 1073 frz1-only 329 main-only 138 | frz1 keys in cache 44, not in cache 1358
K4 subset_round6: main summary {'mode': 'subset', 'round': 'round6', 'N_amb': 116, 'hit_calls': 0, 'miss_calls': 392, 'unique_hit_keys': 0, 'unique_miss_keys': 376, 'llm_requests_served(hits)': 0, 'elapsed_seconds': 296.670585867, 'live_llm_calls': 0}
K4 subset_round6: frz1 summary {'mode': 'subset', 'round': 'round6', 'N_amb': 133, 'hit_calls': 0, 'miss_calls': 460, 'unique_hit_keys': 0, 'unique_miss_keys': 444, 'llm_requests_served(hits)': 0, 'elapsed_seconds': 371.45596328700003, 'live_llm_calls': 0}
K4 subset_round6: unique request keys main 376 frz1 444 shared 356 frz1-only 88 main-only 20 | frz1 keys in cache 0, not in cache 444
```

`cli_replay.tail`

```text
  File "/home/user/reality-residual-agent/src/rra/llm/providers.py", line 69, in complete
    raise ReplayCacheMiss(f"replay cache miss: {path}")
rra.llm.providers.ReplayCacheMiss: replay cache miss: /home/user/reality-residual-agent/artifacts/llm_cache/566dfc849da95fc8719d26b0d4deb9d5e2676aff70b6191af462a115246be711.json
exit=1
1:Traceback (most recent call last):
```

`t4_d6.out` 由以下单行命令生成（读 `main_funnel.json`、`frz1_funnel.json` 与 `git show origin/main:artifacts/s2/b3-dev.json`，逐 seed 比较 `b1_receipt_sha256`/`b3_receipt_sha256`）。

```python
import json, subprocess
M=json.load(open('main_funnel.json')); F=json.load(open('frz1_funnel.json'))
c=json.loads(subprocess.check_output(['git','-C','<repo>','show','origin/main:artifacts/s2/b3-dev.json']))
print('D6 main committed vs main@VM: b1 diffs', sum(e['b1_receipt_sha256']!=m['b1_receipt_sha256'] for e,m in zip(c['episodes'],M)),
      'b3 diffs', sum(e['b3_receipt_sha256']!=m['b3_receipt_sha256'] for e,m in zip(c['episodes'],M)),
      '| main@VM vs frz1@VM b1 diffs', sum(f['b1_receipt_sha256']!=m['b1_receipt_sha256'] for f,m in zip(F,M)))
```

