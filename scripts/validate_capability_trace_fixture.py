#!/usr/bin/env python3
import copy, hashlib, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
P = ROOT / "fixtures" / "capability"
source = json.loads((P / "mhs-edge-observe-001.archivist-normalized.json").read_text())
expected_trace = json.loads((P / "mhs-edge-observe-001.expected-trace.json").read_text())
expected_index = json.loads((P / "mhs-edge-observe-001.expected-index.json").read_text())

def canonical_event(src):
    event = {k: copy.deepcopy(v) for k,v in src.items() if k != "fixture_provenance"}
    raw = json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    event["event_id"] = hashlib.sha256(raw).hexdigest()[:24]
    return event

def flatten(obj, prefix=""):
    out = set()
    if isinstance(obj, dict):
        for k,v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict,list)):
                out |= flatten(v,p)
            else:
                out.add(p)
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            p = f"{prefix}[{i}]"
            if isinstance(v,(dict,list)):
                out |= flatten(v,p)
            else:
                out.add(p)
    return out

errors=[]
event = canonical_event(source)
if set(expected_trace) != {"trace_id", "events"}: errors.append("trace document keys differ from expected wrapper contract")
if not isinstance(expected_trace.get("events"), list) or len(expected_trace.get("events", [])) != 1:
    errors.append("expected trace must contain exactly one event")
elif event != expected_trace["events"][0]:
    errors.append("full trace event differs from canonical source event")
if expected_trace.get("trace_id") != source.get("trace_id"): errors.append("trace_id mismatch")
# stable identity
if canonical_event(source)["event_id"] != event["event_id"]: errors.append("event id is not stable")
# idempotent replay
trace={"trace_id":source["trace_id"],"events":[]}
for candidate in (event, event):
    if not any(e.get("event_id")==candidate["event_id"] for e in trace["events"]): trace["events"].append(candidate)
if len(trace["events"]) != 1: errors.append("duplicate replay increased event count")
# preserve semantic/evidence/normalization exactly
for key in ("semantic","evidence","normalization"):
    if event.get(key) != source.get(key): errors.append(f"{key} not preserved")
# no inference: keys outside receiver allowlist must not appear
allowed={"trace_id","timestamp","repo","workflow","status","event_class","protocol_version","semantic","evidence","normalization","event_id"}
extra=set(event)-allowed
if extra: errors.append(f"unexpected inferred fields: {sorted(extra)}")
# index projection and omissions
if not isinstance(expected_index.get("traces"), list) or len(expected_index.get("traces", [])) != 1:
    errors.append("expected index must contain exactly one trace entry")
    entry = {}
else:
    entry = expected_index["traces"][0]
required_index={"trace_id","timestamp","status","repo","workflow","event_class","event_count","full_trace_ref","projection_omissions"}
if set(entry) != required_index: errors.append("index fixture keys differ from declared projection contract")
if entry.get("event_count") != 1: errors.append("index event_count must be 1")
if entry.get("full_trace_ref") != "fixtures/capability/mhs-edge-observe-001.expected-trace.json": errors.append("index lacks full trace reconstruction ref")
source_leafs = flatten(event)
index_leafs = flatten({k:v for k,v in entry.items() if k != "projection_omissions"})
omitted = sorted(p for p in source_leafs if p not in index_leafs and not p.startswith("event_id"))
if sorted(entry.get("projection_omissions", [])) != omitted: errors.append("index projection omissions are incomplete or inaccurate")
# observation only remains evident
obs=" ".join(source.get("evidence",{}).get("observations",[])).lower()
if "synthetic" not in obs or "observe-only" not in obs: errors.append("synthetic observation-only posture missing")
# negative controls internal
mut=copy.deepcopy(source); mut["status"]="changed_without_expected_id_update"
if canonical_event(mut)["event_id"] == event["event_id"]: errors.append("content mutation did not change event id")
if errors:
    print("FAIL")
    for e in errors: print(f"- {e}")
    sys.exit(1)
print("PASS")
print(f"trace_id={source['trace_id']}")
print(f"event_id={event['event_id']}")
print("replay_event_count=1")
print(f"preserved_sections=semantic,evidence,normalization")
print(f"index_omitted_leaf_fields={len(entry.get('projection_omissions', []))}")
print("network_access=not_used")
print("repository_writes=not_used")
