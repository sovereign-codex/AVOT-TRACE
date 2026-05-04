#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

TRACE_DIR = Path("traces")
OUT_FILE = Path("data/trace-index.json")


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# -------------------------
# NORMALIZATION (defensive)
# -------------------------
def normalize_status(status: str) -> str:
    if not status:
        return "unknown"

    s = status.lower()

    if "fail" in s or "error" in s:
        return "failed"
    if "route" in s:
        return "route_selected"
    if "decision" in s:
        return "decision_created"
    if "dispatch" in s:
        return "dispatched"
    if "complete" in s:
        return "execution_completed"
    if "stored" in s:
        return "result_stored"
    if "sent" in s:
        return "result_sent"
    if "received" in s:
        return "result_received"

    return s


# -------------------------
# NODE EXTRACTION
# -------------------------
def extract_nodes(events):
    nodes = set()

    for e in events:
        repo = e.get("source") or e.get("repo")
        workflow = e.get("workflow")

        if repo:
            nodes.add(f"repo:{repo}")

        if workflow:
            nodes.add(f"workflow:{workflow}")

    return sorted(nodes)


# -------------------------
# PHASE DETECTION
# -------------------------
def detect_phase(events):
    if not events:
        return "unknown"

    last = normalize_status(events[-1].get("status"))

    if last == "execution_completed" or last == "result_stored":
        return "completed"

    if last == "failed":
        return "failed"

    return "in_progress"


# -------------------------
# ANOMALY FLAGS
# -------------------------
def detect_flags(events):
    flags = []

    retry_count = 0
    fail_count = 0

    for i in range(1, len(events)):
        prev = events[i - 1]
        curr = events[i]

        if prev.get("workflow") == curr.get("workflow"):
            retry_count += 1

        status = normalize_status(curr.get("status"))
        if status == "failed":
            fail_count += 1

    if retry_count >= 2:
        flags.append("retry_loop")

    if fail_count >= 2:
        flags.append("failure_chain")

    return flags


# -------------------------
# IMPORTANCE SCORE
# -------------------------
def compute_score(events):
    score = 0

    for e in events:
        s = normalize_status(e.get("status"))

        if s == "failed":
            score += 3
        elif s in ("execution_completed", "result_stored"):
            score += 1
        else:
            score += 0.5

    return round(score, 2)


# -------------------------
# MAIN BUILD
# -------------------------
def main():
    traces = []

    if not TRACE_DIR.exists():
        print("[warn] traces directory not found")
        return

    for file in TRACE_DIR.glob("*.json"):
        try:
            trace = json.loads(file.read_text())
        except Exception as e:
            print(f"[warn] failed to read {file}: {e}")
            continue

        trace_id = trace.get("trace_id") or file.stem
        events = trace.get("events", [])

        if not events:
            continue

        # Normalize events (defensive)
        for e in events:
            e["status"] = normalize_status(e.get("status"))

        latest_event = events[-1]

        entry = {
            "trace_id": trace_id,
            "latest": latest_event.get("timestamp"),
            "status": latest_event.get("status"),
            "repo": latest_event.get("source") or latest_event.get("repo"),
            "workflow": latest_event.get("workflow"),
            "event_count": len(events),

            # 🧠 NEW FIELDS
            "nodes": extract_nodes(events),
            "phase": detect_phase(events),
            "flags": detect_flags(events),
            "score": compute_score(events)
        }

        traces.append(entry)

    # Sort newest first
    traces = sorted(traces, key=lambda t: t.get("latest") or "", reverse=True)

    output = {
        "generated_at": now_iso(),
        "count": len(traces),
        "traces": traces
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    print(f"[write] {OUT_FILE} ({len(traces)} traces)")


if __name__ == "__main__":
    main()