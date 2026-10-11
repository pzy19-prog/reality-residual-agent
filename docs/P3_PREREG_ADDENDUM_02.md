# P3 Preregistration Addendum 02 — 2026-10-11 Rule Change: Mandatory Sponsor Integration

Status: **PRE-HACKATHON DESIGN AMENDMENT / PRE-REGISTRATION / NOT SCORED WORK**

Date: 2026-10-11

Trigger: the official rules page changed (snapshot `docs/HACKATHON_RULES.md`, fetched 2026-10-11T07:08:28Z). This amendment is **not** triggered by any evaluation outcome. No eval-v3 seed realization exists at the time of writing (Addendum 01, items 8–9).

This addendum does not move or rewrite `p3-prereg`, and does not alter `docs/P3_SYSTEM2_DESIGN.md` text. Where this addendum and P3 differ, this addendum governs for the listed items only.

## 1. Rule facts this addendum responds to

Verbatim from the 2026-10-11 snapshot (`docs/HACKATHON_RULES.md`):

> 4.1 Building starts 22 October 2026 at 00:00 UTC and ends 27 October 2026 at 23:45 UTC.
>
> 5.1 Every submission must integrate Zetaris and Meterless, and teams must use Cursor for development.
>
> 5.2 Integrate NVIDIA technology wherever it contributes to your project, workflow or use case.
>
> 5.4 Pre-existing open-source libraries are fine. Pre-existing product code must be declared in the submission form.
>
> 6.1 A demo video of 1-4 minutes that shows the main workflow, how the agent solves the selected challenge, its key features, and how Zetaris and Meterless are integrated.
>
> 6.2 A slide deck covering the problem and target users, the solution, the agent workflow or architecture, the technical stack, how Zetaris and Meterless were used, what was unique about your use of the sponsor technologies, product visuals, and future enhancements.
>
> 6.3 A GitHub repository with all source code and a README covering setup, usage and dependencies. If your agents run in Google Colab, include the Colab links.
>
> 6.4 A clear explanation of how Zetaris and Meterless were integrated, how Cursor was used during development, where NVIDIA technology contributes, and what was unique about your use of the sponsor technologies.
>
> 7.1 Scoring out of 100: Impact 30, Technical 20, Innovation 15, Demo 15, Product & UX 10, Sponsor tech 10.

Not a quotation: the 2026-09-28 snapshot's "up to 30 bonus points" text is NOT FOUND ON PAGE in the 2026-10-11 snapshot.

## 2. What does not change

Sponsor integration may not alter any of the following. They remain exactly as preregistered in P3 and Addendum 01:

- hypotheses H1–H6;
- the four DSL primitives and the exact 14-structure recoverable space;
- the deterministic fitter, observation noise `σ = 0.015`, verifier threshold (≥ 6 usable observations, RMSE ≤ 0.030);
- the common-action / ambiguity gate;
- B1, B1-legacy diagnostic, B2 (including its tuning rule), B3 (exhaustive, uncapped), B4-strict, B4-tiebreak;
- fault families, parameter distributions, disposition labels;
- challenge / preservation denominators, `miss` vs `unsafe_action` severity, success and failure criteria;
- text template families and leakage rules (§12);
- the C1 policy-visible whitelists (Addendum 01, item 4);
- eval-v3 seed handling (§18.1).

**No claim that Zetaris or Meterless improves any registered metric is preregistered.** Their role is deployment data access, governance, and auditable persistence/replay. Any metric-improvement claim for a sponsor component requires a separate dated amendment before eval-v3 generation.

## 3. Date and track corrections

- P3 header and §28: the build window is 2026-10-22T00:00Z – 2026-10-27T23:45Z. "WAIT FOR 2026-10-15 00:00 UTC" reads "WAIT FOR 2026-10-22 00:00 UTC".
- P3 §21 "before the build window" means before 2026-10-22T00:00Z.
- P3 §22: primary track remains **Track 03 Reasoning Architecture**. The track formerly named "Connected Agent Context" is now Track 01 "Solving Fragmented Intelligence"; relevance is noted but not scored twice (rule 3.4). Tinkerer is no longer a sponsor-integration fallback, because rule 5.1 applies to every submission.

## 4. Zetaris — evidence data plane

### 4.1 Role

The System-2 Evidence Packet (P3 §4) is assembled from fragmented operational sources through Zetaris federated query. This models plant deployment, where telemetry, MES events, and maintenance records live in separate systems.

Registered source split (at least two distinct sources):

- **S-TELEMETRY**: policy-visible observation samples, target-presence events, and command feedback, using the Addendum 01 C1 schemas only.
- **S-OPS**: MES / equipment events, maintenance work orders, shift notes (P3 §12 template families only), and operator-known configuration.

### 4.2 Governance as structural leakage control

Only C1 whitelist fields and P3 §12 context records may be written to any Zetaris-reachable source. Hidden truth — true disturbance parameters, scenario names, disposition labels, hidden `target_present`, future trajectory, fault state — is never written to any Zetaris-reachable store.

A static check enumerates every column of every registered source and fails on any field outside the whitelist.

### 4.3 Equivalence invariant

A local deterministic **reference loader** assembles the same Evidence Packet from the same source files.

For every decision point in the equivalence set, the SHA-256 of the canonical-JSON Zetaris-assembled packet must equal the SHA-256 of the reference-loader packet.

Equivalence set: 20 dev episodes covering every registered recoverable and fault family and all four context variants. Dev seeds only.

### 4.4 Evaluation path

All registered evaluation runs (eval v3) and all baselines B1–B4 use the reference loader. This keeps evaluation independent of remote-service availability and guarantees that every comparator receives byte-identical evidence.

The Zetaris path is exercised in the demo and in the equivalence receipt. If equivalence fails, that is a reported Zetaris-path defect; registered evaluation results remain valid.

### 4.5 Expected metric effect

None. Zetaris is transport plus governance. A "remove Zetaris" ablation is therefore not a metric test. The claim is deployability and governed access, evidenced by §4.2 and §4.3 receipts.

## 5. Meterless — reasoning-run persistence and replay

### 5.1 Role

Each System-2 decision run — evidence references → proposed hypotheses → fits → verifier results → ambiguity gate → authorization or disposition — is persisted as a Meterless-managed record or graph. This provides:

- inspection of the full reasoning trail (P3 §16 explanation fidelity);
- replay of a recorded run, including replay of B4 with a different model provider (P3 §21 provider replaceability);
- the demo evidence trail (P3 §23).

### 5.2 Memory scope

P3 §11 stands: decision memory is episode-local; there is no cross-episode learning in any registered evaluation run.

In registered runs, Meterless persistence is write-only audit with respect to other episodes. The policy may read only current-episode state. A check asserts that no policy read touches a record whose `episode_id` differs from the current episode.

### 5.3 Exploratory only

Cross-episode "operations memory" (retrieving similar past escalation signatures) may appear in the demo as an explicitly labelled exploratory, non-preregistered feature. It never appears in registered result tables.

### 5.4 Decision invariance

Persistence must not change decisions. On the §4.3 equivalence set, B4 decisions with Meterless persistence on and off must be identical when driven by the same recorded LLM responses (replay cache).

### 5.5 Open item

UNKNOWN: which Meterless component or interface (open specification / reference implementation, or a Gaia / Swarms / Relay application) is integrable from Linux/WSL. This is resolved by the §8 compatibility spike. If only a Windows-hosted component is integrable, persistence runs through a host-side adapter; §5.2–§5.4 still apply unchanged.

## 6. NVIDIA

Unchanged from P3 §21: NVIDIA NIM / Nemotron is the B4 hypothesis-generator provider behind a replaceable adapter. Rule 5.2 makes NVIDIA optional; it is retained because it is the B4 LLM.

NVIDIA components are not used for parameter fitting, verification, ambiguity gating, or authorization.

## 7. Cursor

Build-window development is performed in Cursor (WSL remote workspace). Terminal-hosted coding agents run inside Cursor.

To make rule 6.4 auditable:

1. `.cursor/rules` encodes P3 §25 stop conditions, the eval-v3 seed prohibition, and the C1 whitelist.
2. `docs/DEV_WORKFLOW.md` records, per module, which tool authored and which reviewed.
3. At least one bounded component (the demo / replay UI) is implemented with Cursor's native agent.

This section has no effect on the benchmark.

## 8. Pre-window compatibility spikes (extends P3 §21)

Before 2026-10-22T00:00Z, only access and compatibility experiments are allowed, and only in a separate temporary repository or context — not in RRA. Scope:

- **Zetaris**: access path (sponsor credits vs. 30-day Z-Cloud trial); whether Z-Cloud can reach the registered sources. A WSL-local database is not reachable from a cloud service, so sources may need hosting or a self-managed deployment.
- **Meterless**: the integrable interface on Linux/WSL (§5.5).
- **NVIDIA NIM**: as in P3 §21.

No RRA System-2 code and no RRA source schemas are committed before the window. Spike output is a go / no-go feasibility note per sponsor, which may be committed to RRA `docs/` before the window as declared pre-existing design input.

Unless sponsor access is provided, the Zetaris trial is started no earlier than 2026-10-20 so that it covers judging through results (2026-11-06).

## 9. Deliverables mapping (rules 6.1–6.4)

P3 §23 minimum demo adds two visible steps:

- the Evidence Packet is assembled through a Zetaris federated query across at least two sources;
- the System-2 run is persisted in, and replayed from, Meterless.

The video is 1–4 minutes. A slide deck (6.2), README (6.3), and integration explanation covering Zetaris, Meterless, Cursor, and NVIDIA (6.4) are required.

Failure-mode documentation is no longer a listed requirement but is retained, because it supports the Technical criterion (reliability).

## 10. Scope-cut amendment (P3 §24)

Add to **do not cut**:

- minimal Zetaris evidence path with the §4.2 and §4.3 receipts;
- minimal Meterless run persistence and replay;
- deliverables 6.1–6.4.

Add to **cut first**:

- Meterless cross-episode memory (§5.3);
- Zetaris sources beyond the two registered;
- live replay with a second model provider (recorded replay suffices).

## 11. Added stop conditions (P3 §25)

Stop and reassess if:

- sponsor integration changes the content of any Evidence Packet relative to the reference loader;
- any hidden-truth field becomes reachable through a Zetaris-registered source;
- the policy reads Meterless records from another episode in a registered run;
- registered evaluation results depend on sponsor-service availability, other than the preregistered B4 LLM call path;
- sponsor integration is redesigned after seeing eval-v3 outcomes.

## 12. Gate

```text
P3_PREREG_ADDENDUM_02_DRAFT
-> OWNER DISPOSITION
-> COMMIT TO main BEFORE THE pre-window-freeze TAG
-> pre-window-freeze
-> 2026-10-22T00:00Z BUILD WINDOW
```
