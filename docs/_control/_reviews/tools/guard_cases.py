import json, subprocess, sys
HOOK = "/home/mxfclaw/reality-residual-agent-worktrees/_control/.claude/hooks/deny_guard.py"
CASES = [
    # (command, expect_block)
    ("git -C ~/reality-residual-agent push --dry-run origin main", True),
    ("git push origin main", True),
    ("cd x && git push", True),
    ("gh pr merge 19", True),
    ("gh -R o/r pr create --fill", True),
    ("pass show ai/nvidia-nim", True),
    ("timeout 10 pass show ai/nvidia-nim | wc -c", True),
    ("timeout -k 2 10 pass show k", True),
    ("env A=1 pass show k", True),
    ("sudo pass show k", True),
    ("echo timeout passes", False),
    ("x && pass show ai/nvidia-nim", True),
    ("echo $(pass show k)", True),
    ("ls\npass show k", True),
    ('grep -rn "pass show" .', False),
    ("pytest -k pass", False),
    ("git -C ~/reality-residual-agent fetch origin feat/l5a-hygiene", False),
    ("git log --oneline -5", False),
    ("gh pr view 19", False),
    ("grep -rn push .github/", False),
]
bad = 0
for cmd, exp in CASES:
    r = subprocess.run([sys.executable, HOOK], input=json.dumps({"tool_input": {"command": cmd}}),
                       capture_output=True, text=True)
    got = r.returncode == 2
    ok = got == exp
    bad += not ok
    print(f"{'OK ' if ok else 'BAD'} block={got!s:5} rc={r.returncode} {cmd!r}")
print("FAILURES:", bad)
