# Reality Residual Agent

Reality Residual Agent（RRA）是用于研究 2D 传送带抓取的确定性仿真。它面向需要检查“模型偏差如何变成动作风险、何时应停止并升级”的机器人开发者；它不是已部署的工业控制器。每集由明确 seed 驱动，扰动、观测与动作保存在 receipt 中，便于复现和审计。

## 架构

快速残差层将观测与名义运动预测作比较，在边界内修正抓取时刻；超出边界时停止并升级。System 2 的 B3 在受限候选空间中做确定性假设搜索。B4 可选用 NVIDIA NIM 提案排序与 TIEBREAK，但提案须经过白名单、拟合器、验证器及明确授权检查才会执行。未经验证的提案不会直接成为控制动作。STRICT 与 B3 的结果按 A04 §2 的构造相同，这不是模型带来收益的新证据。

Zetaris 提供证据视图；Meterless 按 episode 持久化决策、拒绝跨 episode 读取，并支持从保存的 manifest 重放。两者边界及已有证据见下文；quickstart 不需要密钥、NIM 或在线服务。

## 快速开发 smoke

需要 Python 3.12。仓库依赖见 [`requirements.txt`](requirements.txt)：NumPy 2.5.4、Pydantic `>=2.6,<3`、pytest `>=8,<9`。安装应用依赖后即可运行确定性开发 smoke；默认 receipt 写入 `outputs/`，建议显式指定外部目录：

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
mkdir -p /tmp/rra-demo
PYTHONPATH=src .venv/bin/python ./rra run --scenario bias --seed 7 --compensation on --output-dir /tmp/rra-demo
```

实测 Python 3.12.3、NumPy 2.5.4；命令成功并生成 `bias-seed7-on.json`，attempted=12、successes=12、escalations=0。这个单 episode smoke 不调用模型，也不代表正式评估。

Meterless 是可选的开发集成，需要 Node 22；按 pin 安装并运行真实持久化演示的步骤见 [开发演示 runbook](docs/DEMO_RUNBOOK.md)。可选 Zetaris live 环境需要自行配置服务，本文不要求提供或读取凭据。记录的 Zetaris receipt 是历史集成证据，不是本次新查询。

Docker 镜像也仅用于同一 Python-only 开发 smoke：

```bash
docker build -t rra-dev-smoke .
docker run --rm rra-dev-smoke
```

基础镜像为 Python 3.12 slim；本次构建实际运行 Python 3.12.13、NumPy 2.5.4。镜像包含随 `src` 复制的 `rra.eval.final_v3` 模块，但不含 `.git` 元数据、已评分 eval-v3 artifacts 或可选 sponsor runtime，因此不支持正式 replay；也不是 sponsor stack 镜像。

## 正式 eval-v3 结果

以下数字来自已注册的 100-seed 结果及其静态审计，**不是本次 smoke 或 Meterless dev demo 的新分数**。分母是 614 个 recoverable challenges；unsafe 是动作计数，不能解释为 episode 百分比。

| 条件 | 挑战恢复 | unsafe 动作 | 解释 |
|---|---:|---:|---|
| B2 | 104 / 614 | 47 | 同一正式比较中的 broader-envelope 静态基线 |
| B3 | 41 / 614 | 15 | 15 个均来自 fast layer；S2-authorized unsafe actions = 0（授权事件总数为 159） |
| B4 STRICT（四种文本条件各自） | 41 / 614 | 15 | 与 B3 按构造相等，不是独立模型收益证据 |
| B4 TIEBREAK（四种文本条件各自） | 39 / 614 | 58–59 | 每个条件含 15 个 fast-layer unsafe 和 43–44 个 S2-authorized unsafe；恢复数未提高 |

结果、receipt 字段和审计：[`B2`](artifacts/eval_v3/b2.md) / [`B2 JSON`](artifacts/eval_v3/b2.json)、[`B3`](artifacts/eval_v3/b1b3.md) / [`B3 JSON`](artifacts/eval_v3/b1b3.json)、[`B4`](artifacts/eval_v3/b4.md) / [`B4 JSON`](artifacts/eval_v3/b4.json)、[逐条件响应分类与报告审计](artifacts/eval_v3/reporting_audit.md) / [机器可读审计](artifacts/eval_v3/reporting_audit.json)。审计指出 STRICT=B3 是设计构造；TIEBREAK 的恢复为 39 且 unsafe 为 58–59，不能宣称模型提高恢复或系统总体零风险。

上述计数对应 receipt 字段：B2 使用 `challenge_success_count`，B3 使用 `recoverable_challenge_success_count`；二者的分母均使用 `recoverable_challenge_count`。B3、B4 的来源拆分见 `unsafe_action_by_source`、`unsafe_by_source`，STRICT/TIEBREAK 分类及 gate 计数见 reporting audit。不要把 action count 当作 episode 比例。

调用统计分属不同阶段与单位。原始 live fill 的 `b4_live.json` 记录 provider `llm_calls` 1,519 次、`distinct_live_requests` 1,523 个。scored replay 的 `b4.json` 记录 `llm_calls` 1,519 次、**本次 scored replay 新增 live requests 为 0**（`distinct_live_requests=0`），并保留 1,523 条 `cache_provenance.ledger` 记录。这个 replay 零值不表示没有使用模型：它复用了之前记录的 fill。四种文本条件共 2,700 次 proposer invocation（STRICT 1,352、TIEBREAK 1,348）。这些计数单位不同，不能都称作 HTTP calls；TIEBREAK 行共享 provider 的 `llm_calls=0` 字段也不代表没有使用模型。

Zetaris 已记录的等价性证据位于 [`zetaris-equivalence.json`](artifacts/sponsor/zetaris-equivalence.json)：base `18041e5`、T3/T4 mismatch 均为 0、T8 receipt bytes identical 为 true。这是保存的既有 receipt，并非当前 live 查询。

## 复现与范围

正式离线复现应使用原始 scored result commit `dce9e802b024943cb21b8cdb621bdad34187dd73`；实现冻结标签 `impl-freeze-v3` 指向 `2365a220`，这是两个不同提交。当前维护分支上的 unchanged guard 会拒绝后续维护路径；不要用当前 main 代替原始结果提交。完整隔离 worktree、venv 与离线命令见 [eval-v3 复现说明](docs/REPRODUCING_EVAL_V3.md)。其中命令供未来复现使用，本次文档制作未重跑正式评估。bitwise 一致性仅承诺于注册 runner；跨机器可移植性不代表逐位哈希一致。

项目声明的既有工作边界见 [`HACKATHON_BASELINE.md`](HACKATHON_BASELINE.md) 与 `pre-window-freeze^{commit}`（`3b56637681551f21c6b4c253be6def59389d1051`）。边界之前的 H1 实现也属于既有工作；不应把其后所有提交都描述成活动期新实现。Cursor 为可选项，本文不声称使用过 Cursor。

简短历史入口：[旧 eval-v2 基准报告](bench.md)。它不是当前结果的 headline。
