# AVOT-TRACE

Central observability layer for AVOT signal propagation.

## Purpose
Tracks all workflow events across repositories.

## Structure
- /logs → daily aggregated logs
- /traces → individual trace events
- /schemas → payload definitions

## Event Format
All systems must emit:

- trace_id
- repo
- workflow
- status
- timestamp

## Usage
Used by:
- AVOT Engine
- Control Center
- Archivist
- Dispatcher

## Future
- Live dashboard via Codex-interface
- Signal replay + debugging