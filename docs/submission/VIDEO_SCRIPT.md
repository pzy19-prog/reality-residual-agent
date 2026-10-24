# 演示视频分镜脚本（初稿）— Reasoning Architecture 赛道

状态：**DRAFT / 未经所有者审阅 / 未录制**。基线 `main` @ `520b7cfdf13b805c9258ab06c79a658ee62aef8b`。[来源: `git rev-parse origin/main`]

## 0. 约定与边界

- 规则：演示视频 1–4 分钟，须展示主流程、agent 如何解决所选挑战、关键功能、Zetaris 与 Meterless 如何集成（Rule 6.1，新版）。目标约 3 分钟；下表合计 180 秒。[来源: docs/HACKATHON_RULES.md:21]
- P3 对最小演示的要求：同时包含一次成功恢复与一次有依据的拒绝；可见序列为 残差增长/快速层升级 → 文本与结构化证据 → 多个假设 → 至少一个假设被验证器拒绝 → 有依据的假设获得有界授权 → 恢复 → 第二个故障示例（误导性上下文或不安全条件）→ 验证器拒绝恢复且系统保持升级 → 回执显示 证据→假设→验证→授权/处置。[来源: docs/P3_SYSTEM2_DESIGN.md:938-960]
- 所有涉及 eval-v3 结果或 B4 效果之处，旁白一律为"待 eval-v3，尚无结果"。旁白不使用结论性措辞，不引用 System-2 的性能数字，不替所有者决定负结果的措辞。[来源: docs/P3_PREREG_ADDENDUM_04.md:7; docs/P3_PREREG_ADDENDUM_05.md:7]
- 画面中的 seed 仅限 `config/dev_seeds.json`；不展示、不读取 `config/eval_seeds*.json`。[来源: docs/EVAL_PROTOCOL.md:18-19; .cursor/rules/rra.mdc]
- "命令"栏只列仓库文档、CLI 帮助或脚本头部已有的命令。"外部依赖/执行者"栏标明是否需要外部服务或密钥、由谁执行。本草稿作者未执行任何命令，也未访问 Zetaris、Meterless 远端或 NVIDIA。[来源: 任务约束]
- 合并状态：**[main]** / **[FRZ-1 未合并]**。除另行标注外，所有镜头只使用 main 上的功能。录制时若要使用 FRZ-1 分支，须先由所有者裁决合并（见 `DRAFT_SUBMISSION_v2.md` 第 10 节第 15 项）。
- 提醒：`rra s2-b3-dev` 与 `rra s2-b4-dev` 的默认输出目录是 `artifacts/s2`（已被 git 跟踪的产物所在目录）；录制时应加 `--output-dir <临时目录>`，避免覆盖已提交产物。[来源: src/rra/cli.py:133, 135]
- 耗时提醒：`artifacts/s2/b3-dev.md` 记录全量并行运行墙钟 61.249 s（nproc=8）；`artifacts/s2/b4-dev.json` 的 `operational_cost.elapsed_seconds` 约 723 s（nproc=4）。这两个命令不适合现场实录，建议预先跑好后在视频中展示输出，或展示已提交产物。[来源: artifacts/s2/b3-dev.md "Operational cost"; artifacts/s2/b4-dev.json operational_cost]
- 配音语言、音乐、字幕：[所有者填写]。

## 1. 分镜总表

| 镜 | 时间码 | 时长 | 内容 |
|---|---|---:|---|
| 1 | 0:00–0:15 | 15 s | 问题与背景 |
| 2 | 0:15–0:35 | 20 s | 快速层基线：单回合与回执 |
| 3 | 0:35–0:55 | 20 s | System-2 架构 |
| 4 | 0:55–1:35 | 40 s | 主流程：一次恢复 + 一次有依据的拒绝 |
| 5 | 1:35–1:55 | 20 s | 关键功能：歧义门与 B4 离线重放 |
| 6 | 1:55–2:20 | 25 s | Zetaris 集成 |
| 7 | 2:20–2:45 | 25 s | Meterless 集成 |
| 8 | 2:45–3:00 | 15 s | NVIDIA 位置、结果状态、收尾 |

## 2. 逐镜脚本

### 镜 1 — 问题与背景（0:00–0:15，15 s）

- 画面：标题卡 → `README.md:9-15` 的 V0 流程图（重绘）；叠字"快速层声明超出授权工作包络时怎么办"。
- 旁白（草稿）："确定性快速层能在受限包络内修正残差；当它判定超出授权包络并升级时，System-2 能否提出可证伪的假设、经确定性验证获得有界权限，并在证据不足时拒绝行动。" [来源: docs/P3_SYSTEM2_DESIGN.md:15-19]
- 命令：无。
- 外部依赖/执行者：无。
- 备注：项目名、团队名 [所有者填写]。

### 镜 2 — 快速层基线：单回合与回执（0:15–0:35，20 s）

- 画面：终端运行一个单回合，随后用编辑器打开打印出的 `outputs/*.json` 回执，滚动展示字段。实际画面内容以命令真实输出为准；本草稿未运行该命令，不预设输出内容。
- 旁白（草稿）："V0 是一个确定性基线：种子化的 2D 传送带仿真、残差监视器与有界时间修正，每个回合输出 JSON 回执。" [来源: README.md:3-7]
- 命令：
  ```bash
  .venv/bin/python ./rra run --scenario bias --seed 7 --compensation on
  ```
  [来源: README.md:26]
- 外部依赖/执行者：无外部服务、无密钥；需先 `python3.12 -m venv .venv` 与 `.venv/bin/pip install -r requirements.txt`（需要 Python 3.12）。任何人可执行。[来源: README.md:21-25]
- 备注：若需展示"升级"画面，应选择会升级的 dev 场景/seed：[所有者裁决]（README 只记载了 `bias`、seed 7 的命令；其他场景名见 `config/scenarios.json`，本草稿未核对哪个 dev seed 会升级）。

### 镜 3 — System-2 架构（0:35–0:55，20 s）

- 画面：架构图（`docs/P3_SYSTEM2_DESIGN.md:130-170` 重绘）：快速层 → 证据包 → LLM 假设生成器 → 确定性拟合器 → 反事实验证器 → 授权门 → 执行器 → 回执；三处用颜色标出 Zetaris（证据装配）、NVIDIA（假设生成器）、Meterless（运行持久化）。
- 旁白（草稿）："LLM 只提出结构；参数由确定性拟合器估计；验证与授权是确定性的，LLM 输出不进入拟合、验证、歧义门或授权。" [来源: docs/P3_SYSTEM2_DESIGN.md:28; docs/P3_PREREG_ADDENDUM_04.md:19]
- 命令：无。
- 外部依赖/执行者：无。
- 备注：重观测保持（Addendum 05 §1）的实现在 **[FRZ-1 未合并]**，本镜不展示其行为。[来源: docs/P3_PREREG_ADDENDUM_05.md:11-23; 提交 56f36b0, e942024]

### 镜 4 — 主流程：一次恢复 + 一次有依据的拒绝（0:55–1:35，40 s）

- 画面（两段各约 20 s）：
  - 段 A（恢复）：回执中依次高亮 升级触发 → 证据包字段 → 提议的多个假设 → 验证器拒绝了哪些 → 授权记录 → 处置。
  - 段 B（拒绝）：同样的字段，高亮"验证器拒绝恢复且目标保持升级"的回合。
  - 回合选择：从 dev 产物中选一个"恢复"回合与一个"拒绝"回合：[所有者裁决]。`artifacts/s2/b3-dev.json` 仅为前 20 个 seed 保留逐决策记录，故候选回合应从这 20 个 dev seed 中选。[来源: T3_failure_funnel.md §1.1（分支 `cloud/t3-failure-funnel` @ b8f0e104，未并入 main）；`src/rra/eval/b3_dev.py:165-167`（T3 报告引用）]
- 旁白（草稿）：只描述所见字段，例如"这里是证据包，这里是被验证器拒绝的假设，这里是授权记录"。不使用"安全""成功"等结论性措辞；不引用计数。
- 命令（预先运行，视频中展示输出或已提交产物）：
  ```bash
  .venv/bin/python ./rra s2-b3-dev --output-dir outputs/demo-b3
  ```
  [来源: src/rra/cli.py:132-133, 152-155]
- 外部依赖/执行者：无外部服务、无密钥（仅读 dev 种子）；耗时见第 0 节；由所有者或 Luna 预先执行。[来源: decisions.md:34 "CLI `s2-b3-dev` … 仅读 dev seeds"]
- 备注：main 上 B3 dev 的记录含非零 `unsafe_action` 计数，决策记录写明"结果不得作为安全成功结论"；是否在视频中出现该计数、如何措辞：[所有者裁决]。[来源: artifacts/s2/b3-dev.md; decisions.md:34]

### 镜 5 — 关键功能：歧义门与 B4 离线重放（1:35–1:55，20 s）

- 画面：歧义门示意（`|V|≥2` 且无公共安全动作 → AMBIGUOUS → B4-strict 暂停并重观测；B4-tiebreak 在验证通过的假设间择一，仍过授权门），随后展示 `s2-b4-dev --replay` 的打印输出（`receipt_sha256`、`llm_calls`、`serial_parallel_check`）。
- 旁白（草稿）："仅当歧义门判定歧义时才调用生成器；响应进入内容寻址缓存，评分工件由冻结缓存、禁用网络的代码离线重放生成。B4 在注册证据包下的效果：待 eval-v3，尚无结果。" [来源: docs/P3_PREREG_ADDENDUM_04.md:13, 43, 7]
- 命令：
  ```bash
  .venv/bin/python ./rra s2-b4-dev --replay --subset --output-dir outputs/demo-b4
  ```
  选项来源：`--replay`（"run offline from artifacts/llm_cache"）、`--subset`（"use the registered L1g 33-seed subset"）、`--output-dir`、`--nproc`。[来源: src/rra/cli.py:134-138, 157-162]
- 外部依赖/执行者：`--replay` 时 `_ReadThroughProvider` 不构造实时提供者，按代码不需要网络与 `NVIDIA_API_KEY`；本草稿未运行该命令，未核实实际行为。耗时约 723 s 量级（见第 0 节），建议预先执行，由所有者或 Luna 执行。[来源: src/rra/eval/b4_dev.py:30-32; artifacts/s2/b4-dev.json operational_cost]
- 备注：不展示 B4 与 B3 的差异数字。2026-10-23 dev 运行的格式失败披露（Addendum 04 §5）是否在视频中出现：[所有者裁决]。[来源: docs/P3_PREREG_ADDENDUM_04.md:45-51]

### 镜 6 — Zetaris 集成（1:55–2:20，25 s）

- 画面：Zetaris 中两个数据源（S-TELEMETRY、S-OPS）与一条跨源 JOIN 查询；随后回执 `artifacts/sponsor/zetaris-equivalence.json` 中的等价字段与 `artifacts/sponsor/zetaris-whitelist.json` 的 `extra_count`。
- 旁白（草稿）："证据包由两个分离的数据源通过 Zetaris 联邦查询装配；白名单检查逐列枚举，白名单外字段即失败；Zetaris 装配的证据包与本地参考加载器的规范 JSON 做 SHA-256 等价比对，回执记录 20 个回合、各项 mismatch 计数为 0。注册评估使用本地参考加载器，Zetaris 路径用于演示与等价回执。" [来源: docs/P3_PREREG_ADDENDUM_02.md:58-81; docs/P3_PREREG_ADDENDUM_03.md:49-51; artifacts/sponsor/zetaris-equivalence.json:14; artifacts/sponsor/zetaris-whitelist.json]
- 命令（仅脚本名；命令行参数 [UNKNOWN]，本草稿未逐一核对）：
  - `scripts/l3_zetaris_up.sh`（启动 `rra-l3-pg` 与 `rra-l3-ops` 并注册）[来源: scripts/l3_zetaris_up.sh:7-27]
  - `scripts/l3_equivalence.py`（等价检查）[来源: scripts/l3_equivalence.py:1]
  - `scripts/l3_secret_audit.py`（密钥审计）[来源: scripts/l3_secret_audit.py:7]
- 外部依赖/执行者：**需要 Zetaris 自管本地部署（docker compose 网络 `zetaris_default`）与环境变量 `ZETARIS_TOKEN`；由所有者执行**；令牌到期日 2026-11-17。录制时不得露出令牌（客户端错误信息已将令牌替换为 `[REDACTED]`，但终端环境变量与命令历史仍须遮挡）。[来源: scripts/l3_zetaris_up.sh:5-6; src/rra/sponsor/zetaris.py:19-35; docs/SPIKE_NOTES_20261019.md:12]
- 备注：若录制时不能访问 Zetaris，可只展示已提交回执文件，并在画面上标明"已提交的记录值，非本次实时运行"。

### 镜 7 — Meterless 集成（2:20–2:45，25 s）

- 画面：终端运行持久化，再运行 `trail` 展示某回合的持久化记录，再运行 `replay`；叠字"持久化开/关决策相同的检查"，并展示回执 `artifacts/sponsor/meterless-persistence.json` 中的 `M3_cross_episode_reads`、`M4_replay_match` 与 B4 块字段。
- 旁白（草稿）："每次 System-2 决策运行被持久化为 Meterless 记录，可检视推理轨迹并回放；记忆范围仅限回合内，对其他回合只写不读。回执记录 20 个回合：跨回合读取为 0，重放匹配 20。" [来源: docs/P3_PREREG_ADDENDUM_02.md:95-107; artifacts/sponsor/meterless-persistence.json summary]
- 命令：
  ```bash
  scripts/setup_meterless.sh
  .venv/bin/python scripts/l6_persist_and_replay.py run --run-tag demo --seeds 14
  .venv/bin/python scripts/l6_persist_and_replay.py trail  --run-tag demo --episode ep-014
  .venv/bin/python scripts/l6_persist_and_replay.py replay --run-tag demo --episode ep-014
  ```
  [来源: bridges/meterless/README.md:9-15, 41-45]
- 可选（实时桥测试）：
  ```bash
  RRA_METERLESS_LIVE=1 .venv/bin/python -m pytest tests/test_meterless_bridge.py -q
  ```
  [来源: bridges/meterless/README.md:46]
- 外部依赖/执行者：需要 Node 22；`setup_meterless.sh` 会克隆开源 Meterless 仓库（固定提交 `1742dec56a66e58eef9dda2d2b865823758ca8cd`）并 `npm ci --ignore-scripts`，因此**需要对 GitHub 与 npm 的网络访问**；不需要 API 密钥。持久化使用本地桥（`tsx` 下的 `bridge.ts`），按仓库文档不是对 Meterless 托管服务的远端调用；由所有者或 Luna 执行。[来源: bridges/meterless/README.md:1-15]
- 备注：`--seeds 14` 的含义与 `ep-014` 的对应关系以脚本为准，本草稿未核对（`scripts/l6_persist_and_replay.py:309-315` 仅给出参数声明）。Meterless 的"组件"与"最小集成"要求的主办方期望：[UNKNOWN]。[来源: docs/SPIKE_NOTES_20261019.md:33]

### 镜 8 — NVIDIA 位置、结果状态、收尾（2:45–3:00，15 s）

- 画面：三栏边界图（Zetaris / Meterless / NVIDIA）→ 结果页占位 → 仓库地址卡。
- 旁白（草稿）："NVIDIA NIM 上的 Nemotron 只作为假设生成器，位于可替换适配器之后。注册评估的结果：待 eval-v3，尚无结果。" [来源: docs/P3_PREREG_ADDENDUM_02.md:121-125; docs/P3_PREREG_ADDENDUM_04.md:7]
- 命令：无。
- 外部依赖/执行者：无。
- 备注：`scripts/nemotron_smoke.py` 是需要 `NVIDIA_API_KEY` 的单次实时烟测（"One authorized live NIM smoke call with at most two backoff retries"），其命令行用法 [UNKNOWN]；本脚本不列入分镜，除非所有者决定录制并自行核对用法。[来源: scripts/nemotron_smoke.py:1; src/rra/llm/providers.py:82-84]
- 仓库地址、提交 sha、致谢：[所有者填写]。

## 3. Rule 6.1 覆盖核对

| Rule 6.1 要求 | 镜 |
|---|---|
| 主流程 | 2、3、4 |
| agent 如何解决所选挑战 | 3、4、5 |
| 关键功能 | 4、5 |
| Zetaris 与 Meterless 如何集成 | 6、7 |

[来源: docs/HACKATHON_RULES.md:21]

## 4. 录制前须所有者确认

- 镜 2、4：选用的 dev 场景与 seed（"恢复"与"拒绝"各一）。
- 镜 4、5：dev 数字与格式失败披露是否出现在视频中及其措辞（`DRAFT_SUBMISSION_v2.md` 第 10 节第 3、4 项）。
- 镜 6：Zetaris 部署与令牌可用性；录屏时的密钥遮挡。
- 镜 7：Node 22 与网络环境。
- 是否采用 `feat/frz1-b3core`（**[FRZ-1 未合并]**）录制：第 10 节第 15 项。
- Cursor 的使用方式是否在视频中出现：[所有者填写]（Rule 6.1 未要求；Rule 6.4 在文字说明中要求）。[来源: docs/HACKATHON_RULES.md:24]
- 视频托管位置与最终长度：[所有者填写]。
