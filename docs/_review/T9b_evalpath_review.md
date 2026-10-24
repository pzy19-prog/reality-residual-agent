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
- 补充：§9 在收到协调会话 08:08Z 的消息（X1、X2、`command_id` 口径）之后加入，前文的 M-8 与 §5.1 的 `command_id` 行也是这时加的。
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
| B4 请求体 `command_feedback[].command_id` | `f"{seed}:{target_id}:{step}"`（#28 `episode.py:1032`；#27 `episode.py:1058`） | 无（旧请求反馈行只有 4 个时间/布尔字段） | 有（§9.3 实测） | 仍有，除非按协调会话口径改写为 `"{target_id}:{step}"`；今天的所有者裁决条文只列出 `episode_id` |
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
- **M-8** B4 请求 `command_feedback[].command_id` 含种子（§9.3）；按协调会话口径改写后，需重做 §9.3 检查（附录 B.4 最后一个用例）。

### 8.3 建议

- **S-1** 守卫加固：清除 `GIT_*` 环境变量后再调用 git；检查 tag 是 HEAD 祖先且种子提交的父提交为 tag；检查 `git ls-files -v` 中的 skip-worktree/assume-unchanged 标记；考虑 `--ignored`。
- **S-2** `b4.json` 收录 `llm_request_spec`、`served_models`、两变体 proposer 调用数（E-6、E-12）。
- **S-3** A04 §6.1 逐类计数与 §6.2 判定在结果代码中实现或在报告步骤中明确由谁计算（E-13）。
- **S-4** 生成器文件权限（0o644）与 `python -X dev`/带局部变量 traceback 环境下的打印风险，在执行说明中写明。
- **S-5** 现有测试以子进程真实运行生成器（tmp 中产生 CSPRNG 值）；与"agent 会话不运行生成器"的操作规则冲突，执行者运行全量 pytest 时须知悉。
- **S-6** `--role dev` 拒绝名为 `eval_seeds_v3.json` 或 `role: eval_v3` 的文件；eval 角色下禁止调高 `--max-live-calls`。
- **S-7** b1b3 在 eval 角色下由 `run_b3_dev` 再次读取种子文件（与 `final_v3` 校验后的列表不是同一对象）；可改为传入已校验列表。

---

## 9. 协调会话补充（2026-10-24 08:08Z 消息）复核

协调会话的消息提出 X1、X2 两个阻塞项，并给出本地拟定修复与种子口径。本节逐条复核。所提修复尚未出现在任何分支上，所以只能写成"拟定行为"的测试草案；草案在当前代码上运行，失败计数照实记录。

### 9.1 X1（守卫与 `artifacts/llm_cache/`）

- 复核：与本报告 §2.3 / M-1 一致。实测：未跟踪的新缓存文件被拒（`working tree must be clean`）；提交后的新缓存文件被拒（`outside the eval allowlist`）。另外，**允许列表内的未跟踪文件同样被拒**：`artifacts/eval_v3/b4.json`、`artifacts/eval_v3/live_ledger.jsonl` 未跟踪时也因工作树不干净而拒绝。所以每行运行之后都要先提交回执，下一行才能开始；而 B4 live 中断之后，按 X2 写出的 ledger 本身也会触发拒绝。
- 拟定修复的可检验点（附录 B.4 第 1 部分）：允许列表内的未跟踪文件放行；提交后的新缓存文件放行；已有缓存文件的修改或删除（已提交、未提交两种）拒绝；`src/`、`tests/` 下的未跟踪文件，以及前缀相似的 `artifacts/llm_cache_x/` 拒绝；工作区里未提交的 `src` 修改拒绝。
- 草案当前结果：4 个"应放行"用例全部失败（被现行规则拒绝），8 个"应拒绝"用例通过。在现行代码下，这 8 个是因为任何改动都会让工作树不干净而被拒，不是因为区分了新增与修改。
- 与 §2.2 绕过的关系：拟定修复没有涉及 `GIT_DIR`/`GIT_WORK_TREE`、`--skip-worktree`、换 tag、非后代 HEAD。这四种绕过在修复后仍然成立，除非另行处理。
- 关于"只允许新增"（FACT）：缓存文件名是请求 SHA-256，live 只写缺失的键（`_ReadThroughProvider` 先查缓存），正常流程不会改写已有文件。dev 缓存与 eval 缓存同在 `artifacts/llm_cache/`，修复后 `<tag>..HEAD` 中新增的文件全部来自 eval-v3 live。

### 9.2 X2（distinct-live 计数持久化）

- 复核：与 §3.2 / M-3 一致，包括崩溃、`KeyboardInterrupt`、401/403 的 `SystemExit`、replay 覆盖 `b4.json`、换输出目录这几条路径。
- 拟定修复的可检验点（附录 B.4 第 2 部分）：每次 live 调用之前追加写 ledger，401 之后 ledger 中已有该请求；ledger 行只含 64 位十六进制 SHA；续跑时已用次数取 ledger 中不同 SHA 的个数，与输出目录无关，2,499 条记录之后只能再发 1 个新请求。
- 草案当前结果：3 个用例全部失败（ledger 不存在；续跑时已用次数为 0，没有在上限处停止）。
- 实现时需要注意的事实：
  - 计数登记发生在 `LimitedProvider.complete` 中，位于发送之前（`final_v3.py:96-100`）。B4 使用线程池（`b4_dev.py:244-249`），写 ledger 需要与 `_lock` 同步，否则多个线程可能交错写入。
  - 5xx 重试复用同一个键，ledger 去重后计 1 次。
  - 若 ledger 放在 `artifacts/eval_v3/`，按 X1 修复之前的规则，它未跟踪时会让下一条命令被拒（见 9.1）。
  - 两次 replay 不发 live 请求，不写 ledger。若 replay 仍写回同一目录的 `b4.json`，`distinct_live_requests` 字段会是 0；这只影响回执中的该字段，不再影响上限。

### 9.3 种子口径：去掉 `episode_id`，`command_id` 改写为 `"{target_id}:{step}"`

**实测（附录 B.5 `seed_strings_in_request.py`）**：dev seed 3、21，4 个文本变体，B4_STRICT，空提案 provider。在 user content 中找"等于 `str(seed)` 或以 `"{seed}:"` 开头"的字符串：

| 树 | 不同请求 | 命中的键路径（次数） |
|---|---|---|
| #28 head | 36 | 无 |
| #27 + #28 + main 合并 | 36 | `command_feedback[].command_id` 56、`command_feedback[].episode_id` 56、`decision.episode_id` 36、`observations[].episode_id` 1388、`presence_events[].episode_id` 1388 |

`command_id` 的格式是 `f"{seed}:{target_id}:{step}"`（#28 `src/rra/evidence/episode.py:1032`，#27 `:1058`）。#27 把 `policy_feedbacks` 的整行（`**item`）放进 `command_feedback`，所以 `command_id` 随之进入请求。本报告 §4 合并行的打桩运行只统计了 `episode_id` 键，没有覆盖 `command_id`，这里补上。

**按协调口径修改后，剩余位置（FACT）**：

| 位置 | 是否写出种子值 | 说明 |
|---|---|---|
| B4 请求体、外部服务 | 否（按口径） | 剩下与种子有关的只有 `context.text` 的模板与措辞选择（`seed % k`）和 `context.content_sha256`；仿真数值由种子决定 |
| 缓存文件名 | 否 | 最终请求的 SHA-256 |
| 缓存文件内容 | 否（按口径） | 请求 + 响应；响应由服务端生成 |
| ledger（`artifacts/eval_v3/live_ledger.jsonl`，拟定） | 否 | 只有请求 SHA-256，与缓存文件名是同一组值 |
| `artifacts/eval_v3/<row>.json` | **是** | b1b3、b2、b4 的 `episodes[].seed`；b1-legacy 的 `diagnostic.seeds.values` |
| `artifacts/eval_v3/b4-dev.json`（旁路） | **是** | `seed_identity.values` 全部种子、`seed_identity.path` 绝对路径、`episodes[].seed` |
| `.md` 回执、stdout | 否 | 实测 |
| 失败路径的 stderr / traceback | **是** | §5.2 的 7 处 |
| 行回执中的 episode receipt 哈希 | 否（值） | 哈希的输入含种子 |
| L3 导出（`sources.py`） | 是（`episode_id = str(seed)`、`command_id`） | eval-v3 路径不调用；只有单独对 eval 种子运行 L3 导出时才写出 |
| Meterless / Zetaris | 不涉及 | eval-v3 路径不导入 `sponsor/*` |
| `/tmp/eval-v3-b1b3-*/b3-dev.json` | 是（临时） | 进程结束时删除 |

**提交到公开仓库的影响（只陈述）**：

- 缓存文件与 ledger 本身不含种子值。但请求内容（观测数值、`context.text` 的选择）是种子的确定性函数，代码又是公开的，理论上可以穷举候选种子、比对请求或 SHA 来反推。候选空间约 2.1×10⁹。本机每个 episode 约 1.2 s（b1b3 在 4 核上 80 s 跑完 130 seed × 2 个 episode 加串/并行检查），单核穷举约 2.6×10⁹ 核秒；可以并行分摊。这是对可行性量级的事实估计，没有实际尝试。
- 行回执与 `b4-dev.json` 一经提交即公开种子值。A06 §1.3 写的是"所有登记基线运行完后，种子值出现在结果回执中"。若 b1b3/b2/b1-legacy 先于 B4 live 完成就提交（现行守卫要求每行之后先提交，§9.1），种子值会在 B4 live 期间公开。
- `b4-dev.json` 的绝对路径会公开运行机器的目录结构。

### 9.4 协调会话其他要求的现状

| 要求 | 现状（FACT） |
|---|---|
| #27 合并后，把 main 合进 #28 | #27 未合并；#28 与 #27 冲突两处（§6.1）。本节的合并树为临时 worktree，未推送 |
| eval 的 b4 路径传递 `format_mode` | 未传；`rra eval-v3` 无该参数（§3.3） |
| 带上 `llm_request_spec`、`served_models` | 只在旁路 `b4-dev.json`，不在 `b4.json`（§6.3 实测） |
| 重跑 dev 等价验证 | 已在合并树上运行：b1b3 130/130（同机）；b4 打桩 replay 两次一致、444 个请求（§4）。修复提交出现后需要再跑一次 |

### 9.5 新增（X1、X2 之外，本报告发现的协议或实现问题）

与 §8 对应，列出编号以便追踪：

- **N-1** tag 名不固定（生成器与守卫，§1.1、§2.2）——对应 M-2。
- **N-2** 守卫可以通过 `GIT_DIR`/`GIT_WORK_TREE`、`--skip-worktree`、另建 tag、非后代 HEAD 绕过（§2.2）；`--role dev` 可读 eval 文件且没有守卫；eval 角色下 `--max-live-calls` 可以调高。
- **N-3** 没有截止时间实现；非上限情形不产生 incomplete 标记；没有部分 replay 的入口（§3.2）——对应 M-4、T9a M-4。
- **N-4** 401/403 的退出码为 1，且不写回执（§3.2）。
- **N-5** 失败路径消息中写出种子值，共 7 处（§5.2）——对应 M-7。
- **N-6** B4 请求中的 `command_id` 携带种子（§9.3）。今天的所有者裁决条文没有提到它，协调会话口径提到了。
- **N-7** b1-legacy 按 14 个场景 × 全部种子运行，不按 `index % 19`；`diagnostic.seeds.path` 硬编码为 dev 路径（§3.1、§8.1 第 8 项）。
- **N-8** `b4-dev.json` 旁路文件含全部种子值和绝对路径；`b4.json` 缺 `llm_request_spec`、`served_models`（§3.3）。
- **N-9** A04 §6.1 的逐类计数和 §6.2 的 50% 判定没有实现（§3.4）。
- **N-10** 现有测试以子进程真实运行生成器（§7、S-5）。
- **N-11** 生成器的干净检查忽略 `.gitignore` 中的文件和 skip-worktree 标记（§1.1）。

---

## 10. 补充：PR #27 合并后（main `edd54c0`）与 #28 的合并复核

本节在协调会话 09:12Z 的消息之后加入。按要求不改动前文；前文 §4、§6、§9.3 的"合并"指 `a9fa6c3`（R11 之前的 #27）+ #28 + 旧 main，结论仍按当时的对象成立。

### 10.1 对象核对（FACT）

- `git rev-parse origin/main` = `edd54c053953576c9b08c32f31613ba34e9ba5fa`（Merge pull request #27），`origin/feat/frz2-b4req` = `466bec6613f3950b12c00c789ed81c4c36aa3e39`，`466bec6` 是 `origin/main` 的祖先。与消息一致。
- `466bec6`（"Strip seed identifiers from the B4 generator request"）只改 `src/rra/evidence/episode.py`、`src/rra/evidence/packet.py`、`tests/test_frz2_packet_equivalence.py`。新增 `packet.generator_view(packet)`：深拷贝之后删除 `decision.episode_id` 以及三组行级 `episode_id`，并把每条反馈的 `command_id` 改写为 `f"{row['target_id']}:{row['step']}"`（`packet.py:40-57`）。`episode.py:705` 的 B4 调用点改为 `generator_view(build_packet(...))`。`build_packet` 与 L3 导出没有改动。
- `git merge-tree --write-tree --name-only origin/main 52bdd47` → 树 `e980415…`，冲突文件仍是 `src/rra/cli.py`、`src/rra/eval/b4_dev.py`，内容与 §6.1 相同（`--format-mode` 对 `eval-v3` 子解析器；`run_b4_dev` 签名的 `format_mode` 对 `seeds_path`）。
- 临时 worktree：从 `52bdd47` 出发，`merge --no-ff origin/main`，两处冲突取并集，签名为 `replay_only=False, format_mode="json_object", seeds_path=None`。合并树 `4fbdddf9e0b5f3d03aa892060065dc6dd310daae`，未推送。下文所说的"R11 合并树"即指此树。

### 10.2 请求中的种子字符串（dev 种子 3、21，以及 diag 子集 33 个种子）

方法：`seed_strings_in_request.py`（附录 B.7，为附录 B.5 的修订版）对每个种子跑 4 个文本变体的 B4_STRICT，provider 返回空提案，检查 user content。判定分两步：
1. 值检查：某个字符串值等于 `str(seed)`，或以 `"{seed}:"` 开头；
2. 位置检查：每条 `command_feedback` 的 `command_id` 必须恰好等于本行的 `f"{target_id}:{step}"`。

dev 种子都是 0–129 的小整数，与 `target_id`、`step` 取值重叠，所以值检查对 `command_id` 会误报。以位置检查为准。

| 树 | 种子 | 不同请求 | 值检查命中 | `command_id` 位置检查 |
|---|---|---|---|---|
| #28 head | 3、21 | 36 | 无 | 请求中无 `command_id` |
| `a9fa6c3`+#28（§9.3） | 3、21 | 36 | 5 个键路径（含 `command_id` 56、`episode_id` 共 2,868） | 未做（当时格式是三段式 `{seed}:…`） |
| R11 合并树 | 3、21 | 36 | 只剩 `command_feedback[].command_id` 4 处 | 56/56 是两段式且等于本行 `{target_id}:{step}` |
| R11 合并树 | diag 33 个 | 444 | 只剩 `command_feedback[].command_id` 4 处 | 1,096/1,096 是两段式且与本行一致 |

剩下的 4 处值检查命中：位置检查显示它们是两段式，并且等于本行的 `{target_id}:{step}`。它们都以 `"3:"` 开头，对应 seed 3 的 episode 中 `target_id = 3` 的反馈行，属于上面说的误报。R11 合并树的请求中再没有 `episode_id` 键的值等于种子。

**M-8**：在上述 36 + 444 个请求上，R11 已经去掉 `command_id` 中的种子前缀，以及全部 `episode_id`。`test_request_has_no_seed_strings` 改用位置检查（附录 B.6）之后，在 #28 head 与 R11 合并树上都是 `1 passed`。按本报告的检验，M-8 的条件已不再出现。生成 `command_id` 的源头仍是 `episode.py:1058` 的 `f"{seed}:{observation.target_id}:{observation.step}"`；只在发给生成器的视图里改写，episode 内部和 L3 的数据仍保留种子前缀。

### 10.3 全量 pytest 与测试草案（R11 合并树，钩子开启）

```
FAILED tests/test_bench.py::test_benchmark_includes_nominal_and_all_intensity_bands
FAILED tests/test_eval_v3.py::test_seed_generator_creates_100_unique_in_range_without_printing_values
FAILED tests/test_eval_v3.py::test_seed_generator_refuses_unsafe_states_without_writing[tag_mismatch]
FAILED tests/test_eval_v3.py::test_seed_generator_refuses_unsafe_states_without_writing[dirty_tree]
FAILED tests/test_eval_v3.py::test_seed_generator_refuses_unsafe_states_without_writing[target_exists]
5 failed, 230 passed, 4 skipped in 348.96s (0:05:48)
```

5 个 failed 与 §6.2 是同一批钩子拦截。输出中出现 14 次 `T9B guard`，都来自这 5 个测试的 traceback。这次运行的环境变量里漏设了钩子日志路径，所以没有拦截日志，以 traceback 为准。

测试草案（R11 合并树）：
- `test_t9b_scratch.py`：25 个用例全部通过（同 §7，断言当前行为）。
- `test_t9b_x1x2_drafts.py` 首次运行：8 failed。7 个是 X1/X2 拟定行为（与 §9 相同），1 个是 `test_request_has_no_seed_strings`，失败原因是上面说的值检查误报。
- 草案改用位置检查之后，该用例在 #28 head 与 R11 合并树上都是 `1 passed`；整体为 `7 failed, 9 passed`，7 个失败全部是 X1/X2 尚未实现。

### 10.4 dev 等价（R11 合并树）

| 检查 | 结果 |
|---|---|
| `eval-v3 b1b3 --role dev` 对同机 `s2-b3-dev` | 130/130 哈希相同；130/130 行相同；metrics 相同。b1b3 `receipt_sha256` = `a0c4dbda331784c2238f8142d4bb6e87c20100b02dcbed07cd738dd29949e8b4`，与 §4 的 `a9fa6c3` 合并树相同，因为 R11 只改 B4 请求 |
| 对合并树中已提交的 `artifacts/s2/b3-dev.json` | 15/130 哈希相同；metrics 相同（跨机） |
| b4 打桩 replay，dev 子集，两次 | 两次退出码 0；`receipt_sha256` 两次相同（`97ac505781e2cc74b6cc24478cf14b0e5d5720c3abeaa2e79e3165b635e72fbc`，与 `a9fa6c3` 合并树相同：桩返回空提案，决策不受请求体变化影响，回执中也不含请求体）；不同最终请求 444 个；user 内容中 `episode_id` 键 0 处 |

### 10.5 R11 之后剩余的种子暴露点（FACT）

| 位置 | 是否写出种子值 | 说明 |
|---|---|---|
| B4 请求体 / 外部服务 | 否 | §10.2 实测。剩下与种子相关的只有 `context.text` 的模板与措辞选择（`seed % k`）和 `context.content_sha256`；观测数值由种子决定，但不是种子值 |
| 缓存文件名 / 缓存内容 | 否 | 文件名是请求 SHA-256；内容是请求加响应。响应由服务端生成，而请求中已无种子 |
| 拟定的 ledger | 否 | 只有请求 SHA-256 |
| 行回执 `b1b3.json`、`b2.json` | **是** | 只在 `episodes[].seed`（构造值实测：`b1b3.json` 中唯一的命中路径是 `.episodes[].seed`；`b2.json` 同样 1 处） |
| `b4.json` | **是** | `episodes[].seed` |
| `b1-legacy.json` | **是** | `diagnostic.seeds.values`，`path` 硬编码为 `config/dev_seeds.json`（`dev_diagnostics.py:53`） |
| `b4-dev.json`（旁路） | **是** | `seed_identity.values`（全部种子）、`seed_identity.path` 绝对路径（`b4_dev.py:331-333`）、`episodes[].seed` |
| 错误信息 | **是**（R11 未涉及） | 行号对应 R11 合并树：`b4_dev.py:243`（B-1 mismatch）、`b4_dev.py:295`（serial/parallel mismatch）、`b3_dev.py:211`（parity 中的 `seeds`）、`b3_dev.py:66,83,95`（T7/T8）、`context_v3.py:218`（`episode=str(seed)`，被 `final_v3.main` 捕获后打印到 stderr） |
| episode 内部数据（`command_id`）与 L3 导出（`sources.py`） | 是（`{seed}:…` 前缀；`episode_id = str(seed)`） | 不写入 eval-v3 行回执（构造值实测）。只有单独对 eval 种子运行 L3 导出时才写出 |
| Meterless / Zetaris | 不涉及 | eval-v3 路径不调用 |
| stdout、`.md` | 否 | §5、A.4 实测 |
| `/tmp/eval-v3-b1b3-*` | 是（临时） | 进程结束时删除 |

公开仓库的影响与 §9.3 相同。行回执与 `b4-dev.json` 一旦提交就公开种子值；缓存文件、ledger 和请求本身不含种子值，但都是种子的确定性函数。

### 10.6 需所有者裁决（本节新增或更新）

1. **穷举可行性**（保留 §9.3 的估算）：代码公开，请求内容、缓存 SHA 与 ledger SHA 又都是种子的确定性函数，在提交缓存或 ledger 之后、种子按 A06 §1.3 公开之前，理论上可以穷举反推种子。候选约 2.1×10⁹，本机每个 episode 约 1.2 s，单核约 2.6×10⁹ 核秒，可以并行分摊。没有实际尝试。是否在全部行运行完之前提交缓存或 ledger，需要裁决。
2. 回执与 `b4-dev.json` 中种子值的提交时机，以及旁路文件是否保留（§8.1 第 1、2 项不变）。
3. 失败路径错误信息中的种子值（M-7 不变，R11 未涉及）。
4. `context.text` 的模板选择携带 `seed % k`（§8.1 第 9 项不变）。

### 10.7 冻结前事项状态更新

| 项 | R11 合并树上的状态 |
|---|---|
| M-1 / X1 守卫与缓存 | 未变（草案仍失败） |
| M-2 tag 名 | 未变 |
| M-3 / X2 计数持久化 | 未变（草案仍失败） |
| M-4 截止 / incomplete | 未变 |
| M-5 #27/#28 冲突 | #27 已合并进 main；#28 与 main 冲突两处，内容同前，仍待解决；`final_v3` 仍不传 `format_mode`，`b4.json` 仍不含 `llm_request_spec`/`served_models` |
| M-6 去掉 `episode_id` | R11 已实现于生成器视图（§10.2） |
| M-7 错误信息中的种子 | 未变 |
| M-8 `command_id` | R11 已改写；本报告的检验中未再出现（§10.2） |

### 10.8 §2.2 四个守卫绕过点：触发方式、代码位置、修复后应满足的条件

行号以 #28 head `52bdd47` 为准；R11 合并树中 `final_v3.py` 与 `scripts/gen_eval_v3_seeds.py` 未改动，行号相同。四点都已在临时仓库实测放行（附录 B.1 中对应的测试名列在每点开头）。"修复后应满足的条件"是可检验的实现条件，不是预注册条文措辞。

**B-1 `--skip-worktree` / `--assume-unchanged` 隐藏工作区修改**（`test_guard_bypass_skip_worktree`；生成器侧 `test_gen_clean_check_ignores_gitignored_and_skip_worktree`）
- 触发：`git update-index --skip-worktree src/<file>`（或 `--assume-unchanged`），然后在工作区修改该文件，不提交。`git status --porcelain` 不再列出这个文件，`git diff <tag> HEAD` 只比较已提交的树，所以两项检查都通过，而运行时 Python 导入的是修改过的源码。被 `.gitignore` 或 `.git/info/exclude` 忽略的未跟踪文件同样不出现在 status 中（因为没有加 `--ignored`）。
- 代码：`src/rra/eval/final_v3.py:127`（`status --porcelain --untracked-files=all`）、`:128`（`diff --name-only <tag> HEAD`，只比较提交）、`:131-135`；生成器 `scripts/gen_eval_v3_seeds.py:32,37-38`。
- 修复后应满足：(a) 工作区中所有已跟踪文件的内容都与 HEAD 一致，不受 index 标志影响。例如 `git ls-files -v` 中不存在 `S`/小写标志的条目，或者直接把工作区文件与 `git ls-tree -r HEAD` 的 blob 逐一比对；(b) 允许列表之外不存在任何未跟踪文件，被忽略的也算在内（`status --ignored` 或 `ls-files --others`，不加 `--exclude-standard`）；(c) 生成器的干净检查满足同样的 (a)(b)。检验：对 `src/` 下一个文件设置 skip-worktree 并修改后，守卫与生成器都拒绝；在 `src/` 下放一个被 `.git/info/exclude` 忽略的文件后，两者都拒绝。

**B-2 `GIT_DIR` / `GIT_WORK_TREE` 等环境变量把 git 指向别的仓库**（`test_guard_bypass_git_dir_env`）
- 触发：在运行 `rra eval-v3` 的环境中设置 `GIT_DIR=<另一个仓库>/.git` 和 `GIT_WORK_TREE=<另一个仓库>`，另一个仓库是只含 tag 加种子提交的干净克隆。守卫的全部 git 调用（status、diff、rev-parse）都落到另一个仓库上，而运行时导入的仍是 `ROOT` 下的源码。`GIT_INDEX_FILE`、`GIT_OBJECT_DIRECTORY`、`GIT_CONFIG_*` 等其他 `GIT_*` 变量也会影响结果（未逐一实测）。
- 代码：`src/rra/eval/final_v3.py:40-42`（`_git` 用 `subprocess.run`，未传 `env`，继承父进程环境）；生成器 `scripts/gen_eval_v3_seeds.py:17-21` 同理。
- 修复后应满足：(a) 守卫与生成器调用 git 时，使用移除了全部 `GIT_*` 变量的环境（或显式设定 `GIT_DIR=<ROOT>/.git`、`GIT_WORK_TREE=<ROOT>`）；(b) `git rev-parse --show-toplevel` 的结果等于 `ROOT`（运行时导入源码的仓库根，`final_v3.py:18`）。检验：设置 `GIT_DIR`/`GIT_WORK_TREE` 指向一个干净克隆、`ROOT` 中 `src/` 已改时，守卫拒绝。

**B-3 tag 名不固定，可以另建 tag**（`test_guard_bypass_retag`；生成器侧 `test_gen_accepts_any_tag_name`）
- 触发：在 `impl-freeze-v3` 之后修改 `src/` 并提交，在新提交上建 `other-tag`；种子文件的 `freeze_tag` 写 `other-tag`、`freeze_commit` 写新提交，运行时传 `--freeze-tag other-tag`。守卫只核对"种子文件中的 tag 名 = 参数"以及"`freeze_commit` = 该 tag 指向的提交"，两者都满足。另一种方式是用 `git tag -f impl-freeze-v3` 移动 tag 后重新生成种子文件。
- 代码：`src/rra/eval/final_v3.py:421`（`--freeze-tag` 自由参数）、`:124-125`、`:128`、`:167-174`；生成器 `scripts/gen_eval_v3_seeds.py:27-36`、`:67`。
- 修复后应满足：(a) 守卫与生成器只接受 `impl-freeze-v3`（常量，或拒绝其他值）；(b) 该 tag 是注释 tag 或带签名，并且其目标提交与某个已公开记录的值一致（例如回执或文档中登记的 X 的 sha）。只有 (a) 不能防止 `tag -f` 移动 tag。检验：传其他 tag 名时，守卫与生成器都拒绝；把 `impl-freeze-v3` 移到另一个提交后，守卫按 (b) 拒绝。

**B-4 HEAD 不是 tag 的后代，种子提交的父提交不是 tag**（`test_guard_head_not_descendant_of_tag`）
- 触发：用 `git commit-tree <tag 的树>` 造一个与 tag 树相同、但没有父子关系的提交，在其上提交种子文件。`git diff <tag> HEAD` 只比较树，结果只有种子文件，守卫放行；A06 §1.3 要求"父提交为 freeze-tag commit"，这里实际不满足。同理，种子文件与其他改动分在多个提交里、但最终树差异落在允许列表内时，守卫也放行；它不检查"种子文件单独提交"。
- 代码：`src/rra/eval/final_v3.py:128`（树差异）、`:133-135`；`tests/test_holdout.py:26-37` 只检查"引入种子文件的提交只改该文件"，不检查父提交。
- 修复后应满足：(a) `git merge-base --is-ancestor <tag> HEAD` 为真；(b) 在 `<tag>..HEAD` 中，引入 `config/eval_seeds_v3.json` 的提交恰有一个父提交，且父提交等于 `<tag>^{commit}`，该提交只改这一个文件；(c) 之后的提交（Z）只在允许列表内（与 X1 的新规则合并）。检验：orphan 提交加种子文件时拒绝；种子文件与其他文件同一提交时拒绝；种子提交的父提交不是 tag 时拒绝。

另外两项虽不属于"四个绕过点"，但影响同一个保护目标（`test_role_dev_reads_any_file_without_guard`、`test_main_role_dev_accepts_eval_seed_path_and_cap_override`）：
- `--role dev` 可读取任意种子文件（包括 `config/eval_seeds_v3.json`），并且不经过守卫（`final_v3.py:138-148,438-444`）。修复后应满足：路径等于 `config/eval_seeds_v3.json`、或文件中 `role == "eval_v3"`、或 `schema_version == "rra.eval-seeds.v3"` 时，dev 角色拒绝。
- eval 角色下 `--max-live-calls` 可以调高（`final_v3.py:428,432-433`）。修复后应满足：eval 角色下该值不得大于 2500（或者 eval 角色不接受该参数）。

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

### B.4 `test_t9b_x1x2_drafts.py`（§9 拟定行为；依赖 B.1 中的辅助函数）

运行结果：#28 head `7 failed, 9 passed in 21.50s`；合并树 `8 failed, 8 passed in 22.72s`（多出的失败为 `test_request_has_no_seed_strings`）。失败原因（head）：`working tree must be clean` ×3、`outside the eval allowlist` ×1、ledger 不存在 ×2、`DID NOT RAISE LiveBudgetExceeded` ×1。

```python
"""Drafts for the coordinator's proposed X1/X2 fixes and the seed-free request view.
They state the proposed behaviour; on the current code they are expected to fail.
Assumed interfaces (not in the code yet): `final_v3.LIVE_LEDGER_PATH` (Path, patched to
tmp here); ledger lines hold only a 64-hex request SHA-256."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from rra.eval import b4_dev, final_v3
from test_t9b_scratch import FAKE, TAG, FakeLive, body, commit_seed_file, git, init_repo


def _guard(root: Path, path: Path):
    return final_v3.load_seed_file(path, "eval_v3", freeze_tag=TAG, root=root)


@pytest.fixture
def frozen(tmp_path):
    init_repo(tmp_path)
    cache = tmp_path / "artifacts/llm_cache"
    cache.mkdir(parents=True)
    (cache / "existing.json").write_text("{}\n")
    git(tmp_path, "add", "-A"); git(tmp_path, "commit", "-qm", "dev cache")
    git(tmp_path, "tag", TAG)
    return tmp_path, commit_seed_file(tmp_path)


# ---- X1: allowlist covers seed file, artifacts/eval_v3/**, new files under artifacts/llm_cache/** ----

@pytest.mark.parametrize("rel", ["artifacts/llm_cache/new.json", "artifacts/eval_v3/b4.json",
                                 "artifacts/eval_v3/live_ledger.jsonl"])
def test_x1_untracked_allowed_paths_pass(frozen, rel):
    root, path = frozen
    p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("{}\n")
    assert _guard(root, path)[0] == FAKE


def test_x1_committed_new_cache_file_passes(frozen):
    root, path = frozen
    (root / "artifacts/llm_cache/new.json").write_text("{}\n")
    git(root, "add", "-A"); git(root, "commit", "-qm", "cache")
    assert _guard(root, path)[0] == FAKE


@pytest.mark.parametrize("committed", [False, True])
@pytest.mark.parametrize("change", ["modify", "delete"])
def test_x1_existing_cache_file_change_rejected(frozen, change, committed):
    root, path = frozen
    target = root / "artifacts/llm_cache/existing.json"
    target.write_text('{"x": 1}\n') if change == "modify" else target.unlink()
    if committed:
        git(root, "add", "-A"); git(root, "commit", "-qm", change)
    with pytest.raises(ValueError):
        _guard(root, path)


@pytest.mark.parametrize("rel", ["src/new.py", "tests/new_test.py", "artifacts/llm_cache_x/a.json"])
def test_x1_untracked_outside_allowlist_rejected(frozen, rel):
    root, path = frozen
    p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("x\n")
    with pytest.raises(ValueError):
        _guard(root, path)


def test_x1_uncommitted_src_edit_rejected(frozen):
    root, path = frozen
    (root / "src/mod.py").write_text("x = 2\n")
    with pytest.raises(ValueError):
        _guard(root, path)


# ---- X2: ledger appended before each live call; resume counts distinct ledger SHAs ----

@pytest.fixture
def ledger(monkeypatch, tmp_path):
    FakeLive.script, FakeLive.sent = [], []
    monkeypatch.setattr(b4_dev, "NvidiaNimProvider", FakeLive)
    monkeypatch.setattr(b4_dev.time, "sleep", lambda s: None)
    path = tmp_path / "artifacts/eval_v3/live_ledger.jsonl"
    monkeypatch.setattr(final_v3, "LIVE_LEDGER_PATH", path, raising=False)
    return path, tmp_path / "cache"


def _shas(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def test_x2_ledger_written_before_401(ledger):
    path, cache = ledger
    with final_v3._LiveBudgetScope(10):
        rt = b4_dev._ReadThroughProvider(cache)
        FakeLive.script = [401]
        with pytest.raises(SystemExit):
            rt.complete(body(1))
    assert path.is_file() and len(_shas(path)) == 1


def test_x2_ledger_holds_only_hex_sha(ledger):
    path, cache = ledger
    with final_v3._LiveBudgetScope(10):
        rt = b4_dev._ReadThroughProvider(cache)
        rt.complete(body(1)); rt.complete(body(2))
    lines = _shas(path)
    assert len(set(lines)) == 2 and all(re.fullmatch(r"(\{\"sha256\":\")?[0-9a-f]{64}(\"\})?", s) for s in lines)


def test_x2_resume_counts_ledger_after_crash(ledger, monkeypatch, tmp_path):
    path, cache = ledger
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{i:064x}\n" for i in range(2499)))
    with final_v3._LiveBudgetScope(2500, final_v3._prior_distinct_live_requests(tmp_path / "any_dir")) as budget:
        rt = b4_dev._ReadThroughProvider(cache)
        rt.complete(body(1))
        with pytest.raises(final_v3.LiveBudgetExceeded):
            rt.complete(body(2))
    assert budget.distinct_total() == 2500


# ---- seed-free request view (owner ruling 2026-10-24 and coordinator note on command_id) ----

def test_request_has_no_seed_strings():
    """Run seed 3 / 21 under all variants; no user-content string equals str(seed) or starts with "{seed}:"."""
    import subprocess, sys
    script = Path(__file__).with_name("seed_strings_in_request.py")
    out = subprocess.run([sys.executable, str(script), "3", "21"], cwd=final_v3.ROOT,
                         capture_output=True, text=True, check=True).stdout
    assert json.loads(out)["seed_string_paths"] == {}
```

### B.5 `seed_strings_in_request.py`

```python
"""For given dev seeds, run B4_STRICT under every text variant with a recording provider and
report which user-content key paths hold a string equal to str(seed) or starting with f"{seed}:"."""
import json, sys
from rra.eval.b4_dev import _realization
from rra.eval.context_v3 import VARIANTS, freeze_episode_contexts
from rra.eval.framework import v3_world_config
from rra.evidence import run_episode
from rra.llm.adapter import HypothesisProposer
from rra.llm.providers import finalize_payload, request_sha256

dev = json.load(open("config/dev_seeds.json"))["seeds"]
seeds = [int(x) for x in sys.argv[1:]]
hits, requests = {}, {}
def walk(v, seed, path):
    if isinstance(v, dict):
        for k, x in v.items(): walk(x, seed, f"{path}.{k}")
    elif isinstance(v, list):
        for x in v: walk(x, seed, path + "[]")
    elif isinstance(v, str) and (v == str(seed) or v.startswith(f"{seed}:")):
        hits[path] = hits.get(path, 0) + 1
for seed in seeds:
    real = _realization(dev.index(seed), seed)
    ctx = freeze_episode_contexts(str(seed), seed, real.fault_family or real.structure)
    class P:
        last_http_status = None
        def complete(self, body):
            payload = finalize_payload(body, {})
            requests[request_sha256(payload)] = seed
            for m in payload["messages"]:
                try: walk(json.loads(m["content"]), seed, "user")
                except (json.JSONDecodeError, TypeError): pass
            return {"choices": [{"message": {"content": "{\"items\": []}"}}]}
    for v in VARIANTS:
        run_episode(v3_world_config("nominal"), seed, True, terminal_monitoring="corrected",
                    realization=real, text_context=ctx[v].text, system2_enabled=True,
                    s2_variant="B4_STRICT", proposer=HypothesisProposer(P()))
print(json.dumps({"seeds": seeds, "distinct_requests": len(requests), "seed_string_paths": hits}, indent=1))
```

### B.6 `test_t9b_x1x2_drafts.py`（§10 修订版，只改最后一个用例为位置检查）

R11 合并树上运行：`7 failed, 9 passed`（7 个为 X1/X2 拟定行为）；修订用例在 #28 head 与 R11 合并树上都是 `1 passed`。

```python
"""Drafts for the coordinator's proposed X1/X2 fixes and the seed-free request view.
They state the proposed behaviour; on the current code they are expected to fail.
Assumed interfaces (not in the code yet): `final_v3.LIVE_LEDGER_PATH` (Path, patched to
tmp here); ledger lines hold only a 64-hex request SHA-256."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from rra.eval import b4_dev, final_v3
from test_t9b_scratch import FAKE, TAG, FakeLive, body, commit_seed_file, git, init_repo


def _guard(root: Path, path: Path):
    return final_v3.load_seed_file(path, "eval_v3", freeze_tag=TAG, root=root)


@pytest.fixture
def frozen(tmp_path):
    init_repo(tmp_path)
    cache = tmp_path / "artifacts/llm_cache"
    cache.mkdir(parents=True)
    (cache / "existing.json").write_text("{}\n")
    git(tmp_path, "add", "-A"); git(tmp_path, "commit", "-qm", "dev cache")
    git(tmp_path, "tag", TAG)
    return tmp_path, commit_seed_file(tmp_path)


# ---- X1: allowlist covers seed file, artifacts/eval_v3/**, new files under artifacts/llm_cache/** ----

@pytest.mark.parametrize("rel", ["artifacts/llm_cache/new.json", "artifacts/eval_v3/b4.json",
                                 "artifacts/eval_v3/live_ledger.jsonl"])
def test_x1_untracked_allowed_paths_pass(frozen, rel):
    root, path = frozen
    p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("{}\n")
    assert _guard(root, path)[0] == FAKE


def test_x1_committed_new_cache_file_passes(frozen):
    root, path = frozen
    (root / "artifacts/llm_cache/new.json").write_text("{}\n")
    git(root, "add", "-A"); git(root, "commit", "-qm", "cache")
    assert _guard(root, path)[0] == FAKE


@pytest.mark.parametrize("committed", [False, True])
@pytest.mark.parametrize("change", ["modify", "delete"])
def test_x1_existing_cache_file_change_rejected(frozen, change, committed):
    root, path = frozen
    target = root / "artifacts/llm_cache/existing.json"
    target.write_text('{"x": 1}\n') if change == "modify" else target.unlink()
    if committed:
        git(root, "add", "-A"); git(root, "commit", "-qm", change)
    with pytest.raises(ValueError):
        _guard(root, path)


@pytest.mark.parametrize("rel", ["src/new.py", "tests/new_test.py", "artifacts/llm_cache_x/a.json"])
def test_x1_untracked_outside_allowlist_rejected(frozen, rel):
    root, path = frozen
    p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("x\n")
    with pytest.raises(ValueError):
        _guard(root, path)


def test_x1_uncommitted_src_edit_rejected(frozen):
    root, path = frozen
    (root / "src/mod.py").write_text("x = 2\n")
    with pytest.raises(ValueError):
        _guard(root, path)


# ---- X2: ledger appended before each live call; resume counts distinct ledger SHAs ----

@pytest.fixture
def ledger(monkeypatch, tmp_path):
    FakeLive.script, FakeLive.sent = [], []
    monkeypatch.setattr(b4_dev, "NvidiaNimProvider", FakeLive)
    monkeypatch.setattr(b4_dev.time, "sleep", lambda s: None)
    path = tmp_path / "artifacts/eval_v3/live_ledger.jsonl"
    monkeypatch.setattr(final_v3, "LIVE_LEDGER_PATH", path, raising=False)
    return path, tmp_path / "cache"


def _shas(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def test_x2_ledger_written_before_401(ledger):
    path, cache = ledger
    with final_v3._LiveBudgetScope(10):
        rt = b4_dev._ReadThroughProvider(cache)
        FakeLive.script = [401]
        with pytest.raises(SystemExit):
            rt.complete(body(1))
    assert path.is_file() and len(_shas(path)) == 1


def test_x2_ledger_holds_only_hex_sha(ledger):
    path, cache = ledger
    with final_v3._LiveBudgetScope(10):
        rt = b4_dev._ReadThroughProvider(cache)
        rt.complete(body(1)); rt.complete(body(2))
    lines = _shas(path)
    assert len(set(lines)) == 2 and all(re.fullmatch(r"(\{\"sha256\":\")?[0-9a-f]{64}(\"\})?", s) for s in lines)


def test_x2_resume_counts_ledger_after_crash(ledger, monkeypatch, tmp_path):
    path, cache = ledger
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{i:064x}\n" for i in range(2499)))
    with final_v3._LiveBudgetScope(2500, final_v3._prior_distinct_live_requests(tmp_path / "any_dir")) as budget:
        rt = b4_dev._ReadThroughProvider(cache)
        rt.complete(body(1))
        with pytest.raises(final_v3.LiveBudgetExceeded):
            rt.complete(body(2))
    assert budget.distinct_total() == 2500


# ---- seed-free request view (owner ruling 2026-10-24 and coordinator note on command_id) ----

def test_request_has_no_seed_strings():
    """Run seed 3 / 21 under all variants: no user-content value equals str(seed) or starts with
    "{seed}:", except command_id, which must be exactly "{target_id}:{step}" of its own row."""
    import subprocess, sys
    script = Path(__file__).with_name("seed_strings_in_request.py")
    out = subprocess.run([sys.executable, str(script), "3", "21"], cwd=final_v3.ROOT,
                         capture_output=True, text=True, check=True).stdout
    result = json.loads(out)
    # command_id "{target_id}:{step}" can start with "{seed}:" when target_id == seed; judge it by position
    paths = {k: v for k, v in result["seed_string_paths"].items() if not k.endswith("command_id")}
    assert paths == {}
    assert set(result["command_id_formats"]) <= {"two_part_matches_row"}
```

### B.7 `seed_strings_in_request.py`（§10 修订版，增加 `command_id` 位置检查）

```python
"""For given dev seeds, run B4_STRICT under every text variant with a recording provider and
report which user-content key paths hold a string equal to str(seed) or starting with f"{seed}:"."""
import json, sys
from rra.eval.b4_dev import _realization
from rra.eval.context_v3 import VARIANTS, freeze_episode_contexts
from rra.eval.framework import v3_world_config
from rra.evidence import run_episode
from rra.llm.adapter import HypothesisProposer
from rra.llm.providers import finalize_payload, request_sha256

dev = json.load(open("config/dev_seeds.json"))["seeds"]
seeds = [int(x) for x in sys.argv[1:]]
hits, requests, formats = {}, {}, {}
def walk(v, seed, path):
    if isinstance(v, dict):
        for k, x in v.items(): walk(x, seed, f"{path}.{k}")
    elif isinstance(v, list):
        for x in v: walk(x, seed, path + "[]")
    elif isinstance(v, str) and (v == str(seed) or v.startswith(f"{seed}:")):
        hits[path] = hits.get(path, 0) + 1
def check_feedback(user, seed):
    # positional check: command_id must be exactly "{target_id}:{step}" of its own row
    for row in user.get("evidence_packet", {}).get("command_feedback", []):
        cid = str(row.get("command_id"))
        key = "two_part_matches_row" if cid == f"{row['target_id']}:{row['step']}" else "other:" + str(cid.count(":") + 1) + "_parts"
        formats[key] = formats.get(key, 0) + 1
for seed in seeds:
    real = _realization(dev.index(seed), seed)
    ctx = freeze_episode_contexts(str(seed), seed, real.fault_family or real.structure)
    class P:
        last_http_status = None
        def complete(self, body):
            payload = finalize_payload(body, {})
            requests[request_sha256(payload)] = seed
            for m in payload["messages"]:
                try:
                    u = json.loads(m["content"]); walk(u, seed, "user")
                    if isinstance(u, dict): check_feedback(u, seed)
                except (json.JSONDecodeError, TypeError): pass
            return {"choices": [{"message": {"content": "{\"items\": []}"}}]}
    for v in VARIANTS:
        run_episode(v3_world_config("nominal"), seed, True, terminal_monitoring="corrected",
                    realization=real, text_context=ctx[v].text, system2_enabled=True,
                    s2_variant="B4_STRICT", proposer=HypothesisProposer(P()))
print(json.dumps({"seeds": seeds, "distinct_requests": len(requests), "seed_string_paths": hits, "command_id_formats": formats}, indent=1))
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
