#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="$ROOT/outputs/l3/sources"
NETWORK=zetaris_default
for name in rra-l3-pg rra-l3-ops; do
  if docker inspect "$name" >/dev/null 2>&1; then docker rm -f "$name" >/dev/null; fi
done
docker run -d --name rra-l3-pg --network "$NETWORK" --network-alias rra-l3-pg \
  -e POSTGRES_DB=rra_telemetry -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine >/dev/null
until docker exec rra-l3-pg pg_isready -U postgres -d rra_telemetry >/dev/null 2>&1; do sleep 1; done
docker exec -i rra-l3-pg psql -U postgres -d rra_telemetry -v ON_ERROR_STOP=1 <<'SQL'
CREATE TABLE observation_samples (episode_id text, seq integer, target_id integer, step integer, time double precision, observed_x double precision, observed_y double precision, nominal_x double precision, nominal_y double precision, nominal_speed double precision);
CREATE TABLE presence_events (episode_id text, seq integer, target_id integer, step integer, time double precision, target_observed boolean);
CREATE TABLE command_feedback (episode_id text, seq integer, command_id text, target_id integer, issued_time double precision, execution_time double precision, accepted boolean, success boolean, reason_code text);
SQL
for table in observation_samples presence_events command_feedback; do
  python3 - "$DATA/$table.jsonl" "$table" <<'PY' | docker exec -i rra-l3-pg psql -U postgres -d rra_telemetry -v ON_ERROR_STOP=1 -c "COPY $table FROM STDIN WITH (FORMAT csv)"
import csv,json,sys
for line in open(sys.argv[1], encoding="utf-8"):
 r=json.loads(line); w=csv.writer(sys.stdout,lineterminator="\n"); w.writerow([r[k] for k in (("episode_id","seq","target_id","step","time","observed_x","observed_y","nominal_x","nominal_y","nominal_speed") if sys.argv[2]=="observation_samples" else (("episode_id","seq","target_id","step","time","target_observed") if sys.argv[2]=="presence_events" else ("episode_id","seq","command_id","target_id","issued_time","execution_time","accepted","success","reason_code")))])
PY
done
docker run -d --name rra-l3-ops --network "$NETWORK" --network-alias rra-l3-ops \
  -v "$ROOT:/work:ro" -v "$DATA:/data:ro" -w /work python:3.12-alpine \
  python scripts/l3_source_server.py --group ops --directory /data --port 8000 >/dev/null
PYTHONPATH="$ROOT/src" "$ROOT/.venv/bin/python" - <<'PY'
from rra.sponsor.zetaris import ZetarisClient
c=ZetarisClient()
names={str(r[0]).upper() for r in c.rows(c.query("SHOW DATASOURCES"))}
if "RRA_L3_TELEMETRY" not in names:
 c.query('''CREATE DATASOURCE RRA_L3_TELEMETRY DESCRIBE BY "L3 whitelisted policy telemetry" OPTIONS (jdbcdriver "org.postgresql.Driver", jdbcurl "jdbc:postgresql://rra-l3-pg:5432/rra_telemetry", username "postgres", password "")''')
 c.query("REGISTER DATASOURCE TABLES FROM RRA_L3_TELEMETRY")
try:
 ops={str(r[0]).split(".")[-1].lower() for r in c.rows(c.query("SHOW TABLES IN RRA_L3_OPS"))}
except Exception:
 c.query('CREATE LIGHTNING DATABASE RRA_L3_OPS DESCRIBE BY "L3 whitelisted operational context"')
 ops=set()
for table, endpoint in (("known_config","known_config"),("ops_context","ops_context")):
 if table not in ops:
  c.query(f'''CREATE LIGHTNING REST TABLE {table} FROM RRA_L3_OPS REQUEST(endpoint "http://rra-l3-ops:8000/{endpoint}", method "get", response_type "json", http_encoding "URLENCODED") HEADER () BODY ()''')
print("sources_ready")
PY
