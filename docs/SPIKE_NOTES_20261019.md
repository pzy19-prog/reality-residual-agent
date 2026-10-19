Pre-window compatibility spike output under Addendum 02 §8. Access and compatibility only; declared pre-existing design input. Date: 2026-10-19.

## Zetaris — GO
- [FACT] Access path used: self-managed local deployment (Docker Compose bundle downloaded from the Zetaris Cloud portal; sponsor-issued registry credentials). The Z-Cloud trial path was not needed.
- [FACT] Stack: zetaris-ndp-api, zetaris-ndp-driver and zetaris-new-ui images tagged 2.4.3-v2.4.3.1-hackathon, plus postgres:16-alpine; init and bootstrap run once and exit 0.
- [FACT] The bundle's verify script passed 9/9 checks (2026-10-18).
- [FACT] REST: POST {base}/sql-editor/sqls/run with a Bearer API token, header X-Org-ID: 1, a fresh X-Request-ID (UUID); JSON body {queryId, sql, source: "SqlEditor", limit}. `SELECT 1` returns data[0][0] == 1.
- [FACT] A REST source (public PokeAPI) was registered through the SQL Workspace (CREATE LIGHTNING DATABASE / REST TABLE / SCHEMASTORE VIEW); a query over the resulting view returned 2 rows.
- [FACT] After a host reboot (2026-10-19) the containers came back healthy and the REST check passed again.
- [FACT] The API token has an expiry on 2026-11-17, after the build window.
- [UNKNOWN] Registering a local Postgres container as a source; the JDBC path (port 10000 is exposed); the §4.3 SHA-256 equivalence against the reference loader; throughput and latency; any hackathon-specific limits.

## NVIDIA — GO
- [FACT] OpenAI-compatible endpoint https://integrate.api.nvidia.com/v1 with a free API key from build.nvidia.com; model nvidia/nemotron-3.5-super-vl-120b-a12b.
- [FACT] Responses carry reasoning_content; with a small max_tokens the visible content can be empty. max_tokens=1500 returned content.
- [FACT] 20 parallel requests all returned HTTP 200; no rate-limit headers were returned.
- [FACT] The key has an expiry on 2027-04-18.
- [UNKNOWN] The per-minute and daily rate limits.

## Meterless — GO for the open-source path; organizer-intended component UNKNOWN
- [FACT] github.com/meterless/Meterless (Apache-2.0, TypeScript) clones and runs on Linux (Ubuntu under WSL) with Node v22.22.1; no API keys needed.
- [FACT] The H-MEM reference implementation (@meterless/hmem-reference 0.1.0, zero runtime dependencies) installed with `npm ci --ignore-scripts`; its 10 vitest smoke tests pass.
- [FACT] templates/agentathon-starter: the seed, ask and audit commands ran; state persisted across separate processes in .notebook/; the audit ledger is append-only and records create and read events.
- [FACT] On a 5-memory sample, retrieval ranked the relevant memory first (relevance 0.14) but an unrelated memory scored 0.12. Mode was retrieval-only (no LLM).
- [INFERENCE] Retrieval looks lexical/deterministic and is not suited as RRA's core retrieval.
- [FACT] RRA is Python and Meterless is TypeScript, so any integration needs a host-side adapter (for example a subprocess or a small Node bridge).
- [FACT] This partly resolves the UNKNOWN in Addendum 02 §5.5: the open specification and reference implementation are integrable from Linux/WSL.
- [FACT] npm audit reports 9 findings (3 moderate, 4 high, 2 critical) in the reference's dev dependencies; [INFERENCE] dev-only; not remediated.
- [NOT VERIFIED] The H-MEM conformance suite (engines/hmem), the World Model and Markovian engines, the Gaia/Relay/Swarms Windows apps, Nightshift. Scout Intent is spec-only per its README.
- [UNKNOWN] Which Meterless component the organizers mean and what minimum "integration" they expect; to be asked at the 2026-10-21 onboarding call.

## Decisions
No integration design is decided here; any design is decided by a later addendum.
