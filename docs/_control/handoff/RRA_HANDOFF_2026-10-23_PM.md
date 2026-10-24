# RRA 黑客松交接文档 — 2026-10-23 12:10（北京时间）

上一份交接文档：RRA_HANDOFF_2026-10-23.md（10:15）。本文件只写增量和当前状态；更细的过程可以用 conversation_search 查原对话（关键词：L3 Zetaris、L6 Meterless、L1g、M16）。

## 0. 时间
- 提交目标：10-27 20:00 北京时间。官方截止：10-28 07:45 北京时间。
- D4（10-25）：冻结实现 → 在隔离环境生成 eval v3 seeds → 每个 baseline 跑一次 → 产出 artifact。

## 1. 仓库状态（pzy19-prog/reality-residual-agent）
- origin/main = `2a3b52d`（已合并 PR #16，即 L1d–L1g）。PR #16 的远端分支、本地分支、s2-triggers worktree 都已删除。
- **PR #17 `feat/l6-meterless`（head `8eb7492`）**：Claude 审查通过，待合并。
- **PR #18 `feat/l3-zetaris`（head `92dac5a`）**：Claude 审查通过，待合并。
- 合并顺序：先 #17，后 #18。Claude 在本地试合并过：无冲突，合并后 pytest 183 passed / 4 skipped。
- 报告归档在 `~/reality-residual-agent-worktrees/_reports/`：
  - ARCHIVE_D1.sha256（L1d–L1g 报告的哈希）
  - REPORT_D2_L3.md：sha 5de44d5f…，报告正文自带的哈希
  - REPORT_D2_L3_nogo.md：第一次因缺凭据停下的版本，保留备查
  - REPORT_D2_L6.md：sha 37f25f57…
- Zetaris 源容器 `rra-l3-pg`、`rra-l3-ops` 要保留，D4 和 demo 会用到。启动脚本：scripts/l3_zetaris_up.sh。
- GPG agent 缓存已改为 8 小时（~/.gnupg/gpg-agent.conf），10-23 11:46 解锁过一次。黑客松结束后恢复默认值。

## 2. 已完成线的结论
- **L1g**：T1–T8 全部 PASS（Claude 独立复核：pytest 157 passed；B1 130/130 哈希一致；锁存后 0 条 S2 授权命令；无陈旧授权；absent 样本只出现在 OBJECT_MISSING 族）。
  - F-L1g-1：SENSOR_STUCK 族 0/7 个 episode 锁存，S2 在这些 episode 里从未报出 SENSOR_STUCK 故障。它们的安全结果来自普通升级路径。SENSOR_STUCK 锁存只在 BELT_STOP episode 里被交叉触发过。因此叙事里**不能声称按故障类别正确识别**。
- **L3**：方案 A（Postgres 走 JDBC 存 S-TELEMETRY，Zetaris REST 表存 S-OPS），T1–T8 全部 PASS。
  - 24,000/24,000 个决策点的 packet 哈希一致。
  - T3：285 条诊断行，0 不一致。授权 evidence 的字段位置是 `system2_decisions[].authorization.evidence_ids`。
  - 联邦方式：每个 episode 用一条跨源 UNION ALL 取回全部行；另有一条 JOIN 语句单独证明 T5。每个 episode 的查询耗时 0.67–1.27 s。
- **L6**：M1–M8 全部 PASS（20 个 episode、305 条决策）。
  - B4 一栏 = DEFERRED，留给 L5/D4。
  - 配对裁决 D7：`trigger="hard_fault_latch"` 的决策不配对，持久化时 diagnostic=null（seed 16、18 各 10 条）。
  - M2 采用的口径：同一组 run_episode 参数下，持久化开/关两次运行的 receipt 哈希 20/20 相同。

## 3. 本轮新增裁决
- **M2 口径（已裁决）**：接受 L6 的口径。A02 §5.4 要求的是"决策不变"：system2_decisions 在生产配置和持久化配置之间 20/20 相同，满足要求。字面 receipt 哈希只有 2/20 相同，原因见 L5-1。
- **manifest 里带真值标签（case / fault_family）**：允许保留，供回放使用。约束：任何策略路径都不得读取 `kind:manifest`。注册评测里 Meterless 只写不读（A02 §5.2）；如果做 §5.3 的探索性跨 episode 记忆，必须把 manifest 排除。
- **跨环境哈希（已基本定位）**：Luna 机器（python 3.12.3、numpy 2.5.4）能复现已提交 artifact 20/20；Claude 沙箱（numpy 2.5.3）有 7/20 不一致。推断：fitter 用 lstsq，结果依赖 numpy/BLAS。D4 前在 requirements 里钉死 numpy==2.5.4，并把 python/numpy 版本写进 eval receipt。

## 4. L5 必须包含的项（尚未出卡）
- L5-0（原有）：接入 B4-strict 和 tiebreak；dev 集上跑全部 B1–B4；结构 ID 收敛到只在 rra.s2 定义；登记 B4 的调用策略；去掉 adapter 里硬编码的模型名。
- L5-1：`include_s2_diagnostics=True` 会给 `evaluator_objects` 加上 actual_x_at_execution / execution_time，并改变 receipt_sha256。必须把这两个仅诊断用的字段移出哈希输入（放到 s2_diagnostic_trace 或排除键里）。验收：B1 130/130 哈希不变；B3 在诊断开/关两种情况下 receipt 哈希 20/20 相同。
- L5-2：L3 代码里写死了常量 1200 / 100 / 0.1（scripts/l3_equivalence.py 和 sources.load_packets）。`decision.time` 用的是 step*dt，不是实际采样时间。feedback 的 seq 由 round(issued_time/dt) 推出来。L5 在把 load_packets 接进 B4 之前要修正：从 known_config 和 presence 行里读取，seq 从 command_id 或 step 解析。修完后 L3 等价 receipt 重跑一次。
- L5-3：absent 分支里的 run_b3 已经是死代码（L1g 之后锁存先于它执行），删除。SENSOR_STUCK / BELT_STOP 锁存证据目前用 `evidence_ids[-4:]`，改为检测器实际支持的窗口。
- L5-4：D4 前钉死 numpy==2.5.4，receipt 记录环境版本。

## 5. 其余排程
| 线 | 内容 | 执行者 | 状态 |
|---|---|---|---|
| M17/18 | 合并 #17 → #18，收尾两个 worktree | Luna | 卡已给出 |
| L5 | 见 §4 | Luna（新会话） | 等 M17/18 完成后出卡 |
| A04 | Addendum 04：撤销 A02 §7.3（Cursor 改为可选）+ 刷新 HACKATHON_RULES.md 快照；DEV_WORKFLOW 补 L3/L6 的作者和审查者 | Luna/Gemini | 未出卡 |
| L7 | 回放 demo UI（读 L3/L6 的 receipt 和 Meterless trail；demo 命令见 REPORT_D2_L6.md） | claude.ai/code 云会话 | D3 |
| D4 | 冻结 → eval v3 → artifact | Luna | 10-25 |
| D5–D6 | 视频、slides、README、6.1–6.4 集成说明 | 待定 | — |

## 6. 待议：价值叙事（11%）
- L1g 最后一次调用漏斗（33 个 seed 子集）：n_usable<6 87、AMBIGUOUS 64、已授权但 miss 4、窗口外 2。
- 候选叙事：可辨识才恢复，不可辨识就拒绝；S2 授权的不安全动作为 0，对照 B1 有 43 次。
- 需要和 omniscient upper bound、B2 的对照数一起定稿。

## 7. 流程规则（在 10:15 版基础上新增）
- 卡里的凭据条目写明完整路径；先用 `timeout 10 pass show … | wc -c` 预检。Codex 没有 TTY，GPG 必须由用户在交互终端里先解锁。
- 卡都是在聊天里给的，新会话看不到。下发时必须给完整卡（v2 合并版），不要只给补丁。
- 新增 `src/rra/sponsor/` 包；L3 和 L6 同名的 `__init__.py` 已验证可以自动合并。
