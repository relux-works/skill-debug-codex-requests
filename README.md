# skill-debug-codex-requests

Open-source Codex skill for capturing and inspecting the exact provider requests that Codex sends through an OpenAI-compatible proxy.

It is useful when you need to debug:

- request size and payload shape
- injected `instructions` and `system_prompt`
- exposed tools and provider overrides
- profile differences from `~/.codex/config.toml`
- TTFT, warm generation speed, and near-context behavior

## What Is Included

- `SKILL.md` with the operational workflow
- `scripts/codex_proxy.py` for request capture and forwarding
- `scripts/inspect_proxy_log.py` for log inspection
- `scripts/run_codex_benchmark.py` for multi-phase throughput benchmarking
- `references/` with field semantics and benchmark guidance
- `agents/openai.yaml` for UI metadata

## Install

Use the standalone installer to install or update the managed copy:

```bash
./setup.sh global --locale ru-en
```

This creates a managed runtime copy in:

- `${XDG_DATA_HOME:-~/.local/share}/agents/skills/skill-debug-codex-requests`
- Symlinks in `~/.claude/skills/debug-codex-requests` and `~/.codex/skills/debug-codex-requests`

The setup flow also registers localized triggers in `~/.agents/.instructions/INSTRUCTIONS_SKILL_TRIGGERS.md` for automatic skill activation.

## Main Flows

1. Capture a fresh Codex request through the bundled proxy.
2. Inspect sanitized `system_prompt`, `instructions`, `input`, tools, and request sizes.
3. Run the multi-phase benchmark for cold TTFT, warm raw speed, and near-context behavior.

## License

MIT

## Author

Ivan Oparin
