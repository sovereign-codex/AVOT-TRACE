# Sovereign Capability TRACE Crosswalk

## Status
Offline conformance fixture for `FPP-SCC-TRACE-FIXTURE-001`.

This document is non-canonical and does not modify the live TRACE receiver, trace schema, index runtime, dispatch behavior, or default branch.

## Purpose
`MHS-EDGE-OBSERVE-001` tests whether the exact Archivist-normalized synthetic capability event can become a deterministic, idempotent full TRACE event while keeping the discovery index explicitly lossy.

## Provenance
The source fixture is copied from:

- repository: `sovereign-codex/AVOT-ARCHIVIST`
- branch: `experiment/scc-archivist-fixture-001`
- commit: `dea7c0cec916b5985c82dd23fae01d6fb2957d58`
- path: `fixtures/capability/mhs-edge-observe-001.expected-normalized.json`
- blob: `84f27291ac85be43ca238aa876931ba55f73f4ed`

A fixture-only `fixture_provenance` object records these coordinates and is excluded from the canonical TRACE event because the reviewed receiver preserves only the normalized event fields.

## Contract distinction
```text
full trace event
  = witness record
  = content-derived event identity
  = semantic + evidence + normalization preservation

index projection
  = discovery aid
  = deliberately incomplete
  = must point back to the full trace fixture
```

## Event identity rule
The validator mirrors the reviewed `trace-receiver.yml` rule:

```text
canonical JSON of event content
→ sort object keys
→ compact encoding
→ SHA-256
→ first 24 hexadecimal characters
```

The expected event ID is derived by the validator from source content; it is not an authority token and does not imply admission.

## Replay rule
An event with the same `event_id` must not be appended twice to one trace. The offline validator replays the same event and requires the trace event count to remain one.

## Preservation rule
`semantic`, `evidence`, and `normalization` must survive byte-for-value equivalent at the JSON data level. TRACE may witness what it receives; it may not reconstruct missing authority, capability, device, constraint, or evidence fields that Archivist did not supply.

## Index projection rule
The fixture index retains only discovery fields plus a fixture-only `full_trace_ref`. Every omitted event leaf is listed in `projection_omissions` so loss is explicit and reversible through the full trace reference.

This does not authorize adding `full_trace_ref` or `projection_omissions` to the live index.

## Run locally
```bash
python3 scripts/validate_capability_trace_fixture.py
```

The validator reads local files only, performs no network calls, invokes no workflow, dispatches no event, and writes no repository file.

## Promotion boundary
Passing this fixture proves offline full-trace preservation and projection accounting only. It does not prove live Archivist-to-TRACE circulation, MHS compatibility, hardware readiness, capability admission, or deterministic procedure promotion.
