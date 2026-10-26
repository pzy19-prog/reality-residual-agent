# 项目简介

**Reality Residual Agent（RRA）** 是面向自动化和机器人实验的二维输送带仿真及受证据约束的恢复 agent。快速残差层处理即时偏差；B3 在有限恢复 DSL 中穷举搜索；B4 Nemotron 提议或排序候选结构。确定性拟合、反事实验证、共同动作门控与显式有界授权决定是否继续，并用回执记录结果。语言模型不控制执行器，也不替代验证。

开发轨迹中可见的四项拟合检查只是十四个候选中的前四项。有多个检查通过时，只要它们支持共同安全动作，更新仍可继续；在 `AMBIGUOUS` 时，多个通过项之间没有共同安全动作，因此策略暂停。这不表示策略总要求唯一因果模型。`SENSOR_STUCK` 是开发场景标签；`BELT_STOP_OR_MOTION_LOSS` 是记录中的策略故障标签。

正式的 100-episode 对比中，B2 在 614 个可恢复挑战中恢复 104 个，有 47 个不安全事件。B3 恢复 41/614，有 15 个不安全事件，全部来自快速层；S2 授权的不安全事件为 0，而 B3 实际授权次数为 159。按注册的 A04 §2 构造，B4 STRICT 等同 B3。B4 TIEBREAK 恢复 39/614，在四种文本条件下有 58–59 个不安全事件，其中 43–44 个为 S2 授权的不安全事件。TIEBREAK 没有测得恢复收益。不安全数字是事件数，不是 episode 比率。

这是二维仿真中的有界研究原型。Case 9 在开发中已出现，因此不声称对未见组合泛化。结果不能证明实体部署、生产客户、商业投资回报或广义安全 agent 保证。

# 集成说明

**NVIDIA Nemotron** 在 B4 中提议或排序候选结构。之后的确定性拟合、反事实验证、共同动作门控和有界授权仍负责决定是否执行。排序更强或 JSON 有效，不能证明动作更安全或带来恢复收益。

**Zetaris** 用于联邦查询并组装共同的白名单 C1 packet。PostgreSQL telemetry 源提供 `observation_samples`、`presence_events` 和 `command_feedback`；两个只读 REST 源提供 `known_config` 与 `ops_context`。`scripts/l3_equivalence.py` 通过 Zetaris 组装 packet，并与本地 reference loader 对比。已记录回执显示 T3 锚点不匹配 0、T3 授权不匹配 0、T4 不匹配 0、T8 参考回执字节完全相同。这是归档验证，不是新实时查询。注册 eval-v3 使用本地 reference loader。

**Meterless** 通过固定版本的本地 H-MEM reference 实现集成（提交 `1742dec56a66e58eef9dda2d2b865823758ca8cd`），不是托管云服务。持久化包装器存储已完成的 episode 运行和 manifest，将读取限制在当前 episode，并从已存 manifest 重放作比较。现有新鲜开发证据覆盖四个 episode、四次重放匹配、零跨 episode 读取且全部检查通过。`ep-014` 记录了 14 项决策重放及相同回执。这些是开发期集成检查，不是 eval-v3 正式结果。

当前规则将 Cursor 设为可选；本文不声称实际使用过 Cursor。
