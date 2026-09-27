# Reality Residual Agent（RRA）V0

一个完全确定性的 2D 传送带抓放仿真与残差补偿基线。V0 不调用 LLM、网络、NIM 或 Jev；每个物体位置由显式 seed 生成。扰动强度由 [`config/scenarios.json`](config/scenarios.json) 配置。

## 问题与架构

固定名义模型会在传感器偏移、随时间变化的偏移、移动目标或速度阶跃下产生抓取误差。RRA 记录“观测值 − 名义预测值”，用滑动窗口分类，并由 EWMA 估计和受限时刻补偿器与无补偿基线做同 seed 对照。残差超过固定安全阈值时停止抓取并发出 `ESCALATE`。

```text
seeded 2D World → nominal ScriptedPlanner → ResidualMonitor → bounded Corrector
        ↑                    ↓                    ↓                 ↓
 perturbations          pick plan           residual receipt    Controller
                                                                     ↓
                                                     episode metrics + JSON receipt
```

2D 状态包含传送带方向的 x 与横向 y；抓爪固定在 `(x_pick, y_pick)`。V0 的补偿作用于抓取时刻，抓爪位置保持固定。所有速度、位置和抓取窗口由配置及 Controller 限位。

## 安装与运行

需要 Python 3.11。

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
export PATH="$PWD:$PATH"
rra run --scenario bias --seed 7 --compensation on
rra run --scenario bias --seed 7 --compensation off
rra bench
```

`rra run` 会在 `outputs/` 写入 JSON receipt 并打印路径。`rra bench` 默认使用冻结的 eval seeds `1000–1099`，对 nominal、四种扰动的 low/mid/high 档和 combo 执行补偿开/关对照，在当前目录写入 `bench.json` 和 `bench.md`。迭代只用 dev seeds `0–129`。本地开发冒烟可运行：

```bash
RRA_SEED_FILE=config/dev_seeds.json rra bench
```

Docker：

```bash
docker build -t reality-residual-agent .
docker run --rm -e RRA_SEED_FILE=/app/config/dev_seeds.json reality-residual-agent rra bench
```

要保留 Docker 输出到宿主机，可执行：

```bash
docker run --rm -e RRA_SEED_FILE=/app/config/dev_seeds.json -v "$PWD:/results" reality-residual-agent rra bench --output-dir /results
```

## Bench 指标定义

- **成功率** = 成功抓取数 / 基准中的全部生成物体数（每个 seed、配置生成 12 个物体）。成功要求 Controller 接受命令且抓取窗口判定成功。升级后未尝试的物体仍留在分母中，按失败计；Controller 拒绝的尝试也不计成功。
- **MAE** = 所有实际发出抓取尝试的 pick-window error 之和 / 抓取尝试数。单次 error 是 `max(二维欧氏位置误差, |实际时间 − 命令时间| × 命令速度)`，单位为世界距离。它包含成功和失败尝试；升级后未尝试的物体不进入 MAE 分子或分母。如果全组都没有尝试，MAE 按 0 报告。
- **升级数** = episode 中首次触发的安全升级数，加上 Controller 拒绝导致的升级数；同一 episode 的 residual 超限只记一次。

因此，旧聚合口径下 combo 补偿关闭曾出现 MAE `0.011`、成功率 `0`：多数 episode 升级后没有抓取，episode MAE 被记为 0 并参与 episode 均值；少数已尝试抓取全部失败，所以按全部生成物体计算的成功率仍为 0。该 MAE 聚合是 bug，当前 bench 改为按实际尝试数加权，未尝试物体只影响成功率分母。

完整评估表由盲测完成后的 `bench.json` 与 `bench.md` 记录。已知 combo 失败模式及 V0 边界见 [FAILURE_MODES.md](FAILURE_MODES.md)。
