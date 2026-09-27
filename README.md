# Reality Residual Agent（RRA）V0

一个完全确定性的 2D 传送带抓放仿真与残差补偿基线。V0 不调用 LLM、网络、NIM 或 Jev；每个物体位置由显式 seed 生成。

## 问题与目标

固定名义模型会在传感器偏移、随时间变化的偏移、移动目标或速度阶跃下产生抓取误差。RRA 记录“观测值 − 名义预测值”，用滑动窗口分类，并由 EWMA 估计和受限时刻补偿器与无补偿基线做同 seed 对照。残差超过固定安全阈值时停止抓取并发出 `ESCALATE`。

## 架构

```text
seeded 2D World → nominal ScriptedPlanner → ResidualMonitor → bounded Corrector
        ↑                    ↓                    ↓                 ↓
 perturbations          pick plan           residual receipt    Controller
                                                                     ↓
                                                     episode metrics + JSON receipt
```

2D 状态包含传送带方向的 x 与横向 y；抓爪固定在 `(x_pick, y_pick)`。V0 的补偿作用于抓取时刻，抓爪横向/纵向位置保持固定。所有速度、位置和抓取窗口由配置及 Controller 限位。

## 安装与运行

需要 Python 3.11。

```bash
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export PATH="$PWD:$PATH"
rra run --scenario bias --seed 7 --compensation on
rra run --scenario bias --seed 7 --compensation off
rra bench
```

`rra run` 会在 `outputs/` 写入 JSON receipt 并打印路径。`rra bench` 使用 eval seeds `100–129`，运行 5 个场景的 on/off 对照，在当前目录写入 `bench.json` 和 `bench.md`。tune seeds 固定为 `0–9`，与 eval seeds 不相交；CLI 不会自动调参。

Docker：

```bash
docker build -t reality-residual-agent .
docker run --rm reality-residual-agent rra bench
```

结果写入容器内 `/app/bench.json`、`/app/bench.md`。要保留到宿主机，可执行：

```bash
docker run --rm -v "$PWD:/results" reality-residual-agent rra bench --output-dir /results
```

## Eval benchmark

固定 eval seeds `100–129`，共 30 seeds/配置。成功率以全部生成物体为分母，因升级而未尝试的物体计为失败；MAE 是已尝试抓取的 2D 位置误差均值。数值来自离线 smoke 基准，见 `bench.json`；本次执行环境没有 Python 3.11 的 Pydantic/pytest，因此正式 `pytest` 与 Docker build 尚未验证。

| 场景 | 补偿关闭成功率 | 补偿开启成功率 | 差值 | 关闭 MAE | 开启 MAE | 开启升级数 |
|---|---:|---:|---:|---:|---:|---:|
| bias | 0.000 | 0.992 | +0.992 | 0.453 | 0.051 | 0 |
| drift | 0.133 | 1.000 | +0.867 | 0.271 | 0.052 | 0 |
| moving | 0.000 | 0.847 | +0.847 | 0.596 | 0.105 | 0 |
| load | 0.000 | 0.714 | +0.714 | 0.633 | 0.140 | 0 |
| combo | 0.000 | 0.006 | +0.006 | 0.011 | 0.071 | 30 |

**评估集偏离**：实现迭代期间曾查看 eval seeds 的早期 smoke 结果，并据此修正移动目标与阶跃负载的补偿算法。因此这些数字是探索性结果，不能作为未污染的盲验收；该偏离已记录于 `decisions.md`。禁止进一步基于 eval seeds 调参。combo 中叠加残差会越过固定阈值并升级；升级后本 episode 不再尝试抓取。具体原因见 [FAILURE_MODES.md](FAILURE_MODES.md)。
