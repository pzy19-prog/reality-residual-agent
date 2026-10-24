# 续接指令 — 合并核对 + 收尾卡 + N1/证据包卡（2026-10-23 夜）

## 续接 prompt（新会话整段粘贴）
> 你是 RRA 控制会话。先按 CLAUDE.md "开工必做"执行（STATE.md、本目录 handoff/RESUME_2026-10-23_MERGE-CLEANUP.md 全文、fetch 核对、指南书 current），再按本文"执行步骤"执行。不运行任何 pass 命令。

## 上一会话已完成（详见 STATE.md）
- A04 出卡 → Luna 执行 → PR #21（head 3319655，只新增 docs/P3_PREREG_ADDENDUM_04.md）→ 审查 PASS（`_reviews/PR21.md`）
- R1 修复 → PR #20 新 head c852566 → 审查 PASS（`_reviews/PR20_R1.md`）
- 两个 PR 都交给用户合并：#21 直接合；#20 先 `gh pr edit 20 --base main`，核对 files 后再合

## 分工规则（用户已定，沿用）
- 机械复跑交给 Agent(model="sonnet") 子代理，给完整命令清单；判断、PASS/FAIL、出卡由主会话负责
- 子代理复跑算复跑证据，不算独立审查
- 派发 Luna：命令以 `codex exec` 开头、全用绝对路径，run_in_background
- **新教训**：codex 沙箱里主库 `.git` 只读。卡里的 bootstrap 不能让 Luna 在主库执行 `git fetch` 或 `git worktree add`。做法二选一：控制会话先建好 worktree（这算控制会话写仓库元数据，需要先问用户同不同意），或者派发前实测 `--add-dir ~/reality-residual-agent/.git` 是否可行
- deny_guard hook 会拦截 Bash 命令文本中的 "gh pr merge" 字样；改文件时用 Edit/Write 工具

## 执行步骤
### 1. 核对合并状态
- `gh pr view 20`、`gh pr view 21`：是否 MERGED，merge commit 是什么；origin/main 的新 SHA
- 若 #21 未合并且已到 10-25 → 立即提醒用户（D4 截止）
- 若 #20 未合并：确认 base 是否已改为 main，files 是否只有 L5b 的改动

### 2. 收尾卡 `_cards/CLEANUP-L5_v1.md`（两个 PR 都合并后）
- 先在新位置建 venv（python 3.12.3 / numpy 2.5.4，`pip install -r requirements.txt pytest`），更新 STATE 中的 $PY，然后再删 l5a-hygiene（当前 $PY 就在 l5a-hygiene 里）
- 删 worktree：l5a-hygiene、l5b-b4；从 `/tmp/a04-bootstrap` 删 prereg-a04（`git -C /tmp/a04-bootstrap worktree remove …`），然后删掉该克隆
- 删分支：本地 feat/l5a-hygiene、feat/l5b-b4；远端 feat/l5a-hygiene、feat/l5b-b4、docs/prereg-addendum-04（**每个都先 ls-remote 确认**，并确认已并入 main：`git merge-base --is-ancestor`）
- 主库本地 main：由用户决定是否 `git pull --ff-only`
- 参考指南书 evidence OBS-0004（worktree 清理）

### 3. N1 + 证据包修复卡（用户定预算后）
- 依据 A04：§1.2 证据包必须是完整的 C1 白名单；§5.4 receipt 记录模型 ID 和请求模板的 sha256；§3 rule 1 的回落规则；§6 报告口径
- 内容：补全证据包；修 prompt/schema（比较 schema 提示和 guided JSON）；ReplayCacheMiss 单独记原因；先做探针（10–20 次 NIM 调用，比较有效率），再决定是否全量重跑
- 需要密钥：P13 条目 ai/nvidia-nim，由用户在交互终端解锁 GPG

### 4. 其余待办（STATE.md "下一批卡"）
- PR19 N1–N6 卡（N4 锁存改回 fail-closed；N2 base_git_sha。并入 PR20_R1 N2：Meterless manifest 写入了运行时 HEAD）
- ops 容器稳定挂载
