# S2 D1d diagnostic

Dev subset: 27 seeds

## Wrong-disposition first-failure funnel

| First failure | L1c after | L1d after |
|---|---:|---:|
| AMBIGUOUS | 50 | 31 |
| n_usable<6 | 0 | 280 |
| 从未升级到 S2 | 95 | 0 |
| 已授权但 miss/未执行 | 10 | 6 |
| 门控时刻已在拾取窗口外 | 4 | 2 |

## Unsafe diagnostic cases

### Seed 48, target 0

```json
{
  "seed": 48,
  "target_id": 0,
  "true_speed_step_time": 2.529261594326517,
  "s2_authorization_decisions": [
    {
      "decision_time": 5.1000000000000005,
      "V": [
        {
          "structure": [
            "SENSOR_BIAS",
            "SPEED_STEP"
          ],
          "fitted_tau": 2.3500000000000014,
          "predicted_x_at_execution": -0.0830222549495565
        },
        {
          "structure": [
            "SENSOR_BIAS",
            "VELOCITY_OFFSET",
            "SPEED_STEP"
          ],
          "fitted_tau": 2.5500000000000016,
          "predicted_x_at_execution": 0.010275569709042087
        }
      ],
      "command_time": 5.8,
      "execution_actual_x": 0.4012193296743414
    }
  ],
  "command_time": 5.8,
  "execution_actual_x": 0.4012193296743414,
  "step_after_decision": false,
  "conclusion": {
    "FACT": [
      "realized speed_step_time=2.529261594326517",
      "final S2 decision time=5.1000000000000005",
      "command time=5.8",
      "actual execution x=0.4012193296743414"
    ],
    "INFERENCE": [
      "阶跃是否发生在最终授权决策之后由以上 sim-time 比较计算；S2 只接收截至决策时刻的 policy-visible 观测。"
    ]
  }
}
```

### Seed 88, target 0

```json
{
  "seed": 88,
  "target_id": 0,
  "true_speed_step_time": 1.320033704175537,
  "s2_authorization_decisions": [
    {
      "decision_time": 5.0,
      "V": [
        {
          "structure": [
            "SENSOR_BIAS",
            "SPEED_STEP"
          ],
          "fitted_tau": 1.3000000000000007,
          "predicted_x_at_execution": 0.04922439119179467
        },
        {
          "structure": [
            "SENSOR_BIAS",
            "VELOCITY_OFFSET",
            "SPEED_STEP"
          ],
          "fitted_tau": 1.3000000000000007,
          "predicted_x_at_execution": 0.04697098214002127
        }
      ],
      "command_time": 6.3,
      "execution_actual_x": 0.7127792887954973
    }
  ],
  "command_time": 6.3,
  "execution_actual_x": 0.7127792887954973,
  "step_after_decision": false,
  "conclusion": {
    "FACT": [
      "realized speed_step_time=1.320033704175537",
      "final S2 decision time=5.0",
      "command time=6.3",
      "actual execution x=0.7127792887954973"
    ],
    "INFERENCE": [
      "阶跃是否发生在最终授权决策之后由以上 sim-time 比较计算；S2 只接收截至决策时刻的 policy-visible 观测。"
    ]
  }
}
```

