# Known failure modes

- **Combined disturbances exceed the safety threshold.** With the V0 combo defaults, the accumulated residual eventually crosses the fixed `1.25` threshold. The controller then stops attempts for that episode and reports `ESCALATE`; its lower success rate is expected fail-closed behavior.
- **Compensation can hurt when the residual signature changes after the correction is latched.** The timing offset is bounded, but a second unmodeled speed change can make the latched estimate stale. A later residual breach stops picks; smaller changes may instead increase error.
- **Lateral error is not compensated.** The 2D plant randomizes y in a narrow seeded band, but the gripper is fixed at `y_pick`; V0 only adjusts timing. Wider lateral distributions can reduce success even when x timing is correct.
- **Configured gripper response delay is not estimated by the residual monitor.** `load_response_delay` defaults to zero; when enabled after the load step, it can make compensation ineffective or worse because the monitor observes object position, not actuator latency.
- **Classification is heuristic.** Drift, constant speed change, and a speed step can look alike over a short window. Classification can lag the first samples; corrections remain clamped while the monitor accumulates evidence.
- **The simulator is an idealized baseline.** It has no actuator noise, occlusion, collisions, object rotation, or stochastic sensor noise. The result does not establish performance on hardware.
- **Some clean or weak disturbances leave little headroom.** If the uncompensated controller already succeeds, success rate cannot improve further; MAE may be the more informative metric.
