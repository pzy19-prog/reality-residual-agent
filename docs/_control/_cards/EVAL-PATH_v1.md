# 任务卡 EVAL-PATH — eval-v3 的 seed 生成脚本与各 baseline 运行入口（v1，不调用 NIM，不生成 eval-v3）
执行者：Luna（GPT-6 Luna，Codex CLI，WSL），新会话
仓库：pzy19-prog/reality-residual-agent；主库 ~/reality-residual-agent
工作区（由你创建）：~/reality-residual-agent-worktrees/eval-v3-path　分支 feat/eval-v3-path　基线 origin/main = 5a05f6d（PR #24 合并）
git 身份："Xifeng Ming" <274782819+pzy19-prog@users.noreply.github.com>；提交与 PR 不加任何 Claude/AI 署名行
测试框架：pytest；预期基线：5a05f6d 上 200 passed / 4 skipped
**本卡不调用 NIM、不得读取任何密钥；绝不在真实仓库路径下运行 seed 生成脚本，不创建 `config/eval_seeds_v3.json`，不打开 `config/eval_seeds*.json`**（测试一律用临时目录）。
派发已开放主库 .git 写权限。另有 FRZ-2A（worktree frz2-b4req，会改 `src/rra/eval/b4_dev.py`、`src/rra/llm/*`、`src/rra/evidence/episode.py`）和 A06（docs）并行执行，不要读写它们的 worktree。为减少冲突，本卡对 `b4_dev.py`、`b3_dev.py`、`cli.py` 只做最小改动（见 E3）。
依据：P3 §12.2、§14、§15、§18.1；EVAL_PROTOCOL 规则 1–3；A04 §4；A05 §3.1、§4；**A06 草案**（卡 `_cards/A06_v1.md` K3，正在另一会话写成 `docs/P3_PREREG_ADDENDUM_06.md`；本卡实现其 §1、§2.3、§3.3–3.5 的代码部分）。

## §0.0 Bootstrap
```
cd ~/reality-residual-agent && git fetch origin
git merge-base --is-ancestor 5a05f6d origin/main || 停
git ls-remote --exit-code origin refs/heads/feat/eval-v3-path && 停
git worktree add -b feat/eval-v3-path ~/reality-residual-agent-worktrees/eval-v3-path origin/main
cd ~/reality-residual-agent-worktrees/eval-v3-path
git config user.name "Xifeng Ming"; git config user.email "274782819+pzy19-prog@users.noreply.github.com"
/usr/bin/python3.12 -m venv .venv && .venv/bin/pip install -q -r requirements.txt pytest
PY=$PWD/.venv/bin/python
PYTHONPATH=$PWD/src $PY -c "import rra;print(rra.__file__)"   # 指向本 worktree
PYTHONPATH=$PWD/src $PY -m pytest -q -p no:cacheprovider      # 记录基线
test ! -e config/eval_seeds_v3.json || 停
```

## §0 实测核对表（控制会话 2026-10-24 读 origin/main 5a05f6d）
| # | 前提 | 实测值 | 复核命令 |
|---|---|---|---|
| Q1 | 没有 eval-v3 路径 | CLI 只有 run、bench、s2-b3-dev、s2-b4-dev（`src/rra/cli.py:124-137`）；`run_b3_dev` 写死 `config/dev_seeds.json`（`b3_dev.py:205`）；`run_b4_dev` 写死 dev seed 与 diag 子集（`b4_dev.py:185-190`）；`holdout.py:41-58` 只做禁止检查 | `grep -n "dev_seeds" src/rra/eval/*.py` |
| Q2 | 场景分配 | `b3_dev._run_seed((index, seed))`：case = `index % 19`（14 个组合结构 + 5 个 fault family），同时跑 B1 corrected 与 B3 并计分（`b3_dev.py:100-125`）；`b4_dev._realization` 同规则 | `sed -n 100,125p src/rra/eval/b3_dev.py` |
| Q3 | B2 | 冻结参数在 `artifacts/h1/b2-grid.json` 的 `selected`（T 1.15、R 2.15）；`run_episode` 有 `fast_time_limit`、`fast_residual_threshold` 参数（`episode.py:58-59`）；仓库里没有在 v3 实现上逐 episode 跑 B2 并计分的函数（`b2_grid.py` 只做 V0 场景标定） | `grep -n "def run_b2\|fast_time_limit" -r src` |
| Q4 | B1-legacy | `src/rra/eval/dev_diagnostics.py:21` `run_b1_diagnostic(mode, seeds)`；已提交 `artifacts/h1/b1-legacy-dev.json` | `sed -n 1,60p src/rra/eval/dev_diagnostics.py` |
| Q5 | 禁止检查测试 | `tests/test_holdout.py:14-19` 断言 `config/eval_seeds_v3.json` 不存在；seed 提交之后这条会失败 | `sed -n 1,25p tests/test_holdout.py` |
| Q6 | B4 读穿缓存 | `_ReadThroughProvider`：先查缓存、未命中再 live 调用，401/403 停（`b4_dev.py:29-58`）；缓存按请求写入 `artifacts/llm_cache` | `sed -n 29,58p src/rra/eval/b4_dev.py` |

## §1 已裁决
- E1 **seed 生成脚本** `scripts/gen_eval_v3_seeds.py`（A06 §1.1–1.3）：
  - 用 `secrets.SystemRandom().sample(range(10000, 2147483647), 100)` 生成 100 个不重复整数，保持抽样顺序（顺序即 index，决定 case）。
  - 写 `config/eval_seeds_v3.json`：`{"schema_version":"rra.eval-seeds.v3","role":"eval_v3","count":100,"range":[10000,2147483647],"generator":"secrets.SystemRandom().sample","freeze_tag":<tag>,"freeze_commit":<sha>,"seeds":[…]}`。
  - 必填参数 `--freeze-tag <tag>`；以下任一不满足就非零退出且不写文件：tag 存在且 `HEAD` 等于 tag 指向的提交；工作区干净；目标文件不存在。
  - 标准输出只打印 count 和文件 sha256；任何日志、异常信息都不得包含 seed 值。
  - 支持 `--root <dir>` 只供测试使用（测试在临时 git 仓库里跑）。
- E2 **eval 运行模块** `src/rra/eval/final_v3.py` + CLI 子命令 `rra eval-v3 <row>`，row ∈ `b1b3`、`b2`、`b1-legacy`、`b4`：
  - seed 来源：默认 `config/eval_seeds_v3.json`（role eval_v3）；`--seeds-file <path> --role dev` 只用于在 dev 上验证（V2）。index = 文件中的位置，case = `index % 19`。
  - eval_v3 角色下的守卫：必填 `--freeze-tag`；`git diff --name-only <tag> HEAD` 只允许 `config/eval_seeds_v3.json` 和 `artifacts/eval_v3/` 下的文件；工作区干净；否则非零退出。
  - `b1b3`：对每个 seed 调用与 `b3_dev._run_seed` 完全相同的逻辑（直接复用，不复制），输出 B1 corrected 与 B3。
  - `b2`：`run_episode(config, seed, True, terminal_monitoring="corrected", realization=…, fast_time_limit=T, fast_residual_threshold=R)`，T、R 从 `artifacts/h1/b2-grid.json` 的 `selected` 读取（不写死），用 `score_against_b1_denominators(..., b1)` 计分，与 B1 同一 realization；receipt 记录 b2-grid.json 的 `receipt_sha256`。
  - `b1-legacy`：复用 `run_b1_diagnostic("legacy", …)` 的语义；如果它不能按 `index % 19` realization 跑任意 seed 列表，就最小改动使其可以，并在 dev 上证明与 `artifacts/h1/b1-legacy-dev.json` 一致（V2）。
  - `b4`：调用 `run_b4_dev`，参数见 E3；`--replay`（只读缓存，生成计分 artifact）或 `--live`（读穿缓存，需要 NVIDIA_API_KEY，本卡不运行）；`--max-live-calls`（默认 1600，A06 §3.3），达到上限即停止并写出不完整状态，非零退出。中断后重跑能从缓存续跑。
  - 输出到 `--output-dir`（默认 `artifacts/eval_v3/`）：每个 row 一个 `<row>.json` 和 `<row>.md`。receipt 含 schema、row、seed 文件 sha256、seed 数、各 case 的 episode 数、metrics、`runtime_versions`（不进哈希，A05 §4.1）、git sha（不进哈希，同 FRZ-1 F7）、`receipt_sha256`。
- E3 **对现有文件的最小改动**（FRZ-2A 在改同一批文件，冲突要小）：
  - `run_b3_dev`、`run_b4_dev` 只增加一个可选关键字参数 `seeds_path: Path | None = None`（为 None 时行为与现在逐字节相同；不为 None 时从该文件读 seeds 与 index，`subset` 必须为 False，`seed_identity.path` 记录该路径）。不改函数体的其他部分。
  - `cli.py` 只追加 `eval-v3` 子命令的解析和分派。
  - 如果 FRZ-2A 先合并导致冲突：把 origin/main merge 进本分支（merge 提交，不 rebase），解决冲突后重跑全部验收。
- E4 **禁止检查测试**（Q5）：改 `tests/test_holdout.py`，使其在 seed 提交前后都成立：文件不存在时保持现有断言；文件存在时断言它是由一个只改动该文件的提交引入的、schema 与 count 正确、seed 不重复且在范围内（只做程序断言，不打印值）。`artifacts/h1/final-eval-v3-prohibition.json` 作为 H1 历史回执不改。
- E5 **B4 调用量估计**（不联网）：`rra eval-v3 b4 --estimate`：用只记录请求、返回空提案的假 proposer 跑一遍，输出去重后的请求数；只允许在 `--role dev` 下运行（eval_v3 角色下拒绝，避免在冻结前接触 eval 数据）。
- E6 不改：docs、requirements、verifier/门控/授权、DSL、评估器计分规则、`episode.py`、`src/rra/llm/*`、已提交 artifacts。
- E7 交付：分若干提交；push；`gh pr create --base main --head feat/eval-v3-path --title "EVAL-PATH: eval-v3 seed generation and baseline runners"`。不合并。

## §2 验收
- V1 pytest 全绿，计数 = 基线 + 新增测试（列出测试名）。新增测试至少覆盖：E1 的三个拒绝条件、输出不含 seed 值、100 个不重复且在范围内（临时仓库）；E2 守卫（tag 后有 src 改动时拒绝）；`--max-live-calls` 达到上限时停止（假 provider）；E4 前后两种状态
- V2 **dev 等价**（关键）：`rra eval-v3 b1b3 --seeds-file config/dev_seeds.json --role dev --output-dir /tmp/ev-dev` 的逐 seed B1、B3 receipt 哈希与 `rra s2-b3-dev --output-dir /tmp/b3-dev` 相同 130/130，metrics 相同；`b1-legacy` 与 `artifacts/h1/b1-legacy-dev.json` 的逐 seed 结果一致（写明比较口径）；`b4 --replay --role dev`（用 diag 子集文件）与 `s2-b4-dev --replay --subset` 一致，或在缓存失效时两者都在同一个请求上报 ReplayCacheMiss（写明）
- V3 `b2 --role dev` 在 dev 130 seed 上的 metrics 表（只报告，不设门槛）
- V4 `b4 --estimate --role dev`：全 dev 与 diag 子集的去重请求数
- V5 `config/eval_seeds_v3.json` 不存在；`git log --all -- config/eval_seeds_v3.json` 为空
- V6 身份、密钥、范围：作者 Xifeng Ming noreply；`nvapi-` 计数 0；`git diff --name-only origin/main...HEAD` 不含 docs、requirements、episode.py、src/rra/llm/
- V7 PR 的 CI：test 和 determinism 均 pass

## §4 自主权
实现细节自行处理（模块结构、并行方式、markdown 版式）。硬停只限：§0 不符；需要改 E6 范围；V2 的 B1/B3 等价不成立且原因不在本卡新代码；任何步骤需要读取或生成真实的 eval-v3 seed。

## §5 失败报告
`~/reality-residual-agent-worktrees/_reports/REPORT_D4_EVALPATH_nogo.md`，给出 sha256。

## §6 收尾
报告写 `~/reality-residual-agent-worktrees/_reports/REPORT_D4_EVALPATH.md`（§0、E1–E5 改动及代码行、V1–V7、PR 编号与 head）。**先定稿再算哈希**：末行写 `Report SHA-256 (body = content before this line, trailing whitespace stripped, plus one "\n"): <sha>`，并追加到 `ARCHIVE_D3.sha256`。不合并，不删 worktree 或分支。
