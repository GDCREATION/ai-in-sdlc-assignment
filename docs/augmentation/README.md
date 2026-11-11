# AI augmentation log

`.cursor/hooks/augmentation-log.py` appends one JSON object per line to `log.jsonl`. The hook fails open: a script error does not block the agent. Prompt text is stored with the demo password `ChangeMe123!` replaced by `[redacted]`. MCP result bodies are not stored.

| Event | Fields |
| --- | --- |
| `beforeSubmitPrompt` | `timestamp`, `conversation_id`, `session` (same id), `prompt_length`, `prompt` |
| `afterMCPExecution` | `timestamp`, `conversation_id`, `mcp_server_name`, `tool_name`, `duration` |
| `afterFileEdit` | `timestamp`, `conversation_id`, `file_path` |
| `subagentStop` | `timestamp`, `conversation_id`, `agent` (the subagent type), `status` |
| `stop` | `timestamp`, `conversation_id`, `status` |

`log.jsonl` is the hand-in. Cursor loads the hook from `.cursor/hooks.json` on the next agent turn after the file is saved.
