#!/usr/bin/env python3
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT / "fixtures/capability-live/scc-live-observe-001.expected-event.json"


def canonical_event(received):
    out = {
        "trace_id": received.get("trace_id") or "unknown",
        "timestamp": received.get("timestamp") or "1970-01-01T00:00:00Z",
        "repo": received.get("repo") or "unknown-repo",
        "workflow": received.get("workflow") or "unknown-workflow",
        "status": received.get("status", "unknown-status"),
    }
    for key in ("event_class", "protocol_version"):
        if key in received:
            out[key] = received[key]
    for key in ("semantic", "evidence", "normalization", "capability_context"):
        if isinstance(received.get(key), dict):
            out[key] = received[key]
    return out


def event_id(event_without_id):
    payload = json.dumps(event_without_id, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def append_idempotently(trace, event):
    if not any(existing.get("event_id") == event.get("event_id") for existing in trace["events"]):
        trace["events"].append(event)
    return trace


def main():
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    expected_without_id = {k: v for k, v in expected.items() if k != "event_id"}
    computed = canonical_event(expected_without_id)
    errors = []

    if computed != expected_without_id:
        errors.append("expected event contains fields TRACE would not preserve or changes canonical values")

    computed_id = event_id(computed)
    if expected.get("event_id") != computed_id:
        errors.append("expected event_id does not match canonical content hash")

    ctx = expected.get("capability_context")
    if not isinstance(ctx, dict):
        errors.append("capability_context missing from expected event")
    elif canonical_event(expected).get("capability_context") != ctx:
        errors.append("capability_context was not preserved exactly")

    mutated = copy.deepcopy(computed)
    mutated["capability_context"]["authority"]["ceiling"] = "bounded_execute"
    if event_id(mutated) == computed_id:
        errors.append("capability_context mutation did not change event_id")

    trace = {"trace_id": expected["trace_id"], "events": []}
    event_with_id = copy.deepcopy(computed)
    event_with_id["event_id"] = computed_id
    append_idempotently(trace, event_with_id)
    append_idempotently(trace, event_with_id)
    if len(trace["events"]) != 1:
        errors.append("duplicate replay increased event count")

    inferred = copy.deepcopy(computed)
    inferred["capability_context"]["authority"]["authorized"] = True
    if inferred == computed:
        errors.append("inference negative control did not mutate event")
    if "authorized" in expected["capability_context"]["authority"]:
        errors.append("expected event contains inferred authorization")

    legacy = {
        "trace_id": "legacy-test",
        "timestamp": "2026-01-01T00:00:00Z",
        "repo": "example/legacy",
        "workflow": "legacy",
        "status": "observed",
        "semantic": {"institutional_state": "legacy"},
    }
    legacy_out = canonical_event(legacy)
    if "capability_context" in legacy_out:
        errors.append("legacy event gained capability_context")

    stale = copy.deepcopy(event_with_id)
    stale["capability_context"]["constraints"]["safe_state"] = "changed"
    if stale["event_id"] == event_id({k: v for k, v in stale.items() if k != "event_id"}):
        errors.append("stale event_id negative control did not fail")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("PASS")
    print("fixture_id=SCC-LIVE-OBSERVE-001")
    print(f"event_id={computed_id}")
    print("capability_context=preserved_exactly")
    print("replay_event_count=1")
    print("legacy_behavior=unchanged")
    print("index_authority=none")


if __name__ == "__main__":
    main()
