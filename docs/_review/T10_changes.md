# T10 变更说明：README / Docker / l6_b4 脚本

- 分支：`cloud/t10-readme-docker`，基于 main `349d1e68ebf196f9f3b25d5e2f6746b6029401fe`（与任务卡一致）
- 输入：`cloud/t8-repro-check` @ `ce3e950fb13defa138fd90b83422f5f74be87a0a` 的 `docs/_review/T8_repro_check.md`
- 执行环境：Claude Code 云会话（Linux，4 核，Python 3.12.3 venv，Node v22.22.0，Docker 29.9.2，dockerd 手动启动）
- 未改动 `src/`、`tests/`、`config/`、`docs/`（本文件除外）、`artifacts/`。未打开 `config/eval_seeds*.json`；未运行默认 `rra bench`；未设置或使用任何密钥。

## 未完成项

- 预算未触及上限。以下是未做到的事：
  1. 镜像内没有 `git`（见 §2），镜像内 pytest 有 4 个失败。原因：沙箱出口代理不允许访问 Debian 软件源（`apt-get update` 得到 403），Docker Hub 拉取 `python:3.12` 返回 429，因此无法在本沙箱验证"装 git 的镜像"，没有提交未经验证的 Dockerfile。
  2. `rra s2-b4-dev --replay --subset` 与 `scripts/l6_b4_meterless_replay.py` 在 `349d1e6` 上均以 `ReplayCacheMiss` 退出（见 §2、§3），原因未核实。
  3. 全量 `rra s2-b4-dev --replay` 未再运行（T8 已记录 28 分钟未完成）。

## 1. 提交 1 — README（`README.md`、`README.en.md`、本文件）

| 变更 | 对应 T8 缺口 |
|---|---|
| 开头改为分层说明：V0 基线 / System-2 层 / 赞助技术接入；保留 V0 架构一节 | §5「其他」；§1.3 第 11 条 |
| 新增「依赖」表（Python 3.12 及获取方式、固定版本包、git/Node 22/npm、Meterless 固定提交、Docker、`NVIDIA_API_KEY`、`ZETARIS_TOKEN`） | §5 setup、dependencies |
| 「安装与运行」补 `--compensation off`、`rra run` 输出位置、`rra bench` 输出位置；加提示：仓库根目录运行 `rra bench` 会覆盖已提交的 `bench.md`/`bench.json`；`RRA_SEED_FILE` 用绝对路径 | §5 usage；§1.1 偏差；§1.3 第 2–4、10 条 |
| 新增「无需密钥即可复现」命令表（含 pytest 命令与量级） | §5 usage、「容器 + 一条命令」 |
| 新增「System-2 / B3 / B4 用法」：`s2-b3-dev`、`s2-b4-dev`（`--replay`/`--subset`/`--nproc`）、`--output-dir` 提醒（默认值是 `artifacts/s2`） | §5「System-2 / B3 / B4 用法」 |
| 新增「赞助技术」：Meterless（Node 22、`setup_meterless.sh`、`l6_persist_and_replay.py`）、Zetaris（opt-in 先决条件）、NVIDIA NIM（`NVIDIA_API_KEY`）、Cursor 占位 | §5「赞助技术路径」 |
| Docker 一节：命令改用 dev 种子、列出镜像内外范围 | §2；§5「容器 + 一条命令」；§1.3 第 5、6 条 |
| 新增「eval v3 状态」（未生成，无数字，链接协议文档与 Addendum 06） | §5 eval-v3 状态 |
| 新增「已知局限」 | §5 已知局限 |
| 英文版补入中文版独有内容：问题与架构、`off` 命令、receipt/bench 输出位置、完整 14 行 eval v2 表、Docker 保留输出命令、旧 combo MAE 说明 | §1.3 第 1–5、7–9 条 |
| 删去 V0 描述中的形容词，只保留"固定阈值""升级" | 措辞约束 |
| `bench.json` 链接保留（该文件已被跟踪，尽管 `.gitignore` 列了它） | — |

dev 数字来源：`artifacts/s2/b3-dev.md`（recoverable success 0.1084，84/775；wrong disposition 588；miss 97；unsafe action 7；preservation regression 0/582），已用容器内 `rra s2-b3-dev` 复现一致（§2）。README 中没有 eval v3 数字。

## 2. 提交 2 — Docker（`Dockerfile`、`.dockerignore`）

变更：
- 增加 `ENV RRA_SEED_FILE=/app/config/dev_seeds.json`；`CMD` 改为 `rra bench --output-dir /tmp/rra-out`（dev 种子，输出写到容器临时目录）。
- 增加 `COPY`：`pyproject.toml`、`tests/`、`scripts/`、`bridges/`、`artifacts/h1`、`artifacts/llm_cache`、`artifacts/s2/diag-d1g.json`。
- `.dockerignore` 增加 `bridges/meterless/vendor`、`bridges/meterless/node_modules`（`bench.md` 原本已在其中）。
- 未放进镜像（写在 README「镜像外运行」）：Meterless 运行时（需要 Node 与联网安装）、`scripts/l6_*` 的运行、Zetaris 路径、全量 `artifacts/`（约 155 MB）、`docs/`。
- `config/eval_seeds*.json` 仍在镜像中：`src/rra/cli.py:103` 在 `_run_bench` 里读取 `eval_seeds_v2.json`，仅用于给结果标注 `seed_role`。`src/` 冻结，未改。默认 `CMD` 的输入种子集合是 dev 种子（容器内 `RRA_SEED_FILE=/app/config/dev_seeds.json`，读出 130 个 seed；stdout 表中 combo 升级数为 130，而 eval v2 集合只有 100 个 seed）。
- 对应 T8：§2 D1/D4–D8、「镜像中缺失的路径」、「默认 CMD 读 eval seeds」。

为了在本沙箱构建，使用 scratchpad 里的副本 Dockerfile，仅追加两行（`COPY ca.crt /ca.crt`、`ENV PIP_CERT=/ca.crt`，证书为沙箱出口代理 CA）。提交的 Dockerfile 不含代理 CA，也没有关闭 TLS 校验。去掉这两行后副本与提交版逐行一致（`diff` 确认）。

实测（镜像 `rra-t10`，上述副本构建；镜像大小 337185902 B ≈ 337 MB；T8 记录的旧镜像为 317 MB）：

| 命令 | 退出码 | 耗时 | 说明 |
|---|---:|---:|---|
| `docker build`（冷缓存，含 pip 安装；添加 `tests/` 等之后的首次构建，尚未含 `artifacts/h1`） | 0 | 68 s | 之后增量重建约 9 s |
| `docker run --rm rra-t10`（默认 CMD） | 0 | 416 s | stdout 为 14 行 bench 表（dev 种子）；与其他命令间隔运行 |
| `docker run --rm rra-t10 rra run --scenario bias --seed 7 --compensation on` | 0 | 约 1 s | 打印 `outputs/bias-seed7-on.json` |
| `docker run --rm rra-t10 rra s2-b3-dev --output-dir /tmp/o` | 0 | 104 s、122 s（两次） | `recoverable_success 0.10838709677419354`、`recoverable_challenge_success_count 84`、`recoverable_challenge_count 775`、`wrong_disposition 588`、`miss 97`、`unsafe_action 7`、`preservation_count 582`、`authorization_count 210`，与已提交 `artifacts/s2/b3-dev.md` 的指标行一致 |
| `docker run --rm rra-t10 python -m pytest -q -rs` | 1 | 262 s | `4 failed, 195 passed, 5 skipped`。4 个失败均为 `FileNotFoundError: [Errno 2] No such file or directory: 'git'`（`test_b1_diagnostic_uses_common_v3_framework_and_mode`、`test_omniscient_dev_upper_bound_is_exactly_frozen_six_scenarios`、`test_final_eval_v3_seed_realization_is_absent` 等调用 `git rev-parse`/`git ls-files` 的测试）。镜像没有 `git`，也没有 `.git` |
| `docker run --rm rra-t10 rra s2-b4-dev --replay --subset --output-dir /tmp/o` | 1 | 100 s | `rra.llm.providers.ReplayCacheMiss: replay cache miss: /app/artifacts/llm_cache/566dfc849da95fc8719d26b0d4deb9d5e2676aff70b6191af462a115246be711.json` |

第一次构建的镜像（未含 `artifacts/h1`）pytest 为 `4 failed, 195 passed` 且其中一个失败是缺 `artifacts/h1/omniscient-upper-bound.json`；补 `COPY artifacts/h1` 后剩 4 个均为缺 `git`。

试过的 git 方案：在 Dockerfile 里 `apt-get install git` 并在构建时 `git init`。本沙箱构建时 `deb.debian.org` 被出口代理拒绝（HTTP 403 / 405），无法验证，未提交。拉取 `python:3.12` 完整镜像（带 git）被 Docker Hub 返回 `429 Too Many Requests`。所有者可在可联网的机器上尝试这个方案；它不影响其他命令。

## 3. 提交 3 — `scripts/l6_b4_meterless_replay.py`

变更：
- 增加 `sys.path.insert(0, str(ROOT / "src"))`（与 `scripts/l6_persist_and_replay.py` 相同做法）；不设 `PYTHONPATH` 可导入 `rra`（对应 T8 §3「L6 B4 重放」第一个问题）。
- 增加 `--output`，默认 `outputs/l6/meterless-persistence.json`；写回已跟踪文件需显式 `--output artifacts/sponsor/meterless-persistence.json`（对应 T8 §3 的"改写已跟踪文件"问题）。输入仍读已跟踪的 `artifacts/sponsor/meterless-persistence.json`。
- 提交信息注明：按本地意见，本提交在 eval 结果提交之后再合并。

实测：
- `349d1e6` 上、不设 `PYTHONPATH`、默认输出：能导入 `rra`，运行 5 秒后以 `ReplayCacheMiss`（同一个 `566dfc84…` 请求）退出，退出码 1；未写入任何文件，`git status` 中 `artifacts/` 无改动。改动前的脚本（`PYTHONPATH=src`）在同一提交上同样 `ReplayCacheMiss`，所以该失败与本提交无关；`src/` 在 `520b7cf..349d1e6` 之间有改动，缓存缺失的原因未核实。
- `520b7cf` 的 `git archive` 副本（含本提交的脚本、同一份 Meterless vendor）：不设 `PYTHONPATH`，退出码 0，74 s，stdout `status PASS`（脚本原文）、`episode_count 20`、`decisions_equal 20`、`receipt_equal 20`、`live_llm_calls 0`；写出 `outputs/l6/meterless-persistence.json`，已跟踪文件逐字节未变。该副本里的 `--output` 取默认值；显式传 `--output` 的写入分支未单独运行。

## 4. 其他实测（`349d1e6`，云 VM，宿主 venv）

| 命令 | 结果 |
|---|---|
| `python -m pytest -q -p no:cacheprovider -rs` | 退出码 0，`200 passed, 4 skipped in 257.31s`；4 个跳过：3 个 `tests/test_meterless_bridge.py`（需 Node/Meterless/`RRA_METERLESS_LIVE=1`）、1 个 `tests/test_packet_sources.py:48`（Zetaris live 为 opt-in） |
| `bash scripts/setup_meterless.sh` | 退出码 0，4 s；`meterless=1742dec56a66e58eef9dda2d2b865823758ca8cd tsx=tsx v4.23.0 node=v22.22.0` |
| `RRA_METERLESS_LIVE=1 python -m pytest -q tests/test_meterless_bridge.py` | 退出码 0，`25 passed in 6.60s` |
| `scripts/l6_persist_and_replay.py persist/verify/trail/replay --run-tag t10 --out-root <scratch> --seeds 0 1 2`（trail/replay 用 `--episode ep-001`） | 全部退出码 0（6 s、3 s、1 s、2 s）；verify `all_ok: true`；replay `decisions_match: true`、`receipt_match: true` |

## 5. 留给所有者填写或核对的占位

1. `README.md`、`README.en.md`：`[所有者填写：Cursor 使用方式（Rule 6.4）]`（赞助技术 → Cursor）。
2. `[待 FRZ-2A 合并后核对]` / `[pending FRZ-2A merge — to be checked]`：System-2 层一节（证据包补全、§3.4 取整、提示词 v2、回执字段）。
3. `[待 EVAL-PATH 合并后核对]` / `[pending EVAL-PATH merge — to be checked]`：System-2 用法一节末尾（`rra eval-v3` 子命令与种子生成脚本）和「eval v3 状态」一节。
4. 核对：README 里 FRZ-2A / EVAL-PATH 合并后 `s2-b3-dev` 的 dev 数字（`b3-dev.md` 当前值：84/775、588、97）是否变化。
5. 核对：`349d1e6` 上 B4 回放缓存缺失（`566dfc84…`）的原因，以及 `s2-b4-dev --replay --subset` 与 `l6_b4_meterless_replay.py` 的退出状态；解决后更新 README 两处说明。
6. 核对/决定：镜像是否需要 `git`（pytest 4 个失败）；本沙箱无法验证 apt 方案。
7. README 中的耗时（dev bench 约 6 分钟、`s2-b4-dev --replay --subset` 在 `520b7cf` 约 11 分钟、全量回放 >28 分钟）来自 T8，且部分当时与其他命令并发。
8. 提交 3 按本地意见在 eval 结果提交之后再合并。
