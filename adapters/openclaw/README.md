# Hypha × OpenClaw

Status: **P1 (placeholder)** — native integration pending.

## What is OpenClaw

OpenClaw is a self-hosted agent framework. Integration details depend on its
lifecycle surface; this adapter is a placeholder until the maintainer defines:

1. Session start / end events and where they fire
2. Where transcripts are persisted
3. How tool calls are observable
4. Configuration mechanism analogous to `~/.claude/settings.json`

## Integration sketch

Regardless of surface, the mapping is always the same four calls:

| Lifecycle point | Hypha command |
|---|---|
| Session start | `hypha export <format>` → inject into agent's context |
| Session end, failure signal | `hypha reflect --trajectory <transcript>` |
| Session end, success signal | `hypha harvest --trajectory <transcript>` |
| Periodic (or every N sessions) | `hypha consolidate` |
| Before mutating agent config | `hypha guard` |

## Contribute

If you maintain OpenClaw, open an issue with your lifecycle doc and we'll
draft the adapter together.
