# 失败模式说明（草稿）/ Failure Modes (Draft)

状态 / Status：**DRAFT / 未经所有者审阅 / 不是提交内容 / not reviewed by the owner / not a submission**。

先中文，后英文，内容一致。/ Chinese first, then English; same content.

---

# 中文

## 0. 元信息与记号

- 起草基线：`main` 头 `520b7cfdf13b805c9258ab06c79a658ee62aef8b`（与任务书核对值一致）。本文只新增本文件与 `DRAFT_SUBMISSION_v3.md`，不修改任何已有文件。
- 输入（本文所有数字都转录自它们；本会话没有重跑任何代码，也没有打开 `config/eval_seeds*.json`）：
  - **T1** = `docs/_review/T1_pr20_review.md` @ `cloud/t1-pr20-review` `1baed167a4545cf0df0a5960ca56287411a88d27`（对 PR #20 的审查，评审时 head `c852566db1e10d4e267eb32f3a8f3912d9685db7`）。
  - **T3** = `docs/_diag/T3_failure_funnel.md` @ `cloud/t3-failure-funnel` `b8f0e104fbc62e3495f8371cec9ba4b5588b647e`（基线 `54f5006`）。
  - **T4** = `docs/_review/T4_frz1_review.md` @ `cloud/t4-frz1-review` `550cdc6464ba6c4825a2eab3d23b577b84a9a26a`，sha256 `f5a89ee6423d6ec27969e4f3ce4fe4980ac6c4b709e0405ce3a08b07f22365d0`（对 `feat/frz1-b3core` `cb771079c1c119d73d0ebd0e24704a1935731cea` 的审查；该分支未合并）。
  - **A04** = `docs/P3_PREREG_ADDENDUM_04.md`；**A05** = `docs/P3_PREREG_ADDENDUM_05.md`；**FM** = 根目录 `FAILURE_MODES.md`（V0 快速层失败模式，本文不改动，也不重复）。
  - 出处写法：`T4 §4.6 (R1)` 表示 T4 第 4.6 节，括号内为 T4 附录脚本的派生行前缀（Hk/Rk/Sk/Xk/Kk/Dk）；`T3 §1.2a (R4)` 同理。
- **dev 标注**：本文每个数字都来自 dev 数据（`config/dev_seeds.json`，130 个 dev seed，或其 33 个 seed 的诊断子集），一律视为"dev，非注册结果"。每条现象末尾重复标注。
- **eval-v3**：种子未生成也未被查看；凡涉及 eval-v3 结果或 B4 效果之处一律写"待 eval-v3，尚无结果"。[来源: A05 Trigger 段；T4 头部]
- **FACT / INFERENCE**：FACT 可直接从代码行、已提交文件字段或复现脚本输出读到；INFERENCE 是由 FACT 推出的解释，附"确认还缺的证据"。仓库里找不到出处的写 [UNKNOWN]。
- **所有者裁决（2026-10-24，已定）**：R1 保持入口取窄读法（只有快速层 ESCALATE 路径上的 PAUSE 进入保持）；R2 §1.3 维持 FRZ-1 现状，88/5 在提交材料中披露；R3 episode 级 `safe_stop` 主导 84/775 不在本次冻结范围内，作为失败模式披露；R4 注册 runner 为所有者本地机器（Intel i7-10750H，Python 3.12.3，NumPy 2.5.4，scipy-openblas 0.3.34）；R5 §3.4 由所有者本地实现，B4 缓存在注册 runner 上 live 重建。
- 合并状态：Addendum 05 在 main；其实现分支 `feat/frz1-b3core` **未合并**。下文"FRZ-1"的行为描述指该分支。
- 本文不使用结论性措辞；每节的最终对外表态句留 [所有者裁决]。
- 未完成项：无因预算中止的项。

### 0.1 FRZ-1 与 main 的 dev 总计数（供各节引用）

| 量 | main | FRZ-1（未合并） | 出处 |
|---|---:|---:|---|
| recoverable challenge success / recoverable challenge | 84 / 775 | 84 / 775 | T4 §4.6 (R1)；T3 §1.1 |
| wrong_disposition | 589 | 588 | T4 §0（插桩一致性）；T3 §1.1 |
| ordinary miss | 96 | 97 | 同上 |
| unsafe_action | 7 | 7 | 同上 |
| `system2_calls` | 1961 | 2009 | 同上 |

以上均为 dev，非注册结果。

---

## A. episode 级 `safe_stop` 主导可恢复挑战（T4 C2，R3）

**现象**（dev，非注册结果）
- 775 个 recoverable challenge 对象中，298 个以 `safe_stop_before_command` 被跳过，且在它们首次 S2 调用时 `safe_stop` 已为 True；main 与 FRZ-1 均为 298。[来源: T4 §4.6 (R1)]
- 另有 63 个 recoverable challenge 对象**被 S2 授权之后**仍因 `safe_stop` 没有发出命令（授权后被跳过的共 64 个，且授权当时 `safe_stop` 已为 True）。[来源: T4 §4.6 补充 (S1)]
- 177 个进入保持的对象中，152 个进入时 `safe_stop` 已为 True。[来源: T4 §4.1 (H4c)]
- 成功数 84/775，main 与 FRZ-1 相同。[来源: T4 §4.6 (R1)]

**机制**
- FACT：命令发出要求 `not safe_stop`（`episode.py:982`）；目标切换时 `safe_stop` 不复位（`:545-562`）。[来源: T4 §6 C2]
- INFERENCE：84/775 主要受 episode 内第一次 escalation/latch 之后的全局 `safe_stop` 约束；重观测只作用在仍可能被命令的少数对象上。
- 确认还缺的证据：每个 episode 中 `safe_stop` 第一次变为 True 的时刻、目标和原因；授权对象在授权后剩余窗口内 `safe_stop` 的状态序列。[来源: T4 §6 C2]

**我们怎么发现的**：T4 对 `feat/frz1-b3core`（头 `cb77107`）的离线插桩重跑（`cloud/t4-frz1-review`，`550cdc6`），对 130 个 dev seed 与 main 对照；该模式在 main 上相同，不是 FRZ-1 引入。T4 §7 第 10 项把它列为需所有者裁决。

**当前处置**：**按裁决披露不修**（R3：不在本次冻结范围内）。最终表态句：[所有者裁决]

**可迁移教训**：episode 级的全局 fail-closed 开关会把一次早期升级变成对其后所有对象的耦合；只报成功率会看不到对象在哪一步被拦下。建议同时报告"逐对象停在哪里"的漏斗，并记录该开关第一次置位的时刻、目标和原因。

---

## B. 快速层升级出现太晚，保持来不及重评估（T4 C1）

**现象**（dev，非注册结果）
- 177 个保持对象全部经升级上升沿进入，进入时刻中位 7.1 s（范围 1.3–9.9 s），中位 n_usable 72。[来源: T4 §4.1 (H4)]
- 进入时 153/177 个对象的真实位置已越过拾取点；138 个名义窗口余量 ≤0.5 s，127 个余量 ≤0。[来源: T4 §4.1 (H4、H4b)]
- 149 个保持对象没有任何重评估；有重评估的共 82 次，分布在 28 个对象上。[来源: T4 §4.1 (H3、H5)；§4.5]
- 全部 177 个保持对象是 challenge 对象；其中 recoverable challenge 144 个，success 0 个。[来源: T4 §4.3 (H8)]

**机制**
- FACT：保持开始的时刻就是快速层第一次出现 `ESCALATE` 上升沿的时刻（上列分布）。
- INFERENCE：`ESCALATE: residual exceeded fixed safety threshold` 在这些对象上出现时，对象已无可执行窗口，所以 A05 §1.2 的 0.5 s 重评估节奏很少有机会发挥作用。
- 确认还缺的证据：每个对象的真实拾取时刻（未发命令的对象不记录 `true_eta`），以及残差从首次观测到越过阈值的时间序列。[来源: T4 §6 C1]

**我们怎么发现的**：T4 离线重跑（`550cdc6`）的保持漏斗。

**当前处置**：**已有补遗并已在 FRZ-1 分支实现（未合并）**：A05 §1 的保持机制；它不改变升级本身出现的时刻，上列数字是该机制实现后的 dev 观测。是否另行处理升级时机：**已登记待修**（T4 C1 的离线检验设计未执行）。最终表态句：[所有者裁决]

**可迁移教训**：给"升级后再观测"加一个重评估机制，不等于对象还有可用窗口；要在上游测量"触发时刻相对可执行窗口"的分布，而不是只看重评估次数。

---

## C. 观测少于 6 个时就调用 System-2，PAUSE 后不重观测（T3 C3）及 Addendum 05 的处置

**现象**（dev，非注册结果）
- main 基线，33 个 dev seed 的诊断子集（`diag-d1g.json`）：498 次 S2 调用中 352 次 n_usable<6；323/396 个对象只被调用一次；272 个对象的所有调用都 n<6，这些对象末次调用时 `window_remaining_time` 最小 2.208 s、中位 5.831 s、最大 8.154 s；按末次调用归类，157 个 wrong_disposition 中 87 个属于 n<6。[来源: T3 §1.2a (R4、R5)；§1.3]
- 全 dev 前 20 个 seed：285 次调用中 NO_VERIFIED_HYPOTHESIS 为 210 次。[来源: T3 C3 (R1)]
- FRZ-1，130 个 dev seed：82 次重评估的 n_usable 在 19–77 之间，n<6 的重评估为 0 次。[来源: T4 §4.2 (H7)]
- FRZ-1：1412 次 infeasible 触发的 PAUSE 和 140 次 outcome escalation 的 PAUSE 不进入保持；非 success 的 recoverable challenge 对象中，首次快速路径调用是 infeasible 触发且 n<6、之后再没有快速路径调用的有 432 个。[来源: T4 §4.6 补充 (R2、R3)；§6 C3]

**机制**
- FACT：S2 只在新的升级上升沿或尚未尝试过的 infeasible 事件上进入；`system2_next_retry` 只是下限，不主动安排复查（main `episode.py:619-621, 744-746`，T3 视图）。verifier 要求 n≥6 且 RMSE≤0.030。[来源: T3 C1、C3；§0]
- INFERENCE：触发早（infeasible 事件在 t≈0.2 s 出现）而 PAUSE 之后没有定时重观测，所以对象在还有数秒窗口时停在"样本不足"。并列解释：快速层在 PAUSE 之后自行命令或跳过了目标，终态先于复查到来；T3 未逐对象核对。[来源: T3 C3]
- 确认还缺的证据：逐对象"PAUSE 时刻 → 终态时刻 → 期间是否出现过升级上升沿"的时间线。

**我们怎么发现的**：T3 失败漏斗（`cloud/t3-failure-funnel`，`b8f0e10`）；T3 §5 第 3 项把"PAUSE 之后是否应按时复查"交所有者裁决；A05 的触发段即由此类诊断写成（2026-10-24，build window 内、eval-v3 种子生成之前）。T4 对 FRZ-1 的 §1.1–1.5 逐条对照给出实现状态。

**当前处置**：**已有补遗（A05 §1.1–1.5）并已在 FRZ-1 实现（未合并）**，入口范围按 **R1 取窄读法**：只有快速层 ESCALATE 路径上的 PAUSE 进入保持（T4 §7-1 的两种读法之一）。窄读法之外的 infeasible 触发 PAUSE（1412 次）和 outcome escalation PAUSE（140 次）不进入保持，**按裁决披露不修**。T4 另记：§1.4 的 `;REOBSERVE_EXHAUSTED` 在 6 次"已有终态后再次进入保持"上计数口径未定、窗口终点用名义计划且只在到期样本上检查（T4 §1 表 §1.4；§7-3、§7-4）。最终表态句：[所有者裁决]

**可迁移教训**：用"样本数不足"当门限时，触发时机和重试机制必须一起设计：早触发 + 无定时复查，会把大量对象停在门限之下。给每个入口（升级、不可行、结果升级）分别说明是否进入再观测，并披露未覆盖的入口。

---

## D. 嵌套结构 AMBIGUOUS（T3 C4、T4 C4）

**现象**（dev，非注册结果）
- main 基线，33 个 dev seed 子集：n≥6 的 146 次调用全部 |V|≥1，其中 116 次 AMBIGUOUS、30 次 COMMON_ACTION；AMBIGUOUS 时 |V| 为 3–14，33 次是全部 14 个结构都被验证器放行；非 fault episode 的 114 次 AMBIGUOUS 中，真实结构在 V 里的有 111 次；按末次调用归类，157 个 wrong_disposition 中 64 个属于 AMBIGUOUS。[来源: T3 §1.2a (R4、R5)；§1.3；C4]
- `ambiguous_cases[].all_passing_models_are_supersets` 为 True 的只有 30/307（d1-before）和 30/327（d1-after）。[来源: T3 C4（`diag-d1-before.json`、`diag-d1-after.json`）]
- FRZ-1，130 个 dev seed：82 次重评估中 AMBIGUOUS 42 次（|V| 分布 3:32、2:2、9:5、7:3）、NO_VERIFIED 33 次（全部来自 5 个 SENSOR_SPIKE_BURST episode 的 PAUSE_THEN_RECOVER 对象）、NO_SAFE_ACTION 6 次、COMMON_ACTION 1 次。[来源: T4 §4.2 (H7、H9)]

**机制**
- FACT：common-action 要求所有放行假设在同一时刻的预测误差都 ≤0.20（`verifier.py:37-43`）。
- INFERENCE：短时段观测下，含 SPEED_STEP 或 VELOCITY_OFFSET 的超集模型和不含它们的模型残差都在 0.030 以内，但外推到拾取时刻时分歧超过 0.20，gate 停在 AMBIGUOUS；重观测增加的样本没有消除嵌套结构之间的预测分歧（T4 C4）。
- 并列解释：(i) 识别性不足；(ii) RMSE 阈值 0.030 相对噪声偏宽。已提交数据无法区分。T3 另记：`ambiguous_cases[].predicted_position_spread_world_units` 的公式含 `− sensor_bias`，与 `668fe22` 之后的 `prediction.py` 不一致，该列数值不代表当前预测口径。
- 确认还缺的证据：AMBIGUOUS 调用时各放行假设在候选时刻网格上的逐一误差 `error(h,t)`，以及噪声水平。[来源: T3 C4；T4 §6 C4]

**我们怎么发现的**：T3 C4（`b8f0e10`）与 T4 C4（`550cdc6`）两份诊断各自独立给出；两者的离线检验设计均未执行。

**当前处置**：**已登记待修**（候选成因，无补遗，未改代码）。B4 的文本择一正是为此类 AMBIGUOUS 设计，但其效果：**待 eval-v3，尚无结果**。最终表态句：[所有者裁决]

**可迁移教训**：当候选模型族是嵌套的，"每个模型都拟合得过关"并不意味着动作已定；应记录候选动作时刻上各模型的预测分歧，而不是只记录放行个数。

---

## E. replay 缓存缺失被静默降级为 PROVIDER_ERROR 并退出 0（T1 第 2 条）→ A05 §3.1 → FRZ-1 修复

**现象**（dev，非注册结果）
- T1 在 PR #20 head `c852566` 上跑 `rra s2-b4-dev --replay --subset`（33 个 dev seed）：退出 0 并写出回执；`llm_calls` 62 对比已提交工件的 376；tiebreak 侧提议错误 PROVIDER_ERROR 316、INVALID_PROPOSAL 44、无错 16（已提交工件为 INVALID_PROPOSAL 309、无错 64、PROVIDER_ERROR 5）。[来源: T1 §4]
- 同一命令不带 `--subset`（130 个 dev seed，520 个 episode）：退出 0；`llm_calls` 62；PROVIDER_ERROR 1148、INVALID_PROPOSAL 44、无错 16；缓存只覆盖子集 seed，所以子集之外每次生成器调用都是缓存缺失。[来源: T1 §4]
- T4 在 FRZ-1 头上以只读 replay 探针离线评估：main 代码 replay 子集，命中调用 62、缺失调用 333；FRZ-1 命中 44、缺失 418。[来源: T4 §5 表 (K4)]
- T4 对 FRZ-1 的 CLI 实测：`./rra s2-b4-dev --replay --subset` 在第一次缓存缺失时以 `ReplayCacheMiss` 退出，退出码 1，输出目录中没有写出任何文件。[来源: T4 §5 末条（附录 A.11）]

**机制**
- FACT：适配器 `adapter.py:106-108` 捕获 `OSError`；`ReplayCacheMiss` 继承 `FileNotFoundError`（`providers.py:51`），因此被转成 `Proposal.error`，在 `episode.py:676-691` 标为 `PROVIDER_ERROR` → `TIEBREAK_FALLBACK:PROVIDER_ERROR`，进程退出 0。[来源: T1 §2 表规则 1；§4]
- FACT：A04 §3 规则 1 把"replay-cache miss"列为不可用提议并回退；A04 §4 要求注册 B4 结果由冻结缓存生成且两次连续生成回执一致。两者在 replay 模式下如何并存，T1 交所有者判断（T1 末节第 2 项）。
- FACT（FRZ-1）：`adapter.py:108-109` 的 `except ReplayCacheMiss: raise` 位于 `OSError` 捕获之前；`b4_dev.py:46-48` 在 `live is None` 时重新抛出。[来源: T4 §1 表 §3.1]
- 缺口（FACT）：没有端到端测试覆盖 `rra s2-b4-dev --replay` 缺失时的退出码，只有适配器层测试 `test_adapter_propagates_replay_cache_miss`；回执中没有可供审计的"缺失回退计数"字段（T4 §1 表 §3.1、§5-3）。

**我们怎么发现的**：T1 对 PR #20 的审查（`cloud/t1-pr20-review`，`1baed16`）第 2 条所有者事项；A05 触发段引用同一行为（`adapter.py:106`）；T4（`550cdc6`）核对 FRZ-1 实现。FRZ-1 中对应提交为 `244b670`（"Propagate replay cache misses from the adapter"）。

**当前处置**：**已修复并有补遗**：A05 §3.1；实现在 FRZ-1 分支（未合并）。上述端到端缺口按 T4 §1.1 第 7 项登记。最终表态句：[所有者裁决]

**可迁移教训**：回放路径遇到缺失记录必须失败并让退出码反映出来，而不是降级成"提议错误"后产出看似完整的回执；同时在回执里计数降级次数，使审计可以发现。

---

## F. 跨机器 receipt 哈希差异（115/130，末位浮点与网格平局翻转）→ A05 §2、§4（确定性范围）

**现象**（dev，非注册结果）
- A05 触发段：另一台机器、同 Python 与 NumPy 版本时，130 个逐 seed B3 receipt 哈希中 115 个不同，metrics 与所查决策相同。[来源: A05 Trigger 段]
- T3 复跑（main 基线，云 VM）：`metrics` 全部相同；逐 seed `b1_receipt_sha256` 130/130 相同；逐 seed `b3_receipt_sha256` 115/130 不同；前 20 个 seed 的决策 action/gate_reason/common_action_time 0 处不同；最后一位浮点差在 5441 处 residual 分量与 176 处 rmse 等（量级 1e-17）；`speed_step_time` 在 0.05 s 网格上取到相邻格 8 处，全部在 AMBIGUOUS 调用中、n=7–10、两侧 `passed` 都为 True。[来源: T3 §6]
- T4 在 FRZ-1 头上：同机两次运行 `receipt_sha256` 相同，逐 seed 0/130 不同；对已提交 FRZ-1 `b3-dev.json`，逐 seed B3 哈希 115/130 不同（哈希相同的是 seed 2、6、15、16、49、58、67、73、92、102、105、107、113、114、124），B1 哈希 0/130 不同；metrics、`system2_reobserve`、各 episode 的计分字段相同；前 20 个 seed 的决策序列相同，但有 7785 个浮点叶子不同、最大绝对差 1.33e-15，字段为拟合参数、`rmse`、`residual_vector`、`verifier_score` 的末位，不含网格值。main 同样是 115/130。[来源: T4 §3 (D1–D5b)]
- T1 在 PR #20 上另见：已提交的 `b3-dev.json` 与 `b4-dev.json` 的 B3 哈希在云 VM 上不能复现（B1 哈希能），原因 [UNKNOWN]。[来源: T1 §0]
- T4 §5：在云 VM 上，main 代码按原样 replay 子集也只命中 62 次调用，唯一缺失 317 个；T4 明确该数字混合"跨机器"与"FRZ-1 改动"两种来源。T4 云 VM 为 Intel Xeon，已提交 `b3-dev.json` 记录的是 i7-10750H。[来源: T4 头部；§5]

**机制**
- INFERENCE（T3 §6）：最小二乘在不同机器上最后一位浮点的差别，以及由此引起的网格 argmin 平局翻转；在复跑中这些差别没有传到任何决策或 metrics。T4 在带平局规则的 FRZ-1 上观察到的差异字段不含网格值（FACT，T4 §3）。
- FACT：证据包放原始浮点（`episode.py:692-705`），`adapter.py:79-82` 直接 `json.dumps`，B4 请求体和缓存键因此依赖末位浮点（T4 §1 表 §3.4）。T1 将 B3 哈希差异与缓存键差异的联系列为 [UNKNOWN]。

**我们怎么发现的**：T3 §6 的复跑对照（`b8f0e10`）；T1 §0（`1baed16`）；T4 §3、§5（`550cdc6`）。

**当前处置**：
- 网格平局（A05 §2）：**已有补遗**；FRZ-1 已实现（`67bc419`，未合并），T4 记有测试缺口（actuator-delay 一维与二维平局无测试）。
- 确定性范围（A05 §4）：**已有补遗**，为范围声明——不声称跨机器逐位一致，跨机器只在决策与 metrics 层比较；**R4**：注册 runner 为所有者本地机器（Intel i7-10750H，Python 3.12.3，NumPy 2.5.4，scipy-openblas 0.3.34）。FRZ-1 记录平台（`154522b`），T4 记 BLAS 取自 NumPy 构建配置而非运行时加载的库。
- A05 §3.4（浮点按 6 位小数序列化）：FRZ-1 上 **未找到**（T4 §1）；**R5**：由所有者本地实现，B4 缓存在注册 runner 上 live 重建。实现后效果：待 eval-v3，尚无结果。T4 §5 估计的 live 重新生成次数是下限（subset 约 444、full 约 1400，见 T4 §5）。
- 最终表态句：[所有者裁决]

**可迁移教训**：浮点最小二乘 + 离散网格 argmin 会在机器之间翻转平局；回执哈希只在登记的同一 runner 上有意义。跨机器复现应在决策与指标层比较，并列出逐 seed 的差异；凡进入缓存键的浮点要先取整。

---

## G. 缩减版证据包（A04 §5.3）

**现象**
- A04 §5.3：2026-10-23 的 dev 运行（commit `92e2b89`）发送的是缩减版证据包（观测仅 time/observed_x/nominal_x；反馈仅 issued_time/execution_time/accepted/success；无在场事件；已知配置仅 dt 与 tolerance），不符合 Addendum 03 §2 第 4 项，被记为须在实现候选冻结前更正的实现缺陷；该次运行的结果不构成注册证据包下 B4 的证据。[来源: A04 §5.3]
- T1 §5 逐字段对照：缺 `target_id`、`step`、`observed_y`、`nominal_y`、`nominal_speed`，整个在场事件组，`x_pick`、`y_pick`、`belt_speed`，`command_id`、`target_id`、`reason_code`；另有白名单之外的 `passing`、`current_time`、`horizon`。T1 读 `c852566` 的代码确认（未检视存储的请求）该时点的证据包仍是缩减形式。[来源: T1 §5]
- 相关披露：该次运行的 386 条缓存响应中，71 条解析为 `{items:[...]}`，310 条解析为 JSON 但形状不符，5 条因 token 上限停止；多数 B4-tiebreak 调用以 INVALID_PROPOSAL 回退（dev，非注册结果）。[来源: A04 §5.1、§5.2]

**机制**：形式上请求体是证据包与文本上下文的确定函数（A04 §1.3），内容上未达注册包（T1 §1）。**修复状态：[UNKNOWN，待 T6 核对]**（T1 的观察止于 `c852566`；T4 的 FRZ-1 的 12 个提交范围内未就此项下结论）。

**我们怎么发现的**：A04 §5.3 自述（2026-10-23）；T1 §5（`1baed16`）逐字段确认。

**当前处置**：已登记（A04 §5.3）；修复状态 [UNKNOWN，待 T6 核对]。附带未核对项：B4 回执未记录模型标识与请求模板 SHA-256（A04 §5.4 要求；T1 §6），其现状同样待核对。最终表态句：[所有者裁决]

**可迁移教训**：把送给模型的输入对照注册的白名单逐字段审计，并在回执里记录请求模板哈希与模型标识；格式失败（本例 310/386）会淹没文本上下文的任何效应，须预先登记报告规则（A04 §6.2）。

---

## H. 88/5 的 `safe_stop` 解除行为（R2）

**现象**（dev，非注册结果）
- 保持期间目标被授权的唯一一次是 seed 88 的 target 5：`safe_stop` 在 t=0.2 已为 True，t=5.9 授权后被解除，随后发出命令；结局 `attempt_failed`（`missed pick window`），计分为 miss。[来源: T4 §1 表 §1.3；§4.2 (H9)；§4.5 (X4)]
- 它是 main→FRZ-1 之间唯一改变 class/status 的对象：main 上为 escalated（not issued，wrong_disposition）；恰好解释 wrong 589→588、miss 96→97。[来源: T4 §4.5 (X4)]
- 授权数：保持后授权（`authorized_after_hold`）1 次。[来源: T4 §4.1 (H0)]

**机制**
- FACT：实现把"无保持且无 latch"当作解除 `safe_stop` 的**充分**条件（`episode.py:879-885`）；保持开始前由别的目标设下的 `safe_stop` 也会因此被解除。该分支没有测试。[来源: T4 §1 表 §1.3；§1.1 第 1 项]
- INFERENCE：这是 wrong 589→588、miss 96→97 的直接原因（T4 C5(b)）。
- 确认还缺的证据：A05 §1.3 "cleared only when…" 是必要条件还是充分条件的读法——**所有者已于 2026-10-24 裁决（R2）维持 FRZ-1 现状**。[来源: T4 §7-2]
- 相关但不同的对象：T3 C2 中 88/1 由快速层命令，T3 推测与同 episode 的 88/0 被 S2 授权后没有置位 `safe_stop` 有关（INFERENCE，另有并列解释）。[来源: T3 C2]

**我们怎么发现的**：T4 保持后授权的逐对象追踪（`550cdc6`）。

**当前处置**：**按裁决披露不修**（R2：不改代码；88/5 在提交材料中披露）。最终表态句：[所有者裁决]

**可迁移教训**：授权解除全局停止的规则，需要说明是否会解除"由别的原因设下的停止"；没有测试的分支，在 dev 上也可能恰好被一个对象触发并改变指标。

---

## I. 已提交 B3 历史中的早期授权与 sensor_bias 重复扣除（T3 C5、C6）——历史，已不在当前 unsafe 中

**现象**（dev，非注册结果）
- `1cc7d07` 版 `b3-dev.json`：unsafe 8 个，全部 `s2_authorized`（`unsafe-traces-d1d.json`）。A 组 5 个（24/1、26/2、30/2、116/1、119/1）：t=0.5、n_usable=6 授权，选中枚举顺序第一个结构 h00 = SENSOR_BIAS，evaluator position_error 0.431、0.753、0.799、0.446、1.127。B 组 3 个（48/0、48/1、88/0）：授权在 t=5.0–5.2、n=51–53，所选结构 SB+SS，position_error 0.401、0.460、0.713，所选模型 bias 拟合值 0.450、0.449、0.343。[来源: T3 §2.2 (R7)]
- 当前 `b3-dev.json` 的 unsafe 为 7 个，`unsafe_action_by_source` 为 fast_layer_command 7、s2_authorized 0；这 8 个对象不在其中（88/0 现为 miss）。[来源: T3 §1.1、§2.2]
- 提交演进：s2 来源 unsafe：`1cc7d07` 8 → `48116ad` 9 → `cdd6e59` 4 → `dbebe35` 0。[来源: T3 §3.2]

**机制**
- FACT：A 组每个对象只有一次 S2 调用，样本数恰好 6（下限）；`episode.py:690` 用 `next(...)` 取枚举顺序里第一个满足容差的假设。[来源: T3 C5]
- INFERENCE（C5）：A 组离开 unsafe 集是因为 `cdd6e59` 要求授权带非空 `temporary_policy_exception` 而被挡住，不是预测被纠正；只要出现需要 exception 的早期 UPDATE，"6 个样本、选第一个结构"路径仍可达。并列解释：A 组误差也可能主要来自 t=0.5 之后才发生的阶跃或速度偏移（只对 48/0、88/0 算过 `step_after_decision`）。
- INFERENCE（C6）：`668fe22` 删除了预测中的 `− sensor_bias`；B 组误差量级与 bias 相当，与"bias 被当作物理位移重复扣除"相符；88/0 的余量与 0.266 s 执行延迟同号同量级，并列解释是所选模型没有包含 ACTUATOR_DELAY。
- 确认还缺的证据：A 组真实 `speed_step_time` 与授权时刻的比较；`1cc7d07` 与 `668fe22` 两版下逐项分解预测误差。

**我们怎么发现的**：T3 §2.2、§3.1、§3.2、C5、C6（`b8f0e10`），对照 `1cc7d07` 版 `unsafe-traces-d1d.json` 与后续提交（`668fe22`、`cdd6e59`、`dbebe35`）。

**当前处置**：历史记录；Addendum 04/05 均未就此立条。C5 路径是否仍可达：已登记待修（离线检验设计未执行）。FRZ-1 是否改变该路径：[UNKNOWN]（T4 未就此项下结论）。最终表态句：[所有者裁决]

**可迁移教训**：授权所依据的样本数下限应显式登记，并记录"同一决策点上被放行的结构有几个、选哪个"；修复若来自新增的门（而不是纠正预测），应单独标注，避免被读成预测变好。

---

## J. 补充：当前 7 个 unsafe 均为快速层命令（T3 §2.1、C1）

此节不在任务书的最低清单内，但属于当前 dev 数字；列出以免只披露历史。

**现象**（dev，非注册结果）
- `b3-dev.json` 的 7 个 unsafe 全部为 `fast_layer_command`，全部在含 ACTUATOR_DELAY 的 case：46/0、51/1、88/1、103/1、106/0、106/1、106/2。其中 6 个（46/0、51/1、103/1、106/0-2）所在 episode 的 B1 与 B3 终态计数相同，B1 unsafe 数相同；每个对象只有一次 S2 调用（t=0.2–0.3，n=3–4，NO_VERIFIED_HYPOTHESIS → PAUSE）。FRZ-1 的 unsafe 同为 7。[来源: T3 §2.1；T4 §0]
- B1-corrected unsafe 43 → B3 7；43 中 37 个在 FAULT:OBJECT_MISSING，6 个在含 ACTUATOR_DELAY 的组合。[来源: T3 §2.3]

**机制**：INFERENCE：沿袭 B1 的快速层命令；未建模的执行延迟与命令时刻偏晚共同造成超过 2×tolerance 的误差（两成分比重因对象而异）。确认还缺的证据：B1 逐目标 unsafe id 与 evaluator 行。[来源: T3 C1]

**我们怎么发现的**：T3 §2（`b8f0e10`）。**当前处置**：已登记，无补遗，R1–R5 未涉及；是否披露与如何表态：[所有者裁决]。**可迁移教训**：未建模的执行延迟在"更晚的命令"上会放大；按来源拆分 unsafe 才能看出哪些来自推理层、哪些来自沿用的快速层。

---

# English

## 0. Metadata and notation

- Drafting baseline: `main` head `520b7cfdf13b805c9258ab06c79a658ee62aef8b` (matches the value in the task). This change adds only this file and `DRAFT_SUBMISSION_v3.md`; no existing file is modified.
- Inputs (every number below is transcribed from them; this session re-ran no code and did not open `config/eval_seeds*.json`):
  - **T1** = `docs/_review/T1_pr20_review.md` @ `cloud/t1-pr20-review` `1baed167a4545cf0df0a5960ca56287411a88d27` (review of PR #20; head at review time `c852566db1e10d4e267eb32f3a8f3912d9685db7`).
  - **T3** = `docs/_diag/T3_failure_funnel.md` @ `cloud/t3-failure-funnel` `b8f0e104fbc62e3495f8371cec9ba4b5588b647e` (baseline `54f5006`).
  - **T4** = `docs/_review/T4_frz1_review.md` @ `cloud/t4-frz1-review` `550cdc6464ba6c4825a2eab3d23b577b84a9a26a`, sha256 `f5a89ee6423d6ec27969e4f3ce4fe4980ac6c4b709e0405ce3a08b07f22365d0` (review of `feat/frz1-b3core` `cb771079c1c119d73d0ebd0e24704a1935731cea`, which is not merged).
  - **A04** = `docs/P3_PREREG_ADDENDUM_04.md`; **A05** = `docs/P3_PREREG_ADDENDUM_05.md`; **FM** = root `FAILURE_MODES.md` (V0 fast-layer failure modes; neither modified nor repeated here).
  - Citation form: `T4 §4.6 (R1)` means section 4.6 of T4, with the derivation-line prefix of T4's appendix scripts in parentheses (Hk/Rk/Sk/Xk/Kk/Dk); `T3 §1.2a (R4)` likewise.
- **dev tag**: every number here comes from dev data (`config/dev_seeds.json`, 130 dev seeds, or its 33-seed diagnostic subset) and is "dev, not a registered result". The tag is repeated at the end of each Phenomenon block.
- **eval-v3**: seed values were neither generated nor inspected; wherever an eval-v3 result or a B4 effect would appear, this document says "pending eval-v3, no result yet". [source: A05 Trigger paragraph; T4 header]
- **FACT / INFERENCE**: a FACT can be read directly from a code line, a committed file field, or a reproduction-script output; an INFERENCE is an explanation derived from FACTs, with the "evidence still missing". Anything without a source in the repository is marked [UNKNOWN].
- **Owner rulings (2026-10-24, decided)**: R1 hold entry takes the narrow reading (only a PAUSE on the fast-layer ESCALATE path enters the hold); R2 §1.3 stays as in FRZ-1, 88/5 is disclosed in the submission material; R3 episode-level `safe_stop` dominance of 84/775 is outside this freeze and is disclosed as a failure mode; R4 the registered runner is the owner's local machine (Intel i7-10750H, Python 3.12.3, NumPy 2.5.4, scipy-openblas 0.3.34); R5 §3.4 is implemented locally by the owner and the B4 cache is rebuilt live on the registered runner.
- Merge state: Addendum 05 is on main; its implementation branch `feat/frz1-b3core` is **not merged**. "FRZ-1" below means that branch.
- No conclusory wording is used; the final outward-facing statement of each section is left as [所有者裁决 / owner decision].
- Unfinished items: none aborted by budget.

### 0.1 Aggregate dev counts for main and FRZ-1 (referenced below)

| Quantity | main | FRZ-1 (unmerged) | Source |
|---|---:|---:|---|
| recoverable-challenge success / recoverable challenges | 84 / 775 | 84 / 775 | T4 §4.6 (R1); T3 §1.1 |
| wrong_disposition | 589 | 588 | T4 §0 (instrumentation consistency); T3 §1.1 |
| ordinary miss | 96 | 97 | same |
| unsafe_action | 7 | 7 | same |
| `system2_calls` | 1961 | 2009 | same |

All dev, not registered results.

---

## A. Episode-level `safe_stop` dominates recoverable challenges (T4 C2, R3)

**Phenomenon** (dev, not a registered result)
- Of 775 recoverable-challenge objects, 298 were skipped as `safe_stop_before_command`, with `safe_stop` already True at their first S2 call; 298 on both main and FRZ-1. [source: T4 §4.6 (R1)]
- A further 63 recoverable-challenge objects issued no command because of `safe_stop` **after S2 had authorized them** (64 authorized-then-skipped in total, `safe_stop` already True at authorization). [source: T4 §4.6 supplement (S1)]
- Of 177 objects that entered the hold, 152 had `safe_stop` already True on entry. [source: T4 §4.1 (H4c)]
- Success 84/775, identical on main and FRZ-1. [source: T4 §4.6 (R1)]

**Mechanism**
- FACT: issuing a command requires `not safe_stop` (`episode.py:982`); `safe_stop` is not reset on target switch (`:545-562`). [source: T4 §6 C2]
- INFERENCE: 84/775 is mainly bounded by the episode-wide `safe_stop` after the first escalation/latch; re-observation acts only on the few objects that can still be commanded.
- Evidence still missing: for each episode, when, on which target, and for what reason `safe_stop` first became True; the `safe_stop` state sequence between authorization and window end for authorized objects. [source: T4 §6 C2]

**How we found it**: T4's offline instrumented re-run of `feat/frz1-b3core` (head `cb77107`; branch `cloud/t4-frz1-review`, `550cdc6`) over the 130 dev seeds, compared with main. The mode is identical on main, so FRZ-1 did not introduce it. T4 §7 item 10 lists it as an owner decision.

**Current disposition**: **disclosed, not fixed, per owner ruling** (R3: outside this freeze). Final statement: [owner decision]

**Transferable lesson**: a global fail-closed switch at episode level couples one early escalation to every later object; a success rate alone hides where objects were stopped. Report a per-object stop-point funnel as well, and record when, on which target, and why the switch was first set.

---

## B. Fast-layer escalation arrives too late for the hold to re-evaluate (T4 C1)

**Phenomenon** (dev, not a registered result)
- All 177 held objects entered on an escalation rising edge; median entry time 7.1 s (range 1.3–9.9 s), median n_usable 72. [source: T4 §4.1 (H4)]
- At entry, 153/177 objects were already past the pick point in true position; 138 had a nominal window margin ≤0.5 s, and 127 a margin ≤0. [source: T4 §4.1 (H4, H4b)]
- 149 held objects had no re-evaluation at all; the 82 re-evaluations fall on 28 objects. [source: T4 §4.1 (H3, H5); §4.5]
- All 177 held objects are challenge objects; 144 are recoverable challenges, of which 0 are successes. [source: T4 §4.3 (H8)]

**Mechanism**
- FACT: the hold begins at the moment of the first `ESCALATE` rising edge in the fast layer (distribution above).
- INFERENCE: when `ESCALATE: residual exceeded fixed safety threshold` fires on these objects, no executable window is left, so the 0.5 s re-evaluation cadence of A05 §1.2 rarely gets a chance to act.
- Evidence still missing: the true pick time of each object (objects with no command record no `true_eta`), and the residual time series from first observation to the threshold crossing. [source: T4 §6 C1]

**How we found it**: T4's hold funnel from the offline re-run (`550cdc6`).

**Current disposition**: **covered by an addendum and implemented on the FRZ-1 branch (unmerged)**: the hold mechanism of A05 §1. It does not change when escalation itself occurs; the numbers above are dev observations after that mechanism. Whether escalation timing is addressed separately: **registered, to be fixed** (T4's offline check design for C1 was not executed). Final statement: [owner decision]

**Transferable lesson**: adding a re-evaluation loop after "escalate and re-observe" does not mean the object still has a usable window; measure upstream where the trigger falls relative to the executable window, not only how many re-evaluations ran.

---

## C. System-2 invoked with fewer than 6 observations, no re-observation after PAUSE (T3 C3), and the Addendum 05 treatment

**Phenomenon** (dev, not a registered result)
- main baseline, 33-seed dev diagnostic subset (`diag-d1g.json`): of 498 S2 calls, 352 had n_usable<6; 323/396 objects were called once; 272 objects had every call at n<6, and at their last call `window_remaining_time` was min 2.208 s, median 5.831 s, max 8.154 s; classified by last call, 87 of 157 wrong_disposition objects belong to n<6. [source: T3 §1.2a (R4, R5); §1.3]
- First 20 dev seeds: 210 of 285 calls were NO_VERIFIED_HYPOTHESIS. [source: T3 C3 (R1)]
- FRZ-1, 130 dev seeds: the 82 re-evaluations had n_usable between 19 and 77; re-evaluations at n<6: 0. [source: T4 §4.2 (H7)]
- FRZ-1: 1412 PAUSE calls triggered by infeasibility and 140 PAUSE calls from outcome escalation do not enter the hold; among non-success recoverable-challenge objects, 432 had a first fast-path call triggered by infeasibility at n<6 and no later fast-path call. [source: T4 §4.6 supplement (R2, R3); §6 C3]

**Mechanism**
- FACT: S2 is entered only on a new escalation rising edge or on an infeasible event not yet attempted; `system2_next_retry` is only a lower bound and schedules no re-check (main `episode.py:619-621, 744-746`, as read by T3). The verifier requires n≥6 and RMSE≤0.030. [source: T3 C1, C3; §0]
- INFERENCE: the trigger is early (the infeasible event appears at t≈0.2 s) and there is no timed re-observation after PAUSE, so objects sit below the sample threshold with seconds of window remaining. Parallel explanation: the fast layer commanded or skipped the target after PAUSE, so a terminal state arrived before any re-check; T3 did not check this per object. [source: T3 C3]
- Evidence still missing: a per-object timeline "PAUSE time → terminal time → any escalation rising edge in between".

**How we found it**: T3 failure funnel (`cloud/t3-failure-funnel`, `b8f0e10`); T3 §5 item 3 hands "should a paused target be re-checked on time" to the owner; the A05 Trigger paragraph was written from diagnostics of this kind (2026-10-24, inside the build window, before eval-v3 seeds exist). T4 gives the clause-by-clause implementation state of §1.1–1.5 on FRZ-1.

**Current disposition**: **covered by an addendum (A05 §1.1–1.5) and implemented on FRZ-1 (unmerged)**, with entry scope under **R1, the narrow reading**: only a PAUSE on the fast-layer ESCALATE path enters the hold (one of the two readings in T4 §7-1). Outside the narrow reading, infeasible-triggered PAUSE (1412) and outcome-escalation PAUSE (140) do not enter the hold and are **disclosed, not fixed, per owner ruling**. T4 also records that the counting basis for the 6 "re-entry after a terminal outcome" cases is undecided, and that the §1.4 window end uses the nominal plan and is checked only on due samples (T4 §1 table §1.4; §7-3, §7-4). Final statement: [owner decision]

**Transferable lesson**: when a sample-count gate is used as a threshold, the trigger timing and the retry mechanism must be designed together; an early trigger with no timed re-check leaves many objects below the gate. State for each entry point (escalation, infeasibility, outcome escalation) whether it enters re-observation, and disclose the uncovered ones.

---

## D. Nested-structure AMBIGUOUS (T3 C4, T4 C4)

**Phenomenon** (dev, not a registered result)
- main baseline, 33-seed subset: all 146 calls with n≥6 have |V|≥1, of which 116 are AMBIGUOUS and 30 COMMON_ACTION; |V| at AMBIGUOUS is 3–14, with all 14 structures released by the verifier in 33 calls; of 114 AMBIGUOUS calls in non-fault episodes, the true structure is in V in 111; classified by last call, 64 of 157 wrong_disposition objects belong to AMBIGUOUS. [source: T3 §1.2a (R4, R5); §1.3; C4]
- `ambiguous_cases[].all_passing_models_are_supersets` is True in only 30/307 (d1-before) and 30/327 (d1-after). [source: T3 C4 (`diag-d1-before.json`, `diag-d1-after.json`)]
- FRZ-1, 130 dev seeds: of the 82 re-evaluations, AMBIGUOUS 42 (|V| distribution 3:32, 2:2, 9:5, 7:3), NO_VERIFIED 33 (all from PAUSE_THEN_RECOVER objects in 5 SENSOR_SPIKE_BURST episodes), NO_SAFE_ACTION 6, COMMON_ACTION 1. [source: T4 §4.2 (H7, H9)]

**Mechanism**
- FACT: common-action requires every released hypothesis to have prediction error ≤0.20 at the same time (`verifier.py:37-43`).
- INFERENCE: with short observations, superset models (with SPEED_STEP or VELOCITY_OFFSET) and models without them both have residual within 0.030 but diverge by more than 0.20 when extrapolated to the pick time, so the gate stays AMBIGUOUS; the extra samples from re-observation did not remove the prediction divergence between nested structures (T4 C4).
- Parallel explanations: (i) insufficient identifiability; (ii) the 0.030 RMSE threshold is wide relative to the noise. Committed data cannot tell them apart. T3 also notes that the formula behind `ambiguous_cases[].predicted_position_spread_world_units` contains `− sensor_bias`, inconsistent with `prediction.py` after `668fe22`, so that column does not represent the current prediction.
- Evidence still missing: per-hypothesis errors `error(h,t)` on the candidate-time grid at AMBIGUOUS calls, and the noise level. [source: T3 C4; T4 §6 C4]

**How we found it**: T3 C4 (`b8f0e10`) and T4 C4 (`550cdc6`) each reached it independently; neither's offline check design was executed.

**Current disposition**: **registered, to be fixed** (candidate cause; no addendum; code unchanged). B4's text tie-break is designed for exactly this kind of AMBIGUOUS, but its effect is **pending eval-v3, no result yet**. Final statement: [owner decision]

**Transferable lesson**: when the candidate models are nested, "every model fits well enough" does not fix the action; record the prediction disagreement between models at the candidate action time, not only how many were released.

---

## E. Replay-cache miss silently degraded to PROVIDER_ERROR with exit 0 (T1 item 2) → A05 §3.1 → FRZ-1 fix

**Phenomenon** (dev, not a registered result)
- T1 ran `rra s2-b4-dev --replay --subset` (33 dev seeds) on PR #20 head `c852566`: exit 0 and a receipt written; `llm_calls` 62 versus 376 in the committed artifact; tiebreak-side proposal errors PROVIDER_ERROR 316, INVALID_PROPOSAL 44, no error 16 (committed artifact: INVALID_PROPOSAL 309, no error 64, PROVIDER_ERROR 5). [source: T1 §4]
- Same command without `--subset` (130 dev seeds, 520 episodes): exit 0; `llm_calls` 62; PROVIDER_ERROR 1148, INVALID_PROPOSAL 44, no error 16; the cache covers only the subset seeds, so outside the subset every generator call is a cache miss. [source: T1 §4]
- T4, offline with a read-only replay probe on the FRZ-1 head: main code replaying the subset gives 62 hit calls and 333 miss calls; FRZ-1 gives 44 and 418. [source: T4 §5 table (K4)]
- T4's CLI check on FRZ-1: `./rra s2-b4-dev --replay --subset` exits on the first cache miss with `ReplayCacheMiss`, exit code 1, and no file is written to the output directory. [source: T4 §5 last item (appendix A.11)]

**Mechanism**
- FACT: the adapter at `adapter.py:106-108` catches `OSError`; `ReplayCacheMiss` subclasses `FileNotFoundError` (`providers.py:51`), so it becomes `Proposal.error`, is labelled `PROVIDER_ERROR` at `episode.py:676-691` → `TIEBREAK_FALLBACK:PROVIDER_ERROR`, and the process exits 0. [source: T1 §2 table rule 1; §4]
- FACT: A04 §3 rule 1 lists "replay-cache miss" among unusable proposals that fall back; A04 §4 requires registered B4 results to be generated from a frozen cache with two consecutive generations giving identical receipts. How the two coexist in replay mode is left to the owner by T1 (T1 last section, item 2).
- FACT (FRZ-1): `adapter.py:108-109` has `except ReplayCacheMiss: raise` before the `OSError` catch; `b4_dev.py:46-48` re-raises when `live is None`. [source: T4 §1 table §3.1]
- Gap (FACT): no end-to-end test covers the exit code of `rra s2-b4-dev --replay` on a miss, only the adapter-level `test_adapter_propagates_replay_cache_miss`; the receipt has no auditable "miss-fallback count" field (T4 §1 table §3.1, §5-3).

**How we found it**: T1's review of PR #20 (`cloud/t1-pr20-review`, `1baed16`), owner item 2; the A05 Trigger paragraph cites the same behaviour (`adapter.py:106`); T4 (`550cdc6`) checked the FRZ-1 implementation. The corresponding FRZ-1 commit is `244b670` ("Propagate replay cache misses from the adapter").

**Current disposition**: **fixed and covered by an addendum**: A05 §3.1; the implementation is on the FRZ-1 branch (unmerged). The end-to-end test gap above is registered as T4 §1.1 item 7. Final statement: [owner decision]

**Transferable lesson**: a replay path that meets a missing record must fail and let the exit code show it, rather than degrade to a "proposal error" and emit a receipt that looks complete; also count the degradations in the receipt so an audit can find them.

---

## F. Cross-machine receipt-hash differences (115/130; last-bit floating point and grid-tie flips) → A05 §2, §4 (determinism scope)

**Phenomenon** (dev, not a registered result)
- A05 Trigger paragraph: on another machine with the same Python and NumPy versions, 115 of 130 per-seed B3 receipt hashes differed, while metrics and the decisions checked were the same. [source: A05 Trigger paragraph]
- T3 re-run (main baseline, cloud VM): all `metrics` identical; per-seed `b1_receipt_sha256` 130/130 identical; per-seed `b3_receipt_sha256` 115/130 different; first-20-seed decisions (action/gate_reason/common_action_time) 0 differences; last-digit float differences at 5441 residual components and 176 rmse values (order 1e-17); fitted `speed_step_time` landed on an adjacent 0.05 s grid cell in 8 places, all in AMBIGUOUS calls with n=7–10 and `passed` True on both sides. [source: T3 §6]
- T4 on the FRZ-1 head: two same-machine runs have identical `receipt_sha256` and 0/130 per-seed differences; against the committed FRZ-1 `b3-dev.json`, per-seed B3 hashes differ in 115/130 (the same-hash seeds are 2, 6, 15, 16, 49, 58, 67, 73, 92, 102, 105, 107, 113, 114, 124) and B1 hashes in 0/130; metrics, `system2_reobserve`, and every episode's scoring fields are identical; first-20-seed decision sequences are identical but 7785 float leaves differ, max absolute difference 1.33e-15, in the last digits of fitted parameters, `rmse`, `residual_vector`, `verifier_score`, and not in grid values. main shows the same 115/130. [source: T4 §3 (D1–D5b)]
- T1 on PR #20 also saw that the B3 hashes in the committed `b3-dev.json` and `b4-dev.json` do not reproduce in the cloud VM (B1 hashes do); cause [UNKNOWN]. [source: T1 §0]
- T4 §5: in the cloud VM, main code replaying the subset as-is hits only 62 calls, with 317 unique misses; T4 states the number mixes "cross-machine" and "FRZ-1 change" sources. T4's cloud VM is an Intel Xeon, while the committed `b3-dev.json` records an i7-10750H. [source: T4 header; §5]

**Mechanism**
- INFERENCE (T3 §6): last-bit floating-point differences of least squares across machines, and the grid-argmin tie flips they cause; in the re-run these differences did not reach any decision or metric. On FRZ-1, which has the tie rule, the differing fields T4 saw do not include grid values (FACT, T4 §3).
- FACT: the evidence packet carries raw floats (`episode.py:692-705`) and `adapter.py:79-82` uses `json.dumps` directly, so the B4 request body and cache key depend on last-digit floats (T4 §1 table §3.4). T1 lists the link between the B3 hash difference and the cache-key difference as [UNKNOWN].

**How we found it**: T3 §6 re-run comparison (`b8f0e10`); T1 §0 (`1baed16`); T4 §3, §5 (`550cdc6`).

**Current disposition**:
- Grid ties (A05 §2): **covered by an addendum**; implemented on FRZ-1 (`67bc419`, unmerged); T4 records a test gap (no tests for the one-dimensional actuator-delay tie or the two-dimensional tie).
- Determinism scope (A05 §4): **covered by an addendum**, as a scope statement: bit-identical cross-machine hashes are not claimed; cross-machine reproduction is compared at the decision and metric level. **R4**: the registered runner is the owner's local machine (Intel i7-10750H, Python 3.12.3, NumPy 2.5.4, scipy-openblas 0.3.34). FRZ-1 records platform details (`154522b`); T4 notes the BLAS entry comes from NumPy's build configuration, not the library loaded at runtime.
- A05 §3.4 (floats serialized to 6 decimals): **not found** on FRZ-1 (T4 §1); **R5**: implemented locally by the owner, B4 cache rebuilt live on the registered runner. Effect after implementation: pending eval-v3, no result yet. T4 §5's estimates of live regeneration (about 444 for the subset, about 1400 for full) are lower bounds (see T4 §5).
- Final statement: [owner decision]

**Transferable lesson**: floating-point least squares plus a discrete-grid argmin can flip ties across machines; receipt hashes are meaningful only on the one registered runner. Compare cross-machine reproductions at the decision and metric level and list per-seed differences; round any float that enters a cache key.

---

## G. Reduced evidence packet (A04 §5.3)

**Phenomenon**
- A04 §5.3: the 2026-10-23 dev run (commit `92e2b89`) sent a reduced evidence packet (observations limited to time/observed_x/nominal_x; feedback limited to issued_time/execution_time/accepted/success; no presence events; known configuration limited to dt and tolerance), which does not meet Addendum 03 §2 item 4 and is recorded as an implementation defect to be corrected before implementation-candidate freeze; that run's results are not evidence about B4 under the registered packet. [source: A04 §5.3]
- T1 §5 field-by-field: missing `target_id`, `step`, `observed_y`, `nominal_y`, `nominal_speed`; the whole presence-event group; `x_pick`, `y_pick`, `belt_speed`; `command_id`, `target_id`, `reason_code`; present beyond the whitelist: `passing`, `current_time`, `horizon`. T1 confirmed by reading the code of `c852566` (not by inspecting a stored request) that the packet at that point is still the reduced form. [source: T1 §5]
- Related disclosure: of the 386 cached responses of that run, 71 parse as `{items:[...]}`, 310 parse as JSON but with the wrong shape, 5 stopped at the token limit; most B4-tiebreak calls fell back as INVALID_PROPOSAL (dev, not a registered result). [source: A04 §5.1, §5.2]

**Mechanism**: in form, the request body is a deterministic function of the evidence packet and text context (A04 §1.3); in content it does not reach the registered packet (T1 §1). **Fix status: [UNKNOWN, pending T6 check]** (T1's observation ends at `c852566`; T4 draws no conclusion on this item within the 12 FRZ-1 commits).

**How we found it**: A04 §5.3 self-disclosure (2026-10-23); T1 §5 (`1baed16`) confirmed field by field.

**Current disposition**: registered (A04 §5.3); fix status [UNKNOWN, pending T6 check]. An adjacent unchecked item: the B4 receipt records neither a model identifier nor a request-template SHA-256 (required by A04 §5.4; T1 §6), whose present state is likewise pending a check. Final statement: [owner decision]

**Transferable lesson**: audit what is sent to the model against the registered whitelist field by field, and record the request-template hash and model identifier in the receipt; format failures (here 310 of 386) can swamp any effect of the text context, so register the reporting rule beforehand (A04 §6.2).

---

## H. The `safe_stop` release behaviour at 88/5 (R2)

**Phenomenon** (dev, not a registered result)
- The only authorization of a held target is seed 88, target 5: `safe_stop` was already True at t=0.2, was released after authorization at t=5.9, and a command followed; outcome `attempt_failed` (`missed pick window`), scored as a miss. [source: T4 §1 table §1.3; §4.2 (H9); §4.5 (X4)]
- It is the only object whose class/status changed between main and FRZ-1: on main it is escalated (not issued, wrong_disposition); it exactly accounts for wrong 589→588 and miss 96→97. [source: T4 §4.5 (X4)]
- Authorizations after a hold (`authorized_after_hold`): 1. [source: T4 §4.1 (H0)]

**Mechanism**
- FACT: the implementation treats "no hold and no latch" as a **sufficient** condition for releasing `safe_stop` (`episode.py:879-885`); a `safe_stop` set by another target before the hold began is released too. That branch has no test. [source: T4 §1 table §1.3; §1.1 item 1]
- INFERENCE: this is the direct cause of wrong 589→588 and miss 96→97 (T4 C5(b)).
- Evidence still missing: whether A05 §1.3 "cleared only when…" is a necessary or a sufficient condition — **the owner ruled on 2026-10-24 (R2) to keep the FRZ-1 behaviour**. [source: T4 §7-2]
- A related but different object: in T3 C2, 88/1 was commanded by the fast layer, which T3 conjectures is tied to `safe_stop` not being set after S2 authorized 88/0 in the same episode (INFERENCE, with a parallel explanation). [source: T3 C2]

**How we found it**: T4's per-object trace of post-hold authorization (`550cdc6`).

**Current disposition**: **disclosed, not fixed, per owner ruling** (R2: no code change; 88/5 is disclosed in the submission material). Final statement: [owner decision]

**Transferable lesson**: a rule that lets an authorization release a global stop must say whether it also releases a stop set for another reason; an untested branch can be triggered by a single object even on dev and move a metric.

---

## I. Early authorization and double deduction of sensor_bias in committed B3 history (T3 C5, C6) — history, no longer in the current unsafe set

**Phenomenon** (dev, not a registered result)
- `b3-dev.json` at `1cc7d07`: 8 unsafe, all `s2_authorized` (`unsafe-traces-d1d.json`). Group A, 5 objects (24/1, 26/2, 30/2, 116/1, 119/1): authorized at t=0.5 with n_usable=6, selecting the first structure in enumeration order, h00 = SENSOR_BIAS; evaluator position_error 0.431, 0.753, 0.799, 0.446, 1.127. Group B, 3 objects (48/0, 48/1, 88/0): authorized at t=5.0–5.2 with n=51–53, selected structure SB+SS, position_error 0.401, 0.460, 0.713, fitted bias of the selected model 0.450, 0.449, 0.343. [source: T3 §2.2 (R7)]
- The current `b3-dev.json` has 7 unsafe, `unsafe_action_by_source` fast_layer_command 7 and s2_authorized 0; none of these 8 objects is among them (88/0 is now a miss). [source: T3 §1.1, §2.2]
- Commit progression of s2-sourced unsafe: 8 at `1cc7d07` → 9 at `48116ad` → 4 at `cdd6e59` → 0 at `dbebe35`. [source: T3 §3.2]

**Mechanism**
- FACT: each Group A object had a single S2 call with exactly 6 samples (the lower bound); `episode.py:690` takes the first hypothesis meeting the tolerance via `next(...)`. [source: T3 C5]
- INFERENCE (C5): Group A left the unsafe set because `cdd6e59` requires authorization to carry a non-empty `temporary_policy_exception` and blocked them, not because the prediction was corrected; whenever an early UPDATE that needs an exception appears, the "6 samples, pick the first structure" path remains reachable. Parallel explanation: the Group A error may mainly come from a step or velocity offset after t=0.5 (`step_after_decision` was computed only for 48/0 and 88/0).
- INFERENCE (C6): `668fe22` removed `− sensor_bias` from the prediction; the Group B error magnitude is comparable to the bias, consistent with the bias being deducted twice as physical displacement; for 88/0 the surplus has the same sign and order as the 0.266 s execution delay, with the parallel explanation that the selected model did not include ACTUATOR_DELAY.
- Evidence still missing: Group A's true `speed_step_time` compared with the authorization time; a term-by-term decomposition of the prediction error at `1cc7d07` and at `668fe22`.

**How we found it**: T3 §2.2, §3.1, §3.2, C5, C6 (`b8f0e10`), comparing the `1cc7d07` `unsafe-traces-d1d.json` with later commits (`668fe22`, `cdd6e59`, `dbebe35`).

**Current disposition**: history; neither Addendum 04 nor 05 creates a clause for it. Whether the C5 path is still reachable: registered, to be fixed (the offline check design was not executed). Whether FRZ-1 changes the path: [UNKNOWN] (T4 draws no conclusion on it). Final statement: [owner decision]

**Transferable lesson**: register the minimum sample count an authorization relies on, and record how many structures were released at the same decision point and which was chosen; when a fix comes from an added gate rather than a corrected prediction, label it as such so it is not read as a better prediction.

---

## J. Supplement: the current 7 unsafe are all fast-layer commands (T3 §2.1, C1)

This section is outside the task's minimum list but concerns current dev numbers; it is listed so that only history is not disclosed.

**Phenomenon** (dev, not a registered result)
- All 7 unsafe in `b3-dev.json` are `fast_layer_command`, all in cases containing ACTUATOR_DELAY: 46/0, 51/1, 88/1, 103/1, 106/0, 106/1, 106/2. For 6 of them (46/0, 51/1, 103/1, 106/0-2) the B1 and B3 terminal counts of the episode are equal and so are the B1 unsafe counts; each has a single S2 call (t=0.2–0.3, n=3–4, NO_VERIFIED_HYPOTHESIS → PAUSE). FRZ-1 also has 7 unsafe. [source: T3 §2.1; T4 §0]
- B1-corrected unsafe 43 → B3 7; of the 43, 37 are in FAULT:OBJECT_MISSING and 6 in combinations containing ACTUATOR_DELAY. [source: T3 §2.3]

**Mechanism**: INFERENCE: fast-layer commands carried over from B1; unmodelled actuator delay and a late command time together cause errors above 2×tolerance (the share of each varies by object). Evidence still missing: B1 per-target unsafe ids and the evaluator rows. [source: T3 C1]

**How we found it**: T3 §2 (`b8f0e10`). **Current disposition**: registered; no addendum; not covered by R1–R5; whether and how to disclose it: [owner decision]. **Transferable lesson**: unmodelled actuator delay is amplified by a later command; splitting unsafe by source shows which come from the reasoning layer and which from the inherited fast layer.
