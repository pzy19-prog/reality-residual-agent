# T8 复现检查：评委视角，只按仓库文档装、跑、看

- 执行环境：Claude Code 云会话（Linux 6.18，4 核，Python 3.12.x venv，Node v22.22.0，Docker 29.9.2，dockerd 为手动启动）
- main 实测头：`520b7cfdf13b805c9258ab06c79a658ee62aef8b`（与任务卡一致）
- 实现分支：`feat/frz1-b3core` @ `cb771079c1c119d73d0ebd0e24704a1935731cea`（与任务卡一致）
- 全部执行在 scratchpad 的全新 `git clone` 中；报告所在仓库工作区只新增本文件。
- 日期：2026-10-24

## 0. 范围、约束执行情况与未完成项

| 项 | 状态 |
|---|---|
| 默认 `rra bench`（eval seeds） | **未运行**（README 两个版本中的 `./rra bench` 均指向冻结 eval seeds，按任务卡跳过） |
| `config/eval_seeds*.json` | 未打开、未读取（`ls` 可见文件名；这两个文件也在 Docker 镜像的 `/app/config` 里） |
| 密钥 | 未设置 `NVIDIA_API_KEY` / `ZETARIS_TOKEN`；未运行任何需要 NVIDIA 或 Zetaris 的命令 |
| `rra s2-b4-dev --replay`（全量） | **未完成**：运行 28 分钟后被后台 30 分钟上限终止（`[killed]`），无输出文件、无退出码。改跑 `--replay --subset`（仍只读缓存），见 §3 |
| Docker 构建 | 原样 `docker build` 在本沙箱失败（pip TLS 证书，§2）；用仅追加 CA 证书的临时副本 Dockerfile 构建成功。仓库 Dockerfile 未改 |
| 计时 | 部分命令与其他命令并发运行（4 核），耗时只作量级参考，并发情况在各行标注 |

## 1. 全新克隆 + 逐条执行 README

克隆：`git clone https://github.com/pzy19-prog/reality-residual-agent`，8.6 s，HEAD 与上面 sha 一致。

### 1.1 README.md（中文）

| # | 命令 | 退出码 | 耗时 | 关键输出 |
|---|---|---:|---:|---|
| 1 | `python3.12 -m venv .venv` | 0 | 3.7 s | — |
| 2 | `.venv/bin/pip install -r requirements.txt` | 0 | 16.3 s | 装入 numpy 2.5.4、pydantic 2.14.1、pytest 8.4.2 等 11 个包 |
| 3 | `.venv/bin/python ./rra run --scenario bias --seed 7 --compensation on` | 0 | 0.4 s | 打印 `outputs/bias-seed7-on.json` |
| 4 | `.venv/bin/python ./rra run --scenario bias --seed 7 --compensation off` | 0 | 0.4 s | 打印 `outputs/bias-seed7-off.json` |
| 5 | `.venv/bin/python ./rra bench` | **未运行** | — | 默认 eval seeds 2000–2099，按任务卡禁止 |
| 6 | `RRA_SEED_FILE=<绝对路径>/config/dev_seeds.json .venv/bin/python ./rra bench`（在临时目录运行） | 0 | 356.4 s（与 Docker bench 并发） | 当前目录写出 `bench.json`、`bench.md`，14 行场景表 |
| 7–9 | Docker 三条命令 | 见 §2 | | |

第 6 项的偏差：任务卡写相对路径 `RRA_SEED_FILE=config/dev_seeds.json`，在临时目录中相对路径无法解析，故用绝对路径。README 的命令默认当前目录即仓库根目录；`rra bench` 会在当前目录写 `bench.json`/`bench.md`，在仓库根目录运行会覆盖已提交的 `bench.md`（`bench.json` 在 `.gitignore` 中，`bench.md` 不在）。

dev bench 表节选（`bench.md`）：

```
| nominal | 1.000 | 1.000 | 1.000 | 1.000 | 0.051 | 0.051 | 1560/0/0/0/0 | 0 |
| bias-mid | 0.000 | 1.000 | 1.000 | 1.000 | 0.254 | 0.051 | 1560/0/0/0/0 | 0 |
| drift-high | 0.000 | 0.987 | 1.000 | 0.987 | 0.536 | 0.079 | 1539/21/0/0/0 | 0 |
| moving-mid | 0.000 | 0.818 | 0.863 | 0.947 | 0.595 | 0.088 | 1276/71/0/0/213 | 5 |
| moving-high | 0.000 | 0.008 | 0.011 | 0.765 | 0.965 | 0.179 | 13/4/0/1442/101 | 130 |
```

其他观察：
- `bench.json` 的 `git_sha` 为 `"unknown"`：`_git_sha()`（`src/rra/cli.py:21`）在当前工作目录执行 `git rev-parse HEAD`，临时目录或 Docker（无 `.git`）里取不到。
- README 把 dev bench 称为"本地开发冒烟"，实测约 6 分钟（并发状态），不是秒级。
- `rra` 在 Python ≠ 3.12 时直接以 `RRA requires Python 3.12` 退出（在本机默认 `python3` = 3.13 上复现）。README 写了"需要 Python 3.12"，没写失败表现，也没写 3.12 的获取方式。

### 1.2 README.en.md（英文）

| # | 命令 | 结果 |
|---|---|---|
| 1–2 | `python3.12 -m venv .venv`、`pip install -r requirements.txt` | 同 1.1 #1–2 |
| 3 | `.venv/bin/python ./rra run --scenario bias --seed 7 --compensation on` | 同 1.1 #3，退出码 0 |
| 4 | `.venv/bin/python ./rra bench` | **未运行**（eval seeds）；dev-seed 变体同 1.1 #6 |
| 5 | Docker smoke 两条命令 | 同 1.1 #7–8，见 §2 |

### 1.3 中英文 README 差异（逐条）

1. 中文有"问题与架构"整节（含数据流图、2D 状态说明）；英文没有。
2. 中文给出 `--compensation off` 命令；英文只有 `on`。
3. 中文说明 `rra run` 写 `outputs/` 下的 JSON receipt 并打印路径；英文未提。
4. 中文说明 `rra bench` 在当前目录写 `bench.json`/`bench.md`；英文未提。
5. 中文有保留 Docker 输出到宿主机的命令（`-v "$PWD:/results" … --output-dir /results`）；英文没有。
6. 英文称 Docker 命令为"Docker smoke"，中文称"Docker："。
7. 中文有完整的"冻结 eval v2 结果"14 行表；英文只有一句话摘要并指向"Chinese README"。
8. 关于旧版 combo MAE `0.011` 的说明：两版都有，中文更详细（含"当前 bench 改为按实际尝试数加权"）。
9. 中文"升级数"定义写明"Controller 拒绝导致的升级数；同一 episode 的 residual 超限只记一次"，英文用 "once per episode" + "controller rejections"，含义一致，措辞不同。
10. 中文在"本地开发冒烟可运行："之后插入"评估协议见 …"一行才接代码块，句子被打断；英文中评估协议链接位置正常。
11. 两版都没有：System-2 / B3 / B4 用法、pytest 命令、Meterless / Zetaris / NVIDIA / Cursor 说明、eval v3 状态。中文末尾仅一句"赛中 System-2 层应解决该状态的恢复决策"。

## 2. Docker

VM 默认没有运行中的 daemon（`docker info`：`failed to connect to the docker API at unix:///var/run/docker.sock`）；`dockerd` 二进制存在，手动启动后可用。

| # | 命令 | 退出码 | 耗时 | 结果 |
|---|---|---:|---:|---|
| D1 | `docker build -t reality-residual-agent .`（原样 Dockerfile） | 1 | 15.5 s | 步骤 [4/7] `pip install` 失败：`SSLCertVerificationError … self-signed certificate in certificate chain`、`No matching distribution found for numpy==2.5.4` |
| D2 | 同上，在 scratchpad 的 `git archive` 副本中给 Dockerfile 追加两行（`COPY ca.crt /ca.crt`、`ENV PIP_CERT=/ca.crt`，证书为本沙箱出口代理的 CA） | 0 | 19.9 s | 镜像 317 MB。D1 的失败由本沙箱的出口代理 CA 引起；未关闭 TLS 校验 |
| D3 | `docker run --rm -e RRA_SEED_FILE=/app/config/dev_seeds.json -v <dir>:/results reality-residual-agent rra bench --output-dir /results` | 0 | 约 6 分钟（与宿主 dev bench 并发，未单独计时） | 写出 `bench.json`、`bench.md`；`bench.json` 与 venv 中 dev bench 的结果 `cmp` 一致，`bench.md` 一致（忽略 sha 行） |
| D4 | `docker run --rm reality-residual-agent rra run --scenario bias --seed 7 --compensation on` | 0 | — | 打印 `outputs/bias-seed7-on.json` |
| D5 | `docker run --rm reality-residual-agent rra s2-b3-dev --output-dir /tmp/o` | 0 | — | 末尾 `preservation_count: 582`、`authorization_count: 209` |
| D6 | `docker run --rm reality-residual-agent rra s2-b4-dev --replay --subset --output-dir /tmp/o` | 1 | — | `FileNotFoundError: /app/artifacts/s2/diag-d1g.json` |
| D7 | `docker run --rm reality-residual-agent python -m pytest -q` | 5 | — | `no tests ran` |
| D8 | `docker run --rm reality-residual-agent bash scripts/setup_meterless.sh` | 127 | — | `scripts/setup_meterless.sh: No such file or directory` |

Dockerfile 的 `CMD` 是 `rra bench`，镜像带有 `config/eval_seeds*.json`；不设 `RRA_SEED_FILE` 直接 `docker run reality-residual-agent` 会读冻结 eval seeds（按任务卡未执行）。

### 镜像中缺失的路径

镜像只 `COPY` 了 `requirements.txt`、`src`、`config`、`rra`；`.dockerignore` 排除 `.git`、`.venv`、`outputs`、`bench.*`。

| 缺失路径 | 影响 |
|---|---|
| `tests/` | 无法在镜像内跑 pytest（D7）；pytest 却被装进了镜像 |
| `scripts/` | 无法运行 `setup_meterless.sh`（D8）、`l6_*`、`l3_*`、`nemotron_*`、`d1*_diag` |
| `bridges/` | Meterless 桥（TypeScript）不在镜像；镜像也无 Node → Meterless 持久化/重放不可复现 |
| `artifacts/` | `s2-b4-dev`（含 `--replay`）依赖 `artifacts/llm_cache`、`artifacts/s2/diag-d1g.json`，镜像内失败（D6）；已提交的 `artifacts/{h1,s2,sponsor}` 证据文件也不可见 |
| `docs/`、README、`FAILURE_MODES.md`、`decisions.md` | 镜像内无文档 |
| 已提交的 `bench.json`/`bench.md` | 镜像内无 |
| `pyproject.toml`、`.git` | 无；`PYTHONPATH=/app/src` 代替，`rra` 可运行；receipt 的 `git_sha` 为 `unknown` |

镜像内可复现：`rra run`、dev-seed `rra bench`（D3）、`rra s2-b3-dev`（D5）。

## 3. 系统层功能逐项复现表（main @ 520b7cf）

| 功能 | 命令 | 外部服务/密钥 | 云 VM 实测 | 文档出处 |
|---|---|---|---|---|
| V0 run | `.venv/bin/python ./rra run --scenario bias --seed 7 --compensation on\|off` | 无 | 退出码 0，各 0.4 s | README 安装与运行 |
| dev bench | `RRA_SEED_FILE=…/dev_seeds.json ./rra bench`（临时目录） | 无 | 退出码 0，356.4 s（并发），见 §1.1 | README、`docs/EVAL_PROTOCOL.md` |
| 全量 pytest | `.venv/bin/python -m pytest -q -p no:cacheprovider` | 无（live 测试默认跳过） | `192 passed, 4 skipped in 233.11s`，退出码 0；运行时尚未装 Meterless，且与 Meterless 脚本并发。main 的全量运行未带 `-rs`；4 个跳过的具体位置取自 frz1 全量 `-rs` 输出（3 个 `tests/test_meterless_bridge.py`，1 个 `tests/test_packet_sources.py:48` "Zetaris live checks are opt-in"） | **README 未提 pytest**；`requirements.txt` 含 pytest，`pyproject.toml` 配置 `testpaths` |
| s2-b3-dev | `./rra s2-b3-dev --output-dir <scratchpad>` | 无（`LLM calls: 0`） | 退出码 0，95 s。`recoverable_success 0.1084 (84/775)`、`wrong_disposition 589`、`miss 96`、`unsafe_action 7`、`preservation_count 582`、`authorization_count 209`。与已提交 `artifacts/s2/b3-dev.md` 相比仅耗时/nproc/receipt-sha 行不同（已提交为 nproc=8，本机 4），指标行相同 | **README 未提**；`src/rra/cli.py`；设计见 `docs/P3_SYSTEM2_DESIGN.md` |
| s2-b4-dev `--replay`（全量） | `./rra s2-b4-dev --replay --output-dir <scratchpad>` | 理论上无（读 `artifacts/llm_cache`）；未设 `NVIDIA_API_KEY` | 缓存存在于克隆中，没有出现"缺失即非零退出"；单进程 ~100% CPU 运行 28 分钟后被后台上限终止，无输出文件 | **README 未提** |
| s2-b4-dev `--replay --subset` | `./rra s2-b4-dev --replay --subset --output-dir <scratchpad>` | 同上 | 退出码 0，676 s；`receipt_sha256: 39e3a9e3f8e2a30dde0dceb087241cf736db70a4be2f1b70927eb2d2d5cd866d`、`llm_calls: 62`、`serial_parallel_check.consistent: true`（`sample_pairs 12`）；写 `b4-dev.json`。`llm_calls` 计数含义未核实 | **README 未提** |
| Meterless 安装 | `bash scripts/setup_meterless.sh` | 访问 GitHub + npm；无密钥 | 退出码 0，4.4 s；`meterless=1742dec56a66e58eef9dda2d2b865823758ca8cd tsx=tsx v4.23.0 node=v22.22.0` | 仅脚本头注释 |
| Meterless 桥测试 | `RRA_METERLESS_LIVE=1 .venv/bin/python -m pytest -q tests/test_meterless_bridge.py` | 本地 Node；无密钥 | `25 passed in 6.12s`，退出码 0（不设 `RRA_METERLESS_LIVE`：`23 passed, 3 skipped`） | 测试文件 docstring |
| L6 持久化/重放 | `scripts/l6_persist_and_replay.py persist\|verify\|trail\|replay --run-tag t8 --out-root <scratchpad> --seeds 0 1 2` | 本地 Meterless 桥；无密钥 | 全部退出码 0（persist 5.7 s、verify 3.0 s、trail 0.6 s、replay 1.7 s）。verify：`all_ok: true`、`M1_roundtrip_mismatches: 0`、`M4_replay_match: 3`、`M8_hidden_key_hits: 0`；replay：`decisions_match: true`、`receipt_match: true` | 脚本 docstring |
| L6 B4 重放 | `scripts/l6_b4_meterless_replay.py` | 本地桥 + `artifacts/llm_cache`；无密钥 | 直接运行：退出码 1，`ModuleNotFoundError: No module named 'rra'`（脚本无 `sys.path.insert`，`l6_persist_and_replay.py` 有）。加 `PYTHONPATH=src`：退出码 0，68.8 s，脚本输出 `"status": "PASS"`（脚本原文）、`episode_count 20`、`decisions_equal 20`、`receipt_equal 20`、`live_llm_calls 0`。**该脚本改写了已跟踪文件 `artifacts/sponsor/meterless-persistence.json`**（克隆中 `git diff --stat`：54+/54−），已在克隆中 `git checkout --` 还原 | 脚本 docstring |
| Zetaris 路径 | **未运行**，仅列先决条件 | 需 `ZETARIS_TOKEN`（缺失时 `ZetarisClient` 抛 `ZETARIS_TOKEN is required`）；默认端点 `http://localhost:8888/api/v1.0`；`scripts/l3_zetaris_up.sh` 另需本机 Docker、名为 `zetaris_default` 的 Docker 网络（即已运行的 Zetaris 栈）、`postgres:16-alpine` 与 `python:3.12-alpine` 镜像、以及 `outputs/l3/sources`（由 `scripts/l3_export_sources.py` 生成）；`tests/test_packet_sources.py` 的 live 部分为 opt-in | 无 README 说明；仅 `docs/SPIKE_NOTES_20261019.md`、`P3_PREREG_ADDENDUM_02/03` 提及 |
| NVIDIA NIM | **未运行** | 需 `NVIDIA_API_KEY`；端点 `https://integrate.api.nvidia.com/v1`（`src/rra/llm/providers.py`） | 未执行 | README 未提 |

## 4. `feat/frz1-b3core` @ cb77107 与 main 的差异

方法：同一克隆检出该 sha，新建 venv，命令相同。

| 项 | main @ 520b7cf | frz1 @ cb77107 |
|---|---|---|
| `pytest -q` | `192 passed, 4 skipped`（233 s，退出码 0） | `200 passed, 4 skipped`（301 s，退出码 0；与 s2-b3-dev 并发）。4 个跳过：3×meterless live + 1×Zetaris live opt-in |
| `s2-b3-dev` 退出码/耗时 | 0 / 95 s | 0 / 140 s（与 pytest 并发） |
| `recoverable_success` | 0.1084 (84/775) | 0.1084 (84/775) |
| `wrong_disposition` | 589 | 588 |
| `miss` | 96 | 97 |
| `authorization_count` | 209 | 210 |
| `unsafe_action`（fast_layer_command）/ `b1_corrected_unsafe_action` | 7 (7) / 43 | 7 (7) / 43 |
| `preservation_regression_count` / `preservation_count` | 0 / 582 | 0 / 582 |
| System-2 calls / Verifier calls | 1961 / 27454 | 2009 / 28126 |
| 重新生成的结果与该分支已提交 `artifacts/s2/b3-dev.md` | — | 仅耗时/nproc/receipt-sha 行不同，指标行相同 |

补充：
- `git diff --stat 520b7cf cb77107` 涉及 17 个文件，含 `src/rra/evidence/episode.py`、`src/rra/runtime.py`、`src/rra/s2/fitter.py`、新增 `tests/test_frz1_reobserve.py`，同时该 diff 里 `docs/P3_PREREG_ADDENDUM_05.md` 显示为删除（分支落后于 main 的该文档合并；合并前需留意是否会带出该删除）。
- 该分支未修改 `README.md`、`README.en.md`、`Dockerfile`。

## 5. README 缺口清单（对照 Rule 6.3 / 6.4）

Rule 6.3（`docs/HACKATHON_RULES.md`）："A GitHub repository with all source code and a README covering setup, usage and dependencies."
Rule 6.4："A clear explanation of how Zetaris and Meterless were integrated, how Cursor was used during development, where NVIDIA technology contributes, and what was unique about your use of the sponsor technologies."

| 要求 | README 现状 | 缺口 |
|---|---|---|
| setup | venv + pip；写明需要 Python 3.12 | 未写 3.12 获取方式；未写 `rra` 非 3.12 时的报错；未提 Meterless 所需 Node 22 + git + npm |
| usage | `rra run`、`rra bench`、Docker | 无 `s2-b3-dev`、`s2-b4-dev`（`--replay`/`--subset`/`--nproc`）、`scripts/l6_*`、`scripts/l3_*`；无"仓库根目录运行 bench 会覆盖 `bench.md`"提示；无 pytest 命令及量级（192 passed / 4 skipped，约 4 分钟）；无各命令耗时（dev bench ≈ 6 分钟，s2-b4-dev 全量 replay > 28 分钟） |
| dependencies | 仅指向 `requirements.txt` 的安装命令 | 未列 numpy 固定版本、pydantic；未列 Node/npm、Meterless 固定提交 `1742dec`、Docker、Zetaris 栈、`NVIDIA_API_KEY`、`ZETARIS_TOKEN`；未区分"无需密钥即可复现"与"需要外部服务" |
| System-2 / B3 / B4 用法 | 无（仅一句"赛中 System-2 层应解决…"） | 缺：是什么、入口命令、输出文件、dev-only 说明、B4 replay 对 `artifacts/llm_cache` 的依赖 |
| 赞助技术路径 | 无 | 缺：Meterless（本地桥、固定提交、L6 persist/verify/replay）、Zetaris（先决条件、opt-in）、NVIDIA NIM（密钥、端点）、Cursor 使用说明（Rule 6.4） |
| eval-v3 状态 | 无；`docs/EVAL_PROTOCOL.md` 写 eval v3 "not generated / reserved for H5" | README 未说明 v3 未生成、v2 已冻结、`rra bench` 默认读冻结 seeds 的含义 |
| 已知局限 | v2 结果表、"combo 全部升级"一句、链接 FAILURE_MODES.md | 缺：System-2 当前 dev 指标（`recoverable_success 0.1084`）；Docker 镜像功能范围；Meterless/Zetaris 路径的外部依赖 |
| 容器 + 一条命令（Rule 6.2 旧版） | Docker 路径存在 | 默认 `CMD` 为 `rra bench`，需手动加 `RRA_SEED_FILE` 才不读 eval seeds；镜像只覆盖 V0 + dev bench + s2-b3-dev |
| 其他 | `README.md` 标题与开头为"V0 …不调用 LLM、网络、NIM 或 Jev" | 与仓库内已有的 S2/LLM/Meterless/Zetaris 代码并存，需要分层说明 V0 与 S2 |

## 6. 一条命令演示建议

草案见附录 B。已在 scratchpad 对全新克隆实跑一遍（`bash demo_s2.sh`，real 12.0 s，退出码 0；仅 dev seeds 0/1/2，无密钥）。它展示 Meterless 中持久化后的 System-2 决策链（动作、gate、fault 列表）与回放哈希比较，**不**展示恢复成功：ep-001 的 15 条决策基本是 `PAUSE_AND_REOBSERVE`，gate 为 `NO_VERIFIED_HYPOTHESIS` 或 `AMBIGUOUS`；ep-000 含一条 `UPDATE_MODEL_AND_REPLAN gate=COMMON_ACTION`，若想展示更多种类的动作，用 ep-000 信息量略大。

## 附录 A：建议的 README 修改稿（不改 README 本身）

### A.1 中文，建议加入 `README.md`（"安装与运行"之后）

~~~markdown
## 复现：无需密钥的路径

环境：Python 3.12（`rra` 在其他版本会直接退出）；Meterless 部分另需 git、Node 22、npm。

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q        # 约 4 分钟；未安装 Meterless 时有 4 个 live 测试跳过
.venv/bin/python ./rra run --scenario bias --seed 7 --compensation on
mkdir -p /tmp/rra-dev && cd /tmp/rra-dev    # bench 会在当前目录写 bench.json / bench.md
RRA_SEED_FILE=<repo>/config/dev_seeds.json <repo>/.venv/bin/python <repo>/rra bench   # 约 6 分钟，仅 dev seeds
```

不要在仓库根目录运行 `rra bench`：会覆盖已提交的 `bench.md`；不设 `RRA_SEED_FILE` 时读取冻结的 eval v2 seeds（2000–2099），仅用于最终评估。eval v3 尚未生成（见 docs/EVAL_PROTOCOL.md）。

## System-2 / B3 / B4（dev seeds）

| 命令 | 作用 | 外部依赖 | 参考耗时 |
|---|---|---|---|
| `./rra s2-b3-dev --output-dir <dir>` | B1-corrected 与 B3 在 dev seeds 上配对比较，写 `b3-dev.json/.md` | 无 | 约 1.5–2.5 分钟 |
| `./rra s2-b4-dev --replay --subset --output-dir <dir>` | B4 在 33 个 dev seed 子集上读 `artifacts/llm_cache` 回放 | 无密钥；需仓库中的 `artifacts/` | 约 11 分钟 |
| `./rra s2-b4-dev --replay --output-dir <dir>` | 全量 dev seeds 回放 | 同上 | 超过 28 分钟（未跑完） |

不带 `--replay` 的 `s2-b4-dev` 在缓存未命中时会调用 NVIDIA NIM，需要 `NVIDIA_API_KEY`。

## 赞助技术

- **Meterless**（本地参考实现，无需密钥）：`bash scripts/setup_meterless.sh`（固定提交 `1742dec…`）；`RRA_METERLESS_LIVE=1 .venv/bin/python -m pytest tests/test_meterless_bridge.py`；`scripts/l6_persist_and_replay.py persist|verify|trail|replay`。<补：持久化什么、如何被 System-2 决策链使用>
- **Zetaris**：需要 `ZETARIS_TOKEN`、`http://localhost:8888/api/v1.0` 上的 Zetaris 栈、名为 `zetaris_default` 的 Docker 网络；见 `scripts/l3_*`。<补：集成方式与独特之处>
- **NVIDIA NIM**：需要 `NVIDIA_API_KEY`；回放走 `artifacts/llm_cache`。<补：贡献点>
- **Cursor**：<补：开发过程中如何使用>

## 已知局限

- Docker 镜像只含 `src/`、`config/`、`rra`：可跑 `rra run`、dev bench、`s2-b3-dev`；不含 `tests/`、`scripts/`、`bridges/`、`artifacts/`，pytest、Meterless、B4 回放不能在镜像内复现。
- 默认 `CMD` 为 `rra bench`；运行镜像请设置 `RRA_SEED_FILE=/app/config/dev_seeds.json`。
- 当前 dev 上 B3：`recoverable_success 0.1084 (84/775)`（见 `artifacts/s2/b3-dev.md`）。
~~~

### A.2 英文，建议加入 `README.en.md`

~~~markdown
## Reproduce without keys

Requires Python 3.12 (`rra` exits otherwise); git, Node 22 and npm are needed only for the Meterless part.

    python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/python -m pytest -q                      # ~4 min; 4 live tests skip unless Meterless is installed
    mkdir -p /tmp/rra-dev && cd /tmp/rra-dev           # bench writes bench.json / bench.md into the cwd
    RRA_SEED_FILE=<repo>/config/dev_seeds.json <repo>/.venv/bin/python <repo>/rra bench   # ~6 min, dev seeds only

Do not run `rra bench` at the repo root: it overwrites the committed `bench.md`. Without `RRA_SEED_FILE` it reads the frozen eval v2 seeds. Eval v3 has not been generated (docs/EVAL_PROTOCOL.md).

System-2 / B3 / B4 (dev seeds): `./rra s2-b3-dev --output-dir <dir>` (~2 min, no keys);
`./rra s2-b4-dev --replay --subset --output-dir <dir>` (~11 min, reads `artifacts/llm_cache`, no keys).
Without `--replay`, cache misses call NVIDIA NIM and need `NVIDIA_API_KEY`.

Sponsor technologies: Meterless (local bridge, pinned commit, `scripts/setup_meterless.sh`, no key); Zetaris (`ZETARIS_TOKEN`, local Zetaris stack); NVIDIA NIM (`NVIDIA_API_KEY`); Cursor (<fill in>).

The Docker image contains `src/`, `config/` and `rra` only: `rra run`, dev bench and `s2-b3-dev` work; tests, scripts, bridges and artifacts are not in the image.
~~~

## 附录 B：一条命令演示草案

草案未写入仓库。scratchpad 路径：`/tmp/claude-0/-home-user-reality-residual-agent/b7643554-794b-5afa-801b-b68c35323914/scratchpad/demo/demo_s2.sh`

```bash
#!/usr/bin/env bash
# Draft one-command demo: System-2 decision chain on dev seeds only. No API keys, no external services.
# Usage (from repo root, after `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt`):
#   bash demo_s2.sh [OUT_DIR]
set -euo pipefail
OUT="${1:-$(mktemp -d)}"
PY=.venv/bin/python
L=scripts/l6_persist_and_replay.py
bash scripts/setup_meterless.sh                                    # pinned local Meterless bridge (needs git, node, npm)
$PY $L persist --run-tag demo --out-root "$OUT" --seeds 0 1 2 --workers 2   # run S2 episodes, persist decisions
$PY $L verify  --run-tag demo --out-root "$OUT" --seeds 0 1 2              # re-read stores in a fresh process
$PY $L trail   --run-tag demo --out-root "$OUT" --episode ep-001           # stored System-2 decision chain
$PY $L replay  --run-tag demo --out-root "$OUT" --episode ep-001           # re-execute and compare hashes
```

实跑（全新克隆，`bash demo_s2.sh <scratchpad>/demo/out`，退出码 0，real 12.0 s；npm 提示行与部分中间行省略）：

```
meterless=1742dec56a66e58eef9dda2d2b865823758ca8cd tsx=tsx v4.23.0 node=v22.22.0
persisted ep-000 decisions=12 store_bytes=298678 persist_s=0.42
persisted ep-001 decisions=15 store_bytes=338455 persist_s=0.46
persisted ep-002 decisions=12 store_bytes=272871 persist_s=0.39
verified ep-000 ok=True decisions=12
verified ep-001 ok=True decisions=15
verified ep-002 ok=True decisions=12
{ "B4": "DEFERRED: L5/D4", "M1_roundtrip_mismatches": 0, "M2_equal": 3, ...,
  "M4_replay_match": 3, "M5_identical": 3, "M8_hidden_key_hits": 0, "all_ok": true, "episodes": 3 }
ep-001: seed=1 case=['VELOCITY_OFFSET'] fault_family=None decisions=15 receipt_sha256=2b08878f105edfbc
  mem-1 #0 t=0.200 target=0 action=PAUSE_AND_REOBSERVE gate=NO_VERIFIED_HYPOTHESIS faults=[]
  ...
  mem-13 #12 t=0.500 target=10 action=PAUSE_AND_REOBSERVE gate=AMBIGUOUS faults=[]
  mem-14 #13 t=1.000 target=10 action=PAUSE_AND_REOBSERVE gate=AMBIGUOUS faults=[]
  mem-15 #14 t=0.300 target=11 action=PAUSE_AND_REOBSERVE gate=NO_VERIFIED_HYPOTHESIS faults=[]
{ "decisions": 15, "decisions_match": true, "episode_id": "ep-001", ...,
  "receipt_match": true,
  "replay_decisions_sha256": "4c221e49749bb9aa0b021268fe1b2f06f85e41882070e8061262e3d326620113",
  "replay_receipt_sha256": "2b08878f105edfbc44a67b4680375e333c63f9ef18690e5c99b9cd5b6f22388d" }
```

限制：`setup_meterless.sh` 需要访问 GitHub 与 npm；演示内容是决策链的存取与回放一致性，不含 fast layer 与 System-2 的结果对比；运行后克隆内 `git status` 为空（`verify` 未带 `--artifact`）。
