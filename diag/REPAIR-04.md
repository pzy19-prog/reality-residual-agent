# RRA-V0-REPAIR-04 开发集诊断

## 范围与判据

所有数据仅使用 `config/dev_seeds.json` 中的 seeds 0–129，共 1,560 个对象/场景/模式；未运行或读取 eval seeds/results。实现提交：`21e38a0c05bd7e95f2f4a21a16fd83e6be067940`。

截断后 excess 定义为 `|uncapped_time_delta - clamped_time_delta|`。运动类 disturbance (`moving_target`、`drift`、`load_change`) 使用 `v_hat = nominal_speed + slope`，其他类使用 `nominal_speed`。`clamped = excess > 0` 仅用于记录；仅当 `excess * v_hat > tolerance` 时标记 `infeasible` 并在命令窗口跳过。tolerance 由 episode 配置传入。`MAX_TIME_CORRECTION = 0.50`、tolerance 默认 `0.20`、分类阈值、安全残差阈值及连续失败阈值 3 均未改变；REPAIR-03 S2–S5 保留。

## 14 场景 dev 汇总

每种模式的字段顺序为 success rate / coverage / precision / MAE。success rate 分母为总对象数；coverage = 发出命令对象数 / 总对象数；precision = picked / 发出命令对象数；MAE 仅统计已发命令对象。终态顺序为 picked / attempt_failed / rejected / escalated / skipped；escalations 为 episode 升级数。

| 场景 | Off 成功/coverage/precision/MAE | On 成功/coverage/precision/MAE | On 终态五项 | On escalations |
|---|---|---|---|---:|
| nominal | 1.000 / 1.000 / 1.000 / 0.051 | 1.000 / 1.000 / 1.000 / 0.051 | 1560 / 0 / 0 / 0 / 0 | 0 |
| bias-low | 1.000 / 1.000 / 1.000 / 0.094 | 1.000 / 1.000 / 1.000 / 0.051 | 1560 / 0 / 0 / 0 / 0 | 0 |
| bias-mid | 0.000 / 0.250 / 0.000 / 0.254 | 1.000 / 1.000 / 1.000 / 0.051 | 1560 / 0 / 0 / 0 / 0 | 0 |
| bias-high | 0.000 / 0.250 / 0.000 / 0.452 | 1.000 / 1.000 / 1.000 / 0.051 | 1560 / 0 / 0 / 0 / 0 | 0 |
| drift-low | 1.000 / 1.000 / 1.000 / 0.070 | 1.000 / 1.000 / 1.000 / 0.051 | 1560 / 0 / 0 / 0 / 0 | 0 |
| drift-mid | 0.032 / 0.313 / 0.102 / 0.275 | 1.000 / 1.000 / 1.000 / 0.052 | 1560 / 0 / 0 / 0 / 0 | 0 |
| drift-high | 0.000 / 0.250 / 0.000 / 0.536 | 0.987 / 1.000 / 0.987 / 0.079 | 1539 / 21 / 0 / 0 / 0 | 0 |
| moving-low | 0.987 / 1.000 / 0.987 / 0.129 | 1.000 / 1.000 / 1.000 / 0.052 | 1560 / 0 / 0 / 0 / 0 | 0 |
| moving-mid | 0.000 / 0.250 / 0.000 / 0.595 | 0.818 / 0.863 / 0.947 / 0.088 | 1276 / 71 / 0 / 0 / 213 | 5 |
| moving-high | 0.000 / 0.067 / 0.000 / 0.965 | 0.008 / 0.011 / 0.765 / 0.179 | 13 / 4 / 0 / 1442 / 101 | 130 |
| load-low | 0.677 / 0.952 / 0.711 / 0.167 | 1.000 / 1.000 / 1.000 / 0.052 | 1560 / 0 / 0 / 0 / 0 | 0 |
| load-mid | 0.000 / 0.250 / 0.000 / 0.631 | 0.651 / 0.676 / 0.964 / 0.080 | 1016 / 38 / 0 / 0 / 506 | 21 |
| load-high | 0.000 / 0.057 / 0.000 / 0.879 | 0.022 / 0.025 / 0.897 / 0.099 | 35 / 4 / 0 / 1456 / 65 | 130 |
| combo | 0.000 / 0.002 / 0.000 / 0.338 | 0.008 / 0.009 / 0.929 / 0.149 | 13 / 1 / 0 / 1546 / 0 | 130 |

## On success 与基线对比

三组结果均为 0–129 dev seeds，成功率分母均为 1,560 objects/场景。

| 场景 | 9cb87e4 | 66a3af0 (REPAIR-03) | 21e38a0 (REPAIR-04) |
|---|---:|---:|---:|
| nominal | 1.000 | 1.000 | 1.000 |
| bias-low | 1.000 | 1.000 | 1.000 |
| bias-mid | 1.000 | 1.000 | 1.000 |
| bias-high | 1.000 | 1.000 | 1.000 |
| drift-low | 1.000 | 1.000 | 1.000 |
| drift-mid | 1.000 | 1.000 | 1.000 |
| drift-high | 0.988 | 0.401 | 0.987 |
| moving-low | 1.000 | 1.000 | 1.000 |
| moving-mid | 0.853 | 0.203 | 0.818 |
| moving-high | 0.011 | 0.000 | 0.008 |
| load-low | 1.000 | 1.000 | 1.000 |
| load-mid | 0.673 | 0.242 | 0.651 |
| load-high | 0.024 | 0.008 | 0.022 |
| combo | 0.014 | 0.008 | 0.008 |

相对预期值，drift-high 为 0.986538（约 0.987）、moving-mid 为 0.817949（约 0.818）、load-mid 为 0.651282（约 0.651），drift-mid 与 nominal 均为 1.000；无超过 0.01 的偏差。moving-mid 与 load-mid 相对 9cb87e4 分别下降 0.035 和 0.022，是判据将剩余误差超 tolerance 的对象转为 `correction_infeasible` skip 的预期结果。

## attempt_failed 截断统计

补偿 on 的 14 场景合计有 **139 个 attempt_failed 对象**；其中 **138 个对象**在其 correction records 中至少出现一次 `excess > 0`。该统计按对象计数，不按重复的每步记录计数。

## 检查

- `.venv/bin/pytest -q`: **26 passed**。
- 新增 S1 行为测试在旧代码 `66a3af0` 上先行运行，3 项均失败：旧终态为 `correction_saturated`、trace 缺少 `clamped`、trace 缺少 `excess`；修改后相关测试通过。
- dev invariant audit：14 场景 × 130 seeds 均有每对象唯一终态和非空 reason；无同一对象重复命令。
- `git diff 6377fa6..HEAD -- config/eval_seeds.json` 为空。