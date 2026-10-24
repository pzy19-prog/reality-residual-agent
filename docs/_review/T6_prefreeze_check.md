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
