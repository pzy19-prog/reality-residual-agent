# Design decisions

| 日期 | 问题 | 决定 | 理由 / 验证 |
|---|---|---|---|
| 2026-09-27 | 随机源与运行依赖 | 使用 `numpy.random.default_rng(seed)`；运行依赖为 numpy、pydantic；pytest 是测试依赖 | 确保给定 seed 可复现；通过 Python 3.11 venv 安装真实 requirements 验证 |
| 2026-09-27 | 固定抓爪与补偿接口 | 抓爪固定在 `(x_pick, y_pick)`；V0 只做有界时刻补偿，空间修正为 0 | 保持仿真机械约束，不越过 Controller 限位 |
| 2026-09-27 | 评估 seed 隔离 | 历史开发使用的 `0–129` 统一归为 dev；新 eval 为 `1000–1099`，在 `6377fa6` 单独提交冻结 | 冻结后 eval seeds 只在最终 bench 使用；dev seeds 存于 `config/dev_seeds.json` |
| 2026-09-27 | Bench 场景与强度 | 加入 nominal；bias、drift、moving、load 各增加 low/mid/high，参数集中在 `config/scenarios.json`；combo 保持既有默认值 | 覆盖无扰动基线与强度阶梯；combo 不为提高分数调参 |
| 2026-09-27 | success 分母 | 成功数除以所有生成物体数；升级后未尝试物体和 Controller 拒绝的物体均不是成功 | 衡量整组任务产出，而不是仅对已执行抓取计分 |
| 2026-09-27 | MAE 聚合与误差样本 | 每个已发出抓取尝试的误差为 `max(二维欧氏位置误差, |实际时间 − 命令时间| × 命令速度)`；MAE 对所有尝试等权平均；未尝试不进 MAE，成功或失败的尝试都进 | 旧 bench 对 episode 均值再平均，使零尝试 episode 的 0 MAE 稀释总误差；改为 `absolute_error_sum / attempted`，并加回归测试 |
| 2026-09-27 | 旧 combo MAE `0.011`、success `0` | 判定为聚合 bug，而不是成功抓取 | 旧口径中多数 episode 升级后无尝试、MAE=0；少数尝试全部失败，导致成功率按全物体分母仍为 0。新口径排除无尝试物体的伪零误差 |
| 2026-09-27 | combo 的快速层行为 | 所有场景共享固定安全阈值 `1.25`；combo 快速规则层全部升级并 fail-closed，作为核心失败模式记录 | 不为 combo 单独放宽阈值或调参；赛中 System-2 层应解决恢复决策 |
| 2026-09-27 | Python 兼容层 | 删除/不保留任何 Pydantic shim，直接用 requirements 安装 Pydantic 2 | 真实环境执行测试及确定性校验，避免离线替代层掩盖校验行为 |
| 2026-09-27 | setuptools build-system | 不显式恢复 setuptools build-system | 仓库通过 `rra` source-tree launcher 运行，不构建 Python wheel；Docker 直接复制源码，增加构建依赖没有必要。setuptools 不是运行依赖 |
| 2026-09-27 | CLI / 模块签名 | 保持公开 `rra run`、`rra bench` 命令和 `run_bench(output_dir)` 签名；用 `RRA_SEED_FILE` 选择 dev 冒烟 seed 文件 | 支持本地与 Docker dev 冒烟，正式默认仍由冻结 eval 文件驱动 |
| 2026-10-23 | 运行时 Python 版本 | 统一为 Python 3.12（本机 3.12.3），CI/启动脚本/Dockerfile/README 同步；3.11 时期的历史结果保留为历史记录 | requirements 钉 numpy==2.5.4（L5 D10），该版本要求 Python>=3.12；PR #19 合并后 CI 因此失败 |
| 2026-10-24 | FRZ-2A 所有者裁决 R1–R9 | R1 A05 §1.1 保持入口取窄读法，只限快速层 ESCALATE 路径；R2 §1.3 维持现状不改代码，88/5 在提交材料中披露；R3 episode 级 safe_stop 主导 84/775 不在冻结范围，作为失败模式披露；R4 登记 runner = 本机 i7-10750H、Python 3.12.3、NumPy 2.5.4、scipy-openblas 0.3.34；R5 A05 §3.4 在本机实现，B4 缓存在本机 live 重建；R6 B4 请求保留 passing[]、current_time、horizon；R7 证据包范围：本目标的观测与在场事件、episode 内决策之前的全部指令反馈、known_config 取 C1 的 5 个字段；R8 二维网格平局按 (tau, delay) 字典序；R9 请求模板 SHA-256 = 去掉证据后的请求骨架的哈希，模型标识记录服务端返回的名字 | T4 审查 §7 第 1、2、9、10 条；T6 冻结前核对 §5 第 1–4 条；Addendum 05；登记见 Addendum 06 |

## 评估纪律

盲测冻结提交：`6377fa67a7252ac540b8f5fc6a6e403dd608c452`（`freeze blind eval seeds`）。实现与 dev 验证提交：`b025bd457ca30172371c9e0e8d4a16db7c634c31`。eval seeds 只在该实现提交后运行一次，生成 artifact 的 `git_sha` 为 `b025bd4`；运行后没有修改 `src/`。nominal on/off success 均为 `0.986`，四种 low 档 off success 均大于零；combo 两种模式均在 100/100 episodes 升级。完整结果在 README 和 `bench.json`。

### RRA V0 freeze v2

旧 eval（seeds `1000–1099`）保留为历史记录。v2 seeds `2000–2099` 在 `ff1ac91` 单独冻结；实现提交为 `c66b4bf5b35dedbbf102a77c36f4d0d8a1938246`，盲评只运行一次，artifact 提交为 `2418406`，`bench.json` 的 `git_sha` 与实现提交一致。盲评结束后没有修改 `src/`。本轮固定使用 Python 3.11 venv 运行 CLI，完整结果见 README 与 bench artifacts。

### RRA-D1-L2 — §12 context v3 and Nemotron proposer

- 2026-10-22: Added the six preregistered context families with deterministic wording variants, paired variant generation, content SHA-256 freezing, leakage validation, and fail-closed hash verification in `rra.eval.context_v3`.
- 2026-10-22: Defined the canonical 14 structure IDs and six fault hypothesis IDs within `rra.llm`; the proposer accepts only observable evidence packet and context text, validates output with Pydantic, ignores numeric parameters, and records unknown IDs/numeric omissions.
- 2026-10-22: Used stdlib urllib for NVIDIA NIM and a read-only content-addressed replay provider. Cache records contain request and response bodies only.
- 2026-10-22 (Claude 裁决): `SECOND_DYNAMICS_CHANGE` helpful 按 seed 从 `TXT-MOTOR-SERVICE` / `TXT-PACKAGE-SLIP` 选取；misleading 按 seed 从 `TXT-SENSOR-CAL` / `TXT-ACTUATOR-SLOW` 选取，依据 P3 §13.3 的第二次速度变化语义及 §12.1 速度类相容先验。
- 2026-10-22: 采用 `chat_template_kwargs={"enable_thinking": false}`（模式 a）作为 `NvidiaNimProvider` 默认，并纳入规范化请求及缓存键；单次同 packet 实测 HTTP 200、`finish_reason=stop`、`reasoning_tokens=0`、content 为合法 JSON，解析结构 ID `SENSOR_BIAS` / `VELOCITY_OFFSET` / `SPEED_STEP` / `ACTUATOR_DELAY`，延迟 14.2458 秒；服务端返回模型名 `private/nvidia/nemotron-3.5-super-120b-a12b`。此设置在 eval v3 生成前冻结。
| 2026-10-22 | System-2 确定性核心的拟合实现 | 采用确定性有界枚举：偏置/速度项使用 NumPy 最小二乘；速度阶跃时间以 0.05 s 网格枚举；执行器延迟以 0.01 s 网格拟合 accepted command feedback。缺少 6 条观测返回 no-fit，verifier 固定使用 n≥6、RMSE≤0.030 | 合成带噪参数恢复测试覆盖四个单原语和一个三原语组合；完整 pytest 71 项通过。B3 尚未接入 runner，详见 REPORT_D1.md 卡点。|
| 2026-10-22 | B3 runner 接入与 dev 对照 | `run_episode(system2_enabled=False)` 保持默认关闭；B3 只在 fast escalation / policy-visible presence fault 后运行，按目标重观测时步进复查，只有 verifier + common-action + scoped authorization 全通过才改计划；执行器将候选执行时刻与发令时刻分开处理 ACTUATOR_DELAY。CLI `s2-b3-dev` 配对跑 B1-corrected/B3，仅读 dev seeds | 全量 130 个 dev seeds 已生成 `artifacts/s2/b3-dev.{json,md}`。当前 dev unsafe_action 非零，结果不得作为安全成功结论；挑战集/保全集按 B1-corrected 固定。|
| 2026-10-24 | A06 勘误与冻结前澄清 | R10–R13（生成器请求内容）；A06 勘误（R9(a)、冻结 tag 名、引用更正）；探针、live 运行、计数、未完成处理、产物位置的澄清；结构保留在开发中已被使用的披露；R14（失败响应处理符合 A04 rule 1）、R15（B4 未完成时的计数）、R16（结构保留：如实披露，case 9 单独报告） | Addendum 07；T9a 审查；PR #27、#28 审查 |
