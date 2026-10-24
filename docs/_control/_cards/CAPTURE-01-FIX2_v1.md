CAPTURE-01：FIX2 — thread_key 按会话持久化（B6）+ 合并收尾

<!-- 卡 ID：CAPTURE-01-FIX2 v1。本卡取代网页会话 2026-10-23 14:1x 版本。
     会话首条消息须以 "CAPTURE-01：" 开头（首条卡头规则不认 "CAPTURE-01-FIX2："，会返回 UNKNOWN）。 -->

## 执行者
Luna（GPT-6 Luna，Codex CLI），笔记本 PZY-LAPTOP-01 WSL。
出卡：本地 Claude Code（架构/审查），2026-10-23。

## 工作区
- 仓库：~/conversation-observatory（origin main = 410e235）
- worktree：~/conversation-observatory-worktrees/capture-v0
- 分支：feat/capture-cli-v0，基线 SHA 9597df7（PR #1 head）
- 解释器：/usr/bin/python3（3.12.3）
- 报告目录：~/pzy-taskpacks/reports/2026-10-23/

## §0 阻断条件（只限以下情况；遇到即停，按 §5 回报）
1. §0.1 任何一项复测不符（特别是 PR head ≠ 9597df7，或基线测试 ≠ 19 OK）
2. 必须违反 §1 才能完成
3. 需要读取或输出密钥明文；或 gpg 解密需要交互输入口令，且无法经 agent 完成
4. 需要修改预注册/已登记文件
5. 合并冲突；或 origin/main 在 410e235 之后有新提交
6. 远端出现预期之外的同名分支

## §0.0 Bootstrap
```
cd ~/conversation-observatory-worktrees/capture-v0
git fetch origin && git status -sb      # 期望 HEAD=9597df7，与 origin 同步，工作区干净
/usr/bin/python3 -m unittest discover -s capture/tests -v   # 期望 Ran 19 tests ... OK
```

## §0.1 实测核对（出卡方 2026-10-23 15:4x 实测；开工前逐项复测并写进报告）
| # | 项 | 命令 | 出卡方实测值 |
|---|---|---|---|
| 1 | PR #1 | `gh pr view 1 --json headRefOid,state` | 9597df7213b7…，OPEN |
| 2 | main | `git -C ~/conversation-observatory ls-remote origin refs/heads/main` | 410e2359… |
| 3 | crontab | `crontab -l` | 两条 capture 行以 `# DISABLED CAPTURE-01-FIX: ` 开头，路径指向 worktree；SIS hourly 行未注释 |
| 4 | 基线测试 | §0.0 | Ran 19 tests OK |
| 5 | B6 根因 | 读 capture/capture_cli.py:256、:266 | deltas 每次运行重建；first_user 只取本次 delta 的首条 user 消息 |
| 6 | 游标结构 | 读 capture_cli.py:324 | state 顶层键 = files, seen_ranges, record_ids, last_by_thread（没有 session_keys） |

## §1 已裁决（不再讨论）
1. **B6**：cursors.json 新增顶层键 `session_keys: {"<surface>|<session_id>": "<thread_key>"}`。
   - 每个 delta 计算 tkey 之前先查表：有非 UNKNOWN 的值就直接继承，不再调用 thread_key()。
   - 查不到时按 B3 规则现算：结果不是 UNKNOWN 就写入表；结果是 UNKNOWN 不写，留给后续 delta 再确定。
   - 写入后不再改动，即使后续 delta 出现新的卡头。
   - 写入时机：tkey 一算出来就写，即使该 delta 因 record_id 已存在被跳过。
   - 旧 state 没有 session_keys 时按 {} 处理，不报错。
2. 不回填：FIX2 之前已采集的会话不追溯（不为回填而解密旧记录）。在报告里列为已知限制。
3. 不改 B3 thread_key 规则、schema v0.1、5 个 status 枚举、summary_state，只改持久化。
4. resumes：继承来的 tkey 照常走 last_by_thread，同一会话后续记录的 resumes 指向上一条记录。
5. 新增测试必须用 tests/fixtures/factory.py 的真实结构构造器（claude_row / claude_assistant / codex_row），不得手写虚构结构。至少新增 4 个：
   - T1：两次运行。第 1 段首条 user 为 "CAPTURE-01：…"；第 2 段没有卡头，且正文中另一个前缀（如 SIS-BAKE-01）出现次数更多 → 第 2 段记录 thread_key == "CAPTURE-01"，且 resumes == 第 1 段的 record_id
   - T2：第 1 段 UNKNOWN，第 2 段可以确定键，第 3 段没有线索 → 第 3 段继承第 2 段的键
   - T3：不含 session_keys 的旧 cursors.json 能正常加载并运行
   - T4：claude_code 与 codex 使用相同 session_id 时互不串键
6. 合并：`gh pr merge 1 --merge`，不带 --delete-branch，在 ~/conversation-observatory 主库目录执行。
7. B6 和 unittest 全部通过后不需要复审，Luna 直接收尾。

## §2 验收
- **V1**：按 §1.1 实现；commit 推送到 feat/capture-cli-v0。身份 "Xifeng Ming" <274782819+pzy19-prog@users.noreply.github.com>，不加任何 AI 署名行。
- **V2**：unittest 全绿：原 19 个加新增 ≥4 个，0 失败，0 跳过。
- **V3**：执行 `gh pr merge 1 --merge`，然后 `git -C ~/conversation-observatory pull`，main 包含 B6 提交。
- **V4**：恢复 cron。
  - 先备份：`crontab -l > ~/pzy-capture/state/crontab.bak-<时间戳>`
  - 两条 capture 行去掉 `# DISABLED CAPTURE-01-FIX: ` 前缀，路径改为 `/home/mxfclaw/conversation-observatory/capture/capture_cli.py`
  - flock、PATH、--final、重定向保持原样；SIS 行不动
- **V7**：等下一个 */30 自动刻度，不得用手动运行代替。
  - 通过条件：run.log 在恢复时间点之后没有新增错误行；state/metrics/ 下出现刻度之后的新文件；cursors.json 的 mtime 已更新且包含 session_keys
  - 报告写明：刻度时间、metrics 文件名、session_keys 条目数
- **A12**：当晚 23:30 --final 运行之后，解密最新分片（gpg，经 pass/agent；不打印密钥或口令），找出 thread_key 以 "CAPTURE-01" 开头的记录。
  - 只报告以下字段，不贴正文：record_id 前 12 位、surface、session_id、thread_key、status、summary_state、resumes 是否非空
  - PASS 条件：至少 1 条；status 属于 5 个枚举；schema = capture-record/v0.1；同一会话有多条记录时 thread_key 一致，且 resumes 串成链

## §3 禁止
- 不清理、不移动、不改写 ~/.claude/projects、~/.codex/sessions 下的 CLI 日志（冻结到 11-20，EXP-0002）
- 不删除 ~/pzy-capture-v0-bad-20261023，不重置 ~/pzy-capture
- 任何输出、报告、commit 中都不得出现密钥、口令或会话正文

## §4 自主权
环境问题（依赖、gpg-agent、gh 认证刷新、flock 路径、cron 环境变量等）由 Luna 自行解决，做法写进报告。在不违反 §1 的前提下，实现细节由 Luna 决定。

## §5 失败回报
1. 在 ~/pzy-taskpacks/reports/2026-10-23/ 写 CAPTURE-01-FIX2-report.md，内容包括：
   - 首行写 `STATUS: FAILED`
   - 停在哪一步，触发的是哪条 §0 阻断条件
   - 命令与输出摘要（已脱敏）
   - 当前 `crontab -l`
   - 当前 PR 与分支状态
2. 在报告目录内执行 `sha256sum CAPTURE-01-FIX2-report.md > CAPTURE-01-FIX2-report.md.sha256`（裸文件名）。
3. 提交并推送到 pzy-taskpacks main。cron 停在什么状态就如实写，不要为了"看起来正常"去改动它。

## §6 收尾（V7、A12 均 PASS 后）
1. `git -C ~/conversation-observatory worktree remove ~/conversation-observatory-worktrees/capture-v0`
2. `git -C ~/conversation-observatory branch -d feat/capture-cli-v0`
3. 先执行 `git -C ~/conversation-observatory ls-remote origin refs/heads/feat/capture-cli-v0`，确认分支存在且指向已合并的提交，再执行 `git -C ~/conversation-observatory push origin --delete feat/capture-cli-v0`
4. 报告分两次提交到 pzy-taskpacks main，目录 reports/2026-10-23/，每份都附裸文件名的 .sha256：
   - V7 之后：CAPTURE-01-FIX2-report.md，包含 §0.1 复测值、V1–V7 逐项 PASS/FAIL 及证据、已知限制（§1.2）
   - A12 之后：CAPTURE-01-FIX2-addendum-A12.md，包含 A12 结果、worktree/分支清理证据、最终 `crontab -l`
   - 身份同 V1，不加任何 AI 署名行
