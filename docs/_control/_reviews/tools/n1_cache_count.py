import json, glob, re, collections, sys
S = sys.argv[1]
fs = sorted(glob.glob(S + '/src_x/artifacts/llm_cache/*.json'))
print("1. total files:", len(fs))
ws_keys = collections.Counter(); ws = []; err = []
cnt = collections.Counter(); ok_nonempty = 0; ok_allowed = 0; mal = []
fr_all = collections.Counter()
for f in fs:
    d = json.load(open(f))
    resp = d.get('response')
    content = fin = None
    try:
        ch = resp['choices'][0]; content = ch['message']['content']; fin = ch.get('finish_reason')
    except (KeyError, IndexError, TypeError):
        pass
    fr_all[fin] += 1
    if not isinstance(content, (str, dict)):
        cnt['ERROR'] += 1; err.append((f[-21:], fin, str(resp)[:300])); continue
    try:
        parsed = json.loads(content) if isinstance(content, str) else content
    except json.JSONDecodeError:
        if fin == 'length': cnt['TRUNCATED'] += 1
        else:
            cnt['MALFORMED'] += 1; mal.append(content)
        continue
    if not isinstance(parsed, dict) or not isinstance(parsed.get('items'), list):
        cnt['WRONG_SHAPE'] += 1
        ws_keys[tuple(parsed.keys()) if isinstance(parsed, dict) else type(parsed).__name__] += 1
        if len(ws) < 3: ws.append(content)
        continue
    cnt['PARSE_OK'] += 1
    if parsed['items']:
        ok_nonempty += 1
        sysmsg = next(m['content'] for m in d['request']['messages'] if m['role'] == 'system')
        ids = sysmsg.split('Allowed IDs: ')[1]
        # IDs contain commas inside AND(...); split on commas outside parens
        allowed, depth, cur = set(), 0, ''
        for c in ids:
            if c == '(': depth += 1
            if c == ')': depth -= 1
            if c == ',' and depth == 0: allowed.add(cur.strip()); cur = ''
            else: cur += c
        allowed.add(cur.strip())
        if any(isinstance(i, dict) and i.get('hypothesis_id') in allowed for i in parsed['items']):
            ok_allowed += 1
print("2. finish_reason dist:", dict(fr_all))
print("3. classes:", dict(cnt), "sum =", sum(cnt.values()))
print("   PARSE_OK items nonempty:", ok_nonempty, "| >=1 hypothesis_id in Allowed IDs:", ok_allowed)
print("4. MALFORMED first 3 (120 chars):")
for m in mal[:3]: print("   ", repr(m[:120]))
print("   WRONG_SHAPE top-level keys (top 5):", ws_keys.most_common(5))
print("   WRONG_SHAPE first 3 (120 chars):")
for m in ws: print("   ", repr(m[:120]))
print("   ERROR entries:", err)
d = json.load(open(S + '/b4-dev.json'))
print("5. b4-dev.json top-level keys:", list(d))
print("   'gate_reason' occurrences in file: ", open(S + '/b4-dev.json').read().count('gate_reason'))
tot = collections.Counter(); same = collections.Counter()
for e in d['episodes']:
    for arm in ('B4_STRICT', 'B4_TIEBREAK'):
        tot[arm] += e[arm + '_decision_count']
        same[arm] += e[arm + '_decisions_sha256'] == e['B3_decisions_sha256']
print("   episodes entries:", len(d['episodes']), "decision_count sums:", dict(tot),
      "episodes whose decisions_sha256 == B3's:", dict(same))
b3 = json.load(open(S + '/b3-dev.json'))
e0 = b3['episodes'][0]
gc = collections.Counter(x['gate_reason'] for e in b3['episodes'] for x in e.get('system2_decisions', []))
print("   episodes in b3 without system2_decisions:", sum('system2_decisions' not in e for e in b3['episodes']), "of", len(b3['episodes']))
print("   SUPPLEMENTARY b3-dev.json system2_decisions gate_reason:", dict(gc), "total", sum(gc.values()))
