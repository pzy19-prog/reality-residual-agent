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

## 评估纪律

盲测冻结提交：`6377fa67a7252ac540b8f5fc6a6e403dd608c452`（`freeze blind eval seeds`）。实现与 dev 验证提交：`b025bd457ca30172371c9e0e8d4a16db7c634c31`。eval seeds 只在该实现提交后运行一次，生成 artifact 的 `git_sha` 为 `b025bd4`；运行后没有修改 `src/`。nominal on/off success 均为 `0.986`，四种 low 档 off success 均大于零；combo 两种模式均在 100/100 episodes 升级。完整结果在 README 和 `bench.json`。

### RRA V0 freeze v2

旧 eval（seeds `1000–1099`）保留为历史记录。v2 seeds `2000–2099` 在 `ff1ac91` 单独冻结；实现提交为 `c66b4bf5b35dedbbf102a77c36f4d0d8a1938246`，盲评只运行一次，artifact 提交为 `2418406`，`bench.json` 的 `git_sha` 与实现提交一致。盲评结束后没有修改 `src/`。本轮固定使用 Python 3.11 venv 运行 CLI，完整结果见 README 与 bench artifacts。
