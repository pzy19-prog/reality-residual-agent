# Hackathon rules review — 2026-10-04

Status: **PARTIAL CURRENT-SOURCE REVIEW / DOCUMENTATION ONLY**.

Source: https://hackathon.genai.works/event/open-agent-hackathon-2026  
Reviewed on: 2026-10-04 (Asia/Shanghai)  
Method: public page text retrieval, signed out. The retrieved text exposes the track, scoring and date blocks; official-rule sections 02–10 and most FAQ answers are collapsed. This is not a full expanded-rules snapshot.

## Verified current page facts

| Item | Current visible page |
|---|---|
| Build opens | 2026-10-15 00:00 UTC / 2026-10-15 08:00 Asia/Shanghai |
| Submission closes | 2026-10-20 23:45 UTC / 2026-10-21 07:45 Asia/Shanghai |
| Reasoning Architecture | Track 03 |
| Other primary tracks | Track 01: Solving Fragmented Intelligence; Track 02: The Agent That Can Explain Why |
| Wildcard / Tinkerer | New work extending an existing project; requires both Zetaris and Meterless |
| Scoring | 100 total: Impact 30, Technical 20, Innovation 15, Demo 15, Product & UX 10, Sponsor tech 10 |

The retrieved current scoring block contains no extra 30-point provision. Its absence is **not proof of cancellation**; do not budget those points without current authoritative confirmation.

## Difference from the September 28 snapshot

[HACKATHON_RULES.md](HACKATHON_RULES.md) preserves the earlier capture. Its Track 04 numbering, NVIDIA-based Tinkerer fallback, and extra-30-points wording are historical claims, not current eligibility evidence.

NVIDIA appears in the organizer's September 28 registration confirmation alongside Zetaris and Meterless. That email does not establish that NIM alone satisfies the current Tinkerer requirement or earns Sponsor tech points.

## Project decisions and limits

- **DESIGN CHOICE:** retain Reasoning Architecture as the preferred target; use Track 03 in current planning. This does not change the team's selection in HackOS.
- **INFERENCE:** NIM-only integration is insufficient for the currently visible Tinkerer requirement.
- **DESIGN CHOICE:** keep NIM/Nemotron as a replaceable reasoning-provider candidate. Its suitability must be established by independent compatibility receipts, separately from sponsor eligibility.
- Do not add Zetaris or Meterless to RRA solely to chase a fallback track. Any proposed integration needs a concrete role and owner disposition.
- Continue the existing project restriction: no RRA System-2, B3/B4 runtime, NIM adapter or recovery-authorization implementation before the build window.

## Still unverified

Before treating the submission route as confirmed, retrieve the expanded official rules or current HackOS instructions for:

1. Whether declared pre-existing RRA components may enter the preferred primary track, and the current declaration requirements.
2. Primary/bonus track selection and whether bonus participation is additional or exclusive.
3. Which NVIDIA integrations qualify for Sponsor tech scoring.
4. Whether any extra 30-point provision remains.
5. Current submission deliverables, repository access, deployment/container and video limits. The September 28 snapshot's three-minute video and one-command delivery requirements remain conservative preparation targets, not freshly verified requirements.

No rule uncertainty authorizes implementation before the existing project boundary. Recheck the official page and team workspace before build authorization and submission. This document does not amend the frozen P3 evaluation protocol.
