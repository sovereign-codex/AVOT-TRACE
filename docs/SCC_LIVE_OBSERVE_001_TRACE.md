# SCC-LIVE-OBSERVE-001 — TRACE preservation boundary

Status: branch-local experiment only. No live dispatch has been authorized or executed.

## Purpose

Extend the existing TRACE receiver only enough to preserve an optional `capability_context` object exactly as received.

## Invariants

- Legacy events without `capability_context` retain existing behavior.
- TRACE does not infer capability identity, authority, constraints, or evidence.
- `capability_context` participates in canonical event hashing.
- Replay remains idempotent by `event_id`.
- Full trace is the witness record; the discovery index remains intentionally lossy and non-authoritative.
- No hardware, execution, capability admission, canon promotion, or procedure promotion is authorized by this change.

## Expected synthetic event

For the current fixture, canonical event identity is:

`11b26bdf14ce344997985af9`

The local validator recomputes this value from canonical content and fails if capability context changes without a corresponding event identity change.

## Gate

Merging or running the cross-repository live test requires separate review and explicit human authorization.
