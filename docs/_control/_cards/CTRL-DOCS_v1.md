# 任务卡 CTRL-DOCS — 把控制会话的卡片、审查、状态推到分支 local/control-docs（v1）
执行者：Grok 4.7（Grok CLI，WSL；沙箱 profile `rra-exec`），新会话
仓库：pzy19-prog/reality-residual-agent；主库 ~/reality-residual-agent
工作区（由你创建）：~/reality-residual-agent-worktrees/control-docs　分支 local/control-docs　基线 origin/main
git 身份："Xifeng Ming" <274782819+pzy19-prog@users.noreply.github.com>（作者和提交者）；提交信息不得出现任何 AI 署名行
依据：所有者 2026-10-24 同意（"推"）；云端在 issue #26 17:38 提出的请求。仓库是公开的。
**不改代码，不开 PR，不合并，不读取任何密钥，不打开 `config/eval_seeds*.json`。** `~/reality-residual-agent-worktrees/_control` 只读，不得修改。

## §0.0 Bootstrap
```
cd ~/reality-residual-agent && git fetch origin
git ls-remote --exit-code origin refs/heads/local/control-docs && 停（远端已有同名分支）
git worktree add -b local/control-docs ~/reality-residual-agent-worktrees/control-docs origin/main
cd ~/reality-residual-agent-worktrees/control-docs
git config user.name "Xifeng Ming"; git config user.email "274782819+pzy19-prog@users.noreply.github.com"
```

## §1 已裁决
- C1 复制（只复制，不改内容）到 `docs/_control/`，保持子目录结构：
  - `~/reality-residual-agent-worktrees/_control/_cards/*.md` → `docs/_control/_cards/`
  - `~/reality-residual-agent-worktrees/_control/_reviews/*.md` 和 `_reviews/tools/*.py` → `docs/_control/_reviews/`（tools 放进 `_reviews/tools/`）
  - `~/reality-residual-agent-worktrees/_control/STATE.md` → `docs/_control/STATE.md`
  - `~/reality-residual-agent-worktrees/_control/handoff/*.md` → `docs/_control/handoff/`
  - 不复制 `_control/CLAUDE.md`、`.claude/` 和其他任何文件
- C2 提交前做密钥扫描，命中任一条就**停**，不提交，在报告中列出文件和行号（不打印匹配到的值本身）：
  `grep -rnE "nvapi-[A-Za-z0-9_-]{8,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|BEGIN [A-Z ]*PRIVATE KEY|(NVIDIA_API_KEY|ZETARIS_TOKEN)=[^ \`\"<$]" docs/_control`
  只提到密钥名字（例如反引号里的 `NVIDIA_API_KEY`）不算命中。
- C3 在 `docs/_control/README.md` 写三行说明：这是本地控制会话的任务卡、审查和状态快照；生成时间（UTC）；协调记录见 issue #26；本目录不是已登记文件，也不是实现的一部分。
- C4 一个提交 `docs: snapshot local control cards, reviews and state`；普通推送 `git push -u origin local/control-docs`。不开 PR。
- C5 推送后在 issue #26 发一条评论，第一行写 `**[local → cloud]** control-docs snapshot`，内容包括：分支名、commit sha、文件数。用 `gh issue comment 26 --body ...`。

## §2 验收
- V1 `git diff --name-only origin/main...HEAD` 只有 `docs/_control/` 下的文件
- V2 C2 扫描无命中
- V3 作者和提交者为 Xifeng Ming noreply；提交信息没有 AI 署名
- V4 `git ls-remote origin refs/heads/local/control-docs` 等于本地 HEAD

## §4 自主权
硬停只限：§0.0 不符；C2 命中。

## §6 收尾
在最后一条输出写：分支、commit sha、文件数、V1–V4。不写报告文件。worktree 保留。
