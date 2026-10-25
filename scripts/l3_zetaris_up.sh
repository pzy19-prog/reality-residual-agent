#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="$ROOT/outputs/l3/sources"
NETWORK=zetaris_default
# Container name and network alias follow this prefix. Zetaris JDBC and REST
# hostnames stay rra-l3-pg / rra-l3-ops so they match registration_sql.
PREFIX="${RRA_L3_PREFIX:-rra-l3}"
PG="${PREFIX}-pg"
OPS="${PREFIX}-ops"
for name in "$PG" "$OPS"; do
  if docker inspect "$name" >/dev/null 2>&1; then docker rm -f "$name" >/dev/null; fi
done
docker run -d --name "$PG" --network "$NETWORK" --network-alias "$PG" \
  -e POSTGRES_DB=rra_telemetry -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine >/dev/null
init_ok=0
ready_ok=0
sql_ok=0
pg_ready=0
pg_deadline=$((SECONDS + 120))
while (( SECONDS < pg_deadline )); do
  init_ok=0
  ready_ok=0
  sql_ok=0
  if (set +o pipefail; docker logs "$PG" 2>&1 | grep -q "PostgreSQL init process complete"); then init_ok=1; fi
  if docker exec "$PG" pg_isready -U postgres -d rra_telemetry >/dev/null 2>&1; then ready_ok=1; fi
  if docker exec "$PG" psql -U postgres -d rra_telemetry -c 'select 1' >/dev/null 2>&1; then sql_ok=1; fi
  if (( init_ok && ready_ok && sql_ok )); then pg_ready=1; break; fi
  sleep 1
done
if (( pg_ready != 1 )); then
  echo "ERROR: postgres ${PG} not ready within 120s (init_log=${init_ok} pg_isready=${ready_ok} select_1=${sql_ok}); need docker logs to contain 'PostgreSQL init process complete', pg_isready success, and psql -d rra_telemetry -c 'select 1' success" >&2
  exit 1
fi
docker exec -i "$PG" psql -U postgres -d rra_telemetry -v ON_ERROR_STOP=1 <<'SQL'
CREATE TABLE observation_samples (episode_id text, seq integer, target_id integer, step integer, time double precision, observed_x double precision, observed_y double precision, nominal_x double precision, nominal_y double precision, nominal_speed double precision);
CREATE TABLE presence_events (episode_id text, seq integer, target_id integer, step integer, time double precision, target_observed boolean);
CREATE TABLE command_feedback (episode_id text, seq integer, step integer, command_id text, target_id integer, issued_time double precision, execution_time double precision, accepted boolean, success boolean, reason_code text);
SQL
for table in observation_samples presence_events command_feedback; do
  python3 - "$DATA/$table.jsonl" "$table" <<'PY' | docker exec -i "$PG" psql -U postgres -d rra_telemetry -v ON_ERROR_STOP=1 -c "COPY $table FROM STDIN WITH (FORMAT csv)"
import csv, json, sys
COLUMNS = {
    "observation_samples": ("episode_id", "seq", "target_id", "step", "time", "observed_x", "observed_y", "nominal_x", "nominal_y", "nominal_speed"),
    "presence_events": ("episode_id", "seq", "target_id", "step", "time", "target_observed"),
    "command_feedback": ("episode_id", "seq", "step", "command_id", "target_id", "issued_time", "execution_time", "accepted", "success", "reason_code"),
}
table = sys.argv[2]
fields = COLUMNS[table]
writer = csv.writer(sys.stdout, lineterminator="\n")
with open(sys.argv[1], encoding="utf-8") as handle:
    for line in handle:
        row = json.loads(line)
        writer.writerow([row[key] for key in fields])
PY
done
docker run -d --name "$OPS" --network "$NETWORK" --network-alias "$OPS" \
  -v "$ROOT:/work:ro" -v "$DATA:/data:ro" -w /work python:3.12-alpine \
  python scripts/l3_source_server.py --group ops --directory /data --port 8000 >/dev/null
ops_ready=0
ops_deadline=$((SECONDS + 60))
while (( SECONDS < ops_deadline )); do
  if docker exec "$OPS" wget -qO- http://127.0.0.1:8000/known_config >/dev/null 2>&1; then ops_ready=1; break; fi
  sleep 1
done
if (( ops_ready != 1 )); then
  echo "ERROR: ops ${OPS} HTTP not ready within 60s: docker exec wget -qO- http://127.0.0.1:8000/known_config failed" >&2
  exit 1
fi
if [[ "${RRA_L3_SKIP_ZETARIS:-}" == "1" ]]; then
  echo "zetaris_skipped"
else
PYTHONPATH="$ROOT/src" "$ROOT/.venv/bin/python" - <<'ZETARIS'
import sys
from rra.evidence.sources import C1
from rra.sponsor.zetaris import ZetarisClient

c = ZetarisClient()
names = {str(r[0]).upper() for r in c.rows(c.query("SHOW DATASOURCES"))}
if "RRA_L3_TELEMETRY" in names:
    c.query("DROP DATASOURCE RRA_L3_TELEMETRY")
c.query('''CREATE DATASOURCE RRA_L3_TELEMETRY DESCRIBE BY "L3 whitelisted policy telemetry" OPTIONS (jdbcdriver "org.postgresql.Driver", jdbcurl "jdbc:postgresql://rra-l3-pg:5432/rra_telemetry", username "postgres", password "")''')
c.query("REGISTER DATASOURCE TABLES FROM RRA_L3_TELEMETRY")
try:
    ops = {str(r[0]).split(".")[-1].lower() for r in c.rows(c.query("SHOW TABLES IN RRA_L3_OPS"))}
except Exception:
    c.query('CREATE LIGHTNING DATABASE RRA_L3_OPS DESCRIBE BY "L3 whitelisted operational context"')
    ops = set()
for table, endpoint in (("known_config", "known_config"), ("ops_context", "ops_context")):
    if table in ops:
        c.query(f"DROP LIGHTNING DATABASE TABLE RRA_L3_OPS.{table}")
    c.query(f'''CREATE LIGHTNING REST TABLE {table} FROM RRA_L3_OPS REQUEST(endpoint "http://rra-l3-ops:8000/{endpoint}", method "get", response_type "json", http_encoding "URLENCODED") HEADER () BODY ()''')
checks = (
    ("RRA_L3_TELEMETRY", "observation_samples"),
    ("RRA_L3_TELEMETRY", "presence_events"),
    ("RRA_L3_TELEMETRY", "command_feedback"),
    ("RRA_L3_OPS", "known_config"),
    ("RRA_L3_OPS", "ops_context"),
)
failed = False
for db, table in checks:
    payload = c.query(f"SELECT * FROM {db}.{table} LIMIT 1")
    headers = payload.get("headers")
    if not isinstance(headers, list):
        print(f"schema check failed: {db}.{table} missing headers", file=sys.stderr)
        failed = True
        continue
    got = {str(header).lower() for header in headers}
    want = {name.lower() for name in C1[table]}
    if got != want:
        print(f"schema check failed: {db}.{table} headers {sorted(got)} != C1 {sorted(want)}", file=sys.stderr)
        failed = True
if failed:
    raise SystemExit(1)
print("sources_ready")
ZETARIS
fi
