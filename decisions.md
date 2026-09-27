# Design decisions

| 日期 | 问题 | 选项 | 决定 | 理由 | 验证结果 |
|---|---|---|---|---|---|
| 2026-09-27 | 随机与依赖边界 | 自行 PRNG / numpy seeded generator | 使用 `numpy.random.default_rng(seed)`；运行依赖仅 numpy、pydantic，pytest 仅测试依赖 | 明确随机源并遵守依赖白名单 | 相同 seed 的世界样本 smoke 一致；正式 pytest 待 Python 3.11 依赖环境验证 |
| 2026-09-27 | 固定抓爪与位置补偿接口 | 改变抓爪位置 / 保持机械固定并调整时刻 | 抓爪固定于 `(x_pick, y_pick)`；V0 空间修正为 0，补偿器以受限时刻偏移执行 | 保持仿真约束“固定抓爪”，避免软件命令越过机械假设 | Controller 对 2D 抓取距离限位；eval smoke 中 4 个单扰动成功率提升 |
| 2026-09-27 | 目标重规划策略 | 每个时间步刷新名义 ETA / 首个观测生成固定计划，后续用残差补偿 | 每个目标固定初始名义计划；监视后续残差并锁存有界斜率时刻修正 | 连续重规划会掩盖移动目标偏差，无法形成可比较的名义基线 | 30 eval seeds smoke：bias/drift/moving/load 成功率均较 off 高 |
| 2026-09-27 | 安全阈值和 combo 结果 | combo 单独放宽阈值 / 所有场景共享固定阈值 | 所有场景用相同阈值 `1.25`；超限停止该 episode 的后续抓取并升级 | 禁止通过场景特例绕过 fail-closed | combo smoke 记录 30 个升级，且开启成功率如实低于单扰动 |
| 2026-09-27 | eval seeds 的使用 | 在评估集迭代 / tune 与 eval 分离 | tune seeds 固定 `0–9`，eval seeds 固定 `100–129`；调参不读取 eval 结果 | 避免评估集泄漏 | `rra bench` 元数据写入两组 seed 列表；独立组不相交 |
| 2026-09-27 | 执行环境缺包 | 联网安装 / 使用本地离线兼容 smoke 并披露限制 | 禁止网络安装；以本机 numpy 和临时 Pydantic 兼容层做 bench smoke，不将兼容层放入项目 | 遵守禁止网络调用的任务约束 | smoke bench 可运行；正式 pytest、Pydantic 校验和 Docker build 未完成 |
| 2026-09-27 | Eval/tune 隔离 | 只用 tune seeds 做迭代 / 早期排错时直接查看固定 eval smoke | 已发生偏离：实现迭代中依据 eval seeds 的 early smoke 结果修正 moving/load 补偿逻辑；保留此限制记录，不再据 eval 结果调参 | 排错时未及时将任务 seed 分区落实到迭代循环；已知结果无法撤回，eval 集不能再视为盲验收 | 最终表格仍按 100–129 生成，但只作探索性报告；ACCEPTANCE 4 未满足 |
| 2026-09-27 | Load response delay | 忽略延迟参数 / 将可配置响应延迟纳入物理执行 | 保留 `load_response_delay` 配置，默认 0；load/combo 阶跃后按该延迟推进实际抓取状态 | 满足 load-change 的速度阶跃或夹爪延迟两种建模路径；残差监视器只观测物体位置，因此该模式可能无效或变差 | 默认 eval 场景仍只启用带速阶跃；非零延迟列为已知失败模式 |
| 2026-09-27 | CLI 打包方式 | setuptools console entry point / source-tree launcher | 删除额外 build backend，使用仓库 `rra` 启动脚本和白名单 requirements | 严格保持依赖范围为 numpy、pydantic、pytest | 静态检查依赖清单通过；Docker build 未联网验证 |
