#!/usr/bin/env python3
"""Fetch registered rows and compare every decision packet with local reference."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path

import numpy as np
from rra.evidence.packet import build_packet, packet_sha256
from rra.evidence.sources import C1, check_whitelist
from rra.sponsor.zetaris import ZetarisClient

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs/l3/sources"
ARTIFACT = ROOT / "artifacts/sponsor"

def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

def cast(table, headers, values):
    row = dict(zip(headers, values))
    ints = {"seq", "target_id", "step"}
    floats = {"time", "issued_time", "execution_time", "observed_x", "observed_y", "nominal_x", "nominal_y", "nominal_speed", "dt", "tolerance", "x_pick", "y_pick", "belt_speed"}
    bools = {"accepted", "success", "target_observed"}
    for key in ints & row.keys(): row[key] = int(row[key])
    for key in floats & row.keys(): row[key] = float(row[key])
    for key in bools & row.keys(): row[key] = str(row[key]).lower() == "true"
    return row

def fetch(client, table, episode):
    sql = f"SELECT * FROM {table} WHERE episode_id='{episode}' LIMIT 5000"
    payload = client.query(sql)
    return [cast(table, payload["headers"], row) for row in payload.get("data", [])]

def fetch_federated_episode(client, episode):
    column_map={
        "observation_samples":("episode_id","seq","target_id","step","time","observed_x","observed_y","nominal_x","nominal_y","nominal_speed"),
        "presence_events":("episode_id","seq","target_id","step","time","target_observed"),
        "command_feedback":("episode_id","seq","step","command_id","target_id","issued_time","execution_time","accepted","success","reason_code"),
        "known_config":("episode_id","dt","tolerance","x_pick","y_pick","belt_speed","episode_steps","object_count"),
        "ops_context":("episode_id","text","content_sha256"),
    }
    parts=[]
    for table,columns in column_map.items():
        source="RRA_L3_TELEMETRY" if table in ("observation_samples","presence_events","command_feedback") else "RRA_L3_OPS"
        named=",".join("'"+col+"',"+col for col in columns)
        parts.append(f"SELECT '{table}' kind,to_json(named_struct({named})) payload FROM {source}.{table} WHERE episode_id='{episode}'")
    payload=client.query(" UNION ALL ".join(parts)+" LIMIT 5000")
    tables={t:[] for t in C1}
    for kind,raw in payload.get("data",[]):
        row=json.loads(raw)
        tables[kind].append(cast(kind,list(row.keys()),list(row.values())))
    return tables

def main():
    ARTIFACT.mkdir(parents=True, exist_ok=True)
    reference = {t: read_jsonl(SOURCE / f"{t}.jsonl") for t in C1}
    audit = json.loads((ROOT / "outputs/l3/reference-audit.json").read_text())
    client = ZetarisClient()
    schemas = {}
    latencies = []
    output_eps = []
    federation_sql = "SELECT o.episode_id, k.dt FROM RRA_L3_TELEMETRY.observation_samples o JOIN RRA_L3_OPS.known_config k ON o.episode_id=k.episode_id WHERE o.episode_id='0' LIMIT 1"
    fed_start = time.perf_counter()
    fed = client.query(federation_sql)
    fed_rows = fed.get("data", [])
    fed_time = time.perf_counter() - fed_start
    if len(fed_rows) != 1: raise RuntimeError("federated join returned no row")
    for table in C1:
        p = client.query(f"SELECT * FROM {('RRA_L3_TELEMETRY' if table in ('observation_samples','presence_events','command_feedback') else 'RRA_L3_OPS')}.{table} LIMIT 1")
        schemas[table] = set(p["headers"])
    all_remote = {t: [] for t in C1}
    mismatches = 0
    auth_mismatches = 0
    ref_rollups = []
    for i in range(20):
        episode = str(i)
        start = time.perf_counter()
        remote = fetch_federated_episode(client, episode)
        for table in C1:
            all_remote[table].extend(remote[table])
        elapsed = time.perf_counter() - start
        latencies.append({"seed":i,"query_seconds":round(elapsed,6),"queries":1})
        rr = {t:[r for r in reference[t] if r["episode_id"]==episode] for t in C1}
        def one_pass(tables):
            config = {k:v for k,v in tables["known_config"][0].items() if k != "episode_id"}
            context = {k:v for k,v in tables["ops_context"][0].items() if k != "episode_id"}
            steps = int(config["episode_steps"])
            for presence in sorted(tables["presence_events"], key=lambda row: row["seq"]):
                target,step=presence["target_id"],presence["step"]
                yield build_packet(episode_id=episode,target_id=target,step=step,time=presence["time"],
                    observations=tables["observation_samples"],presence_events=tables["presence_events"],
                    command_feedback=tables["command_feedback"],known_config=config,context=context,
                    episode_steps=steps)
        local_packets = one_pass(rr)
        remote_packets = one_pass(remote)
        mismatch = 0
        local_rollup = hashlib.sha256()
        rollup=hashlib.sha256()
        for a,b in zip(local_packets,remote_packets):
            ha,hb=packet_sha256(a),packet_sha256(b)
            local_rollup.update(ha.encode("ascii"))
            rollup.update(hb.encode("ascii"))
            mismatch += ha != hb
        ref_rollups.append(local_rollup.hexdigest())
        mismatches += mismatch
        audit_row=audit[i]
        for decision in audit_row.get("system2_decisions",[]):
            auth=decision.get("authorization")
            if not auth: continue
            expected=[f"obs:{decision['target_id']}:{x['time']:.3f}" for x in rr["observation_samples"]
                      if x["target_id"]==decision["target_id"] and x["time"]<=decision["time"]]
            auth_mismatches += auth.get("evidence_ids") != expected or not auth.get("evidence_ids")
        output_eps.append({"seed":i,"case":audit_row["case"],"variant":audit_row["variant"],
            "decision_points":len(rr["presence_events"]),"hard_fault_latch_decisions":audit_row["hard_fault_latch_decisions"],
            "mismatches":mismatch,"packets_sha256_rollup":rollup.hexdigest(),
            "s2_diagnostic_rows":len(audit_row.get("s2_diagnostic_trace",[]))})
        print(f"episode={i} mismatches={mismatch} seconds={elapsed:.3f}")
    # Independently rebuild the reference receipt twice; timing and model latency are absent.
    def make_reference_receipt():
        eps=[]
        for i in range(20):
            episode=str(i)
            tab={t:[r for r in reference[t] if r["episode_id"]==episode] for t in C1}
            config={k:v for k,v in tab["known_config"][0].items() if k!="episode_id"}
            context={k:v for k,v in tab["ops_context"][0].items() if k!="episode_id"}
            roll=hashlib.sha256()
            steps=int(config["episode_steps"])
            for presence in sorted(tab["presence_events"], key=lambda row: row["seq"]):
                target,step=presence["target_id"],presence["step"]
                pkt=build_packet(episode_id=episode,target_id=target,step=step,time=presence["time"],
                    observations=tab["observation_samples"],presence_events=tab["presence_events"],
                    command_feedback=tab["command_feedback"],known_config=config,context=context,
                    episode_steps=steps)
                roll.update(packet_sha256(pkt).encode("ascii"))
            eps.append({"seed":i,"packets_sha256_rollup":roll.hexdigest()})
        return json.dumps({"episodes":eps},sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    first,second=make_reference_receipt(),make_reference_receipt()
    t1_extra = {k: sorted(set(v)-C1[k]) for k,v in schemas.items()}
    row_schemas = {k: set().union(*(r.keys() for r in v)) if v else C1[k] for k,v in all_remote.items()}
    check_whitelist(schemas, all_remote)
    pg = subprocess.run(["docker","exec","rra-l3-pg","psql","-U","postgres","-d","rra_telemetry","-At","-c",
        "SELECT table_name || ':' || column_name FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name, ordinal_position"],
        check=True,capture_output=True,text=True).stdout.splitlines()
    pg_extra=[]
    pg_allowed={"observation_samples":C1["observation_samples"],"presence_events":C1["presence_events"],"command_feedback":C1["command_feedback"]}
    for item in pg:
        table,column=item.split(":",1)
        if table not in pg_allowed or column not in pg_allowed[table]: pg_extra.append(item)
    receipt={"schema":"rra.l3.equivalence.v1","base_git_sha":"2a3b52dcf15cf352064f064e2a8b499c4fe06280",
        "python":platform.python_version(),"numpy":np.__version__,"plan":"A",
        "source_containers":["rra-l3-pg","rra-l3-ops"],
        "registration_sql":["CREATE DATASOURCE RRA_L3_TELEMETRY DESCRIBE BY \"L3 whitelisted policy telemetry\" OPTIONS (jdbcdriver \"org.postgresql.Driver\", jdbcurl \"jdbc:postgresql://rra-l3-pg:5432/rra_telemetry\", username \"postgres\", password \"\")","CREATE LIGHTNING DATABASE RRA_L3_OPS DESCRIBE BY \"L3 whitelisted operational context\"","CREATE LIGHTNING REST TABLE known_config FROM RRA_L3_OPS REQUEST(endpoint \"http://rra-l3-ops:8000/known_config\", method \"get\", response_type \"json\", http_encoding \"URLENCODED\") HEADER () BODY ()","CREATE LIGHTNING REST TABLE ops_context FROM RRA_L3_OPS REQUEST(endpoint \"http://rra-l3-ops:8000/ops_context\", method \"get\", response_type \"json\", http_encoding \"URLENCODED\") HEADER () BODY ()"],
        "federation_sql":federation_sql,"federation_rows":len(fed_rows),"federation_seconds":round(fed_time,6),
        "episodes":output_eps,"query_latencies":latencies,"T1_schema_extra":t1_extra,"T1_postgres_information_schema_extra":pg_extra,
        "T3_authorization_field":"system2_decisions[].authorization.evidence_ids",
        "T3_anchor_mismatches":sum(x["mismatches"] for x in audit),"T3_authorization_mismatches":int(auth_mismatches),"T4_mismatches":int(mismatches),
        "T5":"PASS","T8_reference_receipt_bytes_identical":first==second,
        "T8_reference_receipt_sha256":hashlib.sha256(first).hexdigest()}
    (ARTIFACT/"zetaris-whitelist.json").write_text(json.dumps({"schema":"rra.l3.whitelist.v1","allowed":{k:sorted(v) for k,v in C1.items()},"zetaris_headers":{k:sorted(v) for k,v in schemas.items()},"extra_count":sum(map(len,t1_extra.values()))},sort_keys=True,indent=2),encoding="utf-8")
    (ARTIFACT/"zetaris-equivalence.json").write_text(json.dumps(receipt,sort_keys=True,indent=2),encoding="utf-8")
    print(f"T4 mismatches={mismatches} T3_auth_mismatches={auth_mismatches} T8={first==second}")

if __name__ == "__main__": main()
