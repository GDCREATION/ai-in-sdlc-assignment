#!/usr/bin/env python3
"""Append one augmentation-log line. Fail open: never block the agent."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "docs" / "augmentation" / "log.jsonl"
SECRET = "ChangeMe123!"


def redact(value: str) -> str:
    return value.replace(SECRET, "[redacted]")


def respond(event: str) -> None:
    if event == "beforeSubmitPrompt":
        sys.stdout.write(json.dumps({"continue": True}))
    else:
        sys.stdout.write("{}")


def record_for(event: str, payload: dict) -> dict:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "conversation_id": payload.get("conversation_id"),
    }
    if event == "beforeSubmitPrompt":
        prompt = str(payload.get("prompt") or "")
        record["session"] = payload.get("conversation_id")
        record["prompt_length"] = len(prompt)
        record["prompt"] = redact(prompt)
    elif event == "afterMCPExecution":
        record["mcp_server_name"] = payload.get("mcp_server_name")
        record["tool_name"] = payload.get("tool_name")
        record["duration"] = payload.get("duration")
    elif event == "afterFileEdit":
        record["file_path"] = payload.get("file_path")
    elif event == "subagentStop":
        record["agent"] = payload.get("subagent_type")
        record["status"] = payload.get("status")
    elif event == "stop":
        record["status"] = payload.get("status")
    return record


def main() -> None:
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    if not isinstance(payload, dict):
        payload = {}
    event = payload.get("hook_event_name") or (sys.argv[1] if len(sys.argv) > 1 else "unknown")
    record = record_for(str(event), payload)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    respond(str(event))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        fallback = sys.argv[1] if len(sys.argv) > 1 else ""
        if fallback == "beforeSubmitPrompt":
            sys.stdout.write('{"continue": true}')
        sys.exit(0)
