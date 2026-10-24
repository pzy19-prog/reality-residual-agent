# RRA 状态（控制会话维护）— 更新 2026-10-24 17:45（PR #24、#25、#27 已合并 → origin/main = edd54c0）
- origin/main = 9fe1730（PR #22 CI→3.12、PR #20 L5b 均已由用户合并；之前 54f5006 = PR #21 A04）；主库本地 main 仍为 d54faa7，未 pull
- 时间：提交目标 10-27 20:00 北京时间；官方截止 10-28 07:45。D4（10-25）= 冻结 → 隔离生成 eval-v3 seed → 各 baseline 跑一次
- $PY = /home/mxfclaw/reality-residual-agent-worktrees/l5a-hygiene/.venv/bin/python（3.12.3 / numpy 2.5.4；→ /usr/bin/python3.12）。新卡改为每个 worktree 自建 `.venv`（/usr/bin/python3.12 -m venv）
  - editable 安装指向 l5a-hygiene/src；复核时设 `PYTHONPATH=<worktree>/src` 并核对 `rra.__file__`
- 控制会话护栏：PreToolUse hook `.claude/hooks/deny_guard.py`（sha256 2551c763…45a6）拦截 git push、gh pr merge/create、命令位置的 pass；Bash 文本里出现 "gh pr merge" 字样也会被拦，改文件用 Edit/Write
- 派发：`codex exec -C ~/reality-residual-agent --add-dir ~/reality-residual-agent/.git --add-dir ~/reality-residual-agent-worktrees -c sandbox_workspace_write.network_access=true --approve-for-me -o <scratch>/x_last.md "<prompt>" > <scratch>/x.log 2>&1`（加 .git 写权限已实测可行）
- 审查必须看 `gh pr checks`（PR19 审查漏了 CI 红）

## 进行中（2026-10-24 派发，日志在 scratchpad cb54500b…/）
- **FRZ-1 v1 → nogo**（`_reports/REPORT_D4_FRZ1_nogo.md` sha 541327e9…6b92）：fast layer 在 S2 返回 PAUSE 的同一步就写入 `escalated`（终态）并设 safe_stop，所以 S2 实际只有一次机会（通常在 t≈0.2、n=3–4 时）。Luna 停下是对的
- **FRZ-1 v2** `_cards/FRZ-1_v2.md`（sha256 19948b493f38d5e7f8eaa9632e8ad90365de2c6dc02ad6ca287d50ef5fe07b02）已派发。F1 改为"目标级重观测保持"：S2 返回 PAUSE 时先不写 escalated，safe_stop 照设（整线停发令，保守）；每 0.5 s 复查一次，授权后、且保持集为空、且未锁存时才清 safe_stop；窗口耗尽、锁存或 episode 结束时写入 escalated（reason 带 `;REOBSERVE_EXHAUSTED`）。模式照搬已有的 episode 级 outcome_escalation 重试（:430-446）
- **A05**：v1 → PR #23（head a7dfa14，CI 全绿，报告 `_reports/REPORT_D4_A05.md` sha 34e672fd…bebb）。§1 与 FRZ-1 v2 语义不一致 → **A05 v2** `_cards/A05_v2.md`（sha256 87b79a6d138a533fcbadebb5f9a782c7c07ecdbe3cfbea98c2282353f524a826）已派发：在 PR #23 上追加提交，§1 改为"Re-observation hold"、标题改名、§5 第一条停止条件改为两条，§2–§4 不变。两个版本都跑完后一起审 PR #23
- **FRZ-1** `_cards/FRZ-1_v1.md`（sha256 8304b63803f709618c0e89adb2cc104b6e3df2ce333190081a9b407b08fd161a）→ 分支 feat/frz1-b3core，报告 `_reports/REPORT_D4_FRZ1.md`。内容：F1 PAUSE 后每 0.5 s 主动重观测（实现缺陷修复，T3 C3）；F2 锁存 fail-closed（PR19 N4）；F3 回放缓存未命中即中止；F4 无 proposer 时报错；F5 拟合网格平局取最小值；F6 runtime_versions 记录 machine/cpu/blas；F7 git sha 不进哈希（PR19 N2、PR20_R1 N2）；F8 重生成 b3-dev 和 meterless 的 B3 部分（b4-dev 和 meterless B4 部分标为 stale，留给 FRZ-2）；F9 测算新代码下的 B4 调用量和 eval-v3 规模（为 NIM 预算服务）
  - 审查重点：V2 B1 130/130 不变；V4 s2_authorized unsafe（重观测可能放出更多早期授权）；F1 的"终态"判断
- **A05** `_cards/A05_v1.md`（sha256 efbc12b78deab1c8563b4b79ebef08a54c0f842870e20c92e0f1fe469bd741e6）→ 分支 docs/prereg-addendum-05，报告 `_reports/REPORT_D4_A05.md`。登记：重观测节奏、网格平局规则、回放未命中即中止（修订 A04 §3 rule 1）、无 proposer 即中止、llm_calls 口径、B4 请求浮点保留 6 位小数（由 FRZ-2 实现）、确定性范围（只保证同一运行机器上逐位一致；跨机器只比较决策和 metrics）

- **FRZ-1 v2 → PR #24**（head 7e2c4a7，CI 全绿，198/4）：审查 **BLOCK** → `_reviews/PR24.md`（文件 sha 8cbefa69…cd905，body 3a71f9f9…d8ad）。X1：保持在进入后的下一步就被结束（两处条件在 `s2_action=None` 时也会触发），F1 实际无效（进入 195、复查 33、授权 0、metrics 与基线相同）。其余 F2–F7 PASS；Meterless manifest 排除字段一项按卡停下，接受
- **FRZ-1-R1** `_cards/FRZ-1-R1_v1.md`（sha256 69a42f6b4cc3bcd3f8390e0a76e923cbd149c07ff149294f4a96e92ebe9c6259）已派发：只在 S2 本步实际运行过时才判断结束条件；记录 end_reasons；连续升级回归测试 + 复查间隔不变量；重新生成 b3-dev 和 meterless B3 部分；重测 F9

- **FRZ-1-R1 → PR #24 head cb77107**：复审 **PASS** → `_reviews/PR24_R1.md`（文件 sha c7eb947d…6902，body 7d51a977…ab13）。保持机制工作正常（183 次进入、82 次复查、1 次授权），但对 dev 结果几乎没有影响（wrong 589→588、miss 96→97、auth 209→210）。**裁决：冻结前不再改 B3 机制**
- PR #23（A05）已由用户合并 → origin/main = 520b7cf
- ~~FRZ-2A v1~~（8c4ef5f5…a34c，未派发，作废：known_config 字段数写错，且未吸收 T4/T6）
- **FRZ-2A v2** `_cards/FRZ-2A_v2.md`（sha256 f061addb5541e12825a43e9d3fe5e3261da9eaada904b9c33a23558b1a4d56d6；含 G11 decisions.md 记 R1–R5），**等 PR #24 合并后派发**（不需要密钥）：G0 保持逻辑两处 A05 符合性修复（已终态目标不再进入保持；0.5 s 到期判定加 1e-9 容差，A05 §5 第 1 条列为缺陷）→ 重生成 b3-dev；G1 canonical 证据包（known_config 5 字段）+ 等价测试；G2 6 位小数；G3 提示词 v2 + 三种 format_mode；G4 llm_request_spec；G5 调用数分开；G6 补测试并采用 T6 附录 B.1 草案；G7 探针脚本（只 dry-run）

## 进行中（10-24 午后派发，三路并行，日志在 scratchpad cb54500b…/ frz2a.log、a06.log、evalpath.log）
- 所有者已定：eval-v3 = 100 个 seed；NIM 预算已批（探针 30 + dev 子集约 450–550 + eval-v3 上限 1,600 个不同请求）
- **FRZ-2A v2**（f061addb…d56d6）→ feat/frz2-b4req，报告 REPORT_D4_FRZ2A.md
- **FRZ-2A v2 → no-go**（`_reports/REPORT_D4_FRZ2A_nogo.md` sha c2323a93…4945）：G1 等价测试差 known_config。v2 的 Q2 是控制会话写错（读了主库未 pull 的本地 checkout；origin/main L3 导出 known_config 为 7 字段）。G0 已完成（本地 a63523d 代码、2eccd65 artifact，未推送）：metrics 全部不变，88/5 不受影响；hold_entries 183→177，target_switch 16→11，episode_end 2→1，reobservations 82→83，system2_calls 2009→2010
- **FRZ-2A v3** `_cards/FRZ-2A_v3.md`（sha256 833322b11d798a056305af20a2fb28a4d14a564b19da806ab61f0b2ef8373f34）已派发（日志 frz2a3.log）：L3 不动，B4 包 known_config 投影为 C1 5 字段，等价测试按投影比较；吸收 R6–R9（s2_summary 只含 R6 的项；served_models 进 receipt；decisions.md 记 R1–R9）；PR 正文写 T4 条目对应
- 教训：核对仓库前提一律用 `git show origin/main:<path>`，主库本地 main 是 d54faa7（未 pull）
- **A06 v1** `_cards/A06_v1.md`（sha256 07fbd646382ef6141a02c8699a2b5c8b6fd81c5c84661574d8d1f3789413b7f0）→ docs/prereg-addendum-06：eval-v3 100 seed（CSPRNG，[10000, 2^31-1)，冻结 tag 之后单独提交）、index%19 分配、运行顺序 X→Y→Z、B2 T1.15/R2.15、格式模式选择规则（探针 10 个请求、有效数最多者，平局 json_object>json_schema>nvext）、eval B4 上限 1,600、10-27 06:00 UTC 未完成则 B4 报不完整、冻结前实现决定披露、新增停止条件
- **EVAL-PATH v1** `_cards/EVAL-PATH_v1.md`（sha256 40698758eb17bc4f8450f8b9cd7d9728aaabeae102437ee65559ae0ae60fe351）→ feat/eval-v3-path：`scripts/gen_eval_v3_seeds.py`、`rra eval-v3 {b1b3,b2,b1-legacy,b4}`、dev 等价验证、test_holdout 前后兼容、B4 调用量估计
- 合并顺序建议：FRZ-2A → EVAL-PATH（与 FRZ-2A 冲突时 merge main）→ A06 → FRZ-2B（探针 + 选格式 + dev 子集 live）→ 冻结 tag → 生成 seed → eval 运行

- PR #25 = A06（docs/prereg-addendum-06 @ 83440e9）：审查 `_reviews/PR25.md`（文件 sha 57291def…f64e，body f62981ca…5b5e）对卡 PASS、**暂不合并**；等所有者定上限后出 A06-R1 追加提交：登记 R6–R9（云端转来的所有者裁决：R6 保留 passing/current_time/horizon；R7 包范围=本目标观测与在场、全 episode 反馈、known_config 5 字段；R8 二维平局字典序；R9 模板 SHA 定义 + 记录服务端模型名）、s2_summary↔R6 对应、canonical 行带 episode_id/seq/step 记账键、反馈只含决策前、eval B4 上限（待所有者选 A 2,500 / B 1,600）
- 冻结 tag 名：impl-freeze-v3（云端与控制会话建议，待所有者确认）
- 云端将开 T9（只读审查 EVAL-PATH 与 A06）
- **所有者 10-24 已定**：eval B4 上限 2,500；冻结 tag = impl-freeze-v3；协调频道 = 公开仓库 issue **#26**（control ↔ cloud coordination；不写密钥、seed 值、eval 结果；评论以 [local → cloud] / [cloud → local] 开头）
- **14:04 Codex 额度用尽（重置约 18:07）**：FRZ-2A v3（session 01a16c66-da6c-7863-a659-26847c86e1f9）实现到一半，未提交改动留在 frz2-b4req（HEAD 仍 2eccd65）；EVAL-PATH（session 01a16c52-225b-7c61-857d-0f8f8d8a490d）在跑 b4 --estimate 时停，未提交改动留在 eval-v3-path。恢复：`codex exec resume <id> "继续执行卡片…"`（同样的 -C/--add-dir 参数）
- **14:20 改由 Grok 4.7 接续两张卡**（`grok -p … -m grok-4.7 --always-approve --sandbox rra-exec --cwd <worktree>`；提示词在 scratchpad grok_frz2a_prompt.txt / grok_evalpath_prompt.txt，日志 grok_frz2a.log / grok_evalpath.log）。`~/.grok/sandbox.toml` 新增 profile `rra-exec`：在 workspace 基础上可写主库 .git 与 _reports，_control 只读，禁止访问 ~/.password-store、~/.gnupg、~/.ssh。EVAL-PATH 附补丁 P-1：`--max-live-calls` 默认值改为 2500
- EVAL-PATH Grok 第一次运行因后台等待超时（600 s）退出（日志 grok_evalpath_run1.log）：它在 /tmp 做了 POSIX 信号量垫片（libsemshim.so，未进仓库）绕过沙箱；已给 rra-exec 加 /dev/shm 可写，并以 `--background-wait-timeout 7200` 重启（提示词 grok_evalpath_prompt2.txt，要求不用垫片重跑验收）。中间结果：B2 dev（T1.15/R2.15）success 232/775、miss 120、unsafe 45、wrong 454、preservation 2/582（只报告）
- **所有者 14:48（经云端）R9 选 (a)**：模板 SHA 也排除 context_text。FRZ-2A 的请求体只有 {evidence_packet, s2_summary}，文本在 packet.context 里，已经被占位符覆盖。A06 已登记，不能改 → 冻结前出 **A07**（小勘误：说明文本在包内、被占位符覆盖，记录 R9(a)），等 FRZ-2A/EVAL-PATH 审完一起收其他勘误；FRZ-2A 审查要求测试：只差 context/包时模板 SHA 相同，差 format_mode 时不同
- **FRZ-2A → PR #27**（head a9fa6c3，基于 5a05f6d，CLEAN；Grok 报告 REPORT_D4_FRZ2A.md）：自报 221 passed/4 skipped；B3 receipt bfda4d10…1132（两次一致 = G0 artifact）；投影后包等价 444/444；全 dev 去重请求 1400；模板 SHA 三种模式不同。**审查 PASS** → `_reviews/PR27.md`（文件 sha 85708523…c6ca，body 488198d4…2f00），**暂缓合并（所有者 15:53 裁决：B4 请求去掉 episode_id）**；复跑：221/4、B3 bfda4d10 两次一致、B1 130/130、metrics 与 5a05f6d 全同、444/444、模板 SHA 对 context 不变、三模式不同
- **所有者 15:37 裁决 (i)**：context 文本放在 packet.context 内，A07 登记。**15:53 裁决**：B4 请求去掉 decision.episode_id 和行级 episode_id（L3 不变）；其余白名单外的键保留，在 A07 中登记；served_models 聚合形式接受。控制会话另发现 command_id = f"{seed}:{target}:{step}"（episode.py:1058）也会泄漏 seed → 裁决在生成器视图中改写为 "{target}:{step}"（所有者可否决）
- **PR #27 R1 复审 PASS**（head 466bec6）→ `_reviews/PR27_R1.md`（文件 sha 7860a81e…6baf，body 436dd1f3…6632），**待用户合并**；云端 T6 第 3 阶段也全部通过
- PR #29 = A07（head b656859，执行者报告 REPORT_D4_A07.md sha 393e3435…9534，CI 通过）。云端 T12（cloud/t12-a07-review @ ea1e8ef）要求合并前修：§5.1 收窄措辞并加"B4 dev 子集不含 case 9"；X-1（未完成时 A04 §6.1 计数）；X-2（持续 5xx/超时与 A04 rule 1 冲突）；X-4（在 R10 处引用 H1:17）；另有 Q-1/Q-2/Q-5/Q-6。控制会话的建议方案已发到 issue（17:15）：X-2 改回符合 A04（重试 5 次 → 缓存 PROVIDER_ERROR 记录；连续 10 个都失败才停）；X-1 报告能从账本和缓存算出的计数。**等所有者经云端裁决 X-1/X-2/X-4 后，出 A07-R1，一次提交**
- **所有者 17:11（云端）/ 17:30（本地）裁决**：采纳 17:15 方案 → R14（失败响应处理符合 A04 rule 1：重试 5 次后写错误记录；连续 10 个停止）、R15（未完成时报告能算出的 A04 §6.1 计数）、R16（结构保留：披露并单独报告 case 9）
- **A07-R1** `_cards/A07-R1_v1.md`（sha256 3fa6204e1a44abbd5e77fcfcad229b3596f661f33ebea4444ea20b6743a85b5b）→ Grok（日志 grok_a07r1.log），在 PR #29 上追加提交
- A07-R1 已完成（PR #29 head f1cef93，报告 REPORT_D4_A07R1.md sha d767511f…1196，CI 通过）；云端 T12 复审：R14–R16 已落实，另提 Q-1/Q-2/N-1–N-6 → **A07-R2** `_cards/A07-R2_v1.md`（sha256 6336d08ce2040c085c0ce5b0a9132efc2d876e19a486c6ff094e23a19ddc4227）已派给 Grok（日志 grok_a07r2.log）
- 审 EVAL-PATH-R1 时要核对 A07-R2 的规定：所有错误记录都计入连续 10 次；按完成顺序计；成功则清零；每个进程从 0 开始；Retry-After 每次最多 60 s；1xx/非 200 的 2xx 算暂时性；正好 2,500 算完成；时间不进哈希；账本写入要加锁（T9b）；云端 T9b 报告的 4 种守卫绕过（清单待云端给出）
- **PR #29（A07）审查 PASS** → `_reviews/PR29.md`（文件 sha d92a0903…35e5，body 6e4b781e…6a30），head 4d3ee79，**待用户合并**（前提是 CI 通过）；云端 T12 三次复审后，A07 文本已没有必修项
- FRZ-2B 卡必须带一项验收：所有 dev B4 请求都来自 diag-d1g.json 中的 seed（T12 P-4）
- **A07-R3** `_cards/A07-R3_v1.md`（sha256 5ea0f335005bf5bcc781ab237a62e9c770cd551678ce728d21ed75ad46a89a13）写好，等 A07-R2 执行者完成后派发：计数器只算本进程的 live 结果；b4_live.json / b4.json / b4_replay_check.json 三个路径；不完整计数的分类顺序与 not_recorded；退避 2/4/8/16 s；超时 90 s；UTC；FRZ-2B 的 dev live 只跑 33 seed 子集
- **FRZ-2B 只跑 33 seed 子集**（避免 LLM 见到 case 9 保留结构，否则 A07 §5.1 不再成立）
- **EVAL-PATH-R1** `_cards/EVAL-PATH-R1_v1.md`（sha256 9ed8b87131b8dba0da845fd7c9f48d92cc82bac8c28318062c093a0ee1231e3f）→ Grok（日志 grok_evr1.log），在 PR #28 上：merge main、守卫与账本、错误记录、a04_counts、截止时刻、format_mode、不打印 seed
- 之后：合并 #29、#28 → FRZ-2B（Luna 或 Grok，需要密钥）→ 冻结 impl-freeze-v3
- **FRZ-2A-R1** `_cards/FRZ-2A-R1_v1.md`（sha256 337eb9cf15d4e4f0346d080c49815e3e39f98676f2c688e41711c6c231e8ce6d）已派给 Grok（日志 grok_frz2ar1.log）：generator_view 去掉 episode_id、改写 command_id；测试要求 9 位 seed 的 payload 中不出现 str(seed)；B3 receipt 和 L3 不变
- **A07 v1** `_cards/A07_v1.md`（sha256 2e88712aa38a5b095b0f321c7e9c9b2af5288d2553e80faeb320bbcb86a56d72）已派给第二个 Grok 会话（日志 grok_a07.log）：A06 勘误、R10–R13、探针定义、live 运行与计数（§4.1 HTTP 状态码分组、§4.2 账本）、未完成处理、产物位置、**结构保留披露**（AND(SPEED_STEP,ACTUATOR_DELAY) = composition index 9，dev seed 9/28/47/66/85/104/123 自 7ea70ce 起一直在开发中使用，违反 P3 §13.4 → case 9 单独报告，不主张组合泛化）
- EVAL-PATH-R1 须实现 A07 §4.1（失败分类与错误记录写入缓存）、§4.2（账本）、§4.6（不打印 seed）、§4.7，外加 PR28 X1/X2，以及 merge main
- ~~A07 待写~~（原计划）：R10 context 在包内、R11 去掉 seed 标识、R12 白名单外的键逐个登记、R13 served_models 聚合；T9a M-2 tag 名、M-4 B4 未完成时的运行与报告方式、S-1–S-10 中属于协议的项；以及 R9(a) 勘误
- PR #28 = EVAL-PATH（head 52bdd47）：**审查 BLOCK** → `_reviews/PR28.md`（文件 sha 01908815…d7d6，body e17028e7…134d）。X1 守卫要求工作区干净且不允许 artifacts/llm_cache → 无法续跑，也无法在 live 后做 replay；X2 live 计数只从 b4.json 读，崩溃后丢失 → 改成追加写的账本。另须 merge main（与 #27 冲突）、eval b4 路径传入 format_mode。EVAL-PATH-R1 卡等 #27 合并和 T9b 结果后再派
- 合并顺序：#27（R1 后）→ #28（merge main 后）→ A07 → FRZ-2B
- **issue #26 自动监听**：scratchpad `watch_issue.sh <state> 60` 在后台运行，每 60 s 查一次，有新的云端评论就打印并退出（触发通知）；处理完后**要重新启动**（状态文件 issue26_seen.txt 记录已见的云端评论数）。已请云端把轮询间隔缩到 5–10 分钟（原来是每小时 :41）
- 审查 Grok 产出时要多查：作者/提交者身份、提交与 PR 正文有无 AI 署名、是否越出卡片范围
- **PR #25 R1 复审 PASS** → `_reviews/PR25_R1.md`（文件 sha c5c1e02d…f7da，body dd216675…dd42），head 11bc637，**已由用户合并** → origin/main = 349d1e6
- **A06-R1** `_cards/A06-R1_v1.md`（sha256 1a453be74309048ee921eac8a852ff982bfc0311101f39d714382b81471688ad）已派发（日志 a06r1.log）：PR #25 追加 R6–R9（§4A）、§4.7 证据包口径、上限 2,500
- 注意：EVAL-PATH v1 的 `--max-live-calls` 默认值是 1600，审查时要求改为 2500

## 云端只读产出（用户安排，分支只读，不合并）
- 10-24：T4 `cloud/t4-frz1-review` 550cdc6（FRZ-1 对照 A05 + 重观测后漏斗，质量高，结论与 PR24_R1 一致并更细）；T5 `cloud/t5-submission-refresh` 937188e（提交说明 v2、DECK_OUTLINE、VIDEO_SCRIPT）；T6 `cloud/t6-prefreeze-check` f1efec9（冻结前清单 C-01…C-16 + 测试草案，第 1 阶段）；T7 `cloud/t7-failure-modes` 0f3a97f（提交说明 v3 + FAILURE_MODES_DRAFT）。四个提交都只加 docs，作者身份正确，无 AI 署名
- **所有者 10-24 对云端的裁决（记录于 T7 草稿 §10 第 18–22 项）**：R1 保持入口取窄读法（只限 ESCALATE 路径）；R2 §1.3 safe_stop 解除维持现状、不改代码，88/5 披露；R3 episode 级 safe_stop 主导 84/775 不在冻结范围内，作为失败模式披露；R4 登记 runner = 本机 i7-10750H / 3.12.3 / 2.5.4 / scipy-openblas 0.3.34；R5 §3.4 本地实现、B4 缓存在登记 runner 上 live 重建
- T6 的冻结前清单 C-01…C-16 用于 FREEZE 审查；T6 第 2 阶段等 §3.4 实现后由云端再跑
- 云端协调会话给本地的任务单（10-24，用户转贴）已对照：§3.4 和 decisions.md 并入 FRZ-2A；不往 PR #24 追加提交（已审 PASS，先合并）；它第 4 步“B3 receipt 仍为 75115f44”在 FRZ-2A G0 后不成立
- **缺口（实测）**：仓库没有 eval-v3 生成与运行路径（s2-b3-dev/s2-b4-dev 写死 dev seed；holdout.py 只做禁止检查）；P3 §18.1、EVAL_PROTOCOL、H1、A01–A05 都没登记 eval-v3 的 seed 数、生成方式、B4 调用上限。需要 A06（冻结前登记）+ EVAL-PATH 卡（可与 FRZ-2A 并行，只碰 cli.py 有冲突）。seed 数待所有者定（eval v2 为 100）
- 冻结时要写 A06（登记披露）：71ce80d 空 fault 窗口 latch、afa2aa6 运行时 base_git_sha、(tau, delay) 二维平局取字典序、R1/R2/R4、window_end 用名义计划且只在到期样本上检查
- FRZ-2B（未出卡）：解锁密钥 → 探针（3 种模式 × 10 次 = 30 次）→ 按登记规则选格式 → dev 子集 live 运行（约 450–550 次）→ 断网回放生成两次 → 重新生成 b4-dev 和 meterless B4 段

## 等待用户
0. **合并 PR #23（A05）**：head cabff0a，审查 PASS → `_reviews/PR23.md`（文件 sha 41ba154a…bc4a，body d4b7ba6b…ad58）；建议在 FRZ-1 结果出来之前合并
1. NIM 调用预算：FRZ-1 的 F9 会给出调用量估计，可以等数字出来再定
2. L7 demo / 视频 / slides 由谁做；T2 草稿 §10 中需要所有者填写的项（Cursor 使用方式、赛道、集成深度等）
3. 云端分支 cloud/t0–t3 由用户安排；是否合入由用户决定（控制会话只读参考）

## 下一批卡
1. **FRZ-2**（FRZ-1 合并、预算定好之后）：A04 §1.2 证据包补全为 C1 全白名单；请求浮点保留 6 位（A05 §3.4）；修 prompt/schema（或 guided JSON）；receipt 记录模型 ID 与请求模板 sha（A04 §5.4）；strict/tiebreak 调用数分开报告（A05 §3.3）；补齐 T1 §2 列出的未覆盖测试（rule 1、4、5 回落、rule 2 与 3 同时出现时的顺序）；NIM 探针 → dev 重跑 → 重生成 b4-dev 和 meterless B4 部分
2. **OPS**：rra-l3-ops 稳定挂载（挂载源 l3-zetaris worktree 已删除；容器 python:3.12-alpine）→ 冻结时重跑 L3 equivalence。注意 codex 沙箱能否访问 docker 尚未实测
3. **FREEZE（D4）**：冻结实现 → 隔离生成 eval-v3 seed → 各 baseline 跑一次 → artifact
4. **收尾卡**：删 l5a-hygiene（先换掉 $PY）、l5b-b4、ci-py312、prereg-a04（在 /tmp/a04-bootstrap 下）、各远端分支（先 ls-remote 和 merge-base 确认）
5. PR19 剩余 N1（b3-dev 嵌入决策）、N3（诊断关联断言）——低优先级

## 已完成记录
- PR #22（CI 3.12）审查 `_reviews/PR22.md`；PR #20 审查 `_reviews/PR20_R1.md`；PR #21 审查 `_reviews/PR21.md`
- dev 运行事实：缓存 386 = 71 可解析 + 310 形态错误 + 5 length；tiebreak proposal 378 = INVALID 309 + PROVIDER_ERROR 5 + 有效 64；TEXT_TIEBREAK 27（有授权的 25）
- 云端只读诊断（2026-10-23，用户安排）：T1 PR20 审查（跨机器 B3 哈希不一致；回放未命中被悄悄回落；证据包缺字段；receipt 没有模型 ID）；T3 失败漏斗（PAUSE 不复查是主要流失点；B3 dev 有 7 个 unsafe，全部来自 fast_layer_command）；T2 提交说明草稿（§10 列出 14 项需所有者处理）；T0 仓库审计

## 环境与历史
- 容器：rra-l3-pg Up；rra-l3-ops Exited(2)
- 交接文档：handoff/RESUME_2026-10-23_MERGE-CLEANUP.md（已大体执行完；新会话以本 STATE 为准）
- 审查脚本 `_reviews/tools/`：rev19_*、rev20_*、r1_dump_decisions.py、r1_cmp_decisions.py、n1_cache_count.py、guard_cases.py
