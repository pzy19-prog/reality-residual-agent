# 任务卡 CI-PY312 — 项目统一改用 Python 3.12，修复 main 的 CI（v1）
执行者：Luna（GPT-6 Luna，Codex CLI，WSL），新会话
仓库：pzy19-prog/reality-residual-agent；主库 ~/reality-residual-agent
工作区（由你创建）：~/reality-residual-agent-worktrees/ci-py312　分支 ci/python-312　基线 origin/main = 54f5006（PR #21 合并提交）
git 身份："Xifeng Ming" <274782819+pzy19-prog@users.noreply.github.com>；提交与 PR 不加任何 Claude/AI 署名行
测试框架：pytest（pyproject：testpaths=["tests"]，pythonpath=["src"]）。基线：54f5006 上 187 passed / 4 skipped（2ff7a6b 实测值；54f5006 只多一个 .md 文件）
**本卡不调用 NIM、不需要也不得读取任何密钥**（不运行 pass）
派发说明：本次派发已用 `--add-dir ~/reality-residual-agent/.git` 开放主库 .git 写权限（控制会话已实测 fetch 与 worktree 操作可行），直接在主库执行 git 命令，不要另建克隆。

## §0.0 Bootstrap
```
cd ~/reality-residual-agent
git fetch origin
test "$(git rev-parse --short=7 origin/main)" = "54f5006" || 停（报告新 SHA；如果只多了 PR #20 的合并提交，可以以新 SHA 为基线继续，并在报告中注明）
git ls-remote --exit-code origin refs/heads/ci/python-312 && 停（远端已有同名分支）
git worktree add -b ci/python-312 ~/reality-residual-agent-worktrees/ci-py312 origin/main
cd ~/reality-residual-agent-worktrees/ci-py312
git config user.name "Xifeng Ming"; git config user.email "274782819+pzy19-prog@users.noreply.github.com"
PY=/home/mxfclaw/reality-residual-agent-worktrees/l5a-hygiene/.venv/bin/python
PYTHONPATH=$PWD/src $PY -c "import sys,numpy,rra;print(sys.version.split()[0],numpy.__version__,rra.__file__)"   # 须 3.12.3 2.5.4 …/ci-py312/src/rra/__init__.py
PYTHONPATH=$PWD/src $PY -m pytest -q -p no:cacheprovider   # 须 187 passed / 4 skipped（若基线含 PR #20，须 192 passed / 4 skipped）
```

## §0 实测核对表（控制会话 2026-10-23 实测，任一不符 → 停并报告）
| # | 前提 | 实测值 | 复核命令 |
|---|---|---|---|
| Q1 | main 的 CI 自 PR #19 起失败 | run 39947570304（PR #19 合并）、39957209613（PR #21 合并）都是 failure；PR #18 及更早为 success | `gh run list --branch main --limit 5` |
| Q2 | 失败原因 | setup-python 3.11 + `requirements.txt` 的 `numpy==2.5.4` → `No matching distribution found for numpy==2.5.4`（2.5.x 要求 Python>=3.12） | `gh run view 39959169115 --log-failed \| grep -i numpy` |
| Q3 | 3.11 出现的位置（artifacts 除外） | `.github/workflows/ci.yml:17,30`（python-version "3.11"）；`rra:7-8`（`sys.version_info[:2] != (3, 11)` → SystemExit）；`Dockerfile:1`（python:3.11-slim）；`README.md:21,24`；`README.en.md:7,10`；`decisions.md:5,23`（历史记录） | `git grep -n "3\.11" -- ':!artifacts'` |
| Q4 | 本机环境 | python 3.12.3 / numpy 2.5.4；D3 以来所有 receipt 的 runtime_versions 都是这个组合 | 同 §0.0 |
| Q5 | Dockerfile 未被运行中的容器使用 | rra-l3-ops 用的是 `python:3.12-alpine` 镜像，不是用这个 Dockerfile 构建的 | `docker inspect rra-l3-ops --format '{{.Config.Image}}'` |
| Q6 | 远端无 ci/python-312 | `git ls-remote origin 'refs/heads/ci/*'` 为空 | 同左 |

## §1 已裁决
- C1 项目运行时统一为 **Python 3.12**（本机 3.12.3）。不降级 numpy：D3 以来的 receipt 都基于 3.12.3 / 2.5.4。
- C2 改动范围（只改这些）：
  - `.github/workflows/ci.yml`：两个 job 的 `python-version` 都改为 `"3.12.3"`。如果 CI 上 setup-python 拿不到 3.12.3，改为 `"3.12"`，并在报告里写明原因和 CI 实际使用的补丁版本。其他步骤不动。
  - `rra`（启动脚本）：版本检查改为 `sys.version_info[:2] != (3, 12)`，提示文字改为 `"RRA requires Python 3.12"`。
  - `Dockerfile`：`FROM python:3.12-slim`。
  - `README.md` / `README.en.md`：安装说明改为 Python 3.12（`python3.12 -m venv .venv`）。
  - `decisions.md`：在表格末尾追加一行（不改历史行）：日期 2026-10-23；问题"运行时 Python 版本"；决定"统一为 Python 3.12（本机 3.12.3），CI/启动脚本/Dockerfile/README 同步；3.11 时期的历史结果保留为历史记录"；理由"requirements 钉 numpy==2.5.4（L5 D10），该版本要求 Python>=3.12；PR #19 合并后 CI 因此失败"。
- C3 不改：`requirements.txt`、`src/`、`tests/`、`artifacts/`、`docs/`（预注册文件一律不动）、`.cursor/`。
- C4 交付：一个提交（消息 `ci: move runtime to Python 3.12`）；`git push -u origin ci/python-312`；`gh pr create --base main --head ci/python-312 --title "ci: move runtime to Python 3.12"`，正文列出 Q1–Q3 和改动清单。不合并。

## §2 验收（数字写进报告）
- V1 `git diff --name-only origin/main...HEAD` 恰好是 C2 列出的 6 个文件（ci.yml、rra、Dockerfile、README.md、README.en.md、decisions.md）。
- V2 `git grep -n "3\.11" -- ':!artifacts' ':!decisions.md'` 无命中；decisions.md 只有新增行（`git diff origin/main -- decisions.md` 只含 `+` 行）。
- V3 本地复现 CI 两个 job（用 $PY，3.12.3）：
  - `PYTHONPATH=$PWD/src $PY -m pytest -q -p no:cacheprovider`：通过数与 §0.0 基线相同
  - `A=$(mktemp -d); B=$(mktemp -d); RRA_SEED_FILE=config/dev_seeds.json $PY ./rra bench --output-dir $A; RRA_SEED_FILE=config/dev_seeds.json $PY ./rra bench --output-dir $B; diff -u $A/bench.json $B/bench.json`：两次 exit 0，diff 为空；记录耗时
- V4 PR 的 CI：`gh pr checks <PR>` 中 test 和 determinism 两项都是 pass（CI 跑完后再写报告；超过 30 分钟仍未结束，就写当时的状态和 run URL）。
- V5 身份与署名：author/committer 均为 Xifeng Ming noreply；提交消息与 PR 正文 `grep -ciE 'co-authored|claude|generated with'` = 0。

## §4 自主权
环境问题自行解决。硬停只限：§0 Q1–Q6 不符；远端已有同名分支；基线测试不符；需要修改 C3 列出的任何路径；CI 在 3.12 下因与本卡无关的原因失败（报告失败的步骤和日志最后 50 行，不要自行修代码）。

## §5 失败报告
写 `~/reality-residual-agent-worktrees/_reports/REPORT_D3_CI312_nogo.md`：已完成步骤、失败命令原文、输出最后 50 行、判断；给出 sha256。

## §6 收尾
报告写 `~/reality-residual-agent-worktrees/_reports/REPORT_D3_CI312.md`：§0 复核值、V1–V5 逐项结果和数字、PR 编号与 head SHA。**先定稿再算哈希**：末行写 `Report SHA-256 (body = content before this line, trailing whitespace stripped, plus one "\n"): <sha>`，并追加到 `ARCHIVE_D3.sha256`；写完哈希后不得再改正文。不合并，不删 worktree 或分支。
