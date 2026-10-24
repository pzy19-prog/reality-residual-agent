# T9b — EVAL-PATH 审查（冻结前，PR #28）

- 审查对象：PR #28，分支 `feat/eval-v3-path`，head `52bdd47ad2a2df5a4399cf3b9ced1e9ea20b8753`（`git rev-parse HEAD` 与任务卡一致），`git merge-base` = `5a05f6d56f2f08d1d9a985ee17912bcec02a23bc`（一致）。相对 `5a05f6d` 改 7 个文件（866+/11−）。
- 相关：`origin/main` = `349d1e6`（含 A06）；PR #27 `feat/frz2-b4req` = `a9fa6c3`；T9a `cloud/t9a-a06-review` = `e198916`；T6 `cloud/t6-prefreeze-check` = `e1e27d1`。均已补抓并核对 sha。
- 预算：未达软上限，各项均已执行。
- 环境：云 VM，Intel Xeon，scratchpad 中的 venv（Python 3.12，numpy 2.5.4，pydantic 2.14.1）。**不是** A06 §2.1 的注册 runner。
- 执行纪律（FACT）：
  - 未运行 `scripts/gen_eval_v3_seeds.py`（含 dry-run）。为此在所有 pytest 与 rra 命令中通过 `PYTHONPATH` 注入一个 `sitecustomize.py` 审计钩子（附录 C.1），对"打开仓库/worktree 下 `config/eval_seeds*.json`"与"子进程命令行含 `gen_eval_v3_seeds`"直接抛 `PermissionError` 并记日志。生成器只以 `importlib` 载入函数定义后在打桩 CSPRNG 下调用（§1）。
  - 未创建、读取或推断 `config/eval_seeds_v3.json` 或任何 eval-v3 种子值；该文件在本分支不存在（钩子日志中无对它的打开记录）。
  - 测试中出现的种子值全部由测试自己构造：dev 种子 + 10000（落在 eval 区间内以通过 schema 校验），或 dev 种子本身。
  - 没有 live 调用，未设置 `NVIDIA_API_KEY` / `ZETARIS_TOKEN`。所有 rra 输出都写入 scratchpad 的 `--output-dir`。每次运行前后 `git status --porcelain` 在仓库与 worktree 中均为空。
- 措辞：只陈述事实与影响，不做成败判定，不提出预注册条文措辞。

---

## 0. T9a §6 核验要点逐条结果（E-1 … E-14）

| # | 要点 | 方法 | 结果（FACT） | 详见 |
|---|---|---|---|---|
| E-1 | `index % 19`；结构/故障族顺序同 dev；100 seed 下 6×5 + 5×14 | 读码 + 运行 | b2/b4/估计用 `final_v3._case`（`final_v3.py:178-184`）与 `b4_dev._realization`（`b4_dev.py:78-82`），b1b3 用 `b3_dev._run_seed`（`b3_dev.py:101-108`），都按文件列表下标 `index % 19`，先 14 个组合结构、后 5 个故障族（与 dev 同一函数）。receipt 写 `case_episode_counts`（`final_v3.py:187-191`）；按该函数，100 个下标得 case 0–4 各 6、5–18 各 5。**b1-legacy 不按此分配**：它调用 `run_b1_diagnostic("legacy", seeds)`，遍历 `config/scenarios.json` 的 14 个场景 × 全部种子（`dev_diagnostics.py:21-47`），不做 `index % 19` 实现 | §3.1 |
| E-2 | 四个文本条件；只 import 一个生成器；`content_sha256` 不符即中止 | 读码 + 运行 | eval 路径只经 `context_v3.freeze_episode_contexts`（`b4_dev.py:17,212`；`final_v3.py:267`），`VARIANTS` 4 个；`text_context.py` 只被 `context_v3` 导入其 `validate_text_context`（`context_v3.py:10`）。每个任务调用 `verify_frozen_context`（`b4_dev.py:219-220`），不符抛 `ValueError`。该校验比较的是同一进程刚生成的文本与其哈希（自洽性），不与任何已提交的哈希表比较 | §3.1 |
| E-3 | B1/B1-legacy/B2/B3 每 episode 一次、不读文本；B2 从 `b2-grid.json` 读 | 读码 + 运行 | B2 读 `artifacts/h1/b2-grid.json` 的 `selected`（`final_v3.py:222-223`），dev 运行回执 `parameters = {T: 1.15, R: 2.15}`。B1/B3 每 seed 一次（`b3_dev._run_seed`）。B1-legacy 见 E-1（14 场景 × seed，不是"每物理 episode 一次"） | §3.1 |
| E-4 | 命令来自 X；`git diff X..Z -- src/` 为空 | 读码 + 临时仓库 | 守卫只在 eval_v3 角色启动时检查 `git diff --name-only <tag> HEAD`（`final_v3.py:123-135`）；结果提交之后无检查。回执记录 `git_sha`（不进 `receipt_sha256`，`final_v3.py:387-392`）。守卫可被绕过的方式见 §2 | §2 |
| E-5 | stdout/日志不含种子或 `str(seed)` | 运行 + 读码 | 正常路径：b2、b1b3 用 3 个构造值运行，stdout/stderr 0 命中（附录 A.4）。**失败路径会写出种子值**：7 处异常消息（§5.2） | §5 |
| E-6 | 请求模型 `NIM_MODEL`；逐响应记录服务端名，另记请求常量 | 读码 | head：无 served model 记录。合并 #27 后：`b4_dev` 在其 `b4-dev.json` 中写 `served_models` 与 `llm_request_spec`，但 `final_v3._run_b4` 只把 `metrics/episodes/llm_calls` 复制进 `b4.json`（`final_v3.py:326-343`），两字段只在旁路文件 `b4-dev.json` 中 | §3.3 |
| E-7 | 读穿缓存，键为最终请求体 SHA-256；浮点 6 位 | 读码 | 键 = `request_sha256(finalize_payload(...))`（`providers.py:22-23,64-67,127-130`）。6 位舍入只在 #27 的 `finalize_payload` 中（T6 P2.1 C-04 已测）。缓存目录固定为 `ROOT/artifacts/llm_cache`（`b4_dev.py:196`），与 dev 缓存同目录 | §3.3 |
| E-8 | 401/403 非零退出；续跑行为 | 打桩 | `_ReadThroughProvider` 对 401/403 `raise SystemExit("NVIDIA NIM HTTP {status}; stop Phase B")`（`b4_dev.py:57-58`），`final_v3.main` 不捕获 `SystemExit`，进程退出码 1，**不写 `b4.json`**，本次已计数的请求数丢失（scratch 测试 `test_401_is_systemexit_and_counts`、`test_prior_count_lost_after_crash_or_replay`） | §3.2 |
| E-9 | 2,500 计数对象；超限停止 | 打桩 | 计数对象 = 最终请求体 SHA-256 的去重集合，在发 HTTP **之前**登记（`final_v3.py:96-100`）；缓存命中不计；5xx 重试同一键计 1 次；失败请求（5xx 三次、4xx）也计入且不入缓存。超限在发出第 2,501 个新键之前抛 `LiveBudgetExceeded`，写 `status: incomplete` 回执，退出码 3 | §3.2 |
| E-10 | replay 两次 receipt 一致；缓存未命中非零退出、无 fallback | 打桩运行 | dev 子集（33 seed）`--replay` + 打桩 provider，两次 `receipt_sha256` 相同（head：`c309dc4a…`）。`ReplayCacheMiss` 在 `final_v3.main` 中以退出码 2 结束（`final_v3.py:479-484`），无 fallback 分支。eval_v3 角色下 replay 与守卫的冲突见 §2.3 | §3.2、§4 |
| E-11 | 截止检查与 incomplete 路径 | 读码 | `final_v3.py`、`b4_dev.py` 中无截止时间逻辑（`grep 2026-10-27|deadline` 0 命中）。incomplete 只在上限触发时产生；截止、401/403、5xx 用尽重试、中断都不产生 incomplete 回执 | §3.2 |
| E-12 | `llm_calls` 按 (seed, 文本条件) 跨两变体计数，另报两变体调用 | 读码 | `metrics[variant]["B4_STRICT"]["llm_calls"]` = 该变体所有行 `llm_requests_served` 之和（含缓存命中），`B4_TIEBREAK` 行为 0（`b4_dev.py:120-121`）；顶层 `llm_calls` 同口径。两变体分别的 proposer 调用数只在 #27 中加入（`strict_/tiebreak_proposer_invocations`） | §3.4 |
| E-13 | A04 §6.1 计数与 §6.2 50% 判定在结果代码中实现 | 读码 | `metrics` 含 `TEXT_TIEBREAK` 与 `fallbacks`（按 `TIEBREAK_FALLBACK:*` 原因计数，`b4_dev.py:101-124`）。§6.1 中 valid / INVALID_PROPOSAL / PROVIDER_ERROR / truncated 的逐类计数与 §6.2 的 50% 判定，在 `final_v3.py` 与 `b4_dev.py` 中未找到实现 | §3.4 |
| E-14 | receipt 记录 A05 §4.1 平台字段 | 运行 | 每个行回执含 `runtime_versions`：python、numpy、machine、cpu_model、blas（`runtime.py:10-32`），不进 `receipt_sha256` | — |

---

## 1. 种子生成器（`scripts/gen_eval_v3_seeds.py`，读码 + 打桩）

### 1.1 与 A06 §1.1–1.3 逐条对照

| A06 条文 | 代码 | 实测（打桩，附录 B.1） |
|---|---|---|
| 100 个，无放回，`[10000, 2147483647)`，`secrets.SystemRandom().sample` | `:14` `LOW, HIGH, COUNT = 10_000, 2_147_483_647, 100`；`:42` `secrets.SystemRandom().sample(range(LOW, HIGH), COUNT)` | 桩记录的调用参数为 `(10000, 2147483647, 100)`，调用 1 次 |
| 写入 `config/eval_seeds_v3.json` | `:26` `root / "config" / "eval_seeds_v3.json"`；`root` 来自 `--root`（默认脚本上级目录，`:68`） | 写到 `<root>/config/` |
| 列表顺序（T9a A-1） | 无排序；`seeds` 原样写入（`:51`） | 桩返回的乱序列表原样出现在文件中 |
| 只打印数量与 SHA-256 | `:75` `count=100 sha256=<文件字节 SHA-256>` | stdout 只有这一行，stderr 为空 |
| 文件已存在则拒绝 | `:39-40`；另 `os.open(..., O_CREAT\|O_EXCL)`（`:55`） | 现有测试覆盖（本次因钩子拦截未运行，见 §7） |
| 工作树不干净则拒绝 | `:32,37-38`：`git status --porcelain --untracked-files=all` 非空即拒 | **被 `.gitignore` 忽略的文件、`--skip-worktree`/`--assume-unchanged` 标记下的已跟踪文件修改不显示**，此时视为干净（`test_gen_clean_check_ignores_gitignored_and_skip_worktree`） |
| HEAD 不是 freeze-tag commit 则拒绝 | `:30-31,35-36`：`rev-parse <tag>^{commit}` 与 `HEAD` 比较 | **tag 名由 `--freeze-tag` 任意给定**，不固定为 `impl-freeze-v3`；用名为 `not-the-freeze-tag` 的 tag 运行，退出码 0（`test_gen_accepts_any_tag_name`） |
| 种子文件单独提交、父提交为 tag（§1.3） | 脚本不提交（无 `git add/commit`） | 运行后 `git status` = `?? config/`，HEAD 未变。"单独提交、父提交为 tag"由执行者手工完成；代码中只有 `test_holdout.assert_final_seed_rule` 检查"引入提交只含该文件"，不检查父提交是否为 tag（见 §2.2 orphan 用例） |
| 单进程、注册 runner（§1.2） | 无平台检查 | — |

### 1.2 写出的内容、权限与位置

- JSON 字段：`schema_version`、`role`、`count`、`range`、`generator`、`freeze_tag`、`freeze_commit`、`seeds`（`:43-52`），`indent=2`，末尾换行。
- 权限：`os.open(..., 0o644)`，受 umask 影响；umask 022 下实测 `0o644`。文件对同机其他用户可读。
- 写入失败时 `target.unlink(missing_ok=True)` 后重抛（`:59-61`）。

### 1.3 输出路径与失败路径中是否出现种子值

| 路径 | 输出 | 是否含种子值 |
|---|---|---|
| 成功 | stdout `count=100 sha256=…` | 否（打桩实测，按值逐个 grep） |
| 校验失败（tag、工作树、已存在、tag 名含空白） | stderr `error: <固定文案>`，退出码 2 | 否（固定字符串） |
| `os.fdopen`/写入抛 `OSError` | stderr `error: disk full` 一类消息，退出码 2；文件被删 | 否（实测） |
| `config` 是普通文件导致 `mkdir` 失败 | stderr `error: [Errno 17] File exists: '<path>'` | 否（只含路径，实测） |
| 其他异常（如 `TypeError`、`KeyboardInterrupt`、`MemoryError`）在 `json.dumps` 之后 | 不被 `main` 捕获，Python 打印 traceback | traceback 默认不打印局部变量，消息本身不含值（打桩 `TypeError` 实测）。若在调试器或 `python -X dev`/带局部变量的 traceback 工具（如 `faulthandler` 以外的 rich/pytest `--showlocals`）下运行，`seeds`、`payload`、`encoded` 局部变量会被打印——FACT，未在本机复现此类工具 |
| repr | 无 `__repr__` 输出路径；`generate()` 返回 `(COUNT, digest)` | 否 |

---

## 2. 守卫（tag 之后的允许列表）

### 2.1 实现（FACT）

`final_v3._validate_eval_guard`（`final_v3.py:123-135`），仅在 `--role eval_v3` 时由 `load_seed_file` 调用：

1. `git status --porcelain --untracked-files=all` 非空 → 拒绝；
2. `git diff --name-only <freeze_tag> HEAD` 中任一路径既不是 `config/eval_seeds_v3.json` 也不以 `artifacts/eval_v3/` 开头 → 拒绝；
3. 之后 `load_seed_file` 再要求种子文件路径是 `ROOT/config/eval_seeds_v3.json`、schema/count/range 匹配、`freeze_tag` 字段等于 `--freeze-tag`、`freeze_commit` 等于 `<tag>^{commit}`（`:142-174`）。

### 2.2 临时仓库实测（伪造 tag `impl-freeze-v3`，构造的种子文件；附录 B.1 第 2 部分）

| 用例 | 预期（按 PR 描述） | 实测 |
|---|---|---|
| tag 后只提交种子文件 | 放行 | 放行 |
| + 提交 `artifacts/eval_v3/b2.json` | 放行 | 放行 |
| + 提交 `src/mod.py` 修改 | 拒绝 | 拒绝（`outside the eval allowlist`） |
| + 提交 `tests/test_x.py` 修改 | 拒绝 | 拒绝 |
| + 提交 `artifacts/llm_cache/abc.json` | — | **拒绝**（不在允许列表） |
| + 提交 `config/eval_seeds_v3.json.bak` | 拒绝 | 拒绝 |
| 未跟踪的 `artifacts/llm_cache/abc.json` | — | **拒绝**（`working tree must be clean`） |
| `src/mod.py` 标记 `--skip-worktree` 后在工作区修改 | 拒绝 | **放行** |
| 设置 `GIT_DIR`/`GIT_WORK_TREE` 指向另一个只含 tag + 种子提交的克隆，而 `--root` 仓库中 `src/` 已改并提交 | 拒绝 | **放行**（`_git` 继承环境变量） |
| `src/` 改后在新提交上建另一个 tag，种子文件写该 tag 名与 commit，`--freeze-tag` 传新名 | 拒绝 | **放行**（tag 名不固定） |
| HEAD 所在提交与 tag 树相同但不是 tag 的后代（orphan），其上提交种子文件 | 拒绝（A06 §1.3 父提交为 tag） | **放行**（只比较树差异，不查祖先关系） |
| `--role dev --seeds-file <任意名为 eval_seeds_v3.json 的文件>` | — | `load_seed_file(..., "dev")` 不调用守卫，也不检查 schema/count；`main` 对 dev 角色只在 `--subset` 时限制路径（`final_v3.py:438-444`），`--role dev --seeds-file ROOT/config/eval_seeds_v3.json --live` 可通过参数解析（打桩 `load_seed_file`/`run_row`，未读文件） |
| `--role eval_v3 --max-live-calls 999999` | — | 接受（只检查非负，`final_v3.py:432-433`） |

未发现读取环境变量来跳过守卫的专门开关；上表中的绕过来自 git 本身的环境变量与参数。`cli.py` 中 `RRA_SEED_FILE`（`cli.py:117`）只作用于 `rra bench`，不在 eval-v3 路径上。

### 2.3 守卫与 B4 流程的交互（FACT）

- B4 live 写缓存到 `ROOT/artifacts/llm_cache/`（`b4_dev.py:196`；`providers.py:126-130`），该目录不在 `.gitignore` 中（`.gitignore` 只有 `__pycache__/`、`*.py[cod]`、`.pytest_cache/`、`.venv/`、`outputs/`、`bench.json`）。
- 因此一次 eval_v3 live 运行（或被中断的运行）之后：缓存文件未跟踪 → 下一条 eval_v3 命令（续跑、两次 replay）被规则 1 拒绝；若提交这些缓存文件 → 被规则 2 拒绝。两条路径都由上表"未跟踪/已提交 `artifacts/llm_cache/abc.json`"两行实测覆盖。
- 按现有代码，eval_v3 角色下"live 填充 → 续跑 → 两次 replay"（A06 §3.3–3.4）不能在守卫开启的情况下依次执行；只有借助 §2.2 的绕过方式、或改用 `--role dev`（无守卫）才能执行。
- 同理，每行默认把回执写到 `artifacts/eval_v3/<row>.json`（`final_v3.py:422`），写出后工作树不干净，下一行运行前须先提交（允许列表允许）。

---

## 3. `rra eval-v3` 子命令与 A06 对照

### 3.1 行与场景

| 行 | 入口 | 运行次数与场景 | 文本 |
|---|---|---|---|
| `b1b3` | `run_b3_dev(tmpdir, seeds_path=…)`（`final_v3.py:201-213`），在临时目录生成 `b3-dev.json` 后丢弃，只取 `metrics/episodes` | 每 seed 一次，`index % 19`；先做 3 seed 串/并行一致性检查 | 不读 |
| `b2` | `_run_b2`（`:216-251`） | 每 seed 一次 B1 + 一次 B2，`index % 19` | 不读 |
| `b1-legacy` | `run_b1_diagnostic("legacy", seeds)`（`:254-262`） | 14 个 `config/scenarios.json` 场景 × 全部 seed（100 seed 时 1,400 个 episode），不按 `index % 19` | 不读 |
| `b4` | `run_b4_dev(output_dir, seeds_path=…)`（`:316-343`） | 每 (seed, 4 文本条件) 一次 strict + 一次 tiebreak（同一 memo proposer） | 4 条件 |

- `b4` 必须带 `--replay` 或 `--live`（互斥，`:424-426,464-465`）。`--replay` = `replay_only=True`，只读缓存；`--live` = 读穿缓存 + 计数上限。
- `--estimate`、`--subset` 只允许 `--role dev` 的 b4（`:434-437`）。

### 3.2 上限、截止、续跑、401/403（打桩，附录 B.1 第 3 部分）

| 项 | 代码事实 | 实测 |
|---|---|---|
| 计数对象 | `LimitedProvider.complete` 在调用父类前 `reserve(request_sha256(finalize_payload(body, self)))`（`final_v3.py:96-100`） | — |
| 缓存命中 | `_ReadThroughProvider` 先查 `ReplayProvider`，命中不进入 live provider（`b4_dev.py:41-46`） | 同一请求第二次：计数不变 |
| 5xx 重试 | 同一键最多 3 次 HTTP，`2**attempt` 秒退避（`b4_dev.py:49-61`） | 一次 500 + 一次 200：HTTP 3 次（含前一个请求），distinct = 2 |
| 失败请求 | 先登记后发送；失败不写缓存（缓存只在成功后写，`providers.py:126-130`） | 5xx×3 与 400 各计 1，缓存目录无文件 |
| 上限 | `already + len(keys) >= limit` 时抛 `LiveBudgetExceeded`（`:65-66`） | `limit=2, already=1`：第 2 个新键之前抛出，HTTP 只发 1 次 |
| 上限触发后的回执 | `status: incomplete`、`reason: max_live_calls_reached`、`distinct_live_requests`、`completed_text_condition_pairs`，无 metrics；`.md` 写 `Status/Reason/Completed text-condition pairs`；退出码 3 | 现有测试覆盖 |
| `completed_text_condition_pairs` | 线程本地标记"strict 完成后 tiebreak 完成"计 1（`:72-79`）。异常在线程池中出现后，`ThreadPoolExecutor` 退出时仍等待已提交的全部任务，之后完成的任务也计入 | — |
| 跨次累计 | `already` 只从 `<output_dir>/b4.json` 的 `distinct_live_requests` 读（`:301-313`） | 见下三行 |
| 401/403 | `SystemExit`，不写 `b4.json`；本次计数丢失 | `b4.json` 中原有 700 不变，本次的计数未加入 |
| 其他未捕获异常（5xx 用尽后的 `RuntimeError`、B-1 `AssertionError`、`KeyboardInterrupt`） | 同上，不写 `b4.json` | 读码 |
| `--replay` 写回同一输出目录 | 回执 `distinct_live_requests: 0` 覆盖 `b4.json` | 之后在该目录 `--live` 从 0 计 |
| 换输出目录 | `already = 0` | 实测 |
| 截止 2026-10-27 06:00 UTC | 无实现 | — |
| 截止 / 401 / 中断时的 incomplete 标记（T9a M-4） | 无 | — |
| incomplete 后的 replay | 只有全量 replay；未完成对在缓存中缺失 → `ReplayCacheMiss`，退出码 2。没有只 replay 已完成对的入口 | 读码 |
| 产物位置 | 行回执 `--output-dir`（默认 `artifacts/eval_v3/<row>.json/.md`）；B4 另写 `<output_dir>/b4-dev.json`；缓存 `artifacts/llm_cache/` | 实测（scratchpad 输出目录中 `b4.json`、`b4.md`、`b4-dev.json`） |
| 提交步骤 | 代码中无 `git add/commit`；无缓存提交步骤 | — |

### 3.3 B4 回执内容（head 与合并后）

- `b4.json`（`final_v3.run_row`）：`schema_version, row, role, seed_file_sha256, seed_count, case_episode_counts, status, metrics, episodes, llm_calls, subset, max_live_calls, distinct_live_requests, runtime_versions, git_sha, receipt_sha256`。
- 合并 #27 后 `run_b4_dev` 新增的 `llm_request_spec`（含 `format_mode`、`request_template_sha256`）与 `served_models` **不进入 `b4.json`**，只在旁路 `b4-dev.json`。`b4-dev.json` 的 `seed_identity.path` = `str(seeds_path)`，eval 路径下是绝对路径（`b4_dev.py:311-313`），`values` = 全部种子。
- `final_v3` 不传 `format_mode`，合并后 b4 使用 `run_b4_dev` 默认 `json_object`；`rra eval-v3` 无 `--format-mode` 参数。`_estimate_seed_requests` 的 `settings` 字典不含 `format_mode`（`final_v3.py:278-279`），走 `finalize_payload` 的默认值。

### 3.4 与 Addendum 04 §6 的关系（FACT）

- A04 §6.1 要求每个 B4 变体报告：LLM calls；valid / INVALID_PROPOSAL / PROVIDER_ERROR / truncated 计数；gate_reason 分布（TEXT_TIEBREAK 与各 TIEBREAK_FALLBACK 原因）。代码中有 `llm_calls`（只在 strict 行）、`TEXT_TIEBREAK`、`fallbacks`（按原因）；没有 valid / truncated 的逐类计数，INVALID_PROPOSAL / PROVIDER_ERROR 只以 fallback 原因的形式出现在 tiebreak 行。
- A04 §6.2 的 50% 判定没有实现；`.md` 只列 `metrics` 中的标量项（`final_v3.py:409-410`），嵌套的变体指标不展开。
- A05 §3.3 的"两变体分别报告 proposer 调用数"在 head 中没有，合并 #27 后由 `strict_/tiebreak_proposer_invocations` 提供（在 `metrics` 嵌套内）。

---

## 4. 等价验证（dev 种子）

| 检查 | 命令 / 方式 | 结果 |
|---|---|---|
| head：`eval-v3 b1b3 --role dev` 对 同机 `s2-b3-dev` | 两者都在本机运行，`compare_b1b3.py`（附录 B.3） | 130/130 seed 的 B1、B3 receipt 哈希相同；130/130 逐 seed 行完全相同；metrics 相同 |
| head：对已提交的 `artifacts/s2/b3-dev.json` | 同上 | 15/130 哈希相同；metrics 相同（跨机差异，与 T6 P2.1 C-09 的观察一致；本机不是 R4） |
| 合并 #27+#28+main：`eval-v3 b1b3` 对 同机 `s2-b3-dev` | 在合并 worktree 中运行 | 130/130 哈希相同；130/130 行相同；metrics 相同 |
| 合并：对合并树中的 `artifacts/s2/b3-dev.json`（#27 在 i7 上重生成） | 同上 | 15/130 哈希相同；metrics 相同 |
| head：`eval-v3 b4 --role dev --subset --replay`，打桩 `ReplayProvider` 返回 `{"items": []}` | `b4_stub_replay.py`（附录 B.2），同一输出两次 | 两次退出码 0；`receipt_sha256` 两次相同（`c309dc4a11652f0b5a3334ab72eaf35af152ad293fa16e122daeb4ed05944e43`）；不同最终请求 444 个（与 PR 描述中 `--estimate` 子集 444 一致）；请求 user 内容中 `episode_id` 键出现 0 处 |
| 合并：同上 | 同上 | 两次退出码 0；`receipt_sha256` 两次相同（`97ac505781e2cc74b6cc24478cf14b0e5d5720c3abeaa2e79e3165b635e72fbc`）；不同最终请求 444 个；请求 user 内容中 `episode_id` 出现在 4 个键路径：`evidence_packet.decision.episode_id`（444/444 个请求）、`observations[].episode_id`（444）、`presence_events[].episode_id`（444）、`command_feedback[].episode_id`（340，其余请求无反馈行）。这是今天裁决之前的 #27 状态 |

运行时长（本机）：b1b3 head 80 s，合并 164 s（与并行 pytest 争用 CPU）；b4 打桩 replay head 每次约 11.5 min（两次共约 23 min），合并树第二次约 10.6 min。

---

## 5. 种子暴露面

### 5.1 正常路径（FACT）

| 位置 | 内容 | head | 合并 #27 | 按今天裁决去掉 B4 请求中的 `episode_id` 之后 |
|---|---|---|---|---|
| B4 请求体 / 外部服务 | `decision.episode_id`、三组行级 `episode_id` = `str(seed)`（#27 `episode.py` 的 `build_packet` 调用处） | 无（旧请求体只有 time/observed_x/nominal_x/feedback/passing 等） | 有 | 无 `episode_id`。剩余与种子相关的只有：`context.text` 由 `seed % len(候选)` 选择模板与措辞（`context_v3.py:136-141`），即文本携带种子对小模数的余数；`context.content_sha256` 为该文本的哈希。仿真数值由种子决定但不是种子值 |
| 缓存文件 `artifacts/llm_cache/<sha>.json` | 文件名为最终请求 SHA-256；内容为请求与响应 | 无种子值 | 请求中有 `episode_id` | 同上一格；响应内容由服务端产生，若模型复述请求中的字段则随之写入（当前请求中已无种子） |
| 行回执 `b1b3.json` | `episodes[].seed` | 有（实测构造值 3/3 命中） | 同 | 不受影响 |
| 行回执 `b2.json` | `episodes[].seed` | 有（实测 3/3） | 同 | 不受影响 |
| 行回执 `b1-legacy.json` | `diagnostic.seeds.values`，且 `path` 硬编码为 `config/dev_seeds.json`（`dev_diagnostics.py:53`） | 有 | 同 | 不受影响 |
| `b4.json` | `episodes[].seed` | 有 | 同 | 不受影响 |
| `b4-dev.json`（旁路） | `seed_identity.values`（全部）、`seed_identity.path` 绝对路径、`episodes[].seed` | 有 | 同 | 不受影响 |
| `b1b3` 临时目录 | `run_b3_dev` 在 `/tmp/eval-v3-b1b3-*` 写 `b3-dev.json`（含种子），退出时删除 | 有（临时） | 同 | 不受影响 |
| stdout | `{"receipt_sha256","row","status"}` | 无（实测） | 同 | — |
| `.md` | 种子数量、种子文件 SHA-256、metrics 标量 | 无 | 同 | — |
| L3 / Zetaris / Meterless | eval-v3 路径（`final_v3`、`b4_dev`、`b3_dev`、`dev_diagnostics`、`episode.py`）不导入 `sources.export_sources`、`sponsor/*` | 不涉及 | 同 | L3 自身仍以 `str(seed)` 为 `episode_id`（`sources.py:69`），只在单独运行 L3 导出时出现 |

### 5.2 失败路径中写出种子值的位置（FACT，读码）

| 位置 | 消息 | `final_v3.main` 是否捕获 |
|---|---|---|
| `b4_dev.py:230` | `AssertionError(f"B-1 mismatch seed={seed} variant={variant}")` | 否 → traceback |
| `b4_dev.py:281` | `RuntimeError(f"serial/parallel mismatch: {mismatches[0]}")`，dict 含 `seed` | 否 |
| `b3_dev.py:211` | `RuntimeError(json.dumps(parity))`，`parity["seeds"]` = 前 3 个种子 | 否 |
| `b3_dev.py:66,83,95` | `T7/T8 seed={receipt.get('seed')}: …` | 否（在子进程中抛出，经 `Pool.map` 传回） |
| `context_v3.py:218` | `ValueError(f"frozen context mismatch for episode={episode_id}, …")`，`episode_id = str(seed)` | 是 → stderr `eval-v3 error: frozen context mismatch for episode=<seed>…` |

### 5.3 在公开仓库中的影响（只陈述）

- 回执提交到 `artifacts/eval_v3/` 即公开该行所用全部种子值。A06 §2.3 允许结果在 Y 之后分多次提交；若 b1b3/b2/b1-legacy 先于 B4 live 完成提交，种子值在全部行运行完之前公开（T9a A-3）。
- `b4-dev.json` 的绝对路径会公开运行机器上的目录结构（含用户名，若在家目录下）。
- 缓存文件若提交（§2.3 的冲突之外），按今天裁决后不再含 `episode_id`；`context.text` 的模板选择反映 `seed mod k`（k 为候选数，2–若干），由 100 个种子各 4 条文本给出。

---

## 6. 与 PR #27 的合并

### 6.1 `git merge-tree --write-tree --name-only`（只读）

| 合并 | 结果 |
|---|---|
| #27 `a9fa6c3` + #28 `52bdd47` | 冲突：`src/rra/cli.py`、`src/rra/eval/b4_dev.py`（树 `a8cd758…`） |
| main `349d1e6` + #27 | 无冲突（树 `b13144d…`） |
| main + #28 | 无冲突（树 `4c64fbc…`） |

冲突内容：`cli.py` 同一位置分别加 `--format-mode` 与 `eval-v3` 子解析器；`b4_dev.py` 的 `run_b4_dev` 签名分别加 `format_mode` 与 `seeds_path`。`seed_identity` 一行 git 自动合并为 #28 的版本。

### 6.2 临时 worktree 手动合并（未推送）

- 以 #27 为基，`merge --no-ff 52bdd47`，两处冲突取并集：`cli.py` 两段都保留；签名为 `replay_only=False, format_mode="json_object", seeds_path=None`。再合并 `origin/main`（只多 A06 文档，无冲突）。
- 全量 pytest（钩子开启）：`5 failed, 229 passed, 4 skipped in 344.13s`。5 个 failed 全部是钩子拦截（4 个调用生成器子进程，1 个 `test_bench` 打开 `config/eval_seeds_v2.json`），与 head 上的 5 个相同。
- head 上同样运行：`5 failed, 208 passed, 4 skipped in 205.78s`（同 5 个被拦截）；208 + 5 = 213，与 PR 描述"213 passed"一致。
- dev 等价：见 §4。

### 6.3 EVAL-PATH 的 b4 是否使用 FRZ-2A 的新请求

- 合并后 `final_v3._run_b4` → `b4_dev.run_b4_dev` → `run_episode`（#27 版本）→ `build_packet`（canonical packet）+ `s2_summary` → `proposal_request` → `finalize_payload`（§3.4 舍入、`format_mode`）。因此合并后 eval-v3 的 b4 走 #27 的请求。
- `format_mode`：`final_v3` 不传，使用默认 `json_object`；若 §3.2 探针选定其他模式，须在 `run_b4_dev` 默认值处（或 `final_v3` 传参）一并改动，`final_v3._estimate_seed_requests` 也依赖 `finalize_payload` 的默认值。
- `llm_request_spec` / `served_models`：只在 `b4-dev.json`，不在 `b4.json`（§3.3）。
- 实测（合并树打桩 replay）：`b4.json` 中无 `llm_request_spec`、`served_models` 键；`b4-dev.json` 中 `served_models = {"stub/served": 444}`，`llm_request_spec.format_mode = json_object`，`request_template_sha256` 前缀 `6a4bc876`（与 T6 P2.3 记录的 json_object 模板 SHA 一致）。
- `LimitedProvider` 计数键用 `finalize_payload(body, self)`，`self` 带 #27 的 `format_mode` 属性，与缓存键一致。

---

## 7. 测试覆盖

| 行为 | `tests/test_eval_v3.py` / `tests/test_holdout.py` | 本次 scratch 测试（附录 B.1） |
|---|---|---|
| 生成器 100 个、范围、唯一、stdout 不含值 | 有（以子进程**真实运行生成器**，CSPRNG 在 tmp 中产生 100 个值；本次被钩子拦截，未运行） | 打桩版：参数、顺序、权限、不提交、stdout |
| 生成器三项拒绝 | 有（同为子进程运行，本次被拦截） | — |
| 生成器 tag 名不固定 / 忽略文件与 skip-worktree | 无 | 有 |
| 生成器失败路径无值 | 无 | 有（fdopen、mkdir、TypeError） |
| 守卫拒绝 `src` 改动 | 有（1 例） | 有（src、tests、缓存、`.bak`） |
| 守卫放行种子文件 / `artifacts/eval_v3/` | 无 | 有 |
| 守卫绕过（skip-worktree、GIT_DIR、换 tag、非后代） | 无 | 有（4 例，均放行） |
| `--role dev` 读 eval 文件无守卫；`--max-live-calls` 可调高 | 无 | 有 |
| holdout 规则（种子文件引入提交只含该文件） | 有 | — |
| 上限在超出前停止 | 有 | 有 |
| completed pairs 计数 | 有 | — |
| 上限写 incomplete 回执 | 有 | — |
| 默认 2500 | 有 | — |
| 同目录续跑累计 | 有 | 有（另测崩溃 / replay 覆盖 / 换目录时丢失） |
| 缓存命中不计、重试计一次、失败计入 | 无 | 有 |
| 401/403 → SystemExit、不写回执 | 无 | 有 |
| 截止时间 | 无（无实现） | 有（断言无实现） |
| `--estimate` 拒绝 eval 角色且不读种子 | 有 | — |
| `index % 19` / case 计数 | 无直接测试 | §4 运行 |
| b1b3 与 s2-b3-dev 逐 seed 等价 | 无 | §4 运行 |
| b4 replay 两次一致 | 无 | §4 运行 |
| 失败路径异常消息含种子 | 无 | 未写（§5.2 读码） |
| eval_v3 角色下 live → replay 与守卫冲突 | 无 | 有（缓存未跟踪 / 已提交两例） |

scratch 测试运行结果（head 树）：`25 passed in 3.63s`。这些测试断言的是**当前行为**（包括上表中的放行），不是期望行为。

---

## 8. 需所有者裁决与冻结前事项

### 8.1 需所有者裁决

1. **结果回执中的种子值与提交时机**：b1b3/b2/b1-legacy/b4/b4-dev 回执都写出种子值（§5.1）。是否允许在 B4 完成前提交前四行的回执（A06 §1.3、§2.3、T9a A-3）。
2. **`b4-dev.json` 旁路文件**：是否作为 eval-v3 产物保留、是否允许其中的绝对路径与全部种子值。
3. **eval-v3 缓存的位置与是否提交**：现为 `artifacts/llm_cache/`（与 dev 共用），不在守卫允许列表；是否另设目录、是否提交（T9a §2 第 9 项）。
4. **2,500 的计数口径**：现为"发出前登记的不同最终请求"，失败请求计入、重试不重复计；跨次累计依赖输出目录中的 `b4.json`，崩溃/401/replay 覆盖/换目录时丢失（T9a A-12）。
5. **401/403 之后能否续跑**（T9a A-13），以及其退出码（现为 1，且无回执）。
6. **截止 2026-10-27 06:00 UTC 的执行方式**：无代码实现；由执行者手动停止还是代码检查；截止覆盖 live 还是含 replay（T9a A-15）。
7. **incomplete 情形的报告方式**（T9a M-4 / A-14）：现只有上限触发时的计数回执；无部分 replay 入口。
8. **b1-legacy 的运行方式**：14 场景 × 全部种子，与 A06 §1.4/§1.5"每物理 episode 一次、`index % 19`"不同；`diagnostic.seeds.path` 硬编码为 dev 路径。
9. **按今天裁决去掉 `episode_id` 之后剩余的种子关联**：`context.text` 的模板选择携带 `seed mod k`（§5.1）；失败路径消息中的种子值（§5.2）。
10. **`--role dev` 可读任意种子文件（含 eval 文件名）且无守卫；`--max-live-calls` 在 eval 角色下可调高**。

### 8.2 冻结前必须处理

- **M-1** 守卫与 B4 流程冲突（§2.3）：eval_v3 角色下 live 之后的续跑与两次 replay 无法在守卫开启时执行。
- **M-2** tag 名未固定：生成器与守卫都接受任意 `--freeze-tag`（§1.1、§2.2）；所有者已定 tag 名 `impl-freeze-v3`。
- **M-3** 计数跨次累计在崩溃、401/403、replay 覆盖、换输出目录时丢失（§3.2），与 A06 §5"超过 2,500 即无效"直接相关。
- **M-4** 截止时间与非上限情形的 incomplete 标记无实现（§3.2；T9a M-4）。
- **M-5** #27 与 #28 在 `cli.py`、`b4_dev.py` 冲突，须在 X 之前合并；合并后 b4 用默认 `json_object`，须与 §3.2 探针选定模式一致（§6）。
- **M-6** FRZ-2A 去掉 `decision.episode_id` 与行级 `episode_id` 的提交尚未出现；该提交之后应重做 §4 合并行的请求键检查（附录 B.2 的 `episode_id_key_paths_in_user_content`）。
- **M-7** 失败路径异常消息写出种子值（§5.2 七处），与 A06 §1.3"不检视"及 T9a A-3 交互。

### 8.3 建议

- **S-1** 守卫加固：清除 `GIT_*` 环境变量后再调用 git；检查 tag 是 HEAD 祖先且种子提交的父提交为 tag；检查 `git ls-files -v` 中的 skip-worktree/assume-unchanged 标记；考虑 `--ignored`。
- **S-2** `b4.json` 收录 `llm_request_spec`、`served_models`、两变体 proposer 调用数（E-6、E-12）。
- **S-3** A04 §6.1 逐类计数与 §6.2 判定在结果代码中实现或在报告步骤中明确由谁计算（E-13）。
- **S-4** 生成器文件权限（0o644）与 `python -X dev`/带局部变量 traceback 环境下的打印风险，在执行说明中写明。
- **S-5** 现有测试以子进程真实运行生成器（tmp 中产生 CSPRNG 值）；与"agent 会话不运行生成器"的操作规则冲突，执行者运行全量 pytest 时须知悉。
- **S-6** `--role dev` 拒绝名为 `eval_seeds_v3.json` 或 `role: eval_v3` 的文件；eval 角色下禁止调高 `--max-live-calls`。
- **S-7** b1b3 在 eval 角色下由 `run_b3_dev` 再次读取种子文件（与 `final_v3` 校验后的列表不是同一对象）；可改为传入已校验列表。

---

## 附录 A. 命令与原始输出

### A.1 全量 pytest（head，钩子开启）

```
$ cd <repo> && PYTHONPATH=<scratch>/guard T9B_PROTECTED_ROOTS=<repo> python -m pytest -q -p no:cacheprovider -rfE
FAILED tests/test_bench.py::test_benchmark_includes_nominal_and_all_intensity_bands
FAILED tests/test_eval_v3.py::test_seed_generator_creates_100_unique_in_range_without_printing_values
FAILED tests/test_eval_v3.py::test_seed_generator_refuses_unsafe_states_without_writing[tag_mismatch]
FAILED tests/test_eval_v3.py::test_seed_generator_refuses_unsafe_states_without_writing[dirty_tree]
FAILED tests/test_eval_v3.py::test_seed_generator_refuses_unsafe_states_without_writing[target_exists]
5 failed, 208 passed, 4 skipped in 205.78s (0:03:25)
钩子日志：
      4 BLOCKED exec gen_eval_v3_seeds
      1 BLOCKED open <repo>/config/eval_seeds_v2.json
```

5 个 failed 的原因都是 `PermissionError: T9B guard: …`（钩子主动拦截）。

### A.2 全量 pytest（合并 worktree）

```
5 failed, 229 passed, 4 skipped in 344.13s (0:05:44)
      4 BLOCKED exec gen_eval_v3_seeds
      1 BLOCKED open <wt_merge>/config/eval_seeds_v2.json
```

### A.3 merge-tree

```
== origin/feat/frz2-b4req + 52bdd47
a8cd758962551807762aed7ef72aa03419b1f483
src/rra/cli.py
src/rra/eval/b4_dev.py
CONFLICT (content): Merge conflict in src/rra/cli.py
CONFLICT (content): Merge conflict in src/rra/eval/b4_dev.py
== origin/main + origin/feat/frz2-b4req
b13144d13a976929b5e386f1a10f7160c01c9523
== origin/main + 52bdd47
4c64fbc9f4958969b69db164413d74696232bcf2
```

### A.4 等价与暴露检查

```
$ rra eval-v3 b1b3 --role dev --seeds-file config/dev_seeds.json --output-dir <scratch>/eq_head
{"receipt_sha256": "d583362dab7ef2a23aaf5ec5a16b45686bca443d06b1e53ffedcfb3147a69963", "row": "b1b3", "status": "complete"}
$ (合并 worktree) 同上 --output-dir <scratch>/eq_merge
{"receipt_sha256": "a0c4dbda331784c2238f8142d4bb6e87c20100b02dcbed07cd738dd29949e8b4", "row": "b1b3", "status": "complete"}

compare_b1b3.py eq_head/b1b3.json  s2b3_head/b3-dev.json      → {"seeds_a": 130, "seeds_b": 130, "b1_b3_hash_equal": 130, "episode_row_identical": 130, "metrics_equal": true}
compare_b1b3.py eq_head/b1b3.json  <repo>/artifacts/s2/b3-dev.json → {"seeds_a": 130, "seeds_b": 130, "b1_b3_hash_equal": 15, "episode_row_identical": 15, "metrics_equal": true}
compare_b1b3.py eq_merge/b1b3.json s2b3_merge/b3-dev.json     → {"seeds_a": 130, "seeds_b": 130, "b1_b3_hash_equal": 130, "episode_row_identical": 130, "metrics_equal": true}
compare_b1b3.py eq_merge/b1b3.json <wt_merge>/artifacts/s2/b3-dev.json → {"seeds_a": 130, "seeds_b": 130, "b1_b3_hash_equal": 15, "episode_row_identical": 15, "metrics_equal": true}

暴露检查：构造种子文件 {"seeds": [dev 3/21/7 各加 10000]}，
$ rra eval-v3 b2   --role dev --seeds-file <scratch>/constructed_seeds.json --output-dir <scratch>/expo_b2    → rc=0
$ rra eval-v3 b1b3 --role dev --seeds-file <scratch>/constructed_seeds.json --output-dir <scratch>/expo_b1b3  → rc=0
每个值：stdout 0 行、stderr 0 行；文件命中：b2.json / b1b3.json（.md 未命中）

head b4 打桩 replay：
run r1 rc 0
run r2 rc 0
{"distinct_requests": 444, "episode_id_key_paths_in_user_content": {},
 "receipt_sha256": ["c309dc4a11652f0b5a3334ab72eaf35af152ad293fa16e122daeb4ed05944e43",
                    "c309dc4a11652f0b5a3334ab72eaf35af152ad293fa16e122daeb4ed05944e43"],
 "receipts_equal": true}
合并 b4 打桩 replay：
{"receipt_sha256": "97ac505781e2cc74b6cc24478cf14b0e5d5720c3abeaa2e79e3165b635e72fbc", "row": "b4", "status": "complete"}
run r1 rc 0
{"receipt_sha256": "97ac505781e2cc74b6cc24478cf14b0e5d5720c3abeaa2e79e3165b635e72fbc", "row": "b4", "status": "complete"}
run r2 rc 0
{
 "distinct_requests": 444,
 "episode_id_key_paths_in_user_content": {
  ".evidence_packet.command_feedback[].episode_id": 340,
  ".evidence_packet.decision.episode_id": 444,
  ".evidence_packet.observations[].episode_id": 444,
  ".evidence_packet.presence_events[].episode_id": 444
 },
 "receipt_sha256": [
  "97ac505781e2cc74b6cc24478cf14b0e5d5720c3abeaa2e79e3165b635e72fbc",
  "97ac505781e2cc74b6cc24478cf14b0e5d5720c3abeaa2e79e3165b635e72fbc"
 ],
 "receipts_equal": true
}
```

### A.5 scratch 测试

```
$ PYTHONPATH=<scratch>/guard:<repo>/src python -m pytest -q -p no:cacheprovider test_t9b_scratch.py -rA
25 passed in 3.63s
```

（首次运行 24 passed / 1 failed：`test_guard_bypass_git_dir_env` 中两个临时仓库内容与时间戳相同导致提交 sha 相同，"另一仓库"意外满足 `freeze_commit`；改为使其内容不同后 25 passed。该意外本身也是一次放行。）

---

## 附录 B. 测试草案（未写入 tests/）

文件位于 scratchpad，不随本分支提交；以下为全文。

### B.1 `test_t9b_scratch.py`

```python
"""T9b scratch tests. Seed values used here are constructed by the tests from dev
seeds (dev value + 10000 to sit inside the eval range); no CSPRNG output is produced."""
from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

from rra.eval import b4_dev, final_v3

TREE = Path(final_v3.ROOT)
DEV = json.loads((TREE / "config/dev_seeds.json").read_text())["seeds"]
FAKE = [10000 + s for s in reversed(DEV[:100])]  # deliberately unsorted
TAG = "impl-freeze-v3"


def git(root: Path, *args: str, env=None) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                          text=True, env=env).stdout.strip()


def init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q")
    git(root, "config", "user.name", "t9b")
    git(root, "config", "user.email", "t9b@example.invalid")
    (root / "src").mkdir()
    (root / "src/mod.py").write_text("x = 1\n")
    (root / "tests").mkdir()
    (root / "tests/test_x.py").write_text("y = 1\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "baseline")


def load_generator():
    spec = importlib.util.spec_from_file_location("gen_v3_stubbed", TREE / "scripts/gen_eval_v3_seeds.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # defines functions only; main() is not invoked as a script
    return module


class StubRandom:
    calls = []

    def sample(self, population, k):
        StubRandom.calls.append((population.start, population.stop, k))
        return list(FAKE[:k])


@pytest.fixture
def gen(monkeypatch):
    module = load_generator()
    StubRandom.calls = []
    monkeypatch.setattr(module.secrets, "SystemRandom", StubRandom)
    return module


def seed_payload(root: Path, tag: str = TAG) -> dict:
    return {"schema_version": "rra.eval-seeds.v3", "role": "eval_v3", "count": 100,
            "range": [10000, 2147483647], "generator": "secrets.SystemRandom().sample",
            "freeze_tag": tag, "freeze_commit": git(root, "rev-parse", f"{tag}^{{commit}}"),
            "seeds": FAKE}


def commit_seed_file(root: Path, tag: str = TAG) -> Path:
    path = root / "config/eval_seeds_v3.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(seed_payload(root, tag)) + "\n")
    git(root, "add", "config/eval_seeds_v3.json")
    git(root, "commit", "-qm", "seeds")
    return path


# ---------- 1. generator ----------

def test_gen_population_order_mode_and_output(gen, tmp_path, capsys):
    init_repo(tmp_path)
    git(tmp_path, "tag", TAG)
    old = os.umask(0o022)
    try:
        assert gen.main(["--freeze-tag", TAG, "--root", str(tmp_path)]) == 0
    finally:
        os.umask(old)
    out = capsys.readouterr()
    assert StubRandom.calls == [(10000, 2147483647, 100)]
    target = tmp_path / "config/eval_seeds_v3.json"
    data = json.loads(target.read_text())
    assert data["seeds"] == FAKE  # sample order kept, no sort
    assert stat.S_IMODE(target.stat().st_mode) == 0o644
    assert out.err == "" and out.out.startswith("count=100 sha256=")
    assert all(str(s) not in out.out.split("sha256=")[0] for s in FAKE)
    # the script does not commit: file is untracked, HEAD unchanged
    assert git(tmp_path, "status", "--porcelain") == "?? config/"
    assert git(tmp_path, "rev-parse", "HEAD") == git(tmp_path, "rev-parse", TAG)


def test_gen_accepts_any_tag_name(gen, tmp_path):
    init_repo(tmp_path)
    git(tmp_path, "tag", "not-the-freeze-tag")
    assert gen.main(["--freeze-tag", "not-the-freeze-tag", "--root", str(tmp_path)]) == 0


def test_gen_clean_check_ignores_gitignored_and_skip_worktree(gen, tmp_path):
    init_repo(tmp_path)
    git(tmp_path, "update-index", "--skip-worktree", "src/mod.py")
    git(tmp_path, "tag", TAG)
    (tmp_path / "src/mod.py").write_text("x = 2  # modified, hidden by skip-worktree\n")
    assert gen.main(["--freeze-tag", TAG, "--root", str(tmp_path)]) == 0


@pytest.mark.parametrize("where", ["fdopen", "mkdir"])
def test_gen_failure_paths_do_not_print_values(gen, tmp_path, monkeypatch, capsys, where):
    init_repo(tmp_path)
    git(tmp_path, "tag", TAG)
    if where == "fdopen":
        def boom(*a, **k):
            raise OSError("disk full")
        monkeypatch.setattr(gen.os, "fdopen", boom)
    else:
        (tmp_path / "config").write_text("not a dir\n")
        git(tmp_path, "add", "config"); git(tmp_path, "commit", "-qm", "c"); git(tmp_path, "tag", "-f", TAG)
    rc = gen.main(["--freeze-tag", TAG, "--root", str(tmp_path)])
    out = capsys.readouterr()
    assert rc == 2
    assert all(str(s) not in out.out + out.err for s in FAKE)
    assert not (tmp_path / "config/eval_seeds_v3.json").exists()


def test_gen_uncaught_exception_traceback_has_no_values(gen, tmp_path, monkeypatch):
    """A non-OSError/ValueError (e.g. TypeError in json.dumps) escapes main(); its
    traceback locals are not printed by default, and the message holds no values."""
    init_repo(tmp_path)
    git(tmp_path, "tag", TAG)
    def bad_dumps(*a, **k):
        raise TypeError("not serializable")
    monkeypatch.setattr(gen.json, "dumps", bad_dumps)
    with pytest.raises(TypeError) as info:
        gen.main(["--freeze-tag", TAG, "--root", str(tmp_path)])
    assert all(str(s) not in str(info.value) for s in FAKE)


# ---------- 2. guard ----------

@pytest.mark.parametrize("extra,ok", [
    (None, True),
    ("artifacts/eval_v3/b2.json", True),
    ("src/mod.py", False),
    ("tests/test_x.py", False),
    ("artifacts/llm_cache/abc.json", False),
    ("config/eval_seeds_v3.json.bak", False),
])
def test_guard_allowlist(tmp_path, extra, ok):
    init_repo(tmp_path)
    git(tmp_path, "tag", TAG)
    path = commit_seed_file(tmp_path)
    if extra:
        p = tmp_path / extra
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("changed\n")
        git(tmp_path, "add", "-A"); git(tmp_path, "commit", "-qm", "extra")
    if ok:
        seeds, _ = final_v3.load_seed_file(path, "eval_v3", freeze_tag=TAG, root=tmp_path)
        assert seeds == FAKE
    else:
        with pytest.raises(ValueError, match="allowlist"):
            final_v3.load_seed_file(path, "eval_v3", freeze_tag=TAG, root=tmp_path)


def test_guard_rejects_untracked_cache_file(tmp_path):
    init_repo(tmp_path)
    git(tmp_path, "tag", TAG)
    path = commit_seed_file(tmp_path)
    (tmp_path / "artifacts/llm_cache").mkdir(parents=True)
    (tmp_path / "artifacts/llm_cache/abc.json").write_text("{}\n")
    with pytest.raises(ValueError, match="clean"):
        final_v3.load_seed_file(path, "eval_v3", freeze_tag=TAG, root=tmp_path)


def test_guard_bypass_skip_worktree(tmp_path):
    init_repo(tmp_path)
    git(tmp_path, "tag", TAG)
    path = commit_seed_file(tmp_path)
    git(tmp_path, "update-index", "--skip-worktree", "src/mod.py")
    (tmp_path / "src/mod.py").write_text("x = 999\n")
    seeds, _ = final_v3.load_seed_file(path, "eval_v3", freeze_tag=TAG, root=tmp_path)
    assert seeds == FAKE  # accepted although src/ differs from the tag in the working tree


def test_guard_bypass_git_dir_env(tmp_path, monkeypatch):
    real, other = tmp_path / "real", tmp_path / "other"
    init_repo(real); git(real, "tag", TAG); path = commit_seed_file(real)
    (real / "src/mod.py").write_text("x = 999\n"); git(real, "commit", "-qam", "src change")
    with pytest.raises(ValueError, match="allowlist"):
        final_v3.load_seed_file(path, "eval_v3", freeze_tag=TAG, root=real)
    init_repo(other); (other / "src/mod.py").write_text("x = 5\n"); git(other, "commit", "-qam", "differs"); git(other, "tag", TAG)
    # point git at a clean repo whose tag commit equals... a different commit; freeze_commit check then fails
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    with pytest.raises(ValueError):
        final_v3.load_seed_file(path, "eval_v3", freeze_tag=TAG, root=real)
    # same, but the other repo is a clone of real at the tag (freeze_commit matches)
    monkeypatch.delenv("GIT_DIR"); monkeypatch.delenv("GIT_WORK_TREE")
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", str(real), str(clone)], check=True)
    git(clone, "checkout", "-q", TAG)
    git(clone, "config", "user.name", "t"); git(clone, "config", "user.email", "t@x")
    (clone / "config").mkdir(); (clone / "config/eval_seeds_v3.json").write_text(path.read_text())
    git(clone, "add", "-A"); git(clone, "commit", "-qm", "seeds only")
    monkeypatch.setenv("GIT_DIR", str(clone / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(clone))
    seeds, _ = final_v3.load_seed_file(path, "eval_v3", freeze_tag=TAG, root=real)
    assert seeds == FAKE  # accepted: guard inspected the clone, real/ has a src change


def test_guard_bypass_retag(tmp_path):
    init_repo(tmp_path)
    git(tmp_path, "tag", TAG)
    (tmp_path / "src/mod.py").write_text("x = 999\n"); git(tmp_path, "commit", "-qam", "src change")
    git(tmp_path, "tag", "other-tag")
    path = commit_seed_file(tmp_path, tag="other-tag")
    seeds, _ = final_v3.load_seed_file(path, "eval_v3", freeze_tag="other-tag", root=tmp_path)
    assert seeds == FAKE  # tag name is not pinned to impl-freeze-v3


def test_guard_head_not_descendant_of_tag(tmp_path):
    init_repo(tmp_path)
    git(tmp_path, "tag", TAG)
    tagged_tree = git(tmp_path, "rev-parse", f"{TAG}^{{tree}}")
    orphan = git(tmp_path, "commit-tree", tagged_tree, "-m", "orphan with the same tree")
    git(tmp_path, "checkout", "-q", orphan)
    path = commit_seed_file(tmp_path)
    assert git(tmp_path, "rev-parse", "HEAD~1") != git(tmp_path, "rev-parse", TAG)
    seeds, _ = final_v3.load_seed_file(path, "eval_v3", freeze_tag=TAG, root=tmp_path)
    assert seeds == FAKE  # parent of the seed commit is not the tag commit


def test_role_dev_reads_any_file_without_guard(tmp_path):
    path = tmp_path / "eval_seeds_v3.json"
    path.write_text(json.dumps(seed_payload_dummy()) + "\n")
    seeds, _ = final_v3.load_seed_file(path, "dev")
    assert seeds == FAKE


def seed_payload_dummy():
    return {"schema_version": "rra.eval-seeds.v3", "role": "eval_v3", "count": 100,
            "range": [10000, 2147483647], "freeze_tag": TAG, "freeze_commit": "0" * 40,
            "seeds": FAKE}


def test_main_role_dev_accepts_eval_seed_path_and_cap_override(monkeypatch, tmp_path):
    """main() only checks the path for --subset; --role dev takes any file and
    --max-live-calls is accepted for role eval_v3 too (argument parsing only)."""
    seen = {}
    def fake_load(path, role, freeze_tag=None, root=None):
        seen["path"], seen["role"] = Path(path), role
        return FAKE[:2], "0" * 64
    def fake_run_row(row, **kw):
        seen["kw"] = kw
        return {"status": "complete", "receipt_sha256": "x"}
    monkeypatch.setattr(final_v3, "load_seed_file", fake_load)
    monkeypatch.setattr(final_v3, "run_row", fake_run_row)
    target = final_v3.ROOT / "config/eval_seeds_v3.json"  # path string only; never opened here
    assert final_v3.main(["b4", "--role", "dev", "--seeds-file", str(target), "--live",
                          "--output-dir", str(tmp_path)]) == 0
    assert seen["path"] == target.resolve() and seen["role"] == "dev"
    assert final_v3.main(["b2", "--freeze-tag", TAG, "--max-live-calls", "999999",
                          "--output-dir", str(tmp_path)]) == 0
    assert seen["kw"]["max_live_calls"] == 999999


# ---------- 3. cap accounting ----------

class FakeLive:
    script: list = []
    sent: list = []

    def __init__(self, cache_dir=None, **kw):
        self.last_http_status = None
        self.model = b4_dev.NIM_MODEL
        self.max_tokens = 1800
        self.chat_template_kwargs = {"enable_thinking": False}
        self.no_think = False
        self.format_mode = kw.get("format_mode", "json_object")
        self.cache_dir = Path(cache_dir)

    def complete(self, body):
        FakeLive.sent.append(body)
        status = FakeLive.script.pop(0) if FakeLive.script else 200
        self.last_http_status = status
        if status != 200:
            raise RuntimeError(f"HTTP {status}")
        from rra.llm.providers import canonical_json, finalize_payload, request_sha256
        payload = finalize_payload(body, self)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / f"{request_sha256(payload)}.json").write_text(
            canonical_json({"request": payload, "response": {"model": "served/x", "choices": []}}))
        return {"model": "served/x", "choices": []}


def body(i):
    return {"messages": [{"role": "system", "content": "s"}, {"role": "user", "content": json.dumps({"i": i})}]}


@pytest.fixture
def scope(monkeypatch, tmp_path):
    FakeLive.script, FakeLive.sent = [], []
    monkeypatch.setattr(b4_dev, "NvidiaNimProvider", FakeLive)
    monkeypatch.setattr(b4_dev.time, "sleep", lambda s: None)
    return tmp_path / "cache"


def test_cache_hit_not_counted_retry_counted_once(scope):
    with final_v3._LiveBudgetScope(10) as budget:
        rt = b4_dev._ReadThroughProvider(scope)
        rt.complete(body(1)); rt.complete(body(1))          # second is a cache hit
        FakeLive.script = [500, 200]; rt.complete(body(2))  # one 5xx retry, same key
        assert budget.distinct_total() == 2
        assert len(FakeLive.sent) == 3                       # three HTTP attempts


def test_failed_request_still_counted(scope):
    with final_v3._LiveBudgetScope(10) as budget:
        rt = b4_dev._ReadThroughProvider(scope)
        FakeLive.script = [500, 500, 500]
        with pytest.raises(RuntimeError):
            rt.complete(body(3))
        FakeLive.script = [400]
        with pytest.raises(RuntimeError):
            rt.complete(body(4))
        assert budget.distinct_total() == 2  # both counted, neither cached
        assert not any(scope.glob("*.json"))


def test_401_is_systemexit_and_counts(scope):
    with final_v3._LiveBudgetScope(10) as budget:
        rt = b4_dev._ReadThroughProvider(scope)
        FakeLive.script = [401]
        with pytest.raises(SystemExit):
            rt.complete(body(5))
        assert budget.distinct_total() == 1


def test_cap_stops_before_new_request(scope):
    with final_v3._LiveBudgetScope(2, already=1) as budget:
        rt = b4_dev._ReadThroughProvider(scope)
        rt.complete(body(6))
        with pytest.raises(final_v3.LiveBudgetExceeded):
            rt.complete(body(7))
        assert budget.distinct_total() == 2 and len(FakeLive.sent) == 1


def test_prior_count_lost_after_crash_or_replay(tmp_path, monkeypatch):
    """_run_b4 writes nothing on SystemExit/RuntimeError; a replay receipt resets the count."""
    def crash(*a, **k):
        raise SystemExit("NVIDIA NIM HTTP 401; stop Phase B")
    monkeypatch.setattr(b4_dev, "run_b4_dev", crash)
    (tmp_path / "b4.json").write_text(json.dumps({"distinct_live_requests": 700}))
    with pytest.raises(SystemExit):
        final_v3._run_b4(tmp_path / "s.json", tmp_path, replay=False, live=True, subset=False,
                         max_live_calls=2500, nproc=1)
    assert final_v3._prior_distinct_live_requests(tmp_path) == 700  # file untouched; this attempt's count not added
    monkeypatch.setattr(b4_dev, "run_b4_dev", lambda *a, **k: {"metrics": {}, "episodes": [], "llm_calls": 0})
    result = final_v3._run_b4(tmp_path / "s.json", tmp_path, replay=True, live=False, subset=False,
                              max_live_calls=2500, nproc=1)
    assert result["distinct_live_requests"] == 0  # run_row would write this into b4.json
    assert final_v3._prior_distinct_live_requests(tmp_path / "elsewhere") == 0  # new dir starts at 0


def test_no_deadline_logic():
    src = (TREE / "src/rra/eval/final_v3.py").read_text() + (TREE / "src/rra/eval/b4_dev.py").read_text()
    assert "2026-10-27" not in src and "deadline" not in src.lower()
```

### B.2 `b4_stub_replay.py`

```python
"""Run `rra eval-v3 b4 --role dev --subset --replay` in-process with a stubbed replay
provider (no network, no cache read). Records distinct finalized requests and the
keys that carry an episode identifier. Usage: b4_stub_replay.py OUT_DIR [--real-cache]"""
import json
import sys
from pathlib import Path

from rra.eval import b4_dev, final_v3
from rra.llm.providers import finalize_payload, request_sha256

out = Path(sys.argv[1])
real_cache = "--real-cache" in sys.argv
seen: dict[str, dict] = {}


class StubReplay:
    def __init__(self, cache_dir, **kw):
        self.settings = {"model": kw.get("model"), "max_tokens": 1800,
                         "chat_template_kwargs": {"enable_thinking": False}, "no_think": False,
                         "format_mode": kw.get("format_mode", "json_object")}

    def complete(self, body):
        payload = finalize_payload(body, self.settings)
        seen[request_sha256(payload)] = payload
        return {"model": "stub/served", "choices": [{"message": {"content": "{\"items\": []}"}}]}


if not real_cache:
    b4_dev.ReplayProvider = StubReplay
dev = final_v3.DEV_SEEDS_PATH
receipts = []
for run in ("r1", "r2"):
    rc = final_v3.main(["b4", "--role", "dev", "--seeds-file", str(dev), "--subset", "--replay",
                        "--output-dir", str(out / run)])
    receipts.append(json.loads((out / run / "b4.json").read_text())["receipt_sha256"] if rc == 0 else None)
    print("run", run, "rc", rc)


def episode_id_paths(value, path=""):
    if isinstance(value, dict):
        for k, v in value.items():
            if k == "episode_id":
                yield path + "." + k
            yield from episode_id_paths(v, path + "." + k)
    elif isinstance(value, list):
        for item in value:
            yield from episode_id_paths(item, path + "[]")


paths: dict[str, int] = {}
for payload in seen.values():
    for message in payload["messages"]:
        try:
            user = json.loads(message["content"])
        except (json.JSONDecodeError, TypeError):
            continue
        for p in set(episode_id_paths(user)):
            paths[p] = paths.get(p, 0) + 1
summary = {"distinct_requests": len(seen), "receipts_equal": receipts[0] == receipts[1],
           "receipt_sha256": receipts, "episode_id_key_paths_in_user_content": paths}
print(json.dumps(summary, indent=1, sort_keys=True))
```

### B.3 `compare_b1b3.py`

```python
"""compare_b1b3.py EVAL_B1B3_JSON B3DEV_JSON: per-seed B1/B3 receipt hash equality and metrics."""
import json, sys
a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2]))
ea = {e["seed"]: e for e in a["episodes"]}; eb = {e["seed"]: e for e in b["episodes"]}
same = sum(ea[s].get("b1_receipt_sha256") == eb[s].get("b1_receipt_sha256") and
           ea[s].get("b3_receipt_sha256") == eb[s].get("b3_receipt_sha256") for s in eb if s in ea)
full = sum(json.dumps(ea[s], sort_keys=True) == json.dumps(eb[s], sort_keys=True) for s in eb if s in ea)
print(json.dumps({"seeds_a": len(ea), "seeds_b": len(eb), "b1_b3_hash_equal": same,
                  "episode_row_identical": full, "metrics_equal": a["metrics"] == b["metrics"]}))
```

## 附录 C. 执行隔离

### C.1 `sitecustomize.py`（审计钩子）

```python
import os, sys, fnmatch
_ROOTS = [r for r in os.environ.get("T9B_PROTECTED_ROOTS", "").split(":") if r]
_LOG = os.environ.get("T9B_BLOCK_LOG")
def _log(msg):
    if _LOG:
        with open(_LOG, "a") as f:  # opened before hook check matters (not protected path)
            f.write(msg + "\n")
def _hook(event, args):
    if event == "open":
        p = args[0]
        if isinstance(p, (str, bytes, os.PathLike)) and not isinstance(p, int):
            try:
                s = os.path.abspath(os.fsdecode(p))
            except Exception:
                return
            name = os.path.basename(s)
            if fnmatch.fnmatch(name, "eval_seeds*.json") and any(s.startswith(r.rstrip("/") + "/config/") for r in _ROOTS):
                _log(f"BLOCKED open {s}")
                raise PermissionError(f"T9B guard: open of protected seed file blocked")
    elif event == "subprocess.Popen":
        argv = args[1]
        try:
            joined = " ".join(map(os.fsdecode, argv)) if not isinstance(argv, (str, bytes)) else os.fsdecode(argv)
        except Exception:
            joined = str(argv)
        if "gen_eval_v3_seeds" in joined:
            _log(f"BLOCKED exec gen_eval_v3_seeds")
            raise PermissionError("T9B guard: seed generator execution blocked")
sys.addaudithook(_hook)
```
