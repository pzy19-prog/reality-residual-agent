# T6 — 冻结前核对（第 1 阶段）

- 审查对象：`feat/frz1-b3core` 头 `cb771079c1c119d73d0ebd0e24704a1935731cea`（与任务书核对值一致）；`main` 头 `520b7cfdf13b805c9258ab06c79a658ee62aef8b`（一致）。
- 分支：`cloud/t6-prefreeze-check`，从 `feat/frz1-b3core` 头新建。本文件是分支上唯一新增的文件。
- Addendum 05 从 `git show origin/main:docs/P3_PREREG_ADDENDUM_05.md` 读取。Addendum 01–04 在 FRZ-1 头与 `origin/main` 上内容相同（`git diff HEAD origin/main -- docs/P3_PREREG_ADDENDUM_0{3,4}.md` 无输出）。
- 环境：云 VM，`/usr/bin/python3.12` 新建 venv，按 `requirements.txt` 安装：Python 3.12.3，numpy 2.5.4，pydantic 2.14.1，pytest 8.4.2。本机 `runtime_versions`：`x86_64`、`Intel(R) Xeon(R) Processor @ 2.10GHz`、`scipy-openblas 0.3.34.106.0`。**本机不是 R4 的注册 runner**（i7-10750H），所以清单中凡涉及注册 runner 的条目，这里只能给出命令与本机读数。
- 数据范围：只用 `config/dev_seeds.json` 与已提交 artifacts。`config/eval_seeds*.json` 未打开；`config/eval_seeds_v3.json` 只做了存在性检查（`test ! -e`）。所有命令前加 `env -u NVIDIA_API_KEY -u ZETARIS_TOKEN`；没有运行 live 命令。`rra s2-b3-dev`/`s2-b4-dev` 都指定了 scratchpad 下的 `--output-dir`。运行后 `git status --porcelain` 为空。
- 未触发 BLOCKED。预算未到上限。
- 记号：**FACT** = 可直接从代码行、文件字段或命令输出读到；脚本与原始输出见附录。本文不做成败判定；pytest 的 passed/failed 计数照实写。

下文中 `$PY` 指上述 venv 的 python，`$OUT` 指 scratchpad 下的临时目录，`$T6` 指存放附录脚本的目录。

## 1. B4 证据包对照 C1 白名单与 Addendum 03 §2 第 4 项（Addendum 04 §5.3）

### 1.1 要求的出处

- C1 白名单：`docs/P3_PREREG_ADDENDUM_01.md:8`；代码中的同名 dataclass：`src/rra/evidence/policy.py:10-19`（观测）、`:22-27`（在场事件）、`:30-36`（已知配置）、`:39-47`（命令反馈）。
- Addendum 03 §2 第 4 项：`docs/P3_PREREG_ADDENDUM_03.md:35`（"The LLM receives the full whitelisted evidence packet for the episode. Retrieval may not remove evidence from it."）。
- Addendum 04 §1.2：`docs/P3_PREREG_ADDENDUM_04.md:15`；§5.3：`:58`（列出 dev run 的缩减包，并记为冻结前需更正的实现缺陷）。

### 1.2 证据包在代码中的构造（FACT）

- 构造位置：`src/rra/evidence/episode.py:692-706`，调用 `proposer.propose(evidence_packet, text_context)` 在 `:707`。
- 序列化：`src/rra/llm/adapter.py:79-82`，`json.dumps({"evidence_packet": ..., "context_text": ...}, sort_keys=True, ...)`，浮点原样写出。
- FRZ-1 的 12 个提交没有改动这段构造（与 T1 §5 在 `c852566` 上读到的字段相同）。

### 1.3 离线插桩样例（FACT）

脚本 `capture_packet.py`（附录 A.1）：用一个只记录请求体并返回 `{"items": []}` 的 provider 包住真实的 `HypothesisProposer`，跑 dev seed 21、`HELPFUL_TEXT_CONTEXT`、`B4_STRICT`。`src/` 未改动，无网络。输出（节选，全文 A.1）：

```
requests 7
user-message keys ['context_text', 'evidence_packet']
packet keys ['current_time', 'dt', 'feedback', 'horizon', 'observations', 'passing', 'tolerance']
observations: n=10 keys=['nominal_x', 'observed_x', 'time']
passing: n=7 keys=['n_usable', 'rmse', 'structure_id']
observations[0:2] [{"nominal_x": -4.875529644730117, "observed_x": -4.874935120726528, "time": 0.0}, ...]
scalars {'current_time': 0.9, 'dt': 0.1, 'horizon': 9.9, 'tolerance': 0.2}
union over all requests {'observations': ['nominal_x', 'observed_x', 'time'], 'feedback': ['accepted', 'execution_time', 'issued_time', 'success'], 'passing': ['n_usable', 'rmse', 'structure_id'], '_top': [...]}
```

脚本 `check_packet_whitelist.py`（附录 A.2，也是清单 C-06 的核验命令）对 dev seed 21、1、3 的全部请求按组取并集再比对：seed 21 有 7 个请求，seed 3 有 2 个，seed 1 有 0 个（该 seed 没有 AMBIGUOUS 且无 fault 的决策点）。两个有请求的 seed 结果相同，脚本退出码 1，最后一行 `RESULT MISSING_FIELDS`。

### 1.4 逐字段对照

| 组 | 白名单要求的字段（Add.01:8） | 实际包含（episode.py 行） | 缺失 | 该组在策略侧是否已有完整数据（FACT） |
|---|---|---|---|---|
| 观测 | `target_id`, `step`, `time`, `observed_x`, `observed_y`, `nominal_x`, `nominal_y`, `nominal_speed` | `time`, `observed_x`, `nominal_x`（`:693-695`；来源 `S2Observation(time, observed_x, nominal_x)`，`:568-569`） | `target_id`, `step`, `observed_y`, `nominal_y`, `nominal_speed` | `sanitize_observation` 产生全部 8 个字段（`policy.py:50-`；`episode.py:545`），但写入 `system2_observations` 时只保留 3 个（`:568-569`） |
| 在场事件 | `target_id`, `step`, `time`, `target_observed` | 无（包中没有这一组） | 全部 4 个字段 | `policy_target_presence_events` 已含 4 个字段（`:521-526`），传给 `run_b3`（`:688`），未放入包 |
| 已知配置 | `dt`, `tolerance`, `x_pick`, `y_pick`, `belt_speed` | `dt`, `tolerance`（`:703`、`:705`） | `x_pick`, `y_pick`, `belt_speed` | `known_config = sanitize_config(config)` 含 5 个字段（`:67`；`policy.py:78-86`） |
| 命令反馈 | `command_id`, `target_id`, `issued_time`, `execution_time`, `accepted`, `success`, `reason_code` | `issued_time`, `execution_time`, `accepted`, `success`（`:696-699`） | `command_id`, `target_id`, `reason_code` | `policy_feedbacks` 是 `asdict(command_feedback(...))`，含 7 个字段（`:1031-1038`；`policy.py:89-`） |

白名单外多出的内容（FACT）：
- `passing[]`：`structure_id`、`rmse`、`n_usable`（`:700-702`），来自 B3 verifier 的输出。
- 顶层 `current_time`（`:703`）、`horizon`（`:704`）。
- 范围说明：`observations` 只含当前目标的样本（`s2obs = system2_observations[observation.target_id]`，`:673`）；`feedback` 是整个 episode 的 `policy_feedbacks`，不按目标过滤（`:699`）。
- 自由文本 `context_text` 与包并列（`adapter.py:80`），不在包内。

B3：B3 不调用 proposer，不存在发送给 proposer 的包，本项对 B3 不适用。仅作记录（FACT）：`run_b3` 的输入为观测 3 字段、反馈 4 字段（`:683`）、本目标在场事件 4 字段（`:688`）以及 `belt_speed`/`dt`/`tolerance`（`:681-689`）。

### 1.5 结论

**未更正。**（FRZ-1 头上的包与 Addendum 04 §5.3 所描述的缩减包字段相同。）

## 2. 冻结前清单

用法：对候选提交 `<CAND>` 在仓库根目录逐条运行。"第 1 阶段读数"是本机在 `cb77107` 上的结果，只是基线记录。标 [R4] 的条目只有在注册 runner 上运行才有意义。

- [ ] **C-01 候选头已确定**
  命令：`git rev-parse HEAD`
  期望：等于所有者给出的 `<CAND>` sha。
  第 1 阶段读数：`cb771079c1c119d73d0ebd0e24704a1935731cea`。

- [ ] **C-02 工作区干净**
  命令：`git status --porcelain`（在下面所有条目运行前后各一次）
  期望：无输出。
  第 1 阶段读数：两次都无输出。

- [ ] **C-03 pytest 全量**
  命令：`env -u NVIDIA_API_KEY -u ZETARIS_TOKEN $PY -m pytest -q -p no:cacheprovider -rfEs`
  期望：最后一行为 `N passed, 4 skipped`，没有 `failed`/`error`；4 个 skipped 是 meterless live ×3 与 Zetaris live ×1。
  第 1 阶段读数：`200 passed, 4 skipped in 194.81s`，exit 0。

- [ ] **C-04 §3.4 已实现（行为）**
  命令：`env -u NVIDIA_API_KEY -u ZETARIS_TOKEN RRA_REPO=$PWD $PY -m pytest -c pyproject.toml --rootdir=. -p no:cacheprovider -q $T6/test_t6_drafts.py -k "six_decimals or last_digit"`
  期望：`3 passed`。
  第 1 阶段读数：`3 failed`（见 §3.4）。

- [ ] **C-05 §3.4 在 tests/ 中有测试**
  命令：`git diff --name-only cb77107 <CAND> -- tests/`，以及 `git grep -n -E "nextafter|6 decimal|decimals" -- tests/`
  期望：至少一个 tests/ 文件被新增或修改，且 grep 命中一个针对 B4 请求浮点取整的测试；该测试包含在 C-03 的 passed 计数中。
  第 1 阶段读数：grep 无命中（exit 1）。

- [ ] **C-06 §5.3 证据包合规**
  命令：`env -u NVIDIA_API_KEY -u ZETARIS_TOKEN PYTHONPATH=src $PY $T6/check_packet_whitelist.py 21 3`
  期望：exit 0，最后一行 `RESULT ALL_C1_FIELDS_PRESENT`；每组 `missing none`。另外人工读 `keys outside C1 field names` 一行，记录白名单外字段（是否允许由所有者决定，见 §5）。
  第 1 阶段读数：exit 1，`RESULT MISSING_FIELDS`（§1.4）。
  注意：脚本按字段名匹配。若候选实现把在场事件放在独立的列表里，"presence" 组的 best match 应指向那个列表；若仍指向 `observations[]`，说明在场事件组不存在。

- [ ] **C-07 replay 缓存缺失端到端非零退出（Addendum 05 §3.1）**
  命令：`env -u NVIDIA_API_KEY -u ZETARIS_TOKEN RRA_REPO=$PWD $PY -m pytest -c pyproject.toml --rootdir=. -p no:cacheprovider -q $T6/test_t6_drafts.py -k replay_cache_miss`
  期望：`1 passed`。
  第 1 阶段读数：`1 passed`。

- [ ] **C-08 B1 receipt 不变**
  命令：`env -u NVIDIA_API_KEY -u ZETARIS_TOKEN PYTHONPATH=src $PY -m rra.cli s2-b3-dev --output-dir $OUT/b3run1`，然后 `$PY $T6/compare_b3.py $OUT/b3run1/b3-dev.json $OUT/b3run2/b3-dev.json artifacts/s2/b3-dev.json`（b3run2 来自 C-09）；再用 `git show origin/main:artifacts/s2/b3-dev.json > $OUT/main-b3-dev.json` 替换第三个参数重跑一次。
  期望：两次比较都打印 `b1_receipt_sha256: ... run1 vs committed differ 0/130`。
  第 1 阶段读数：对 FRZ-1 已提交文件 0/130；对 main 已提交文件 0/130（本机不是注册 runner，B1 哈希跨机仍相同）。

- [ ] **C-09 同机两次 B3 receipt 一致** [R4]
  命令：同 C-08，再输出到 `$OUT/b3run2`，然后运行 `compare_b3.py`。
  期望：`run1==run2 True`；`b3_receipt_sha256: run1 vs run2 differ 0/130`。在注册 runner 上还应有 `run1 vs committed differ 0/130`，且 run1 的 `receipt_sha256` 等于候选提交里 `artifacts/s2/b3-dev.json` 的 `receipt_sha256`。
  第 1 阶段读数（本机）：run1 = run2 = `3c1ee45a0cc7138c6ac979520b8c8572b930b77478633b3ca6240a4a2b0e659a`；逐 seed B3 0/130 不同；对已提交 `75115f44…a5e32` 115/130 不同，metrics 相同（跨机，Addendum 05 §4.2）。对 main 已提交文件：B3 130/130 不同，metrics 不同（FRZ-1 改了行为，属预期差异，只作记录）。

- [ ] **C-10 runtime_versions 与 R4 一致** [R4]
  命令：`$PY -c "import json;print(json.load(open('artifacts/s2/b3-dev.json'))['runtime_versions'])"`；对 `artifacts/s2/b4-dev.json` 和 C-08 的新输出各做一次。
  期望：三处都是 `{'python': '3.12.3', 'numpy': '2.5.4', 'machine': 'x86_64', 'cpu_model': 'Intel(R) Core(TM) i7-10750H CPU @ 2.60GHz', 'blas': {'name': 'scipy-openblas', 'version': '0.3.34.106.0'}}`。
  第 1 阶段读数：已提交 `b3-dev.json` 与上式相同；已提交 `b4-dev.json` 只有 `{'python': '3.12.3', 'numpy': '2.5.4'}`（缺 machine/cpu_model/blas，该文件最后由 `c852566` 生成，早于 `runtime.py`）；本机新输出的 cpu_model 为 Xeon（非注册 runner）。

- [ ] **C-11 B4 replay 可生成且两次一致（Addendum 04 §4，Addendum 05 §3.1、§5 第 3 项）** [R4]
  前提：所有者已按新包与 §3.4 重新填充 `artifacts/llm_cache/`（live 步骤，不在本会话内）。
  命令：`env -u NVIDIA_API_KEY -u ZETARIS_TOKEN PYTHONPATH=src $PY -m rra.cli s2-b4-dev --replay --subset --output-dir $OUT/b4a`，再输出到 `$OUT/b4b`，然后 `$PY -c "import json;a,b=(json.load(open(f'$OUT/{d}/b4-dev.json')) for d in ('b4a','b4b'));print(a['receipt_sha256']==b['receipt_sha256'], a['receipt_sha256'])"`。
  期望：两次 exit 0；打印 `True <sha>`；`<sha>` 等于候选提交里 `artifacts/s2/b4-dev.json` 的 `receipt_sha256`。
  第 1 阶段读数：第一次运行 61 s 后 exit 1，`rra.llm.providers.ReplayCacheMiss: replay cache miss: .../artifacts/llm_cache/566dfc84….json`；没有写出 `b4-dev.json`。

- [ ] **C-12 已提交 receipt 可由内容重算**
  命令：`$PY $T6/compare_b3.py <三个 b3 文件> artifacts/s2/b4-dev.json`
  期望：`committed receipt stored ... recomputed equal True`，b4 一行也为 `True`。
  第 1 阶段读数：两者都为 `True`（b3 `75115f44…`，b4 `b23231e1…`）。

- [ ] **C-13 B4 receipt 记录模型标识与请求模板 SHA-256（Addendum 04 §5.4）**
  命令：附录 A.4 的单行 key 扫描。
  期望：至少命中一个模型标识键和一个模板 SHA-256 键。
  第 1 阶段读数：`model/template keys: none`。

- [ ] **C-14 eval-v3 禁止状态未变**
  命令：`test ! -e config/eval_seeds_v3.json && echo absent`；`$PY -c "import json;d=json.load(open('artifacts/h1/final-eval-v3-prohibition.json'));print({k:d[k] for k in ('forbidden_seed_file_exists','final_eval_v3_seed_values_created','final_eval_v3_seed_values_inspected')})"`
  期望：`absent`；三个值都为 `False`。
  第 1 阶段读数：与期望相同。

- [ ] **C-15 候选相对 FRZ-1 的改动范围**
  命令：`git diff --stat cb77107 <CAND>`；`git diff --name-only cb77107 <CAND> -- docs/ config/`
  期望：第二条无输出，或只列出所有者明确批准的文件；第一条中 `src/` 的改动与 §3.4（以及所有者选择一并做的 §5.3 修正）对应。
  第 1 阶段：不适用。

- [ ] **C-16 其余测试草案**
  命令：`env -u NVIDIA_API_KEY -u ZETARIS_TOKEN RRA_REPO=$PWD $PY -m pytest -c pyproject.toml --rootdir=. -p no:cacheprovider -q -rA $T6/test_t6_drafts.py`
  期望：9 passed（若 C-04 已满足）。
  第 1 阶段读数：`3 failed, 6 passed in 7.80s`。

## 3. 测试草案（只在附录 B，未写入 tests/）

草案全文见附录 B.1，在 FRZ-1 头上的运行输出见 B.2。运行命令：

```
cd <repo> && env -u NVIDIA_API_KEY -u ZETARIS_TOKEN RRA_REPO=$PWD $PY -m pytest -c pyproject.toml --rootdir=. -p no:cacheprovider -q -rA $T6/test_t6_drafts.py
```

| 覆盖 | 测试 | FRZ-1 头上结果 |
|---|---|---|
| T4 §1.1 第 5 项：B4 下的保持 | `test_b4_variants_enter_and_exhaust_reobserve_hold_like_b3[B4_STRICT]`、`[B4_TIEBREAK]` | passed、passed |
| T4 §1.1 第 6 项：actuator-delay 一维平局 | `test_actuator_delay_fit_chooses_smallest_delay_within_tie_tolerance`；对照 `test_actuator_delay_fit_without_tie_keeps_strict_minimum` | passed、passed |
| T4 §1.1 第 6 项：(tau, delay) 二维平局 | `test_speed_step_and_delay_tie_selects_lexicographic_smallest_tau_then_delay` | passed |
| T4 §1.1 第 7 项：`rra s2-b4-dev --replay` 缺失端到端非零退出 | `test_s2_b4_dev_replay_cache_miss_exits_non_zero` | passed |
| Addendum 05 §3.4：请求体与 cache key 不随末位浮点变化 | `test_b4_request_body_and_cache_key_ignore_last_digit_float_differences` | **failed**（两个请求体在 `rmse` 末位不同：`-0.04795738613622927` vs `-0.04795738613622926`） |
| Addendum 05 §3.4：请求中浮点 ≤6 位小数 | `test_b4_request_floats_have_at_most_six_decimals` | **failed** |
| Addendum 05 §3.4：dev seed 21 实际 episode 请求 | `test_b4_episode_requests_on_dev_seed_are_rounded_to_six_decimals` | **failed** |

pytest 计数：`3 failed, 6 passed in 7.80s`。§3.4 的 3 个失败与任务书的预期一致。

说明（FACT）：
- 第 5 项：用常 PAUSE、`gate_reason="AMBIGUOUS"`、无 fault 的 `run_b3` 桩，使每次 S2 评估都满足 Addendum 04 §1.1 的调用条件。测试断言 B4 下的 S2 调用时刻、`system2_reobserve` 汇总与同一桩下的 B3 完全相同（Addendum 05 §1.5 "identically"），以 window_end 结束且带 `;REOBSERVE_EXHAUSTED`，保持中没有发出命令，proposer 调用次数等于 S2 评估次数；tiebreak 的回退原因为 `NO_PROPOSED_PASSING_STRUCTURE`，动作保持 PAUSE。
- 第 6 项：沿用 `tests/test_s2.py:99` 的做法，替换 `_linear_fit` 控制每个网格点的目标值；反馈延迟 0.055 使 0.05 与 0.06 的反馈项相等。严格最小值放在较大的网格值上，另一个点比它大 5e-13（在 1e-12 容差内）。二维测试中，严格最小值为 (0.55, 0.05)，平局点为 (0.5, 0.06)，期望值 (0.5, 0.06) 编码的是 FRZ-1 实现的 (tau, delay) 字典序读法（`src/rra/s2/fitter.py:64-69`）；条款原文 "the smallest grid value" 的二维读法列入 §5。
- 第 7 项：子进程中把 `rra.eval.b4_dev.ROOT` 指到临时目录（复制 `config/dev_seeds.json`，subset 文件只含 dev seed 21，`artifacts/llm_cache/` 为空），再调用 `rra.cli.main(["s2-b4-dev","--replay","--subset",...])`。断言 returncode ≠ 0、stderr 含 `ReplayCacheMiss`、没有写出 `b4-dev.json`。CLI 没有 `--cache-dir` 选项，所以只能通过替换 `ROOT` 指定缓存目录。
- §3.4：第二个草案用 `round(v, 6) == v` 检查解析后的浮点。如果实现把浮点写成字符串（例如 `"%.6f"`），这个草案会因为 `floats` 为空而失败，需要按实现的形式调整。第一个草案只要求两个末位不同的包产生相同的请求体与相同的 `request_sha256(finalize_payload(...))`，与序列化形式无关。

草案敏感性核对（FACT，附录 B.3）：在 scratchpad 的源码副本中做两处变异，(a) `fitter.py` 中 `tie_tolerance = 0.0`，(b) 删除 `adapter.py` 的 `except ReplayCacheMiss: raise`，然后对副本运行 `-k "delay or replay"`：`3 failed, 1 passed`。失败的是一维平局、二维平局、replay 非零退出（`assert 0 != 0`：变异后 CLI 跑完 subset 并以 0 退出）；通过的是无平局对照。变异只在副本中进行，仓库 `src/` 未改动。

## 4. 第 1 阶段状态

第 1 阶段完成，等待 §3.4 推送。第 2 阶段将另起一节，不改动以上内容。

## 5. 需所有者裁决

1. §1.4 中白名单外的内容（`passing[]` 的 `structure_id`/`rmse`/`n_usable`、`current_time`、`horizon`）是否保留在 B4 请求中。Addendum 04 §1.2 只说请求内容受 Addendum 03 §2 第 4 项与 P3 §12 约束。
2. "full whitelisted evidence packet for the episode" 的范围：当前 `observations` 只含当前目标，`feedback` 含整个 episode；在场事件组若加入，是只含当前目标还是整个 episode。
3. Addendum 05 §2 在 (tau, delay) 二维平局时 "the smallest grid value" 的读法；FRZ-1 实现为字典序，草案按此编码。
4. Addendum 04 §5.4 要求的模型标识与请求模板 SHA-256 尚未写入 B4 receipt（C-13），"请求模板"具体哈希什么（T1 §6 已列为 UNKNOWN）。
5. 已提交 `artifacts/s2/b4-dev.json` 由 `c852566` 生成：缓存按旧包形式，`runtime_versions` 缺 machine/cpu/blas（C-10、C-11）。在 §5.3 与 §3.4 改动后，需要 live 重新填充缓存并在注册 runner 上重新生成，这一步由所有者执行。

---

## 附录 A. 脚本与原始输出

脚本放在会话 scratchpad，没有进入仓库。全文如下。

### A.1 `capture_packet.py`

```python
"""T6: capture the B4 request evidence packet offline (no src/ change, no network)."""
import json, sys
from rra.eval.b4_dev import _realization
from rra.eval.context_v3 import VARIANTS, freeze_episode_contexts
from rra.eval.framework import v3_world_config
from rra.evidence import run_episode
from rra.llm.adapter import HypothesisProposer

seed = int(sys.argv[1]); variant = sys.argv[2]
seeds = json.load(open("config/dev_seeds.json"))["seeds"]
captured = []
class CaptureProvider:
    last_http_status = None
    def complete(self, body):
        captured.append(body)
        return {"choices": [{"message": {"content": '{"items": []}'}}]}
config = v3_world_config("nominal")
real = _realization(seeds.index(seed), seed)
cause = real.fault_family or real.structure
frozen = freeze_episode_contexts(str(seed), seed, cause)[variant]
r = run_episode(config, seed, True, terminal_monitoring="corrected", realization=real,
                text_context=frozen.text, system2_enabled=True, s2_variant="B4_STRICT",
                proposer=HypothesisProposer(CaptureProvider()))
print("requests", len(captured))
def keys(rows): return sorted({k for row in rows for k in row})
for i, body in enumerate(captured[:1]):
    user = json.loads(body["messages"][1]["content"])
    pkt = user["evidence_packet"]
    print("top-level request keys", sorted(body))
    print("user-message keys", sorted(user))
    print("packet keys", sorted(pkt))
    for g in ("observations", "feedback", "passing"):
        print(f"{g}: n={len(pkt[g])} keys={keys(pkt[g])}")
    print("observations[0:2]", json.dumps(pkt["observations"][:2]))
    print("feedback[0:2]", json.dumps(pkt["feedback"][:2]))
    print("passing[0:2]", json.dumps(pkt["passing"][:2]))
    print("scalars", {k: pkt[k] for k in pkt if not isinstance(pkt[k], list)})
    print("context_text[:80]", repr(user["context_text"][:80]))
    print("user content sample", body["messages"][1]["content"][:400])
allk = {}
for body in captured:
    pkt = json.loads(body["messages"][1]["content"])["evidence_packet"]
    for g in ("observations", "feedback", "passing"):
        allk.setdefault(g, set()).update(keys(pkt[g]))
    allk.setdefault("_top", set()).update(pkt)
print("union over all requests", {k: sorted(v) for k, v in allk.items()})
print("receipt has presence events key:", any("presence" in k for k in r))
```

命令：`env -u NVIDIA_API_KEY -u ZETARIS_TOKEN PYTHONPATH=src $PY $T6/capture_packet.py 21 HELPFUL_TEXT_CONTEXT`

```
requests 7
top-level request keys ['max_tokens', 'messages', 'response_format', 'temperature']
user-message keys ['context_text', 'evidence_packet']
packet keys ['current_time', 'dt', 'feedback', 'horizon', 'observations', 'passing', 'tolerance']
observations: n=10 keys=['nominal_x', 'observed_x', 'time']
feedback: n=0 keys=[]
passing: n=7 keys=['n_usable', 'rmse', 'structure_id']
observations[0:2] [{"nominal_x": -4.875529644730117, "observed_x": -4.874935120726528, "time": 0.0}, {"nominal_x": -4.775529644730117, "observed_x": -4.795738613622927, "time": 0.1}]
feedback[0:2] []
passing[0:2] [{"n_usable": 10, "rmse": 0.013638775492247481, "structure_id": "SENSOR_BIAS"}, {"n_usable": 10, "rmse": 0.013579521483704593, "structure_id": "VELOCITY_OFFSET"}]
scalars {'current_time': 0.9, 'dt': 0.1, 'horizon': 9.9, 'tolerance': 0.2}
context_text[:80] 'Operators have observed intermittent package slip or irregular package motion.'
user content sample {"context_text":"Operators have observed intermittent package slip or irregular package motion.","evidence_packet":{"current_time":0.9,"dt":0.1,"feedback":[],"horizon":9.9,"observations":[{"nominal_x":-4.875529644730117,"observed_x":-4.874935120726528,"time":0.0},{"nominal_x":-4.775529644730117,"observed_x":-4.795738613622927,"time":0.1},{"nominal_x":-4.6755296447301165,"observed_x":-4.67374172117
union over all requests {'observations': ['nominal_x', 'observed_x', 'time'], 'feedback': ['accepted', 'execution_time', 'issued_time', 'success'], 'passing': ['n_usable', 'rmse', 'structure_id'], '_top': ['current_time', 'dt', 'feedback', 'horizon', 'observations', 'passing', 'tolerance']}
receipt has presence events key: True
```

（最后一行 `receipt has presence events key: True` 指的是 episode receipt 中存在带 "presence" 的键，与请求内容无关，不作为证据使用。）

### A.2 `check_packet_whitelist.py`

```python
"""T6: compare captured B4 evidence packets against the C1 whitelist (Addendum 01 item 4). Offline."""
import json, sys
from rra.eval.b4_dev import _realization
from rra.eval.context_v3 import freeze_episode_contexts
from rra.eval.framework import v3_world_config
from rra.evidence import run_episode
from rra.llm.adapter import HypothesisProposer

C1 = {
    "observation": ["target_id", "step", "time", "observed_x", "observed_y", "nominal_x", "nominal_y", "nominal_speed"],
    "presence": ["target_id", "step", "time", "target_observed"],
    "known_config": ["dt", "tolerance", "x_pick", "y_pick", "belt_speed"],
    "feedback": ["command_id", "target_id", "issued_time", "execution_time", "accepted", "success", "reason_code"],
}
ALL_C1 = {f for v in C1.values() for f in v}

class Capture:
    last_http_status = None
    def __init__(self): self.bodies = []
    def complete(self, body):
        self.bodies.append(body); return {"choices": [{"message": {"content": '{"items": []}'}}]}

def row_key_sets(packet):
    """(path, keyset) for every list of dicts and every dict in the packet, plus top-level scalars."""
    out = [("$", {k for k, v in packet.items() if not isinstance(v, (list, dict))})]
    def walk(v, path):
        if isinstance(v, dict):
            out.append((path, set(v)))
            for k, x in v.items(): walk(x, f"{path}.{k}")
        elif isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
            out.append((path + "[]", set().union(*map(set, v))))
            for x in v:
                for k, y in x.items():
                    if isinstance(y, (list, dict)): walk(y, f"{path}[].{k}")
    for k, v in packet.items(): walk(v, f"$.{k}")
    return out

seeds_all = json.load(open("config/dev_seeds.json"))["seeds"]
seeds = [int(s) for s in sys.argv[1:]] or [21]
missing_any = False
for seed in seeds:
    real = _realization(seeds_all.index(seed), seed)
    frozen = freeze_episode_contexts(str(seed), seed, real.fault_family or real.structure)["NO_TEXT_CONTEXT"]
    cap = Capture()
    run_episode(v3_world_config("nominal"), seed, True, terminal_monitoring="corrected", realization=real,
                text_context=frozen.text, system2_enabled=True, s2_variant="B4_STRICT",
                proposer=HypothesisProposer(cap))
    union = {}
    for body in cap.bodies:
        pkt = json.loads(body["messages"][1]["content"])["evidence_packet"]
        for path, ks in row_key_sets(pkt):
            union.setdefault(path, set()).update(ks)
    print(f"seed {seed}: requests={len(cap.bodies)}")
    for path, ks in sorted(union.items()):
        print(f"  {path}: {sorted(ks)}")
    for group, fields in C1.items():
        best = max(union.items(), key=lambda kv: len(set(fields) & kv[1]), default=("-", set()))
        miss = [f for f in fields if f not in best[1]]
        missing_any |= bool(miss) and bool(cap.bodies)
        print(f"  C1 {group}: best match {best[0]}; missing {miss if miss else 'none'}")
    extra = sorted({k for ks in union.values() for k in ks} - ALL_C1)
    print(f"  keys outside C1 field names: {extra}")
print("RESULT", "MISSING_FIELDS" if missing_any else "ALL_C1_FIELDS_PRESENT")
sys.exit(1 if missing_any else 0)
```

命令：`env -u NVIDIA_API_KEY -u ZETARIS_TOKEN PYTHONPATH=src $PY $T6/check_packet_whitelist.py 21 1 3`（exit 1）

```
seed 21: requests=7
  $: ['current_time', 'dt', 'horizon', 'tolerance']
  $.feedback[]: ['accepted', 'execution_time', 'issued_time', 'success']
  $.observations[]: ['nominal_x', 'observed_x', 'time']
  $.passing[]: ['n_usable', 'rmse', 'structure_id']
  C1 observation: best match $.observations[]; missing ['target_id', 'step', 'observed_y', 'nominal_y', 'nominal_speed']
  C1 presence: best match $.observations[]; missing ['target_id', 'step', 'target_observed']
  C1 known_config: best match $; missing ['x_pick', 'y_pick', 'belt_speed']
  C1 feedback: best match $.feedback[]; missing ['command_id', 'target_id', 'reason_code']
  keys outside C1 field names: ['current_time', 'horizon', 'n_usable', 'rmse', 'structure_id']
seed 1: requests=0
  C1 observation: best match -; missing ['target_id', 'step', 'time', 'observed_x', 'observed_y', 'nominal_x', 'nominal_y', 'nominal_speed']
  C1 presence: best match -; missing ['target_id', 'step', 'time', 'target_observed']
  C1 known_config: best match -; missing ['dt', 'tolerance', 'x_pick', 'y_pick', 'belt_speed']
  C1 feedback: best match -; missing ['command_id', 'target_id', 'issued_time', 'execution_time', 'accepted', 'success', 'reason_code']
  keys outside C1 field names: []
seed 3: requests=2
  $: ['current_time', 'dt', 'horizon', 'tolerance']
  $.feedback[]: ['accepted', 'execution_time', 'issued_time', 'success']
  $.observations[]: ['nominal_x', 'observed_x', 'time']
  $.passing[]: ['n_usable', 'rmse', 'structure_id']
  C1 observation: best match $.observations[]; missing ['target_id', 'step', 'observed_y', 'nominal_y', 'nominal_speed']
  C1 presence: best match $.observations[]; missing ['target_id', 'step', 'target_observed']
  C1 known_config: best match $; missing ['x_pick', 'y_pick', 'belt_speed']
  C1 feedback: best match $.feedback[]; missing ['command_id', 'target_id', 'reason_code']
  keys outside C1 field names: ['current_time', 'horizon', 'n_usable', 'rmse', 'structure_id']
RESULT MISSING_FIELDS
```

### A.3 `compare_b3.py`

```python
"""T6: same-machine B3 determinism, B1 per-seed hashes vs committed, runtime_versions, receipt recompute."""
import json, sys
from hashlib import sha256
def load(p): return json.load(open(p))
def recompute(d):
    h = {k: v for k, v in d.items() if k not in ("operational_cost", "runtime_versions", "receipt_sha256")}
    return sha256(json.dumps(h, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
r1, r2, com = (load(p) for p in sys.argv[1:4])
print("run1 receipt", r1["receipt_sha256"]); print("run2 receipt", r2["receipt_sha256"])
print("run1==run2", r1["receipt_sha256"] == r2["receipt_sha256"])
per = lambda d, f: {e["seed"]: e[f] for e in d["episodes"]}
for f in ("b1_receipt_sha256", "b3_receipt_sha256"):
    a, b, c = per(r1, f), per(r2, f), per(com, f)
    print(f"{f}: run1 vs run2 differ {sum(a[s]!=b[s] for s in a)}/{len(a)}; run1 vs committed differ {sum(a[s]!=c.get(s) for s in a)}/{len(a)}")
print("metrics run1==committed", r1["metrics"] == com["metrics"])
print("run1 runtime_versions", json.dumps(r1["runtime_versions"]))
print("committed runtime_versions", json.dumps(com["runtime_versions"]))
print("committed receipt stored", com["receipt_sha256"], "recomputed equal", recompute(com) == com["receipt_sha256"])
for extra in sys.argv[4:]:
    d = load(extra); print(extra, "stored", d["receipt_sha256"], "recomputed equal", recompute(d) == d["receipt_sha256"])
```

命令：`$PY $T6/compare_b3.py $OUT/b3run1/b3-dev.json $OUT/b3run2/b3-dev.json artifacts/s2/b3-dev.json artifacts/s2/b4-dev.json`（两次 `s2-b3-dev`：run1 exit 0 73 s，run2 exit 0 62 s）

```
run1 receipt 3c1ee45a0cc7138c6ac979520b8c8572b930b77478633b3ca6240a4a2b0e659a
run2 receipt 3c1ee45a0cc7138c6ac979520b8c8572b930b77478633b3ca6240a4a2b0e659a
run1==run2 True
b1_receipt_sha256: run1 vs run2 differ 0/130; run1 vs committed differ 0/130
b3_receipt_sha256: run1 vs run2 differ 0/130; run1 vs committed differ 115/130
metrics run1==committed True
run1 runtime_versions {"python": "3.12.3", "numpy": "2.5.4", "machine": "x86_64", "cpu_model": "Intel(R) Xeon(R) Processor @ 2.10GHz", "blas": {"name": "scipy-openblas", "version": "0.3.34.106.0"}}
committed runtime_versions {"python": "3.12.3", "numpy": "2.5.4", "machine": "x86_64", "cpu_model": "Intel(R) Core(TM) i7-10750H CPU @ 2.60GHz", "blas": {"name": "scipy-openblas", "version": "0.3.34.106.0"}}
committed receipt stored 75115f44cc3bd212bd461620bd8c8a5a4e8f310a2e8e5823edf1136bd90a5e32 recomputed equal True
artifacts/s2/b4-dev.json stored b23231e1e0ea2fb95c3f52ad19bdb8e37068aa87e0c8aa2e2212dd11862231a6 recomputed equal True
```

对 main 已提交文件（`git show origin/main:artifacts/s2/b3-dev.json > $OUT/main-b3-dev.json`，作为第三个参数）：

```
b1_receipt_sha256: run1 vs run2 differ 0/130; run1 vs committed differ 0/130
b3_receipt_sha256: run1 vs run2 differ 0/130; run1 vs committed differ 130/130
metrics run1==committed False
```

### A.4 其他单行命令与输出

```
$ git grep -n -E "nextafter|6 decimal|decimals" -- tests/ ; echo exit=$?
exit=1

$ $PY -c "<key walk over artifacts/s2/b4-dev.json for keys containing 'model' or 'template'>"
model/template keys: none
runtime_versions {'python': '3.12.3', 'numpy': '2.5.4'}

$ env -u NVIDIA_API_KEY -u ZETARIS_TOKEN PYTHONPATH=src $PY -m rra.cli s2-b4-dev --replay --subset --output-dir $OUT/b4replay
exit=1 61s
rra.llm.providers.ReplayCacheMiss: replay cache miss: /home/user/reality-residual-agent/artifacts/llm_cache/566dfc849da95fc8719d26b0d4deb9d5e2676aff70b6191af462a115246be711.json
ls: cannot access '$OUT/b4replay': No such file or directory

$ test ! -e config/eval_seeds_v3.json && echo "config/eval_seeds_v3.json absent"
config/eval_seeds_v3.json absent
{'forbidden_seed_file_exists': False, 'final_eval_v3_seed_values_created': False, 'final_eval_v3_seed_values_inspected': False}

$ env -u NVIDIA_API_KEY -u ZETARIS_TOKEN $PY -m pytest -q -p no:cacheprovider -rfEs   (tail)
SKIPPED [1] tests/test_meterless_bridge.py:219: needs Node, scripts/setup_meterless.sh and RRA_METERLESS_LIVE=1
SKIPPED [1] tests/test_meterless_bridge.py:240: needs Node, scripts/setup_meterless.sh and RRA_METERLESS_LIVE=1
SKIPPED [1] tests/test_meterless_bridge.py:249: needs Node, scripts/setup_meterless.sh and RRA_METERLESS_LIVE=1
SKIPPED [1] tests/test_packet_sources.py:48: Zetaris live checks are opt-in
200 passed, 4 skipped in 194.81s (0:03:14)
exit=0
```

A.4 第二条的 key 扫描完整命令：

```
$PY -c "
import json
d=json.load(open('artifacts/s2/b4-dev.json'))
hits=set()
def w(v,p):
    if isinstance(v,dict):
        for k,x in v.items():
            if any(s in k.lower() for s in ('model','template')): hits.add(p+'.'+k)
            w(x,p+'.'+k)
    elif isinstance(v,list):
        for x in v: w(x,p+'[]')
w(d,'\$'); print('model/template keys:', sorted(hits) or 'none'); print('runtime_versions', d['runtime_versions'])"
```

## 附录 B. 测试草案

### B.1 `test_t6_drafts.py`（可放入 tests/；放入后 `REPO` 由文件位置解析，不再需要 `RRA_REPO`）

```python
"""T6 test drafts (not committed to tests/). Covers T4 §1.1 items 5, 6, 7 and Addendum 05 §3.4."""
from dataclasses import replace
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from rra.evidence import episode as episode_module
from rra.fast import Corrector
from rra.llm.adapter import HypothesisProposer
from rra.llm.providers import ReplayProvider, finalize_payload, request_sha256
from rra.s2.dsl import Action, Primitive
from rra.s2.fitter import CommandFeedback, Observation
from rra.sim import WorldConfig

REPO = Path(__file__).resolve().parents[1] if (Path(__file__).resolve().parents[1] / "src" / "rra").is_dir() \
    else Path(os.environ.get("RRA_REPO", ".")).resolve()


# --- T4 §1.1 item 5: re-observation hold under B4-strict / B4-tiebreak (Addendum 05 §1.5) ---

def _ambiguous_pause():
    return {"action": Action.PAUSE_AND_REOBSERVE, "action_time": None,
            "faults": (), "passing": [], "fits": [], "verifications": [],
            "gate_reason": "AMBIGUOUS"}


class _CountingProposer:
    def __init__(self):
        self.calls = 0

    def propose(self, evidence_packet, context_text):
        self.calls += 1
        from types import SimpleNamespace
        return SimpleNamespace(items=[], error=None, receipt={"unknown_ids": []})


def _run_with_hold(monkeypatch, variant):
    calls = []
    original = Corrector.correct

    def escalate_once(self, plan, residual, disturbance, nominal_speed):
        result = original(self, plan, residual, disturbance, nominal_speed)
        if plan.observation_time == 0.0:
            return replace(result, reason="ESCALATE: test")
        return result

    def pause(observations, **kwargs):
        calls.append(kwargs["current_time"])
        return _ambiguous_pause()

    monkeypatch.setattr(Corrector, "correct", escalate_once)
    monkeypatch.setattr(episode_module, "run_b3", pause)
    config = WorldConfig(scenario="nominal", object_count=1,
                         initial_position_min=-3.0, initial_position_max=-3.0,
                         episode_steps=40)
    proposer = _CountingProposer() if variant != "B3" else None
    receipt = episode_module.run_episode(config, 4, True, system2_enabled=True,
                                         s2_variant=variant, proposer=proposer)
    return calls, receipt, proposer


@pytest.mark.parametrize("variant", ["B4_STRICT", "B4_TIEBREAK"])
def test_b4_variants_enter_and_exhaust_reobserve_hold_like_b3(monkeypatch, variant):
    b3_calls, b3_receipt, _ = _run_with_hold(monkeypatch, "B3")
    monkeypatch.undo()
    calls, receipt, proposer = _run_with_hold(monkeypatch, variant)

    assert calls[:2] == [0.0, 0.5]
    assert calls == b3_calls
    assert receipt["system2_reobserve"] == b3_receipt["system2_reobserve"]
    assert receipt["system2_reobserve"]["end_reasons"]["window_end"] == 1
    assert receipt["evaluator_objects"][0]["command_issued"] is False
    assert receipt["outcomes"][0]["status"] == "escalated"
    assert receipt["outcomes"][0]["reason"].endswith(";REOBSERVE_EXHAUSTED")
    # Every hold re-evaluation is an AMBIGUOUS, fault-free decision point (Addendum 04 §1.1).
    assert proposer.calls == len(calls)
    if variant == "B4_TIEBREAK":
        assert {d["gate_reason"] for d in receipt["system2_decisions"]} == {
            "TIEBREAK_FALLBACK:NO_PROPOSED_PASSING_STRUCTURE"}
    assert {d["action"] for d in receipt["system2_decisions"]} == {Action.PAUSE_AND_REOBSERVE.value}


# --- T4 §1.1 item 6: Addendum 05 §2 grid ties for actuator delay, 1-D and 2-D ---

def _patched_fit(monkeypatch, objective_by_call):
    import rra.s2.fitter as fitter
    calls = 0

    def fake_linear_fit(A, y):
        nonlocal calls
        objective = objective_by_call(calls)
        calls += 1
        return np.zeros(A.shape[1]), np.array([objective ** 0.5, 0, 0, 0, 0, 0])

    monkeypatch.setattr(fitter, "_linear_fit", fake_linear_fit)
    return fitter


def test_actuator_delay_fit_chooses_smallest_delay_within_tie_tolerance(monkeypatch):
    # Feedback delay 0.055 is equidistant from grid delays 0.05 (call 5) and 0.06 (call 6).
    # 0.06 is the strict minimum; 0.05 is within 1e-12 and must win as the smaller grid value.
    fitter = _patched_fit(monkeypatch, lambda k: 1.0 + 5e-13 if k == 5 else 1.0)
    obs = [Observation(i * .1, 0.0, 0.0) for i in range(6)]
    feedback = [CommandFeedback(1.0, 1.055, True, True)]
    result = fitter.fit((Primitive.ACTUATOR_DELAY,), obs, nominal_speed=1.0, feedback=feedback)

    assert result.parameters["actuator_delay"] == pytest.approx(0.05, abs=1e-12)


def test_actuator_delay_fit_without_tie_keeps_strict_minimum(monkeypatch):
    fitter = _patched_fit(monkeypatch, lambda k: 1.0 + 1e-9 if k == 5 else 1.0)
    obs = [Observation(i * .1, 0.0, 0.0) for i in range(6)]
    feedback = [CommandFeedback(1.0, 1.055, True, True)]
    result = fitter.fit((Primitive.ACTUATOR_DELAY,), obs, nominal_speed=1.0, feedback=feedback)

    assert result.parameters["actuator_delay"] == pytest.approx(0.06, abs=1e-12)


def test_speed_step_and_delay_tie_selects_lexicographic_smallest_tau_then_delay(monkeypatch):
    # Candidates are product(taus, delays): call index = i_tau * 51 + i_delay.
    # Strict minimum: (tau=0.55, delay=0.05) at call 56. Tied within 1e-12: (tau=0.5, delay=0.06), call 6.
    # Expected value encodes the FRZ-1 reading "(tau, delay) lexicographic"; Addendum 05 §2 says
    # "the smallest grid value", whose 2-D reading is listed for the owner.
    objective = {6: 1.0 + 5e-13, 56: 1.0}
    fitter = _patched_fit(monkeypatch, lambda k: objective.get(k, 2.0))
    obs = [Observation(i * .1, 0.0, 0.0) for i in range(6)]
    feedback = [CommandFeedback(1.0, 1.055, True, True)]
    result = fitter.fit((Primitive.SPEED_STEP, Primitive.ACTUATOR_DELAY), obs,
                        nominal_speed=1.0, feedback=feedback)

    assert result.parameters["speed_step_time"] == pytest.approx(0.5, abs=1e-12)
    assert result.parameters["actuator_delay"] == pytest.approx(0.06, abs=1e-12)


# --- T4 §1.1 item 7: `rra s2-b4-dev --replay` exits non-zero on a replay-cache miss (Addendum 05 §3.1) ---

_DRIVER = r"""
import sys
from pathlib import Path
import rra.eval.b4_dev as b4_dev
from rra import cli
b4_dev.ROOT = Path(sys.argv[1])
raise SystemExit(cli.main(["s2-b4-dev", "--replay", "--subset", "--nproc", "1",
                           "--output-dir", sys.argv[2]]))
"""


def test_s2_b4_dev_replay_cache_miss_exits_non_zero(tmp_path):
    root = tmp_path / "root"
    (root / "config").mkdir(parents=True)
    (root / "artifacts" / "s2").mkdir(parents=True)
    (root / "artifacts" / "llm_cache").mkdir(parents=True)  # empty cache: every request misses
    (root / "config" / "dev_seeds.json").write_text(
        (REPO / "config" / "dev_seeds.json").read_text())
    # Dev seed 21 has AMBIGUOUS fault-free decision points, so the generator is called.
    (root / "artifacts" / "s2" / "diag-d1g.json").write_text(json.dumps({"seeds": [21]}))
    out = tmp_path / "out"
    env = {k: v for k, v in os.environ.items() if k not in ("NVIDIA_API_KEY", "ZETARIS_TOKEN")}
    env["PYTHONPATH"] = str(REPO / "src")
    proc = subprocess.run([sys.executable, "-c", _DRIVER, str(root), str(out)],
                          cwd=REPO, env=env, capture_output=True, text=True, timeout=600)

    assert proc.returncode != 0
    assert "ReplayCacheMiss" in proc.stderr
    assert not (out / "b4-dev.json").exists()


# --- Addendum 05 §3.4: B4 request floats serialized at 6 decimals ---

class _CaptureProvider:
    last_http_status = None

    def __init__(self):
        self.bodies = []

    def complete(self, body):
        self.bodies.append(body)
        return {"choices": [{"message": {"content": '{"items": []}'}}]}


def _packet(x):
    return {"observations": [{"time": 0.1, "observed_x": x, "nominal_x": -4.775529644730117}],
            "feedback": [], "passing": [{"structure_id": "SENSOR_BIAS", "rmse": x / 100, "n_usable": 10}],
            "current_time": 0.9, "dt": 0.1, "horizon": 9.9, "tolerance": 0.2}


def _floats(value):
    if isinstance(value, float):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _floats(item)
    elif isinstance(value, list):
        for item in value:
            yield from _floats(item)


def test_b4_request_body_and_cache_key_ignore_last_digit_float_differences():
    x = -4.795738613622927
    provider = _CaptureProvider()
    proposer = HypothesisProposer(provider)
    proposer.propose(_packet(x), "ctx")
    proposer.propose(_packet(float(np.nextafter(x, np.inf))), "ctx")
    first, second = provider.bodies
    settings = ReplayProvider("unused").settings

    assert first == second
    assert request_sha256(finalize_payload(first, settings)) == \
        request_sha256(finalize_payload(second, settings))


def test_b4_request_floats_have_at_most_six_decimals():
    provider = _CaptureProvider()
    HypothesisProposer(provider).propose(_packet(-4.795738613622927), "ctx")
    user = json.loads(provider.bodies[0]["messages"][1]["content"])

    floats = list(_floats(user["evidence_packet"]))
    assert floats
    assert all(round(v, 6) == v for v in floats)


def test_b4_episode_requests_on_dev_seed_are_rounded_to_six_decimals():
    from rra.eval.b4_dev import _realization
    from rra.eval.context_v3 import freeze_episode_contexts
    from rra.eval.framework import v3_world_config
    from rra.evidence import run_episode

    seeds = json.loads((REPO / "config" / "dev_seeds.json").read_text())["seeds"]
    seed = 21
    realization = _realization(seeds.index(seed), seed)
    cause = realization.fault_family or realization.structure
    frozen = freeze_episode_contexts(str(seed), seed, cause)["NO_TEXT_CONTEXT"]
    provider = _CaptureProvider()
    run_episode(v3_world_config("nominal"), seed, True, terminal_monitoring="corrected",
                realization=realization, text_context=frozen.text, system2_enabled=True,
                s2_variant="B4_STRICT", proposer=HypothesisProposer(provider))

    assert provider.bodies
    for body in provider.bodies:
        packet = json.loads(body["messages"][1]["content"])["evidence_packet"]
        assert all(round(v, 6) == v for v in _floats(packet))
```

### B.2 FRZ-1 头 `cb77107` 上的运行输出

```
......FFF                                                                [100%]
=================================== FAILURES ===================================
____ test_b4_request_body_and_cache_key_ignore_last_digit_float_differences ____

    def test_b4_request_body_and_cache_key_ignore_last_digit_float_differences():
        x = -4.795738613622927
        provider = _CaptureProvider()
        proposer = HypothesisProposer(provider)
        proposer.propose(_packet(x), "ctx")
        proposer.propose(_packet(float(np.nextafter(x, np.inf))), "ctx")
        first, second = provider.bodies
        settings = ReplayProvider("unused").settings
    
>       assert first == second
E       assert {'max_tokens'...mperature': 0} == {'max_tokens'...mperature': 0}
E         
E         Omitting 3 identical items, use -vv to show
E         Differing items:
E         {'messages': [{'content': 'Propose an ordered list of hypotheses from the registered IDs only. Choose model structures...ssing":[{"n_usable":10,"rmse":-0.04795738613622927,"structure_id":"SENSOR_BIAS"}],"tolerance":0.2}}', 'role': 'user'}]} != {'messages': [{'content': 'Propose an ordered list of hypotheses from the registered IDs only. Choose model structures...ssing":[{"n_usable":10,"rmse":-0.04795738613622926,"structure_id":"SENSOR_BIAS"}],"tolerance":0.2}}', 'role': 'user'}]}
E         Use -v to get more diff

$SCRATCH/t6/test_t6_drafts.py:212: AssertionError
_______________ test_b4_request_floats_have_at_most_six_decimals _______________

    def test_b4_request_floats_have_at_most_six_decimals():
        provider = _CaptureProvider()
        HypothesisProposer(provider).propose(_packet(-4.795738613622927), "ctx")
        user = json.loads(provider.bodies[0]["messages"][1]["content"])
    
        floats = list(_floats(user["evidence_packet"]))
        assert floats
>       assert all(round(v, 6) == v for v in floats)
E       assert False
E        +  where False = all(<generator object test_b4_request_floats_have_at_most_six_decimals.<locals>.<genexpr> at 0x7f8b03b46960>)

$SCRATCH/t6/test_t6_drafts.py:224: AssertionError
_______ test_b4_episode_requests_on_dev_seed_are_rounded_to_six_decimals _______

    def test_b4_episode_requests_on_dev_seed_are_rounded_to_six_decimals():
        from rra.eval.b4_dev import _realization
        from rra.eval.context_v3 import freeze_episode_contexts
        from rra.eval.framework import v3_world_config
        from rra.evidence import run_episode
    
        seeds = json.loads((REPO / "config" / "dev_seeds.json").read_text())["seeds"]
        seed = 21
        realization = _realization(seeds.index(seed), seed)
        cause = realization.fault_family or realization.structure
        frozen = freeze_episode_contexts(str(seed), seed, cause)["NO_TEXT_CONTEXT"]
        provider = _CaptureProvider()
        run_episode(v3_world_config("nominal"), seed, True, terminal_monitoring="corrected",
                    realization=realization, text_context=frozen.text, system2_enabled=True,
                    s2_variant="B4_STRICT", proposer=HypothesisProposer(provider))
    
        assert provider.bodies
        for body in provider.bodies:
            packet = json.loads(body["messages"][1]["content"])["evidence_packet"]
>           assert all(round(v, 6) == v for v in _floats(packet))
E           assert False
E            +  where False = all(<generator object test_b4_episode_requests_on_dev_seed_are_rounded_to_six_decimals.<locals>.<genexpr> at 0x7f8b11502ce0>)

$SCRATCH/t6/test_t6_drafts.py:246: AssertionError
==================================== PASSES ====================================
=========================== short test summary info ============================
PASSED ::test_b4_variants_enter_and_exhaust_reobserve_hold_like_b3[B4_STRICT]
PASSED ::test_b4_variants_enter_and_exhaust_reobserve_hold_like_b3[B4_TIEBREAK]
PASSED ::test_actuator_delay_fit_chooses_smallest_delay_within_tie_tolerance
PASSED ::test_actuator_delay_fit_without_tie_keeps_strict_minimum
PASSED ::test_speed_step_and_delay_tie_selects_lexicographic_smallest_tau_then_delay
PASSED ::test_s2_b4_dev_replay_cache_miss_exits_non_zero
FAILED ::test_b4_request_body_and_cache_key_ignore_last_digit_float_differences
FAILED ::test_b4_request_floats_have_at_most_six_decimals - assert False
FAILED ::test_b4_episode_requests_on_dev_seed_are_rounded_to_six_decimals - a...
3 failed, 6 passed in 7.80s
```

### B.3 变异敏感性核对（源码副本，`-k "delay or replay"`）

```
../t6/test_t6_drafts.py:168: AssertionError
==================================== PASSES ====================================
=========================== short test summary info ============================
PASSED ::test_actuator_delay_fit_without_tie_keeps_strict_minimum
FAILED ::test_actuator_delay_fit_chooses_smallest_delay_within_tie_tolerance
FAILED ::test_speed_step_and_delay_tie_selects_lexicographic_smallest_tau_then_delay
FAILED ::test_s2_b4_dev_replay_cache_miss_exits_non_zero - assert 0 != 0
3 failed, 1 passed, 5 deselected in 81.52s (0:01:21)
```

---

## 第 2 阶段（FRZ-2A，PR #27）

本节在第 1 阶段之后追加，第 1 阶段内容未改动。

- 审查对象：PR #27，分支 `feat/frz2-b4req`，head `a9fa6c3ec912161bdcf13e6d9170ce09b68fe4a1`（`git rev-parse origin/feat/frz2-b4req` 与协调消息一致）；基于 `5a05f6d56f2f08d1d9a985ee17912bcec02a23bc`（`git merge-base` 一致）。`origin/main` 当前为 `349d1e68ebf196f9f3b25d5e2f6746b6029401fe`（含 A06）。
- 5 个提交：`a63523d`、`2eccd65`、`37b0563`、`53d7410`、`a9fa6c3`；相对 `5a05f6d` 改 16 个文件（`git diff --stat 5a05f6d a9fa6c3`，A.P2-1）。
- 运行方式：对 `a9fa6c3` 建只读 worktree（scratchpad），环境与第 1 阶段相同（Python 3.12.3、numpy 2.5.4、Xeon，非 R4 runner）。没有运行 live 命令；`scripts/b4_probe.py` 只跑 `--dry-run`。`config/eval_seeds*.json` 未打开。
- 判定口径：协调消息转达的 R6–R9、G0–G7、known_config 截取、反馈只含决策之前、B3 基准改为 PR 中重新生成的 `artifacts/s2/b3-dev.json`、B1 0/130。
- 分支说明：`cloud/t6-prefreeze-check` 仍以 `cb77107` 为基（是 `5a05f6d` 的祖先）。本节只是在其上追加一个提交，没有改写历史。

### P2.1 清单 C-01 至 C-16 实测

| 项 | 命令（同 §2，在 worktree 中运行） | 实测 |
|---|---|---|
| C-01 | `git rev-parse HEAD` | `a9fa6c3ec912161bdcf13e6d9170ce09b68fe4a1` |
| C-02 | `git status --porcelain` | 所有运行前后都无输出（worktree 与仓库） |
| C-03 | 全量 pytest | `221 passed, 4 skipped in 320.15s`，exit 0；skipped 为 meterless live ×3、Zetaris live ×1 |
| C-04 | §3.4 行为 | 我的原草案 `-k "six_decimals or last_digit"`：3 failed（草案检查的是 `propose()` 交给 provider 的请求体，而 PR 把取整放在 `finalize_payload`，`src/rra/llm/providers.py:54-71`，见 P2.6）。PR 中对应测试（检查 finalized payload）：`tests/test_t6_frz2.py` 中 3 个 passed，`tests/test_frz2_request.py::test_provider_payload_rounds_embedded_json_floats_to_six_places` passed |
| C-05 | §3.4 在 tests/ 中有测试 | `git diff --name-only cb77107 a9fa6c3 -- tests/` 含 `tests/test_t6_frz2.py`、`tests/test_frz2_request.py`、`tests/test_frz2_packet_equivalence.py`；原 grep 模式 `nextafter|6 decimal|decimals` 无命中，按 `six` 命中 `tests/test_frz2_request.py:8`；这些测试计入 C-03 |
| C-06 | `check_packet_whitelist.py 21 3` | exit 0，`RESULT ALL_C1_FIELDS_PRESENT`。完整对照见 P2.2 |
| C-07 | replay 缺失端到端 | 原草案 `-k replay_cache_miss`：1 passed；PR 中 `test_s2_b4_dev_replay_cache_miss_exits_nonzero_without_artifact`：passed |
| C-08 | B1 receipt | 本机重跑对 PR 中 `b3-dev.json`：`b1 ... differ 0/130`；对 `cb77107` 已提交文件：0/130 |
| C-09 | 同机两次 B3 [R4] | run1 = run2 = `0fbebcb9f5d024a8d2fbed49a7313d7628fb4129c20abc29538c6920e1968914`；逐 seed B3 0/130 不同；对 PR 中 `b3-dev.json`（`bfda4d101bd79f8d62738807402b33e24aba29028f5f4bc550a9b13304cb1132`，i7-10750H 生成）115/130 不同，metrics 相同（跨机，本机不是 R4 runner） |
| C-10 | runtime_versions [R4] | PR 中 `b3-dev.json` 与 R4 一致；`artifacts/s2/b4-dev.json` 未在 PR 中重新生成（最后提交 `c852566`），仍只有 python/numpy；本机新输出为 Xeon |
| C-11 | B4 replay 两次一致 [R4] | `s2-b4-dev --replay --subset`：64 s 后 exit 1，`ReplayCacheMiss: .../cfda7646….json`，未写出 `b4-dev.json`。缓存仍为 `c852566` 的 386 条（`ls artifacts/llm_cache | wc -l`），尚未按新请求重建（R5 的 live 步骤） |
| C-12 | 已提交 receipt 重算 | PR 中 `b3-dev.json` 重算 = 存储值（True）；`b4-dev.json`（`b23231e1…`）True |
| C-13 | B4 receipt 模型标识与模板 SHA | 已提交 `b4-dev.json` 未重新生成，仍无。代码层面：`run_b4_dev` 写入 `llm_request_spec`（含 `model`、`format_mode`、`max_tokens`、`chat_template_kwargs`、`request_template_sha256`）与 `served_models`（`src/rra/eval/b4_dev.py:335-345`），实测见 P2.3 |
| C-14 | eval-v3 禁止状态 | `config/eval_seeds_v3.json` absent；三个标志均为 `False` |
| C-15 | 改动范围 | `git diff --name-only 5a05f6d a9fa6c3 -- docs/ config/`：无输出（PR 不含 A06；A06 在 main 的 `349d1e6`）。相对 `cb77107`：17 个文件，多出的一个是 `docs/P3_PREREG_ADDENDUM_05.md`（来自 main）。`decisions.md` 新增 1 行，记录 R1–R9（A.P2-2）。`git merge-tree --write-tree --name-only origin/main a9fa6c3` → `b13144d…`，exit 0，无冲突文件；main 相对 `5a05f6d` 只多 `docs/P3_PREREG_ADDENDUM_06.md` |
| C-16 | 测试草案 | 原草案在 `a9fa6c3` 上：`5 failed, 4 passed`（2 个保持测试因 `_CountingProposer.propose()` 不接受新的 `s2_summary` 关键字参数而 TypeError；3 个 §3.4 原因同 C-04）。PR 改写版 `tests/test_t6_frz2.py`：9 passed |

### P2.2 证据包（C-06、R6、R7、A06 §4.7，附加项 (a)/(b)）

脚本 `check_packet_p2.py`（A.P2-3）：130 个 dev seed、`HELPFUL_TEXT_CONTEXT`、`B4_STRICT`，捕获经 `finalize_payload` 之后实际发出的请求，共 350 个。每次调用时读取 `run_episode` 帧中的 `policy_observation_samples`、`canonical_presence_events`、`policy_feedbacks`、`text_context`，与包比较完整性。

| 组 | 包中键 | 缺 C1 | 白名单外键 | 范围实测（350 个请求） |
|---|---|---|---|---|
| `observations` | target_id, step, time, observed_x, observed_y, nominal_x, nominal_y, nominal_speed, episode_id, seq | 无 | `episode_id`, `seq` | 只含当前目标，`seq ≤ decision.seq`；条数等于该目标到此刻的全部策略观测（0 违例） |
| `presence_events` | target_id, step, time, target_observed, episode_id, seq | 无 | `episode_id`, `seq` | 只含当前目标，`seq ≤ decision.seq`；条数完整（0 违例） |
| `command_feedback` | command_id, target_id, issued_time, execution_time, accepted, success, reason_code, episode_id, seq, step | 无 | `episode_id`, `seq`, `step` | 整个 episode；`seq < decision.seq`；条数等于调用时 `policy_feedbacks` 的全部条目（0 违例） |
| `known_config` | dt, tolerance, x_pick, y_pick, belt_speed | 无 | 无 | 恰好 5 个字段（`project_c1_known_config`，`src/rra/evidence/packet.py:9-14`） |

包的其他键（白名单外）：`schema`（`"rra.evidence_packet.v1"`）、`decision`（episode_id, seq, step, target_id, time）、`context`（text, content_sha256）。user message 只有 `evidence_packet` 和 `s2_summary` 两个键。`s2_summary` 的键为 `passing`（行键 structure_id, rmse, n_usable）、`current_time`、`horizon`，没有其他字段。350 个请求中 `context.text` 都等于该 episode 的冻结文本。

逐字段列出，**需所有者确认**（R6 只批准了 `passing[]`、`current_time`、`horizon`）：
1. `evidence_packet.context.text`、`evidence_packet.context.content_sha256`（见下文 (b)）。
2. `evidence_packet.schema`、`evidence_packet.decision.{episode_id, seq, step, target_id, time}`。
3. 行级 `episode_id`、`seq`（三组）与反馈行 `step`。A06 §4.7（main 上，第 61 行）写到 "Rows keep the L3 bookkeeping keys `episode_id` and `seq`, and feedback rows also keep `step`"，但没有提到 `schema`、`decision`、`context`。

时间口径说明（FACT）：每个目标的 `time` 在各自的目标时钟上，跨目标比较用 `seq = target_id × episode_steps + step`（`packet.py:21-26`）。"决策之前"在代码中按 `seq < decision.seq` 实现。`accepted`/`success`/`reason_code` 仍在下发命令那一步写入，`execution_time` = 下发时刻 + 响应延迟（`src/rra/evidence/episode.py` 的 `policy_feedbacks.append`，与 `cb77107` 相同）。

**(b) context 放进 evidence_packet 之后涉及的条文**（只陈述，列入"需所有者裁决/确认"）：
- P3 §12（`docs/P3_SYSTEM2_DESIGN.md:498`）："The System-2 evidence packet may include synthetic but realistic operational text…"
- `docs/H1_EVAL_FOUNDATION.md:17`："Free-form operational text is a separate channel."
- Addendum 02 §4.2（`docs/P3_PREREG_ADDENDUM_02.md:71`）："Only C1 whitelist fields and P3 §12 context records may be written to any Zetaris-reachable source."
- Addendum 03 §2 第 4 项（`:35`）讲 "full whitelisted evidence packet"；第 7 项（`:47`）要求文本按内容哈希与冻结版本一致；包中的 `context.content_sha256` 是 `sha256(text)`（`episode.py` 的 `build_packet` 调用处）。
- Addendum 04 §1.2（`:15`）："Free-form text context enters B4 requests only."；P3 §14（`:629`）："B1/B2/B3 ignore free-form text"。B3 路径不读取这个包（`run_b3` 的输入未变）。
- FACT：`5a05f6d` 上 L3 的 `build_packet` 已经有 `context` 参数并写入 `"context"` 键（PR 对 `packet.py` 只新增了 `project_c1_known_config`），所以 L3 包在 PR 之前就带 context。PR 的变化是 B4 请求改用这个包，不再有单独的 `context_text` 字段（`src/rra/llm/adapter.py` 的 `proposal_request`）。

### P2.3 G4 / R9 模板 SHA 与回执（附加项 3(a)、(b)）

脚本 `g4_check.py`、`b4_receipt_check.py`（A.P2-4、A.P2-5）：

| 检查 | 结果 |
|---|---|
| 只有 `context.text` 不同的两个请求：模板 SHA | 相同（cache key 不同） |
| 证据包与 s2_summary 都不同：模板 SHA | 相同 |
| 从请求体计算 = 默认骨架计算 | 相同 |
| `format_mode` 三种：模板 SHA / cache key | 3 个互不相同 / 3 个互不相同 |
| system prompt 改一个空格：模板 SHA | 不同 |
| 未知 `format_mode` | `ValueError: unknown format_mode: bogus` |
| json_object 模板 SHA | `6a4bc876b1f3bf0c0f68048d55b786bbbf936157c090076b50544decffcf5c25` |

替换方式（FACT）：`request_template_sha256` 把 user message 中的 `evidence_packet` 换成 `"<EVIDENCE_PACKET>"`，`s2_summary` 换成 `"<S2_SUMMARY>"`，再走 `finalize_payload` 和 `canonical_json` 取 SHA-256（`adapter.py` 中 `request_template_sha256`）。context 在 `evidence_packet` 内，所以被一起替换。A06 R9（main，第 75 行）写的是 "the evidence packet and the System-2 summary are replaced by fixed placeholders"，实现与这句文字一致。

回执（临时 ROOT，subset = dev seed 3、21，用桩替换 `ReplayProvider` 并返回 `model = "private/stub-served-model"`）：
- `llm_request_spec.model` = `nvidia/nemotron-3.5-super-vl-120b-a12b`（请求名 `NIM_MODEL`）。服务端返回名记在 `served_models`，形式为 `{model: 响应次数}`，按每次成功响应累加（`b4_dev.py` 的 `_record_model`）：`{'private/stub-served-model': 36}`，等于 `llm_calls` 36。
- 改 `llm_request_spec.request_template_sha256` → 回执哈希变；改 `served_models` → 变；改 `runtime_versions` → 不变。存储哈希 = 按代码规则重算（True）。

### P2.4 G3 format_mode 与 G7 探针（附加项 (c)）

- 三种模式进入 finalized payload：json_object → `response_format.type=json_object`；json_schema → `response_format.type=json_schema`（含 `PROPOSAL_SCHEMA`）；nvext_guided_json → 无 `response_format`，有 `nvext.guided_json`（`providers.py:37-53`）。cache key 是 finalized payload 的 SHA，所以随模式变化（实测 3/3 不同）。
- 默认值 `"json_object"` 定义在 6 处：`finalize_payload` 的 `setting("format_mode", "json_object")`（`providers.py:37`）、`ReplayProvider.__init__`（`:94`）、`NvidiaNimProvider.__init__`（`:117`）、`_ReadThroughProvider.__init__`（`b4_dev.py:32`）、`run_b4_dev`（`:195`）、CLI `--format-mode`（`cli.py:139-140`）。`proposal_request` 本身仍写 `response_format: json_object`，由 `finalize_payload` 覆盖。
- G7 `scripts/b4_probe.py --dry-run --k 10 --max-calls 30`（A.P2-6，把 `NvidiaNimProvider.__init__` 和 `urlopen` 换成抛异常的陷阱）：exit 0，`NvidiaNimProvider constructions: 0`；10 个请求 × 3 种模式，每种模式 10 个不同 key，三种模式之间无重合。代码中 dry-run 在 `:94-98` 返回，live provider 在 `:104` 才构造；dry-run 不写文件（运行后 `git status` 为空）。live 分支会写 `artifacts/s2/b4-probe.json` 和 `artifacts/llm_probe_cache/`（未运行）。

### P2.5 G5 调用计数（附加项 (d)）

- 字段：episode receipt 中的 `strict_proposer_invocations` / `tiebreak_proposer_invocations`（`episode.py` 中 B4 变体才写），按 `run_episode` 内到达 proposer 的次数计（memo 命中也计入）。b4-dev 逐行有同名字段；`metrics.<text_variant>.<mode>` 中两字段都按该文本变体的全部行求和，并在 B4_STRICT 和 B4_TIEBREAK 两行中重复出现。`llm_calls` 仍只记在 B4_STRICT 行（等于 `llm_requests_served` 之和），B4_TIEBREAK 行为 0。
- 桩运行实测：每个 (seed, 变体) `llm_requests_served` = strict = tiebreak（seed 3：2；seed 21：7）；汇总 `llm_calls` 36。

### P2.6 G1 等价测试（附加项 (e)、1(c)）

`tests/test_frz2_packet_equivalence.py`：
- 测试 1：dev seed 0、3、7（`export_sources(..., episodes=8)`），对每个 B4 调用点，比较 B4 内部包与 L3 `load_packets` 的对应包，L3 侧先把 `known_config` 截成 5 字段（`project_c1_known_config`）再比 `packet_sha256`。另外断言 L3 原 `known_config` 比截取后多的正好是 `episode_steps`、`object_count`；断言 `s2_summary` 键为 R6 三项；断言至少一个包带反馈。
- 测试 2：从 `artifacts/s2/b3-dev.json` 的逐决策记录中选出 diag 子集里有 AMBIGUOUS 无 fault 决策的 seed，断言只有 `[3]`，4 个文本变体共 8 个包，对 L3 包截取 known_config 并替换为 B4 的 context 后比哈希。FACT：`b3-dev.json` 只保存前 20 个 seed 的逐决策记录（`src/rra/eval/b3_dev.py:170-172`，`index < 20`），所以测试名中的 "all diag call points" 只覆盖 diag 子集中索引 < 20 的 seed。
- 两个测试比较的都是截取之后的包，且是 `finalize_payload` 取整之前的包；实际发出的是取整后的包。
- 结果：2 passed。

**L3 / Zetaris 路径（附加项 1(b)、3(c)）**：`export_sources(out, 20)` 在 `5a05f6d` 与 `a9fa6c3` 上，5 个表文件 sha256 完全相同（A.P2-7）；20 个 episode 的 `packets_sha256_rollup` 全部相同。审计总哈希不同（`f00df8ea…` → `cecbfbbd…`），唯一差异是 episode 7（seed 7）审计中的 `system2_decisions` 与 `s2_diagnostic_trace`，与 G0-c 改变 seed 7 的复查时刻一致（P2.7）。L3 导出、表结构和包哈希没有因 context 或 known_config 截取而变化。live Zetaris 路径未运行。

### P2.7 G0 保持逻辑改动对照（附加 (1)–(4)）

| 改动 | 改动前（`5a05f6d` = `cb77107` 的 src） | 改动后（`a9fa6c3`） | 对应 Addendum 05 条款 |
|---|---|---|---|
| G0-c 到期容差 | `episode.py:653` `observation.time >= system2_next_retry…`；`:668` 同样 | `:42` `REOBSERVE_RETRY_EPSILON = 1e-9`；`:665`、`:681` 改为 `>= next_retry - REOBSERVE_RETRY_EPSILON` | §1.2；§5 第 1 项 |
| G0-b 已有终态不再进入保持 | `:886-893`（条件在 `:887-888`）：ESCALATE 且 PAUSE 即 `setdefault` 进入保持 | `:913` 增加 `and observation.target_id not in outcomes_by_target` | §1.4；§5 第 2 项相关（终态唯一） |

`episode.py` 中其余改动：新增 `policy_observation_samples`、`canonical_presence_events` 两个列表（只追加、只供 B4 包使用），B4 包构造，以及 B4 receipt 的两个计数字段。B3 路径的输入（`run_b3` 的参数）没有改变。`tests/test_frz1_reobserve.py` 中复查间隔断言从 `<= 0.5 + dt + 1e-9` 收紧为 `<= 0.5 + 1e-9`。

实测（`hold_probe.py`，130 个 dev seed，A.P2-8）：

| 量 | `cb77107` | `a9fa6c3` |
|---|---|---|
| hold_entries / reobservations / authorized_after_hold / exhausted | 183 / 82 / 1 / 182 | 177 / 83 / 1 / 176 |
| end_reasons | window_end 153，latch 11，target_switch 16，episode_end 2，authorized 1，s2_non_pause 0 | window_end 153，latch 11，target_switch 11，episode_end 1，authorized 1，s2_non_pause 0 |
| 以 exhausted 结束的不同对象 + authorized | 176 + 1 = 177 | 176 + 1 = 177 |
| `;REOBSERVE_EXHAUSTED` escalation 行 | 182 | 176 |
| 同一目标多于 1 行的 | 17/9、21/8、39/4、61/11、69/7、83/7 | 无 |
| 保持中 S2 调用与上次调用的间隔 | 0.5 s ×74，0.6 s ×8 | 0.5 s ×83 |
| 间隔 > 0.5 + 1e-9 | 8 个（7/1、7/2、7/7、7/8、53/9、86/1、86/7、91/8，都是 3.8→4.4） | 0 |
| `system2_calls` / `verifier_calls` | 2009 / 28126 | 2010 / 28140 |
| metrics | — | 与 `cb77107` 完全相同：success 84/775，wrong 588，miss 97，unsafe 7（fast_layer_command 7），authorization 210 |

- (1)：hold_entries 177 = 不同对象数 177；exhausted、end_reasons、escalations 中不再有同一目标的重复项。上述 6 个对象的 escalation 行数各减 1（17：9→8，21：5→4，39：11→10，61：9→8，69：10→9，83：9→8）。
- (2)：按本文定义（保持中每次 S2 调用到同目标上一次调用的间隔）共 83 个，全部为 0.5 s。T4/协调消息中的 "11 个 0.6 s" 用的是 T4 的区间定义（245 个区间），与本文的 8 个不是同一口径。变化的调用全部是复查时刻从 x.4/x.9 提前到 x.3/x.8（seed 7、53、86、91），另外 seed 7 target 8 多了一次 4.8 的复查（reobservations +1），seed 61 target 11 一次非保持调用从 8.2 变为 8.1。
- (3)：88/5 的 `trace_88.py` 输出除行号外完全相同：结局 `attempt_failed`/"missed pick window"，命令已下发，position_error 0.2656；决策 0.2 PAUSE、4.9/5.4 PAUSE、5.9 UPDATE；safe_stop 在 4.4（target 2）置 True、5.9（target 5）解除、5.0（target 6）再置 True。行号从 1050/886/905 变为 1076/911/931。
- (4)：130 个 seed 的逐对象结局没有任何变化（`outcomes` 比较无差异）。metrics 不变，`system2_reobserve` 与调用数变化见上表。与协调消息中本地自报的数字（指标不变、88/5 不变、hold_entries 183→177、target_switch 16→11、episode_end 2→1、reobservations 82→83、system2_calls 2009→2010）逐项相同。diff 中 B3/B1 路径上除 G0-b、G0-c 之外没有其他行为改动；B4 路径的改动见 P2.2–P2.5。

### P2.8 `tests/test_t6_frz2.py` 与附录 B.1 草案的对应

| 草案（B.1） | PR 中（`tests/test_t6_frz2.py`） | 断言变化 |
|---|---|---|
| `test_b4_variants_enter_and_exhaust_reobserve_hold_like_b3[B4_STRICT/B4_TIEBREAK]` | 同名 | 断言相同；`_CountingProposer.propose` 签名增加 `s2_summary`（接口变化） |
| `test_actuator_delay_fit_chooses_smallest_delay_within_tie_tolerance` | 同名 | 相同 |
| `test_actuator_delay_fit_without_tie_keeps_strict_minimum` | 同名 | 相同 |
| `test_speed_step_and_delay_tie_selects_lexicographic_smallest_tau_then_delay` | `test_speed_step_delay_tie_selects_lexicographic_smallest_tau_then_delay` | 断言相同；删掉了说明注释 |
| `test_s2_b4_dev_replay_cache_miss_exits_non_zero` | `test_s2_b4_dev_replay_cache_miss_exits_nonzero_without_artifact` | 断言相同（returncode ≠ 0、stderr 含 `ReplayCacheMiss`、无 `b4-dev.json`） |
| `test_b4_request_body_and_cache_key_ignore_last_digit_float_differences` | `test_request_body_and_cache_key_ignore_float_changes_beyond_six_places` | 比较对象从 `propose()` 交给 provider 的请求体改为 `finalize_payload` 之后的 payload；输入从含 `rmse` 的真实形状包、`np.nextafter` 末位改为单个键 `{"value": x}`、x 与 x−1e-15 |
| `test_b4_request_floats_have_at_most_six_decimals` | `test_finalized_request_floats_are_six_decimal_fixed_points` | 检查对象改为 finalized payload，范围扩大到整个 user message（含 `s2_summary`） |
| `test_b4_episode_requests_on_dev_seed_are_rounded_to_six_decimals` | `test_b4_episode_provider_payload_floats_are_rounded_to_six_places` | 检查 finalized payload；新增断言 user message 键 = `{evidence_packet, s2_summary}`，并同时检查 `s2_summary` 中的浮点 |

计数：草案 8 个测试函数、23 条 `assert`；PR 版 8 个、24 条（`grep -c '^\s*assert'`）。没有删除断言。§3.4 的 3 个测试改成检查 finalized payload，这与实现把取整放在 `finalize_payload` 一致。第一个 §3.4 测试的输入不再是真实形状的包，也不再用 `nextafter` 构造末位差异，这一点照实记录。

### P2.9 需所有者裁决/确认（第 2 阶段新增）

1. P2.2 列出的白名单外字段：`evidence_packet.context.{text, content_sha256}`、`schema`、`decision.*`；行级 `episode_id`/`seq`/`step` 已写入 A06 §4.7，另外三项没有。
2. context 放进 `evidence_packet` 与 H1 "separate channel"、Addendum 04 §1.2、Addendum 02 §4.2 的关系（P2.2 (b)）。协调消息提到将用 Addendum 07 登记。
3. 已提交的 `artifacts/s2/b4-dev.json` 与 `artifacts/llm_cache/` 仍是 `c852566` 的版本，`--replay` 在第一个请求就缺失（C-11）；需要在 R4 runner 上 live 重建并重新生成，之后 C-09/C-10/C-11/C-13 才能按期望核验。
4. `served_models` 是 `{model: 次数}` 的汇总，不是逐响应列表；`llm_request_spec.model` 记的是请求名。是否满足 R9 "per response" 的要求，由所有者确认。
5. 等价测试 2 的覆盖范围受 `b3-dev.json` 只存前 20 个 seed 的逐决策记录所限（P2.6）。

### 附录 A.P2 第 2 阶段命令与输出

脚本都在会话 scratchpad 的 `t6/` 目录下。

A.P2-1 `git diff --stat 5a05f6d a9fa6c3`（尾部）与提交列表：

```
a9fa6c3 Record owner rulings R1-R9
53d7410 Add the offline B4 format-mode probe
37b0563 Rebuild the B4 request from the canonical evidence packet
2eccd65 Regenerate B3 artifact after hold conformance fix
a63523d Align re-observation holds with A05 timing
 16 files changed, 6363 insertions(+), 3987 deletions(-)
```

A.P2-2 `git merge-tree --write-tree --name-only origin/main a9fa6c3`：

```
b13144d13a976929b5e386f1a10f7160c01c9523
merge-tree exit=0
```

A.P2-3 `check_packet_p2.py HELPFUL_TEXT_CONTEXT`（在 worktree 中）：

```
variant=HELPFUL_TEXT_CONTEXT seeds=130 requests=350
user message keys ['evidence_packet', 's2_summary']
evidence_packet keys ['command_feedback', 'context', 'decision', 'known_config', 'observations', 'presence_events', 'schema']
observations: keys=['episode_id', 'nominal_speed', 'nominal_x', 'nominal_y', 'observed_x', 'observed_y', 'seq', 'step', 'target_id', 'time'] | missing C1=none | outside C1=['episode_id', 'seq']
presence_events: keys=['episode_id', 'seq', 'step', 'target_id', 'target_observed', 'time'] | missing C1=none | outside C1=['episode_id', 'seq']
known_config: keys=['belt_speed', 'dt', 'tolerance', 'x_pick', 'y_pick'] | missing C1=none | outside C1=none
command_feedback: keys=['accepted', 'command_id', 'episode_id', 'execution_time', 'issued_time', 'reason_code', 'seq', 'step', 'success', 'target_id'] | missing C1=none | outside C1=['episode_id', 'seq', 'step']
decision keys ['episode_id', 'seq', 'step', 'target_id', 'time']
context keys ['content_sha256', 'text']
s2_summary keys ['current_time', 'horizon', 'passing'] | passing row keys ['n_usable', 'rmse', 'structure_id']
scope/timing violations none
examples {}
```

A.P2-4 `g4_check.py`：

```
context-only differ: template equal True | cache key equal False
packet+summary differ: template equal True
template from body == default skeleton template True
template per mode distinct True | cache key per mode distinct True
json_object payload format keys: {'response_format': 'json_object'} False
json_schema payload format keys: {'response_format': 'json_schema'} False
nvext_guided_json payload format keys: {} True
system prompt change -> template differs True
bogus mode -> unknown format_mode: bogus
template sha json_object 6a4bc876b1f3bf0c0f68048d55b786bbbf936157c090076b50544decffcf5c25
```

A.P2-5 `b4_receipt_check.py`：

```
stored == recomputed True
llm_request_spec {"model": "nvidia/nemotron-3.5-super-vl-120b-a12b", "format_mode": "json_object", "max_tokens": 1800, "chat_template_kwargs": {"enable_thinking": false}, "request_template_sha256": "6a4bc876b1f3bf0c0f68048d55b786bbbf936157c090076b50544decffcf5c25"}
served_models {'private/stub-served-model': 36} | llm_calls 36 | llm_requests_served 36
edit llm_request_spec.request_template_sha256 -> hash changes True
edit served_models -> hash changes True
edit runtime_versions -> hash changes False
metrics NO_TEXT_CONTEXT B4_STRICT {'llm_calls': 9, 'strict_proposer_invocations': 9, 'tiebreak_proposer_invocations': 9}
metrics NO_TEXT_CONTEXT B4_TIEBREAK {'llm_calls': 0, 'strict_proposer_invocations': 9, 'tiebreak_proposer_invocations': 9}
metrics HELPFUL_TEXT_CONTEXT B4_STRICT {'llm_calls': 9, 'strict_proposer_invocations': 9, 'tiebreak_proposer_invocations': 9}
metrics HELPFUL_TEXT_CONTEXT B4_TIEBREAK {'llm_calls': 0, 'strict_proposer_invocations': 9, 'tiebreak_proposer_invocations': 9}
metrics IRRELEVANT_TEXT_CONTEXT B4_STRICT {'llm_calls': 9, 'strict_proposer_invocations': 9, 'tiebreak_proposer_invocations': 9}
metrics IRRELEVANT_TEXT_CONTEXT B4_TIEBREAK {'llm_calls': 0, 'strict_proposer_invocations': 9, 'tiebreak_proposer_invocations': 9}
metrics MISLEADING_TEXT_CONTEXT B4_STRICT {'llm_calls': 9, 'strict_proposer_invocations': 9, 'tiebreak_proposer_invocations': 9}
metrics MISLEADING_TEXT_CONTEXT B4_TIEBREAK {'llm_calls': 0, 'strict_proposer_invocations': 9, 'tiebreak_proposer_invocations': 9}
episode keys with proposer ['llm_requests_served', 'strict_proposer_invocations', 'tiebreak_proposer_invocations']
per-episode (seed, variant, served, strict_inv, tie_inv): [(3, 'NO_TEXT_CONTEXT', 2, 2, 2), (3, 'HELPFUL_TEXT_CONTEXT', 2, 2, 2), (3, 'IRRELEVANT_TEXT_CONTEXT', 2, 2, 2), (3, 'MISLEADING_TEXT_CONTEXT', 2, 2, 2), (21, 'NO_TEXT_CONTEXT', 7, 7, 7), (21, 'HELPFUL_TEXT_CONTEXT', 7, 7, 7), (21, 'IRRELEVANT_TEXT_CONTEXT', 7, 7, 7), (21, 'MISLEADING_TEXT_CONTEXT', 7, 7, 7)]
top-level keys ['schema_version', 'subset', 'seed_identity', 'episode_count', 'text_variants', 'N_amb', 'estimated_llm_calls', 'serial_parallel_check', 'llm_requests_served', 'llm_calls', 'metrics', 'episodes', 'llm_request_spec', 'served_models', 'runtime_versions', 'operational_cost', 'receipt_sha256']
```

A.P2-6 `probe_dryrun.py`（输出尾部与 key 统计）：

```
SystemExit 0
NvidiaNimProvider constructions: 0
{'json_object': 10, 'json_schema': 10, 'nvext_guided_json': 10} cross-mode overlap 0
```

A.P2-7 `l3_export_hash.py`，`5a05f6d` 与 `a9fa6c3`：

```
[5a05f6d]
9112912f46366427aaa1c7925c6ba111a2387e840c275ddf8382ad06a40961ef command_feedback.jsonl
d7215ff8a5f54761c78619a61916223184d88bb45c1f58d76855cefbea838f17 known_config.jsonl
f56a175d2a6ae3e827d2f98793c3be36581a94dba747fda21c86aa6164ea004f observation_samples.jsonl
d14c5bca946026ac2671d46a543cd917a228fef9dabc4b512fbbbfc008509184 ops_context.jsonl
bb9ff6bcffee1c063e8602d3b60585d25cec16d3d1f7b32496db3203f8476a92 presence_events.jsonl
audits_sha256 f00df8ea8ca8c6754ff1a5e1fb9dfcfb4028b0000dc7c02d233a5f081e8b4348
episodes 20 decision_points 24000
audit keys ['auth_evidence_nonempty', 'case', 'decision_points', 'hard_fault_latch_decisions', 'mismatches', 'packets_sha256_rollup', 's2_diagnostic_trace', 'seed', 'system2_decisions', 'variant']
[a9fa6c3]
9112912f46366427aaa1c7925c6ba111a2387e840c275ddf8382ad06a40961ef command_feedback.jsonl
d7215ff8a5f54761c78619a61916223184d88bb45c1f58d76855cefbea838f17 known_config.jsonl
f56a175d2a6ae3e827d2f98793c3be36581a94dba747fda21c86aa6164ea004f observation_samples.jsonl
d14c5bca946026ac2671d46a543cd917a228fef9dabc4b512fbbbfc008509184 ops_context.jsonl
bb9ff6bcffee1c063e8602d3b60585d25cec16d3d1f7b32496db3203f8476a92 presence_events.jsonl
audits_sha256 cecbfbbde4cfd735d513863cf309c6399b92ae674ceb4c33742fc8504755fe91
episodes 20 decision_points 24000
audit keys ['auth_evidence_nonempty', 'case', 'decision_points', 'hard_fault_latch_decisions', 'mismatches', 'packets_sha256_rollup', 's2_diagnostic_trace', 'seed', 'system2_decisions', 'variant']
[l3_audit_diff.py 5a05f6d vs a9fa6c3]
0 NO_TEXT_CONTEXT rollup equal True | differing keys []
1 HELPFUL_TEXT_CONTEXT rollup equal True | differing keys []
2 IRRELEVANT_TEXT_CONTEXT rollup equal True | differing keys []
3 MISLEADING_TEXT_CONTEXT rollup equal True | differing keys []
4 NO_TEXT_CONTEXT rollup equal True | differing keys []
5 HELPFUL_TEXT_CONTEXT rollup equal True | differing keys []
6 IRRELEVANT_TEXT_CONTEXT rollup equal True | differing keys []
7 MISLEADING_TEXT_CONTEXT rollup equal True | differing keys ['s2_diagnostic_trace', 'system2_decisions']
8 NO_TEXT_CONTEXT rollup equal True | differing keys []
9 HELPFUL_TEXT_CONTEXT rollup equal True | differing keys []
10 IRRELEVANT_TEXT_CONTEXT rollup equal True | differing keys []
11 MISLEADING_TEXT_CONTEXT rollup equal True | differing keys []
12 NO_TEXT_CONTEXT rollup equal True | differing keys []
13 HELPFUL_TEXT_CONTEXT rollup equal True | differing keys []
14 IRRELEVANT_TEXT_CONTEXT rollup equal True | differing keys []
15 MISLEADING_TEXT_CONTEXT rollup equal True | differing keys []
16 NO_TEXT_CONTEXT rollup equal True | differing keys []
17 HELPFUL_TEXT_CONTEXT rollup equal True | differing keys []
18 IRRELEVANT_TEXT_CONTEXT rollup equal True | differing keys []
19 MISLEADING_TEXT_CONTEXT rollup equal True | differing keys []
```

A.P2-8 `hold_probe.py`，`cb77107` 与 `a9fa6c3`：

```
[cb77107] aggregate {'hold_entries': 183, 'reobservations': 82, 'authorized_after_hold': 1, 'exhausted': 182} {'authorized': 1, 'window_end': 153, 'latch': 11, 'target_switch': 16, 's2_non_pause': 0, 'episode_end': 2}
distinct exhausted targets 176 | REOBSERVE_EXHAUSTED escalation rows 182
targets with >1 REOBSERVE_EXHAUSTED escalation row ['17/9', '21/8', '39/4', '61/11', '69/7', '83/7']
in-hold S2 calls: gap to previous S2 call of same target {0.5: 74, 0.6: 8} total 82
gaps > 0.5+1e-9: 8 ['7/1:3.800->4.400', '7/2:3.800->4.400', '7/7:3.800->4.400', '7/8:3.800->4.400', '53/9:3.800->4.400', '86/1:3.800->4.400', '86/7:3.800->4.400', '91/8:3.800->4.400']
[a9fa6c3] aggregate {'hold_entries': 177, 'reobservations': 83, 'authorized_after_hold': 1, 'exhausted': 176} {'authorized': 1, 'window_end': 153, 'latch': 11, 'target_switch': 11, 's2_non_pause': 0, 'episode_end': 1}
distinct exhausted targets 176 | REOBSERVE_EXHAUSTED escalation rows 176
targets with >1 REOBSERVE_EXHAUSTED escalation row []
in-hold S2 calls: gap to previous S2 call of same target {0.5: 83} total 83
gaps > 0.5+1e-9: 0 []
```

`compare_b3.py`（`a9fa6c3` 两次运行对 PR 中 `b3-dev.json`）：

```
run1 receipt 0fbebcb9f5d024a8d2fbed49a7313d7628fb4129c20abc29538c6920e1968914
run2 receipt 0fbebcb9f5d024a8d2fbed49a7313d7628fb4129c20abc29538c6920e1968914
run1==run2 True
b1_receipt_sha256: run1 vs run2 differ 0/130; run1 vs committed differ 0/130
b3_receipt_sha256: run1 vs run2 differ 0/130; run1 vs committed differ 115/130
metrics run1==committed True
run1 runtime_versions {"python": "3.12.3", "numpy": "2.5.4", "machine": "x86_64", "cpu_model": "Intel(R) Xeon(R) Processor @ 2.10GHz", "blas": {"name": "scipy-openblas", "version": "0.3.34.106.0"}}
committed runtime_versions {"python": "3.12.3", "numpy": "2.5.4", "machine": "x86_64", "cpu_model": "Intel(R) Core(TM) i7-10750H CPU @ 2.60GHz", "blas": {"name": "scipy-openblas", "version": "0.3.34.106.0"}}
committed receipt stored bfda4d101bd79f8d62738807402b33e24aba29028f5f4bc550a9b13304cb1132 recomputed equal True
artifacts/s2/b4-dev.json stored b23231e1e0ea2fb95c3f52ad19bdb8e37068aa87e0c8aa2e2212dd11862231a6 recomputed equal True
```

全量 pytest 尾部：

```
=========================== short test summary info ============================
SKIPPED [1] tests/test_meterless_bridge.py:219: needs Node, scripts/setup_meterless.sh and RRA_METERLESS_LIVE=1
SKIPPED [1] tests/test_meterless_bridge.py:240: needs Node, scripts/setup_meterless.sh and RRA_METERLESS_LIVE=1
SKIPPED [1] tests/test_meterless_bridge.py:249: needs Node, scripts/setup_meterless.sh and RRA_METERLESS_LIVE=1
SKIPPED [1] tests/test_packet_sources.py:48: Zetaris live checks are opt-in
221 passed, 4 skipped in 320.15s (0:05:20)
exit=0
```

第 2 阶段脚本全文：

```python
# ---- check_packet_p2.py
"""T6 phase 2: B4 request packet vs C1 / R6 / R7 / A06 §4.7, over dev seeds. Offline; reads caller-frame
locals of run_episode at each propose() call to compare against the full policy-visible lists."""
import json, sys
from collections import Counter, defaultdict
from rra.eval.b4_dev import _realization
from rra.eval.context_v3 import freeze_episode_contexts
from rra.eval.framework import v3_world_config
from rra.evidence import run_episode
from rra.llm.adapter import HypothesisProposer
from rra.llm.providers import ReplayProvider, finalize_payload

C1 = {"observations": {"target_id", "step", "time", "observed_x", "observed_y", "nominal_x", "nominal_y", "nominal_speed"},
      "presence_events": {"target_id", "step", "time", "target_observed"},
      "known_config": {"dt", "tolerance", "x_pick", "y_pick", "belt_speed"},
      "command_feedback": {"command_id", "target_id", "issued_time", "execution_time", "accepted", "success", "reason_code"}}
SETTINGS = ReplayProvider("unused").settings
seeds_all = json.load(open("config/dev_seeds.json"))["seeds"]
variant = sys.argv[1]; seeds = [int(x) for x in sys.argv[2:]] or seeds_all
keysets = defaultdict(set); viol = Counter(); ex = defaultdict(list); n = 0
top_keys = set(); user_keys = set(); summary_keys = set(); passing_keys = set(); decision_keys = set(); context_keys = set()
def bad(kind, msg):
    viol[kind] += 1
    if len(ex[kind]) < 3: ex[kind].append(msg)
class Cap:
    last_http_status = None
    def complete(self, body):
        global n
        n += 1
        f = sys._getframe(1)  # walk back to run_episode
        while f.f_code.co_name != "run_episode": f = f.f_back
        L = f.f_locals
        sent = finalize_payload(body, SETTINGS)
        user = json.loads(sent["messages"][1]["content"]); user_keys.update(user)
        p = user["evidence_packet"]; s = user.get("s2_summary") or {}
        top_keys.update(p); summary_keys.update(s); decision_keys.update(p["decision"]); context_keys.update(p.get("context", {}))
        for r in s.get("passing", []): passing_keys.update(r)
        d = p["decision"]; tid, seq = d["target_id"], d["seq"]
        for g in ("observations", "presence_events", "command_feedback"):
            for r in p[g]: keysets[g].update(r)
        keysets["known_config"].update(p["known_config"])
        for r in p["observations"] + p["presence_events"]:
            if r["target_id"] != tid: bad("obs/presence other target", (seed, d))
            if r["seq"] > seq: bad("obs/presence after decision", (seed, d, r["seq"]))
        for r in p["command_feedback"]:
            if r["seq"] >= seq: bad("feedback at/after decision seq", (seed, d, r["seq"]))
        # completeness vs the run's own policy-visible lists at call time
        exp_obs = [r for r in L["policy_observation_samples"] if r["target_id"] == tid and r["seq"] <= seq]
        exp_pres = [r for r in L["canonical_presence_events"] if r["target_id"] == tid and r["seq"] <= seq]
        if len(exp_obs) != len(p["observations"]): bad("observations count != policy list", (seed, d, len(exp_obs), len(p["observations"])))
        if len(exp_pres) != len(p["presence_events"]): bad("presence count != policy list", (seed, d))
        if len(L["policy_feedbacks"]) != len(p["command_feedback"]): bad("feedback count != policy_feedbacks so far", (seed, d, len(L["policy_feedbacks"]), len(p["command_feedback"])))
        ctx = p.get("context", {})
        if ctx.get("text") != L["text_context"]: bad("context text != frozen text", (seed, d))
        return {"choices": [{"message": {"content": '{"items": []}'}}]}
for seed in seeds:
    real = _realization(seeds_all.index(seed), seed)
    txt = freeze_episode_contexts(str(seed), seed, real.fault_family or real.structure)[variant].text
    run_episode(v3_world_config("nominal"), seed, True, terminal_monitoring="corrected", realization=real,
                text_context=txt, system2_enabled=True, s2_variant="B4_STRICT", proposer=HypothesisProposer(Cap()))
print(f"variant={variant} seeds={len(seeds)} requests={n}")
print("user message keys", sorted(user_keys)); print("evidence_packet keys", sorted(top_keys))
for g, req in C1.items():
    got = keysets[g]
    print(f"{g}: keys={sorted(got)} | missing C1={sorted(req - got) or 'none'} | outside C1={sorted(got - req) or 'none'}")
print("decision keys", sorted(decision_keys)); print("context keys", sorted(context_keys))
print("s2_summary keys", sorted(summary_keys), "| passing row keys", sorted(passing_keys))
print("scope/timing violations", dict(viol) or "none"); print("examples", dict(ex))
# ---- g4_check.py
"""T6 phase 2: request template SHA (R9 / A06 erratum reading), format_mode in payload & cache key."""
import json
from rra.llm.adapter import proposal_request, request_template_sha256, SYSTEM_PROMPT
from rra.llm.providers import finalize_payload, request_sha256, NIM_MODEL
def settings(mode): return {"model": NIM_MODEL, "format_mode": mode, "max_tokens": 1800,
                            "chat_template_kwargs": {"enable_thinking": False}}
def pkt(text, x=-4.79, tid=5):
    return {"schema": "rra.evidence_packet.v1", "observations": [{"target_id": tid, "observed_x": x}],
            "context": {"text": text, "content_sha256": "h:" + text}}
summ = {"passing": [{"structure_id": "SENSOR_BIAS", "rmse": 0.01, "n_usable": 10}], "current_time": 0.9, "horizon": 9.9}
s = settings("json_object")
a = proposal_request(pkt("motor serviced"), summ); b = proposal_request(pkt("sensor recalibrated"), summ)
c = proposal_request(pkt("motor serviced", x=-1.0, tid=7), {**summ, "current_time": 3.3})
T = lambda body, st=s: request_template_sha256(st, body)
print("context-only differ: template equal", T(a) == T(b), "| cache key equal", request_sha256(finalize_payload(a, s)) == request_sha256(finalize_payload(b, s)))
print("packet+summary differ: template equal", T(a) == T(c))
print("template from body == default skeleton template", T(a) == request_template_sha256(s))
modes = ["json_object", "json_schema", "nvext_guided_json"]
tm = {m: T(a, settings(m)) for m in modes}; ck = {m: request_sha256(finalize_payload(a, settings(m))) for m in modes}
print("template per mode distinct", len(set(tm.values())) == 3, "| cache key per mode distinct", len(set(ck.values())) == 3)
for m in modes:
    p = finalize_payload(a, settings(m)); print(m, "payload format keys:", {k: (v if k != "response_format" else v.get("type")) for k, v in p.items() if k in ("response_format",)} , "nvext" in p)
alt = proposal_request(pkt("x"), summ); alt["messages"][0]["content"] = SYSTEM_PROMPT + " "
print("system prompt change -> template differs", T(alt) != T(a))
try:
    finalize_payload(a, settings("bogus")); print("bogus mode accepted")
except ValueError as e: print("bogus mode ->", e)
print("template sha json_object", tm["json_object"])
# ---- b4_receipt_check.py
"""run_b4_dev on dev seed 3 (subset file in a temp ROOT) with a stub replay provider; then field-edit checks."""
import copy, json, shutil, sys, tempfile
from hashlib import sha256
from pathlib import Path
import rra.eval.b4_dev as b4
tmp = Path(tempfile.mkdtemp(dir=sys.argv[1]))
(tmp / "config").mkdir(); (tmp / "artifacts/s2").mkdir(parents=True); (tmp / "artifacts/llm_cache").mkdir()
shutil.copy("config/dev_seeds.json", tmp / "config/dev_seeds.json")
(tmp / "artifacts/s2/diag-d1g.json").write_text(json.dumps({"seeds": [3, 21]}))
class StubReplay:
    def __init__(self, *a, **k): self.n = 0
    def complete(self, body):
        self.n += 1
        return {"model": "private/stub-served-model", "choices": [{"message": {"content": '{"items": []}'}, "finish_reason": "stop"}]}
b4.ROOT = tmp; b4.ReplayProvider = StubReplay
r = b4.run_b4_dev(tmp / "out", nproc=1, subset=True, replay_only=True)
def rh(d):
    h = {k: v for k, v in d.items() if k not in ("runtime_versions", "operational_cost", "receipt_sha256")}
    return sha256(json.dumps(h, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
print("stored == recomputed", rh(r) == r["receipt_sha256"])
print("llm_request_spec", json.dumps(r["llm_request_spec"]))
print("served_models", r["served_models"], "| llm_calls", r["llm_calls"], "| llm_requests_served", r["llm_requests_served"])
for path, val in ((("llm_request_spec", "request_template_sha256"), "0" * 64), (("served_models",), {"x": 1}),
                  (("runtime_versions",), {"python": "0"})):
    d = copy.deepcopy(r); t = d
    for k in path[:-1]: t = t[k]
    t[path[-1]] = val
    print("edit", ".".join(path), "-> hash changes", rh(d) != r["receipt_sha256"])
m = r["metrics"]
for mode in m:
    for var, row in (m[mode].items() if isinstance(m[mode], dict) else []):
        if isinstance(row, dict) and "strict_proposer_invocations" in row:
            print("metrics", mode, var, {k: row[k] for k in ("llm_calls", "strict_proposer_invocations", "tiebreak_proposer_invocations")})
ep = r["episodes"]
print("episode keys with proposer", sorted(k for k in ep[0] if "proposer" in k or "llm" in k))
print("per-episode (seed, variant, served, strict_inv, tie_inv):", [(e["seed"], e["text_variant"], e["llm_requests_served"], e["strict_proposer_invocations"], e["tiebreak_proposer_invocations"]) for e in ep])
print("top-level keys", list(r))
# ---- probe_dryrun.py
"""Run scripts/b4_probe.py --dry-run with live provider construction and network trapped."""
import sys, runpy, urllib.request
import rra.llm.providers as P
built = []
def trap_init(self, *a, **k): built.append(k); raise AssertionError("NvidiaNimProvider constructed")
P.NvidiaNimProvider.__init__ = trap_init
def trap_net(*a, **k): raise AssertionError("network")
urllib.request.urlopen = trap_net; P.urlopen = trap_net
sys.argv = ["b4_probe.py", "--dry-run", "--k", "10", "--max-calls", "30"]
try:
    runpy.run_path("scripts/b4_probe.py", run_name="__main__")
except SystemExit as e:
    print("SystemExit", e.code)
print("NvidiaNimProvider constructions:", len(built))
# ---- hold_probe.py
"""T6 phase-2 probe (read-only instrumentation, src/ unchanged).
Wraps module-global rra.evidence.episode.run_b3 (same replacement point as tests/test_frz1_reobserve.py)
and reads the caller frame's system2_reobserve_holds / observation at each call."""
import json, sys
from collections import Counter, defaultdict
from rra.eval.b4_dev import _realization
from rra.eval.framework import v3_world_config
from rra.evidence import run_episode
import rra.evidence.episode as ep

out_path = sys.argv[1]
seeds = json.load(open("config/dev_seeds.json"))["seeds"]
config = v3_world_config("nominal")
original = ep.run_b3
calls = []
def wrapped(*a, **k):
    f = sys._getframe(1)
    obs = f.f_locals.get("observation"); holds = f.f_locals.get("system2_reobserve_holds", {})
    tid = getattr(obs, "target_id", None)
    calls.append({"target": tid, "time": k.get("current_time"), "in_hold": tid in holds})
    return original(*a, **k)
ep.run_b3 = wrapped
rows = {}
for index, seed in enumerate(seeds):
    calls.clear()
    r = run_episode(config, seed, True, terminal_monitoring="corrected",
                    realization=_realization(index, seed), system2_enabled=True)
    exhausted = [e["target_id"] for e in r["escalations"] if e["reason"].endswith(";REOBSERVE_EXHAUSTED")]
    rows[seed] = {"reobserve": r["system2_reobserve"], "metrics_inputs": None,
                  "exhausted_targets": exhausted, "calls": list(calls),
                  "outcomes": {str(o["target_id"]): [o["status"], o["reason"]] for o in r["outcomes"]},
                  "escalation_rows": len(r["escalations"])}
json.dump(rows, open(out_path, "w"))
agg = Counter(); ends = Counter(); dup = []; gaps = Counter(); over = []
for seed, row in rows.items():
    for k in ("hold_entries", "reobservations", "authorized_after_hold", "exhausted"):
        agg[k] += row["reobserve"][k]
    ends.update(row["reobserve"]["end_reasons"])
    dup += [f"{seed}/{t}" for t, n in Counter(row["exhausted_targets"]).items() if n > 1]
    last = {}
    for c in row["calls"]:
        if c["in_hold"] and c["target"] in last:
            g = c["time"] - last[c["target"]]; gaps[round(g, 6)] += 1
            if g > 0.5 + 1e-9: over.append(f"{seed}/{c['target']}:{last[c['target']]:.3f}->{c['time']:.3f}")
        last[c["target"]] = c["time"]
print("aggregate", dict(agg), dict(ends))
print("distinct exhausted targets", sum(len(set(r["exhausted_targets"])) for r in rows.values()),
      "| REOBSERVE_EXHAUSTED escalation rows", sum(len(r["exhausted_targets"]) for r in rows.values()))
print("targets with >1 REOBSERVE_EXHAUSTED escalation row", dup)
print("in-hold S2 calls: gap to previous S2 call of same target", dict(sorted(gaps.items())), "total", sum(gaps.values()))
print("gaps > 0.5+1e-9:", len(over), over)
# ---- trace_88.py
"""safe_stop transitions and target-5 events in dev seed 88 (line trace on run_episode frame)."""
import json, sys
from rra.eval.b4_dev import _realization
from rra.eval.framework import v3_world_config
from rra.evidence import run_episode
import rra.evidence.episode as ep
seeds = json.load(open("config/dev_seeds.json"))["seeds"]; seed = 88
trans = []; last = [None]
def tr(frame, event, arg):
    if frame.f_code.co_name != "run_episode" or frame.f_code.co_filename != ep.__file__:
        return None
    def local(frame, event, arg):
        v = frame.f_locals.get("safe_stop")
        if v is not None and v != last[0]:
            obs = frame.f_locals.get("observation")
            trans.append((getattr(obs, "time", None), getattr(obs, "target_id", None), frame.f_lineno, last[0], v))
            last[0] = v
        return local
    return local
sys.settrace(tr)
r = run_episode(v3_world_config("nominal"), seed, True, terminal_monitoring="corrected",
                realization=_realization(seeds.index(seed), seed), system2_enabled=True)
sys.settrace(None)
print("safe_stop transitions (obs.time, obs.target, line, old, new):")
for t in trans: print("  ", t)
o = next(x for x in r["outcomes"] if x["target_id"] == 5); e = next(x for x in r["evaluator_objects"] if x["target_id"] == 5)
print("88/5 outcome", o["status"], o["reason"]); print("88/5 evaluator", {k: e.get(k) for k in ("command_issued", "position_error", "target_exists_at_execution")})
print("88/5 decisions", [(d["time"], d["action"], d["gate_reason"]) for d in r["system2_decisions"] if d["target_id"] == 5])
print("reobserve", r["system2_reobserve"])
# ---- l3_export_hash.py
"""T6: export L3 source tables to a scratch dir and hash files + per-episode audits."""
import hashlib, json, sys
from pathlib import Path
from rra.evidence.sources import export_sources
out = Path(sys.argv[1]); res = export_sources(out, 20)
for p in sorted(out.rglob("*")):
    if p.is_file(): print(hashlib.sha256(p.read_bytes()).hexdigest(), p.relative_to(out))
print("audits_sha256", hashlib.sha256(json.dumps(res["audits"], sort_keys=True).encode()).hexdigest())
print("episodes", len(res["audits"]), "decision_points", sum(a["decision_points"] for a in res["audits"]))
print("audit keys", sorted(res["audits"][0]))
# ---- l3_audit_diff.py
"""Run export_sources in two source trees (via subprocess) and diff per-episode audit fields."""
import json, subprocess, sys
code = "import json,sys;from pathlib import Path;from rra.evidence.sources import export_sources;r=export_sources(Path(sys.argv[1]),20);print(json.dumps(r['audits']))"
def run(tree, out):
    return json.loads(subprocess.run([sys.executable, "-c", code, out], cwd=tree, env={"PYTHONPATH": tree + "/src", "PATH": "/usr/bin:/bin"},
                                     capture_output=True, text=True, check=True).stdout)
a = run(sys.argv[1], sys.argv[3]); b = run(sys.argv[2], sys.argv[4])
for x, y in zip(a, b):
    diff = [k for k in sorted(set(x) | set(y)) if x.get(k) != y.get(k)]
    print(x["seed"], x["variant"], "rollup equal", x["packets_sha256_rollup"] == y["packets_sha256_rollup"], "| differing keys", diff)
```

### P2.10 方案 (i) 条件核对

所有者对 context 选了方案 (i)：保留 FRZ-2A 的结构，文本放在 `evidence_packet.context`，由 A07 登记。下面逐条给出实测，只陈述结果。

**条件 1：L3 / Zetaris 路径的证据包哈希相对 `5a05f6d` 是否不变。**
- `export_sources(out, 20)`：5 个表文件（`command_feedback`、`known_config`、`observation_samples`、`ops_context`、`presence_events`）的 sha256 在 `5a05f6d` 与 `a9fa6c3` 上完全相同。20 个 episode 的 `packets_sha256_rollup` 全部相同（A.P2-7）。
- 包哈希没有变化，所以没有需要用 context 位置或 known_config 截取来解释的字段。审计中唯一不同的是 seed 7 的 `system2_decisions` 与 `s2_diagnostic_trace`（B3 决策记录，不是包），来源是 G0-c（P2.7）。
- L3 侧代码：`packet.py` 的 `build_packet` 在 `5a05f6d` 上已经带 `context` 和 `decision`，PR 只新增了 `project_c1_known_config`；`sources.py` 未改动，L3 包的 `known_config` 仍是 7 个字段（`sources.py:94`、`:107`）。
- live Zetaris 路径未运行。

**条件 2：除 R6 批准的项外，`evidence_packet.context` 是否是唯一新增的白名单外键。**
- 不是。350 个实际请求中，白名单外的键还有：`evidence_packet.schema`；`evidence_packet.decision.{episode_id, seq, step, target_id, time}`；三组行级的 `episode_id`、`seq`；反馈行的 `step`（P2.2）。
- 其中行级 `episode_id`/`seq`/`step` 已写入 A06 §4.7。`schema`、`decision`、`context` 没有写入。
- 这些键在 `5a05f6d` 上的 L3 包中都已存在；对 B4 请求来说，相对 `cb77107` 的旧包都是新增的。

**条件 3：`context.text` 是否与冻结的 §12 文本一致，泄漏校验是否仍然作用于它。**
- 脚本 `m3_context_check.py`（A.P2-9）：130 个 dev seed × 4 个文本变体，每个变体 350 个请求。`context.text == freeze_episode_contexts(...)[variant].text` 为 350/350，`context.content_sha256 == frozen.content_sha256` 为 350/350，四个变体都是如此。
- 生成器：B4 包里的文本来自 `run_episode` 的 `text_context` 参数，`run_b4_dev` 传入的是 `freeze_episode_contexts(str(seed), seed, cause)` 的 `.text`（`b4_dev.py:221`）。L3 的 `ops_context` 也用 `freeze_context`，即同一个生成器。`content_sha256` 由 `episode.py` 自己用 `sha256(text)` 计算，算法与 `context_v3.content_sha256` 相同，实测值一致。
- 泄漏校验：`generate_context` 在生成时调用 `validate_text_context(text, hidden_values)` 与 `_numeric_leak_check(text)`（`src/rra/eval/context_v3.py:171-172`）。`run_b4_dev` 在每个任务开始时调用 `verify_frozen_context(frozen)`（`b4_dev.py:228-229`），检查冻结文本与其哈希一致。
- 请求构造阶段没有对 `evidence_packet.context` 再做一次泄漏校验或哈希比对；正因为文本与冻结版本逐字相同，生成时的校验结果适用于它。`run_b4_dev` 调用 `freeze_episode_contexts` 时没有传 `hidden_values`（使用默认空元组），这与 `5a05f6d` 相同。`context_v3.py` 在 PR 中没有改动。

### P2.11 `decision.episode_id` 中的种子值（T9a M-3）

脚本 `m3_context_check.py`（A.P2-9），只读，离线。

**(a) dev 上实际 B4 请求中 `decision.episode_id` 是否等于 seed。**
- 是。`NO_TEXT_CONTEXT` 下 350 个请求，`decision.episode_id == str(seed)` 为 350/350。例：`{'episode_id': '0', 'seq': 709, 'step': 9, 'target_id': 7, 'time': 0.9}`。
- 同一个值还出现在其他位置：观测行 `episode_id` 16380/16380 等于 `str(seed)`；presence 和反馈行同样带 `episode_id`。C1 字段 `command_id` 的格式为 `f"{seed}:{target_id}:{step}"`（`episode.py` 的 `command_feedback(...)` 调用处，`cb77107` 上已是如此）；279 个请求的反馈非空，且全部以 seed 为前缀。
- 来源：`episode.py:705-706` 用 `episode_id=str(seed)` 调 `build_packet`；`packet.py:34-35` 写入 `decision`。L3 侧 `sources.py:69` 也是 `episode_id = str(seed)`（`5a05f6d` 上已如此）。

**(b) 缓存文件是否保存这个值。**
- live provider 会把它写进缓存。`NvidiaNimProvider.complete` 把 `{"request": payload, "response": response_body}` 写到 `cache_dir/<sha>.json`（`providers.py` 中 `complete` 末尾），其中 `payload` 是 finalized 请求，含完整 user message。
- 离线实测：不调用 `__init__`、不使用任何 key，构造一个 `NvidiaNimProvider` 对象，把 `urlopen` 换成本地假响应，然后发一个 dev 请求。结果写出 1 个缓存文件，文件中 `request.messages[1].content` 的 `decision` 为 `{'episode_id': '0', ...}`，等于 seed；记录中不含占位 key 字符串。临时文件放在 scratchpad。
- 当前已提交的 `artifacts/llm_cache/`（386 条，`c852566` 的旧格式）中，含 `"episode_id` 的文件为 0 个。
- `ReplayProvider` 只读不写。

**(c) 模板 SHA 的占位符替换是否覆盖 `decision`。**
- 覆盖。`request_template_sha256` 把整个 `evidence_packet`（含 `decision`）换成 `"<EVIDENCE_PACKET>"`。实测只改 `decision.episode_id`（`"0"` → `"999999"`）时，模板 SHA 相同，cache key 不同。

**(d) `decision` 中除 R6 批准项之外的非 C1 键。**
- `decision` 的键为 `episode_id`、`seq`、`step`、`target_id`、`time`。
- R6 批准的 `current_time`、`horizon`、`passing[]` 都在 `s2_summary` 中，不在 `decision` 中。
- `target_id`、`step`、`time` 是 C1 观测/在场事件中的字段名；`decision.time` 与 `s2_summary.current_time` 取值相同（同为 `observation.time`）。
- `episode_id`、`seq` 不是 C1 字段。

需所有者裁决（追加到 P2.9）：
6. B4 请求和 live 缓存记录会带种子值：`decision.episode_id`、行级 `episode_id`，以及 C1 字段 `command_id` 的前缀。eval-v3 时这些位置会写入 eval 种子值，并发给 provider、落入 `artifacts/llm_cache/`。这与 P3 §18.1 / Addendum 01–03 中关于 eval 种子隔离的条文之间的关系，由所有者裁决。

A.P2-9 `m3_context_check.py` 输出：

```
context vs frozen per variant: {'NO_TEXT_CONTEXT': {'requests': 350, 'text_eq': 350, 'sha_eq': 350}, 'HELPFUL_TEXT_CONTEXT': {'requests': 350, 'text_eq': 350, 'sha_eq': 350}, 'IRRELEVANT_TEXT_CONTEXT': {'requests': 350, 'text_eq': 350, 'sha_eq': 350}, 'MISLEADING_TEXT_CONTEXT': {'requests': 350, 'text_eq': 350, 'sha_eq': 350}}
decision.episode_id / row episode_id / command_id prefix vs seed: {'requests': 350, 'eq_seed': 350, 'cmd_id_has_seed': 279, 'obs_rows_eq_seed': 16380, 'obs_rows': 16380}
example decision {'episode_id': '0', 'seq': 709, 'step': 9, 'target_id': 7, 'time': 0.9}
template equal when only decision.episode_id differs: True | cache key equal: False
cache files written: 1 | stored request decision: {'episode_id': '0', 'seq': 709, 'step': 9, 'target_id': 7, 'time': 0.9} | episode_id == seed: True
headers/key in record: False
```

```python
"""T6 phase 2 add-on: context text vs frozen §12 text (4 variants), decision.episode_id vs seed,
template-SHA coverage of decision, and whether the live provider writes the request body to disk.
Offline: the live provider is created without __init__ (no API key) and urlopen is replaced by a fake."""
import copy, io, json, sys, tempfile
from pathlib import Path
from rra.eval.b4_dev import _realization
from rra.eval.context_v3 import VARIANTS, freeze_episode_contexts
from rra.eval.framework import v3_world_config
from rra.evidence import run_episode
from rra.llm.adapter import HypothesisProposer, request_template_sha256
import rra.llm.providers as P

seeds_all = json.load(open("config/dev_seeds.json"))["seeds"]
seeds = [int(x) for x in sys.argv[1:]] or seeds_all
SET = P.ReplayProvider("unused").settings
class Cap:
    last_http_status = None
    def __init__(s): s.b = []
    def complete(s, body): s.b.append(body); return {"choices": [{"message": {"content": '{"items": []}'}}]}
stats = {v: dict(requests=0, text_eq=0, sha_eq=0) for v in VARIANTS}
ep = dict(requests=0, eq_seed=0, cmd_id_has_seed=0, obs_rows_eq_seed=0, obs_rows=0); first = None
for seed in seeds:
    real = _realization(seeds_all.index(seed), seed)
    ctx = freeze_episode_contexts(str(seed), seed, real.fault_family or real.structure)
    for v in VARIANTS:
        cap = Cap()
        run_episode(v3_world_config("nominal"), seed, True, terminal_monitoring="corrected", realization=real,
                    text_context=ctx[v].text, system2_enabled=True, s2_variant="B4_STRICT", proposer=HypothesisProposer(cap))
        for body in cap.b:
            sent = P.finalize_payload(body, SET); p = json.loads(sent["messages"][1]["content"])["evidence_packet"]
            st = stats[v]; st["requests"] += 1
            st["text_eq"] += p["context"]["text"] == ctx[v].text
            st["sha_eq"] += p["context"]["content_sha256"] == ctx[v].content_sha256
            if v == "NO_TEXT_CONTEXT":
                ep["requests"] += 1; ep["eq_seed"] += p["decision"]["episode_id"] == str(seed)
                for r in p["observations"]: ep["obs_rows"] += 1; ep["obs_rows_eq_seed"] += r["episode_id"] == str(seed)
                ep["cmd_id_has_seed"] += all(f["command_id"].split(":")[0] == str(seed) for f in p["command_feedback"]) and bool(p["command_feedback"])
                if first is None: first = (seed, body)
print("context vs frozen per variant:", stats)
print("decision.episode_id / row episode_id / command_id prefix vs seed:", ep)
seed0, body = first
print("example decision", json.loads(P.finalize_payload(body, SET)["messages"][1]["content"])["evidence_packet"]["decision"])
# (c) template SHA when only decision.episode_id differs
alt = copy.deepcopy(body); u = json.loads(alt["messages"][1]["content"]); u["evidence_packet"]["decision"]["episode_id"] = "999999"
alt["messages"][1]["content"] = json.dumps(u)
print("template equal when only decision.episode_id differs:", request_template_sha256(SET, body) == request_template_sha256(SET, alt),
      "| cache key equal:", P.request_sha256(P.finalize_payload(body, SET)) == P.request_sha256(P.finalize_payload(alt, SET)))
# (b) does a live provider write the finalized request (with decision) to disk? fake HTTP, no key.
tmp = Path(tempfile.mkdtemp(dir=sys.argv[0].rsplit("/", 1)[0]))
prov = object.__new__(P.NvidiaNimProvider)
prov.api_key = "UNUSED"; prov.cache_dir = tmp; prov.timeout = 1; prov.base_url = "http://invalid"; prov.model = P.NIM_MODEL
prov.max_tokens = 1800; prov.chat_template_kwargs = {"enable_thinking": False}; prov.no_think = False; prov.format_mode = "json_object"
prov.last_http_status = None; prov.last_latency_seconds = None; prov.last_response_body = None; prov.last_request_body = None
class FakeResp(io.BytesIO):
    status = 200
    def __enter__(s): return s
    def __exit__(s, *a): return False
P.urlopen = lambda req, timeout=None: FakeResp(json.dumps({"model": "fake", "choices": [{"message": {"content": '{"items": []}'}}]}).encode())
prov.complete(body)
files = list(tmp.glob("*.json")); rec = json.loads(files[0].read_text())
dec = json.loads(rec["request"]["messages"][1]["content"])["evidence_packet"]["decision"]
print("cache files written:", len(files), "| stored request decision:", dec, "| episode_id == seed:", dec["episode_id"] == str(seed0))
print("headers/key in record:", "UNUSED" in files[0].read_text())
```

---

## 第 3 阶段（PR #27，FRZ-2A-R1）

本节在第 2 阶段之后追加，第 1、2 阶段内容未改动。

- 审查对象：PR #27 新 head `466bec6613f3950b12c00c789ed81c4c36aa3e39`（`git rev-parse origin/feat/frz2-b4req`），单个新提交 "Strip seed identifiers from the B4 generator request"，父提交 `a9fa6c3`。
- 改动文件：`src/rra/evidence/episode.py`（+3/−3）、`src/rra/evidence/packet.py`（+21）、`tests/test_frz2_packet_equivalence.py`（+42/−12）。环境、只读 worktree、离线约束同第 2 阶段；没有 live 调用，没有设置 key。
- 合成种子：第 1 项使用 `100000007`、`987654320` 两个 9 位数。它们是我自己选的值，不来自任何种子文件。PR 中的测试用的是 `987654321`、`123456789`。

### P3.1 最终请求中的种子标识（第 1 项）

脚本 `p3_seed_check.py`（A.P3-1）对每个 B4 请求取 `canonical_json(finalize_payload(...))`，解析 user message 后逐键遍历：

| 范围 | 请求数 | `episode_id` 键 | 字符串值等于 `str(seed)` 或以 `"{seed}:"` 开头 | 9 位种子子串出现在整个 payload 中 |
|---|---|---|---|---|
| 130 个 dev seed，`HELPFUL_TEXT_CONTEXT` | 350 | 0 | 2（都在 `command_feedback[].command_id`，见下） | 不适用 |
| 合成 seed `100000007`、`987654320`，4 个变体 | 4 | 0 | 0 | 0 |

- dev 上的 2 处命中不是种子：生成器视图中 `command_id` 为 `"{target_id}:{step}"`，当 `target_id` 恰好等于一个短 seed（例如 seed 1 的 target 1）时，值也以 `"{seed}:"` 开头。按键值位置看，840 个 `command_id` 全部等于 `f"{target_id}:{step}"`（下一节），所以这 2 处是 target_id。
- 短 seed（0、1 这类）在整个 payload 中做子串检查没有意义，所以只对 9 位种子做了这项检查。
- 用第 2 阶段的方法（不调用 `__init__`、`urlopen` 换成假响应）让 live provider 写出一次缓存：文件中不含种子子串，也不含 `episode_id` 键。
- PR 新增的 `test_b4_finalized_payload_omits_nine_digit_seed_identifiers` 检查 finalized payload 不含 `str(seed)` 和 `"episode_id"`：passed。

### P3.2 `command_id`（第 2 项）

- 生成器视图：dev 350 个请求中 840 个 `command_id`、合成 seed 中 24 个，全部等于 `f"{target_id}:{step}"`。由 `generator_view` 改写（`src/rra/evidence/packet.py` 中新增函数）。
- L3：`export_sources(out, 20)` 的 `command_feedback.jsonl` 共 128 行，`command_id == f"{episode_id}:{target_id}:{step}"` 为 128/128，仍是原格式（例：`"0:0:55"`）。

### P3.3 白名单外键（第 3 项，对照 R12）

`check_packet_p2.py`（第 2 阶段脚本，未改）在 `466bec6` 上运行，130 个 dev seed、350 个请求：
- user message 键：`evidence_packet`、`s2_summary`。
- `evidence_packet` 键：`schema`、`observations`、`presence_events`、`command_feedback`、`known_config`、`context`、`decision`。
- 每组的白名单外键：observations `seq`；presence_events `seq`；command_feedback `seq`、`step`；known_config 无。
- `decision` 键：`seq`、`step`、`target_id`、`time`。`context` 键：`text`、`content_sha256`。`s2_summary` 键：`passing`（行键 structure_id, rmse, n_usable）、`current_time`、`horizon`。
- 白名单外的键是 `schema`、`decision.{seq, step, target_id, time}`、行级 `seq`/`step`、`context.*`。此外没有其他白名单外键（`s2_summary` 为 R6 项）。C1 字段均无缺失；R7 范围与"决策之前"0 违例。

### P3.4 等价测试（第 4 项）

- 两个原有测试的期望值都改为 `_projected_generator_view(reference, context)`，即 `generator_view({**L3 包, known_config: project_c1_known_config(...), context: B4 的冻结 context})`。比较方式从只比 `packet_sha256` 改为先 `internal == expected` 再比 `packet_sha256`。
- 覆盖范围不变：测试 1 仍为 dev seed 0、3、7；测试 2 仍断言 `active_seeds == [3]`、`checked == 8`。
- 新增第 3 个测试（P3.1）。3 个测试都 passed。

### P3.5 回归（第 5、6、7 项）

| 项 | 实测 |
|---|---|
| 全量 pytest | `222 passed, 4 skipped in 350.32s`，exit 0；skipped 同前（meterless ×3、Zetaris ×1） |
| B1 | 对 PR 中 `b3-dev.json`：0/130 不同 |
| B3 同机两次 | run1 = run2 = `0fbebcb9f5d024a8d2fbed49a7313d7628fb4129c20abc29538c6920e1968914`，逐 seed 0/130 不同；与第 2 阶段在 `a9fa6c3` 上的本机值相同 |
| B3 与 PR 中 `b3-dev.json` | metrics 相同；逐 seed 115/130 不同（跨机） |
| PR 中 `b3-dev.json` | 本次提交没有改动 `artifacts/`（`git diff --stat a9fa6c3 466bec6 -- artifacts` 无输出），receipt 仍为 `bfda4d10…`，重算等于存储值 |
| L3 | 5 个表文件 sha256 与 `5a05f6d` 完全相同；20 个 `packets_sha256_rollup` 全部相同；审计总哈希 `cecbfbbd…` 与第 2 阶段相同，唯一差异仍是 seed 7 的 B3 决策记录 |
| 模板 SHA | 只改 context 文本：相同；证据包与 s2_summary 都改：相同；三种 format_mode：互不相同。json_object 模板 SHA 仍为 `6a4bc876…5c25`，与 `a9fa6c3` 相同 |

### P3.6 相对 `a9fa6c3` 的行为改动（第 8 项）

- `src/` 的 diff 只有两处：新增 `generator_view`（深拷贝；删掉 `decision.episode_id` 和三组行级 `episode_id`；把反馈 `command_id` 改写为 `"{target_id}:{step}"`）；`episode.py` 中 B4 包改为 `generator_view(build_packet(...))`。`build_packet`、`sources.py`、B3 路径、`s2_summary`、`adapter.py`、`providers.py` 都没有改动。
- 影响面（FACT）：B4 请求内容和 cache key 随之改变；B3 本机 receipt 与 `a9fa6c3` 相同；L3 导出与包哈希不变；模板 SHA 不变。
- 除 R11 所述内容外，diff 中没有看到其他行为改动。

### 附录 A.P3

A.P3-1 `p3_seed_check.py` 输出：

```
dev 130 seeds: {'requests': 350, 'episode_id_keys': 0, 'string_values_eq_or_prefixed_seed': 2, 'command_ids': 840, 'command_id_target_step': 840, 'long_seed_substring_hits': 0, 'where': ['$.evidence_packet.command_feedback[].command_id']}
synthetic 9-digit seeds (100000007, 987654320): {'requests': 4, 'episode_id_keys': 0, 'string_values_eq_or_prefixed_seed': 0, 'command_ids': 24, 'command_id_target_step': 24, 'long_seed_substring_hits': 0, 'where': []}
fake-HTTP cache file: seed substring False | episode_id key False
```

A.P3-2 `check_packet_p2.py HELPFUL_TEXT_CONTEXT`（`466bec6`）：

```
variant=HELPFUL_TEXT_CONTEXT seeds=130 requests=350
user message keys ['evidence_packet', 's2_summary']
evidence_packet keys ['command_feedback', 'context', 'decision', 'known_config', 'observations', 'presence_events', 'schema']
observations: keys=['nominal_speed', 'nominal_x', 'nominal_y', 'observed_x', 'observed_y', 'seq', 'step', 'target_id', 'time'] | missing C1=none | outside C1=['seq']
presence_events: keys=['seq', 'step', 'target_id', 'target_observed', 'time'] | missing C1=none | outside C1=['seq']
known_config: keys=['belt_speed', 'dt', 'tolerance', 'x_pick', 'y_pick'] | missing C1=none | outside C1=none
command_feedback: keys=['accepted', 'command_id', 'execution_time', 'issued_time', 'reason_code', 'seq', 'step', 'success', 'target_id'] | missing C1=none | outside C1=['seq', 'step']
decision keys ['seq', 'step', 'target_id', 'time']
context keys ['content_sha256', 'text']
s2_summary keys ['current_time', 'horizon', 'passing'] | passing row keys ['n_usable', 'rmse', 'structure_id']
scope/timing violations none
examples {}
```

A.P3-3 `g4_check.py`（`466bec6`）：

```
context-only differ: template equal True | cache key equal False
packet+summary differ: template equal True
template from body == default skeleton template True
template per mode distinct True | cache key per mode distinct True
json_object payload format keys: {'response_format': 'json_object'} False
json_schema payload format keys: {'response_format': 'json_schema'} False
nvext_guided_json payload format keys: {} True
system prompt change -> template differs True
bogus mode -> unknown format_mode: bogus
template sha json_object 6a4bc876b1f3bf0c0f68048d55b786bbbf936157c090076b50544decffcf5c25
```

A.P3-4 L3（`l3_export_hash.py` 与 `l3_audit_diff.py`，`466bec6`）：

```
9112912f46366427aaa1c7925c6ba111a2387e840c275ddf8382ad06a40961ef command_feedback.jsonl
d7215ff8a5f54761c78619a61916223184d88bb45c1f58d76855cefbea838f17 known_config.jsonl
f56a175d2a6ae3e827d2f98793c3be36581a94dba747fda21c86aa6164ea004f observation_samples.jsonl
d14c5bca946026ac2671d46a543cd917a228fef9dabc4b512fbbbfc008509184 ops_context.jsonl
bb9ff6bcffee1c063e8602d3b60585d25cec16d3d1f7b32496db3203f8476a92 presence_events.jsonl
audits_sha256 cecbfbbde4cfd735d513863cf309c6399b92ae674ceb4c33742fc8504755fe91
episodes 20 decision_points 24000
audit keys ['auth_evidence_nonempty', 'case', 'decision_points', 'hard_fault_latch_decisions', 'mismatches', 'packets_sha256_rollup', 's2_diagnostic_trace', 'seed', 'system2_decisions', 'variant']
0 NO_TEXT_CONTEXT rollup equal True | differing keys []
1 HELPFUL_TEXT_CONTEXT rollup equal True | differing keys []
2 IRRELEVANT_TEXT_CONTEXT rollup equal True | differing keys []
3 MISLEADING_TEXT_CONTEXT rollup equal True | differing keys []
4 NO_TEXT_CONTEXT rollup equal True | differing keys []
5 HELPFUL_TEXT_CONTEXT rollup equal True | differing keys []
6 IRRELEVANT_TEXT_CONTEXT rollup equal True | differing keys []
7 MISLEADING_TEXT_CONTEXT rollup equal True | differing keys ['s2_diagnostic_trace', 'system2_decisions']
8 NO_TEXT_CONTEXT rollup equal True | differing keys []
9 HELPFUL_TEXT_CONTEXT rollup equal True | differing keys []
10 IRRELEVANT_TEXT_CONTEXT rollup equal True | differing keys []
11 MISLEADING_TEXT_CONTEXT rollup equal True | differing keys []
12 NO_TEXT_CONTEXT rollup equal True | differing keys []
13 HELPFUL_TEXT_CONTEXT rollup equal True | differing keys []
14 IRRELEVANT_TEXT_CONTEXT rollup equal True | differing keys []
15 MISLEADING_TEXT_CONTEXT rollup equal True | differing keys []
16 NO_TEXT_CONTEXT rollup equal True | differing keys []
17 HELPFUL_TEXT_CONTEXT rollup equal True | differing keys []
18 IRRELEVANT_TEXT_CONTEXT rollup equal True | differing keys []
19 MISLEADING_TEXT_CONTEXT rollup equal True | differing keys []
```

A.P3-5 `compare_b3.py`（`466bec6` 两次运行对 PR 中 `b3-dev.json`）与指定测试：

```
run1 receipt 0fbebcb9f5d024a8d2fbed49a7313d7628fb4129c20abc29538c6920e1968914
run2 receipt 0fbebcb9f5d024a8d2fbed49a7313d7628fb4129c20abc29538c6920e1968914
run1==run2 True
b1_receipt_sha256: run1 vs run2 differ 0/130; run1 vs committed differ 0/130
b3_receipt_sha256: run1 vs run2 differ 0/130; run1 vs committed differ 115/130
metrics run1==committed True
run1 runtime_versions {"python": "3.12.3", "numpy": "2.5.4", "machine": "x86_64", "cpu_model": "Intel(R) Xeon(R) Processor @ 2.10GHz", "blas": {"name": "scipy-openblas", "version": "0.3.34.106.0"}}
committed runtime_versions {"python": "3.12.3", "numpy": "2.5.4", "machine": "x86_64", "cpu_model": "Intel(R) Core(TM) i7-10750H CPU @ 2.60GHz", "blas": {"name": "scipy-openblas", "version": "0.3.34.106.0"}}
committed receipt stored bfda4d101bd79f8d62738807402b33e24aba29028f5f4bc550a9b13304cb1132 recomputed equal True
PASSED tests/test_frz2_packet_equivalence.py::test_b4_packets_match_l3_export_projection_for_three_seeds
PASSED tests/test_frz2_packet_equivalence.py::test_all_diag_b4_call_points_match_projected_export_packets
PASSED tests/test_frz2_packet_equivalence.py::test_b4_finalized_payload_omits_nine_digit_seed_identifiers
PASSED tests/test_t6_frz2.py::test_b4_variants_enter_and_exhaust_reobserve_hold_like_b3[B4_STRICT]
PASSED tests/test_t6_frz2.py::test_b4_variants_enter_and_exhaust_reobserve_hold_like_b3[B4_TIEBREAK]
PASSED tests/test_t6_frz2.py::test_actuator_delay_fit_chooses_smallest_delay_within_tie_tolerance
PASSED tests/test_t6_frz2.py::test_actuator_delay_fit_without_tie_keeps_strict_minimum
PASSED tests/test_t6_frz2.py::test_speed_step_delay_tie_selects_lexicographic_smallest_tau_then_delay
PASSED tests/test_t6_frz2.py::test_s2_b4_dev_replay_cache_miss_exits_nonzero_without_artifact
PASSED tests/test_t6_frz2.py::test_finalized_request_floats_are_six_decimal_fixed_points
PASSED tests/test_t6_frz2.py::test_request_body_and_cache_key_ignore_float_changes_beyond_six_places
PASSED tests/test_t6_frz2.py::test_b4_episode_provider_payload_floats_are_rounded_to_six_places
12 passed in 44.61s
```

A.P3-6 `p3_seed_check.py` 源码：

```python
"""T6 phase 3: seed identifiers in the finalized B4 request (dev seeds + two synthetic 9-digit seeds),
generator-view command_id format, and a fake-HTTP cache write. Offline, no API key."""
import io, json, re, sys, tempfile
from pathlib import Path
from rra.eval.b4_dev import _realization
from rra.eval.context_v3 import VARIANTS, freeze_episode_contexts
from rra.eval.framework import v3_world_config
from rra.eval.scenarios import realize_episode
from rra.evidence import run_episode
from rra.llm.adapter import HypothesisProposer
import rra.llm.providers as P
SET = P.ReplayProvider("unused").settings
class Cap:
    last_http_status = None
    def __init__(s): s.b = []
    def complete(s, body): s.b.append(body); return {"choices": [{"message": {"content": '{"items": []}'}}]}
def walk(v, path="$"):
    if isinstance(v, dict):
        for k, x in v.items():
            yield path + "." + k, k, x
            yield from walk(x, path + "." + k)
    elif isinstance(v, list):
        for i, x in enumerate(v): yield from walk(x, f"{path}[]")
def check(seed, real, text, stats):
    cap = Cap()
    run_episode(v3_world_config("nominal"), seed, True, terminal_monitoring="corrected", realization=real,
                text_context=text, system2_enabled=True, s2_variant="B4_STRICT", proposer=HypothesisProposer(cap))
    for body in cap.b:
        canon = P.canonical_json(P.finalize_payload(body, SET)); stats["requests"] += 1
        user = json.loads(json.loads(canon)["messages"][1]["content"])
        for path, k, x in walk(user):
            if k == "episode_id": stats["episode_id_keys"] += 1
            if isinstance(x, str) and (x == str(seed) or x.startswith(f"{seed}:")) and k != "content_sha256":
                stats["string_values_eq_or_prefixed_seed"] += 1; stats["where"].add(path)
        for f in user["evidence_packet"]["command_feedback"]:
            stats["command_ids"] += 1
            stats["command_id_target_step"] += f["command_id"] == f"{f['target_id']}:{f['step']}"
        if len(str(seed)) >= 9:
            stats["long_seed_substring_hits"] += str(seed) in canon
    return cap.b
dev = json.load(open("config/dev_seeds.json"))["seeds"]
st = dict(requests=0, episode_id_keys=0, string_values_eq_or_prefixed_seed=0, command_ids=0, command_id_target_step=0,
          long_seed_substring_hits=0, where=set())
for i, s in enumerate(dev):
    real = _realization(i, s); ctx = freeze_episode_contexts(str(s), s, real.fault_family or real.structure)
    check(s, real, ctx["HELPFUL_TEXT_CONTEXT"].text, st)
print("dev 130 seeds:", {k: (sorted(v) if isinstance(v, set) else v) for k, v in st.items()})
syn = dict(requests=0, episode_id_keys=0, string_values_eq_or_prefixed_seed=0, command_ids=0, command_id_target_step=0,
           long_seed_substring_hits=0, where=set()); last = None
for s in (100000007, 987654320):  # synthetic, not from any seed file
    real = realize_episode(s, ("VELOCITY_OFFSET",))
    ctx = freeze_episode_contexts(str(s), s, real.structure)
    for v in VARIANTS:
        b = check(s, real, ctx[v].text, syn)
        if b: last = (s, b[0])
print("synthetic 9-digit seeds (100000007, 987654320):", {k: (sorted(v) if isinstance(v, set) else v) for k, v in syn.items()})
s, body = last
tmp = Path(tempfile.mkdtemp(dir=sys.argv[1]))
prov = object.__new__(P.NvidiaNimProvider)
for k, v in dict(api_key="UNUSED", cache_dir=tmp, timeout=1, base_url="http://invalid", model=P.NIM_MODEL, max_tokens=1800,
                 chat_template_kwargs={"enable_thinking": False}, no_think=False, format_mode="json_object",
                 last_http_status=None, last_latency_seconds=None, last_response_body=None, last_request_body=None).items():
    setattr(prov, k, v)
class R(io.BytesIO):
    status = 200
    def __enter__(s): return s
    def __exit__(s, *a): return False
P.urlopen = lambda req, timeout=None: R(json.dumps({"model": "fake", "choices": [{"message": {"content": '{"items": []}'}}]}).encode())
prov.complete(body)
f = next(tmp.glob("*.json")).read_text()
print("fake-HTTP cache file: seed substring", str(s) in f, "| episode_id key", '"episode_id' in f or '\\"episode_id' in f)
```
