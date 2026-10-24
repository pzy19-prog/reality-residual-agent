# Reality Residual Agent（RRA）

确定性的 2D 传送带抓放仿真，外加两层系统：

| 层 | 内容 | 是否调用 LLM / 网络 |
|---|---|---|
| **V0 基线** | 规则快速层：残差监测、受限补偿、Controller、升级（`ESCALATE`）。每个物体位置由显式 seed 生成，扰动强度由 [`config/scenarios.json`](config/scenarios.json) 配置。V0 本身不调用 LLM、网络、NIM 或 Jev。 | 否 |
| **System-2 层** | 快速层升级后的恢复决策：候选假设、验证器、Controller 授权（B1-corrected / B3 / B4 变体）。B4 的假设来自 LLM（NVIDIA NIM），仓库内的 `artifacts/llm_cache` 支持离线回放。 | 仅 B4 且不带 `--replay` 时 |
| **赞助技术接入** | Meterless（决策链持久化与回放）、Zetaris（数据源路径，opt-in）、NVIDIA NIM（B4 假设生成）。见 [赞助技术](#赞助技术)。 | 视路径而定 |

状态说明：

- eval v2 已冻结并已运行一次（结果见文末）。**eval v3 的种子尚未生成，没有任何 eval v3 结果**；协议见 [docs/EVAL_PROTOCOL.md](docs/EVAL_PROTOCOL.md) 与 [docs/P3_PREREG_ADDENDUM_06.md](docs/P3_PREREG_ADDENDUM_06.md)。
- 本 README 中标 **dev** 的数字来自 dev seeds `0–129`，并注明来源文件；dev 数字用于迭代，不是评估结果。
- 标 `[待 FRZ-2A 合并后核对]`、`[待 EVAL-PATH 合并后核对]` 的段落是占位，对应的代码尚未合并，未写具体参数或输出。

## 问题与架构（V0 基线）

固定名义模型会在传感器偏移、随时间变化的偏移、移动目标或速度阶跃下产生抓取误差。RRA 记录“观测值 − 名义预测值”，用滑动窗口分类，将残差拆分为传感器偏移与运动领先，经受限时刻补偿与可行性检查后，与无补偿基线做同 seed 对照；修正不可行的对象显式跳过（correction_infeasible）。残差超过固定阈值时停止抓取并发出 `ESCALATE`。

```text
seeded 2D World → nominal ScriptedPlanner → ResidualMonitor → bounded Corrector
        ↑                    ↓                    ↓                 ↓
 perturbations          pick plan           residual receipt    Controller
                                                                     ↓
                                                     episode metrics + JSON receipt
```

2D 状态包含传送带方向的 x 与横向 y；抓爪固定在 `(x_pick, y_pick)`。V0 的补偿作用于抓取时刻，抓爪位置保持固定。所有速度、位置和抓取窗口由配置及 Controller 限位。

## System-2 层

快速层在 combo 等状态下升级后，V0 只能停止（见 [FAILURE_MODES.md](FAILURE_MODES.md)）。System-2 层在升级点枚举或提出候选假设，由验证器检查，再经 Controller 授权后才改变命令。设计见 [docs/P3_SYSTEM2_DESIGN.md](docs/P3_SYSTEM2_DESIGN.md)，预注册补充见 `docs/P3_PREREG_ADDENDUM_*.md`。

| 变体 | 入口 | 说明 |
|---|---|---|
| B1-corrected | `rra s2-b3-dev` 内的对照臂 | 仅快速层，带修正后的终态监测 |
| B3 | `rra s2-b3-dev` | 在每次快速层升级处枚举全部 14 种 DSL 结构；`LLM calls: 0` |
| B4 | `rra s2-b4-dev` | 假设来自 LLM；`--replay` 只读 `artifacts/llm_cache`；`--subset` 使用登记的 33 个 dev seed 子集（`artifacts/s2/diag-d1g.json`） |

FRZ-2A 的改动（证据包补全、§3.4 取整、提示词 v2、回执字段）：`[待 FRZ-2A 合并后核对]`。

当前仓库中已提交的 **dev** 结果（`artifacts/s2/b3-dev.md`，130 个 dev seeds）：recoverable challenge success 0.1084（84/775），wrong disposition 588，miss 97，unsafe action 7（均为 fast layer command），preservation regression 0/582。B4 的 dev 结果见 `artifacts/s2/b4-dev.json`。这些是 dev 数字，不是 eval 结果。

## 依赖

| 依赖 | 用途 | 何时需要 |
|---|---|---|
| Python 3.12 | 全部 Python 部分；`rra` 在其他版本会以 `RRA requires Python 3.12` 退出 | 必需 |
| `requirements.txt`：`numpy==2.5.4`、`pydantic>=2.6,<3`、`pytest>=8,<9` | 仿真、数据模型、测试 | 必需 |
| git、Node 22、npm | Meterless 桥（TypeScript，`bridges/meterless`）；Meterless 固定提交 `1742dec56a66e58eef9dda2d2b865823758ca8cd` | 仅 Meterless 路径 |
| Docker | 容器运行；`scripts/l3_zetaris_up.sh` | 仅 Docker / Zetaris 路径 |
| `NVIDIA_API_KEY` | NVIDIA NIM（端点 `https://integrate.api.nvidia.com/v1`，见 `src/rra/llm/providers.py`） | 仅实时 LLM 调用 |
| `ZETARIS_TOKEN`、运行中的 Zetaris 栈（默认 `http://localhost:8888/api/v1.0`） | Zetaris 路径 | 仅 Zetaris 路径（opt-in） |

Python 3.12 可由系统包管理器、`pyenv` 或 `uv` 获取；`python3` 指向其他版本时请显式使用 `python3.12` 建立虚拟环境，并用虚拟环境内的 Python 运行 `rra`（`rra` 的 shebang 是 `#!/usr/bin/env python3`）。

## 安装与运行（V0）

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python ./rra run --scenario bias --seed 7 --compensation on
.venv/bin/python ./rra run --scenario bias --seed 7 --compensation off
```

`rra run` 在 `outputs/` 写入 JSON receipt 并打印路径。

`rra bench` 对 nominal、四种扰动的 low/mid/high 档和 combo 执行补偿开/关对照，在 `--output-dir`（默认当前目录）写入 `bench.json` 和 `bench.md`。

> **注意**
> - 在仓库根目录运行 `rra bench` 会覆盖已提交的 `bench.md` 与 `bench.json`（冻结 eval v2 结果）。请在临时目录运行，或加 `--output-dir <dir>`。
> - 不设 `RRA_SEED_FILE` 时，`rra bench` 读取冻结的 eval v2 seeds `2000–2099`；该集合已用过一次，迭代不要使用。
> - 迭代只用 dev seeds `0–129`，且 `RRA_SEED_FILE` 请用绝对路径。

```bash
# dev seeds 的 bench，输出到临时目录（T8 实测约 6 分钟，4 核云 VM）
RRA_SEED_FILE="$PWD/config/dev_seeds.json" .venv/bin/python ./rra bench --output-dir /tmp/rra-dev
```

评估协议见 [docs/EVAL_PROTOCOL.md](docs/EVAL_PROTOCOL.md)。

## 无需密钥即可复现

以下命令不需要 `NVIDIA_API_KEY` 或 `ZETARIS_TOKEN`，在云 VM（4 核，Python 3.12，Node 22）上实测运行过；耗时是量级参考，部分命令当时与其他命令并发。详见 [docs/_review/T8_repro_check.md](docs/_review/T8_repro_check.md) 与 [docs/_review/T10_changes.md](docs/_review/T10_changes.md)。

| 命令（仓库根目录，已建 `.venv`） | 作用 | 实测 |
|---|---|---|
| `.venv/bin/python ./rra run --scenario bias --seed 7 --compensation on` | V0 单次运行 | 退出码 0，约 0.4 s |
| `RRA_SEED_FILE="$PWD/config/dev_seeds.json" .venv/bin/python ./rra bench --output-dir /tmp/rra-dev` | V0 dev bench | 退出码 0，约 6 分钟 |
| `.venv/bin/python -m pytest -q` | 全量测试 | 退出码 0，`200 passed, 4 skipped in 257.31s`（4 个跳过：3 个 Meterless live、1 个 Zetaris live） |
| `.venv/bin/python ./rra s2-b3-dev --output-dir /tmp/rra-s2` | B1-corrected 与 B3 在 dev seeds 上配对比较 | 退出码 0，容器内 104 s 与 122 s（两次） |
| `.venv/bin/python ./rra s2-b4-dev --replay --subset --output-dir /tmp/rra-s2` | B4 在 33 个 dev seed 子集上离线回放 | `520b7cf` 上（T8）：退出码 0，约 11 分钟；`349d1e6` 上（容器内）：退出码 1，约 100 秒后 `ReplayCacheMiss`（见下） |
| `bash scripts/setup_meterless.sh` | 安装固定提交的本地 Meterless 桥 | 退出码 0，约 4 秒（需访问 GitHub 与 npm） |
| `RRA_METERLESS_LIVE=1 .venv/bin/python -m pytest -q tests/test_meterless_bridge.py` | Meterless 桥测试（需先装 Meterless） | `25 passed` |
| `scripts/l6_persist_and_replay.py persist\|verify\|trail\|replay …` | Meterless 持久化与回放，见 [赞助技术](#赞助技术) | 退出码 0，各数秒 |

`349d1e6` 上 `--replay --subset` 以 `ReplayCacheMiss: artifacts/llm_cache/566dfc84….json` 退出：仓库中的 386 个缓存文件里没有这个请求的缓存。`520b7cf` 与 `349d1e6` 之间 `src/` 有改动，缓存缺失的原因未核实。

全量 `rra s2-b4-dev --replay`（不加 `--subset`）在 T8 中运行 28 分钟后被外部时限终止，没有输出，未完成。

## System-2 / B3 / B4 用法（dev seeds）

```bash
# B3（无 LLM 调用）：写 b3-dev.json / b3-dev.md
.venv/bin/python ./rra s2-b3-dev --output-dir /tmp/rra-s2

# B4 离线回放子集：只读 artifacts/llm_cache，写 b4-dev.json
.venv/bin/python ./rra s2-b4-dev --replay --subset --output-dir /tmp/rra-s2
```

- **`--output-dir` 必须指到临时目录。** 默认值是 `artifacts/s2`，会覆盖已提交的 `b3-dev.*`、`b4-dev.json`。
- `--replay` 只读 `artifacts/llm_cache`，不需要密钥；不带 `--replay` 时 B4 会构造 `NvidiaNimProvider`，缺少 `NVIDIA_API_KEY` 时抛出 `RuntimeError`。
- `--nproc N` 控制 B4 并行进程数。
- 这两个命令只使用 dev seeds，不读取 eval seeds。

`rra eval-v3` 子命令及其种子生成脚本：`[待 EVAL-PATH 合并后核对]`。

## 赞助技术

### Meterless（本地桥，无需密钥）

System-2 的决策记录经 `src/rra/sponsor/meterless.py` 与 `bridges/meterless`（Node 22 + TypeScript）写入 Meterless 存储，随后在新进程中读回、重放并比对哈希。需要 git、Node 22、npm：

```bash
bash scripts/setup_meterless.sh                 # 固定提交 1742dec…，vendor/ 与 node_modules/ 被 gitignore
RRA_METERLESS_LIVE=1 .venv/bin/python -m pytest -q tests/test_meterless_bridge.py

OUT=/tmp/rra-l6
.venv/bin/python scripts/l6_persist_and_replay.py persist --run-tag demo --out-root $OUT --seeds 0 1 2
.venv/bin/python scripts/l6_persist_and_replay.py verify  --run-tag demo --out-root $OUT --seeds 0 1 2
.venv/bin/python scripts/l6_persist_and_replay.py trail   --run-tag demo --out-root $OUT --episode ep-001
.venv/bin/python scripts/l6_persist_and_replay.py replay  --run-tag demo --out-root $OUT --episode ep-001
```

`verify` 不带 `--artifact` 时不写仓库文件；`run` 子命令与 `verify --artifact` 会改写已提交的 `artifacts/sponsor/meterless-persistence.json`。`scripts/l6_b4_meterless_replay.py` 用 B4 缓存重放 20 个 episode 并写出更新后的 JSON，用 `--output <path>` 选择输出位置（默认 `outputs/l6/meterless-persistence.json`；写回已提交文件需显式传 `--output artifacts/sponsor/meterless-persistence.json`）。该脚本在 `520b7cf` 上退出码 0（约 74 秒）；在 `349d1e6` 上运行中途以 `ReplayCacheMiss` 退出（退出码 1），改动前的脚本在同一提交上表现相同，原因未核实。

### Zetaris（opt-in，需要外部服务）

Zetaris 路径需要 `ZETARIS_TOKEN`（缺失时 `ZetarisClient` 抛 `ZETARIS_TOKEN is required`）、位于 `http://localhost:8888/api/v1.0` 的 Zetaris 栈，以及 `scripts/l3_zetaris_up.sh` 所需的：本机 Docker、名为 `zetaris_default` 的 Docker 网络、`postgres:16-alpine` 与 `python:3.12-alpine` 镜像、`outputs/l3/sources`（由 `scripts/l3_export_sources.py` 生成）。`tests/test_packet_sources.py` 的 live 部分默认跳过。这些命令不在无密钥复现范围内，本 README 的作者未在这些环境外运行它们。已提交的记录见 `artifacts/sponsor/zetaris-*.json`。

### NVIDIA NIM（需要 `NVIDIA_API_KEY`）

B4 的假设生成使用 NVIDIA NIM（`src/rra/llm/providers.py`，端点 `https://integrate.api.nvidia.com/v1`，请求以内容哈希缓存到 `artifacts/llm_cache`）。`scripts/nemotron_smoke.py` 是一次带重试的实时调用，需要密钥。有缓存时 `--replay` 完全离线。

### Cursor

[所有者填写：Cursor 使用方式（Rule 6.4）]

## Docker

镜像包含 `src/`、`config/`、`tests/`、`scripts/`、`bridges/`（不含 Meterless 的 vendor 与 node_modules）、`pyproject.toml`、`rra`，以及 B4 回放所需的 `artifacts/llm_cache` 与 `artifacts/s2/diag-d1g.json`。默认 `CMD` 为 dev seeds 的 `rra bench`，输出写到容器内 `/tmp/rra-out`。

```bash
docker build -t reality-residual-agent .

# 默认命令：dev seeds 的 bench（RRA_SEED_FILE=/app/config/dev_seeds.json 已写入镜像）
docker run --rm reality-residual-agent

# 保留输出到宿主机
docker run --rm -v "$PWD/out:/results" reality-residual-agent rra bench --output-dir /results

docker run --rm reality-residual-agent rra run --scenario bias --seed 7 --compensation on
docker run --rm reality-residual-agent python -m pytest -q
docker run --rm reality-residual-agent rra s2-b3-dev --output-dir /tmp/o
docker run --rm reality-residual-agent rra s2-b4-dev --replay --subset --output-dir /tmp/o
```

镜像内的 `python -m pytest -q` 实测为 `195 passed, 5 skipped, 4 failed`：4 个失败测试都因镜像没有 `git` 可执行文件（`FileNotFoundError: 'git'`；这些测试调用 `git rev-parse` / `git ls-files`）；在有 git 的检出中同样的测试见上文。

镜像外运行：Meterless（需要 Node 与 `scripts/setup_meterless.sh`）、`scripts/l6_*`、Zetaris 路径、全量 `artifacts/`（约 155 MB，大部分是诊断 JSON）。镜像内没有 `.git`，receipt 的 `git_sha` 为 `unknown`。`rra bench` 为给结果标注 `seed_role` 会读取 `config/eval_seeds_v2.json` 与所用 seed 集合比较，因此该文件仍在镜像中，但默认命令使用的 seed 集合是 dev seeds。

实测镜像大小、命令耗时和退出码见 [docs/_review/T10_changes.md](docs/_review/T10_changes.md)。

## eval v3 状态

- 种子**尚未生成**，没有结果。`config/eval_seeds_v3.json` 不存在；`artifacts/h1/final-eval-v3-prohibition.json` 记录了生成与查看的状态。
- 协议、运行顺序和 B4 调用上限见 [docs/EVAL_PROTOCOL.md](docs/EVAL_PROTOCOL.md) 与 [docs/P3_PREREG_ADDENDUM_06.md](docs/P3_PREREG_ADDENDUM_06.md)。
- 生成与运行命令：`[待 EVAL-PATH 合并后核对]`。

## 已知局限

- V0 快速层的失败模式（修正包络、硬升级、边界放行、模型限制）见 [FAILURE_MODES.md](FAILURE_MODES.md)。仿真是理想化的（无传感器噪声、执行器动力学、遮挡或碰撞），结果不涉及硬件。
- System-2 的 dev 指标见上文及 `artifacts/s2/b3-dev.md`、`artifacts/s2/b4-dev.json`。
- Docker 镜像不含 Meterless 与 Zetaris 路径（见 [Docker](#docker)）。
- Meterless、Zetaris、NVIDIA 路径各有外部依赖（见 [依赖](#依赖)）；只有 Meterless 本地桥与 `--replay` 不需要密钥。
- `349d1e6` 上 `rra s2-b4-dev --replay --subset` 与 `scripts/l6_b4_meterless_replay.py` 因 `ReplayCacheMiss` 退出（见上文），B4 离线回放在该提交上未能复现。
- 全量 `rra s2-b4-dev --replay` 的单进程运行超过 28 分钟（T8 未跑完）；`rra bench` 的 dev 运行约 6 分钟。

## Bench 指标定义

- **成功率** = 成功抓取数 / 基准中的全部生成物体数（每个 seed、配置生成 12 个物体）。成功要求 Controller 接受命令且抓取窗口判定成功。升级后未尝试的物体仍留在分母中，按失败计；Controller 拒绝的尝试也不计成功。
- **MAE** = 所有实际发出抓取尝试的 pick-window error 之和 / 抓取尝试数。单次 error 是 `max(二维欧氏位置误差, |实际时间 − 命令时间| × 命令速度)`，单位为世界距离。它包含成功和失败尝试；升级后未尝试的物体不进入 MAE 分子或分母。如果全组都没有尝试，MAE 按 0 报告。
- **升级数** = episode 中首次触发的升级数，加上 Controller 拒绝导致的升级数；同一 episode 的 residual 超限只记一次。

因此，旧聚合口径下 combo 补偿关闭曾出现 MAE `0.011`、成功率 `0`：多数 episode 升级后没有抓取，episode MAE 被记为 0 并参与 episode 均值；少数已尝试抓取全部失败，所以按全部生成物体计算的成功率仍为 0。该 MAE 聚合是 bug，当前 bench 改为按实际尝试数加权，未尝试物体只影响成功率分母。

### 冻结 eval v2 结果

以下结果使用冻结的 100 个 eval seeds `2000–2099`，代码版本 `c66b4bf`；每个配置 × seed 运行 12 个物体，补偿开/关使用相同 seeds。完整 coverage、precision 和终态计数见 [`bench.md`](bench.md) 与 [`bench.json`](bench.json)。这是 V0 基线的结果，不含 System-2 层。

| 场景 | 参数 | off 成功率 | on 成功率 | 差值 | off MAE | on MAE | off 升级 | on 升级 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| nominal | — | 1.000 | 1.000 | +0.000 | 0.050 | 0.050 | 0 | 0 |
| bias-low | `position_bias=0.08` | 1.000 | 1.000 | +0.000 | 0.093 | 0.050 | 0 | 0 |
| bias-mid | `position_bias=0.25` | 0.000 | 1.000 | +1.000 | 0.255 | 0.050 | 100 | 0 |
| bias-high | `position_bias=0.45` | 0.000 | 1.000 | +1.000 | 0.453 | 0.050 | 100 | 0 |
| drift-low | `drift_per_second=0.008` | 1.000 | 1.000 | +0.000 | 0.070 | 0.050 | 0 | 0 |
| drift-mid | `drift_per_second=0.045` | 0.049 | 1.000 | +0.951 | 0.273 | 0.051 | 100 | 0 |
| drift-high | `drift_per_second=0.09` | 0.000 | 0.981 | +0.981 | 0.534 | 0.076 | 100 | 0 |
| moving-low | `moving_speed_delta=0.02` | 0.977 | 1.000 | +0.023 | 0.129 | 0.051 | 0 | 0 |
| moving-mid | `moving_speed_delta=0.10` | 0.000 | 0.849 | +0.849 | 0.593 | 0.087 | 100 | 1 |
| moving-high | `moving_speed_delta=0.18` | 0.000 | 0.010 | +0.010 | 0.968 | 0.154 | 100 | 100 |
| load-low | `load_speed_delta=0.04` | 0.664 | 1.000 | +0.336 | 0.166 | 0.051 | 18 | 0 |
| load-mid | `load_speed_delta=0.16` | 0.000 | 0.656 | +0.656 | 0.627 | 0.081 | 100 | 18 |
| load-high | `load_speed_delta=0.28` | 0.000 | 0.023 | +0.023 | 0.877 | 0.094 | 100 | 100 |
| combo | existing defaults | 0.000 | 0.008 | +0.008 | 0.315 | 0.154 | 100 | 100 |

结果文件：[`bench.json`](bench.json)、[`bench.md`](bench.md)。combo 规则快速层的全部升级是 V0 核心失败模式；System-2 层的目标是该状态下的恢复决策，详见 [FAILURE_MODES.md](FAILURE_MODES.md)。
