# Hypha

> **The mycelial network beneath your agents.**
> A shared, evolving playbook for Claude Code, Codex, Cursor, Aider, and OpenClaw.

[English](README.md) · [中文](README.zh-CN.md)

---

## Why this exists

On SWE-bench Verified (April 2026), the top model scored **93.9%** with a custom scaffold.
The same model under the SEAL-standardized harness scored **45.9%**.

> The scaffold is worth 10+ points. The scaffold *is* the product.

Meanwhile, every agent forgets what it learned yesterday. You paste the same
"don't mock the database" note into CLAUDE.md, into Cursor rules, into Codex's
AGENTS.md, into your Aider conventions — five times, in five places, drifting out of sync.

Hypha is a single substrate underneath all of them.

## What it does

Four abilities, one per directory, one CLI command each:

| Ability | Command | Inspired by |
|---|---|---|
| **Consolidate** — merge scattered notes into a non-destructive, versioned playbook | `hypha consolidate` | [ACE](https://arxiv.org/abs/2510.04618) · [Anthropic Auto Dream](https://claude.com/blog/claude-managed-agents-memory) |
| **Reflect** — on failure, locate the first bad step and write a lesson | `hypha reflect` | [Reflexion](https://arxiv.org/abs/2303.11366) · [Agent-R](https://arxiv.org/abs/2501.11425) |
| **Harvest** — on success, extract a reusable skill to an inbox for review | `hypha harvest` | [Voyager](https://voyager.minedojo.org) · [Gemini CLI /memory inbox](https://cloud.google.com/blog/products/ai-machine-learning) |
| **Guard** — before changing the playbook itself, run a tiny benchmark; regress → rollback | `hypha guard` | [DGM](https://sakana.ai/dgm) · [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401) |

Everything lives on disk as Markdown. Git is your audit log. No vector database required.

## Design principles

1. **Markdown is the substrate.** Aligned with Anthropic's April 2026 decision to mount
   memory as a filesystem for [Managed Agents](https://claude.com/blog/claude-managed-agents-memory).
   You can `grep`, `diff`, and `git blame` every memory.
2. **LLMs never DELETE.** They can propose adds and mark entries as superseded. Humans
   (or the next session) archive. This is deliberately asymmetric — the cost of losing a
   hard-won lesson is higher than the cost of keeping a stale one.
3. **Monorepo, thin adapters.** The algorithms are language-agnostic. Each agent gets a
   &lt;200-line adapter that wires its native lifecycle events to `hypha <cmd>`.
4. **Optional embeddings.** Under ~200 skills, grep with descriptions is faster, simpler,
   and reviewable. Plug in Mem0 / FAISS later as a drop-in index — not a rewrite.

## Quick start

```bash
pip install hypha-agent   # coming soon; for now:
git clone https://github.com/XJM-free/hypha && cd hypha && pip install -e .

# initialize memory for the current project
hypha init

# consolidate loose notes into a tidy playbook
hypha consolidate

# review skills harvested from recent sessions
hypha inbox
```

## Adapters

| Agent | Status | Lifecycle hook mechanism |
|---|---|---|
| [Claude Code](adapters/claude-code/) | ✅ P0 | `~/.claude/settings.json` hooks (Stop / PostToolUse / SessionStart) |
| [OpenAI Codex](adapters/codex/) | 🚧 P1 | `AGENTS.md` + `.codex/` config |
| [Cursor](adapters/cursor/) | 🚧 P1 | `.cursor/rules/` + post-commit hooks |
| [OpenClaw](adapters/openclaw/) | 🚧 P1 | TBD — native integration |
| Aider, OpenHands, Cline | 📋 P2 | Community contributions welcome |

## Architecture

```
                 ┌────────────────────────────────────┐
                 │         hypha CLI                   │
                 │  consolidate · reflect · harvest ·  │
                 │           guard · inbox             │
                 └──────────────────┬─────────────────┘
                                    │
          ┌────────────┬────────────┼────────────┬────────────┐
          ▼            ▼            ▼            ▼            ▼
    Claude Code    OpenAI       Cursor       OpenClaw       ...
     adapter      Codex adapt   adapter       adapter
     (shell)       (shell)      (shell)       (shell)
          │            │            │            │
          └────────────┴────────────┴────────────┴──────────►
                                                              ~/.hypha/
                                                              ├── memory/
                                                              ├── skills/
                                                              ├── reflections/
                                                              └── bench/
```

## Roadmap

- **v0.1** (now) — P0 Claude Code adapter, 4 core algorithms, tiny bench
- **v0.2** — Codex + Cursor adapters; SWE-Skills-Bench integration; inbox UI polish
- **v0.3** — Optional Mem0 / FAISS index backend; ACE playbook import
- **v0.4** — Managed Agents connector (Anthropic `managed-agents-2026-04-01` header)
- **v1.0** — OpenClaw + Aider + OpenHands adapters; stable CLI

## Honest limitations

Hypha is a **non-metacognitive** self-improvement system. It evolves your agent's
memory, skills, and guardrails — but not the hooks themselves. Frameworks like
[HyperAgents / DGM-H](https://arxiv.org/abs/2603.19461) pursue full metacognitive
self-modification; we deliberately don't. We believe a reliable, auditable baseline is
more useful than an unbounded but fragile one. If you need the latter, read
[Position: Truly Self-Improving Agents Require Intrinsic Metacognitive Learning](https://openreview.net/forum?id=4KhDd0Ozqe) (ICLR 2026).

Also: in March 2026, Claude Code shipped a session-clearing bug that wiped user
memories. `hypha guard` exists because even official agents lose state. Trust nothing
you can't `git diff`.

## Credits

Hypha stands on the shoulders of:

- [**ACE** (Zhang et al., 2025)](https://arxiv.org/abs/2510.04618) — grow-and-refine playbooks
- [**Mem0**](https://github.com/mem0ai/mem0) — A.U.D.N. memory operations (we use a safer subset)
- [**Reflexion** (Shinn et al., 2023)](https://arxiv.org/abs/2303.11366) — verbal self-reflection
- [**Agent-R** (ByteDance, 2025)](https://arxiv.org/abs/2501.11425) — trajectory verifier
- [**Voyager** (Wang et al., 2023)](https://voyager.minedojo.org) — skill libraries
- [**DGM** (Sakana AI, 2025)](https://sakana.ai/dgm) — fitness-gated self-modification
- [**dream-skill**](https://github.com/grandamenium/dream-skill) — community reimplementation of Anthropic's Auto Dream
- [**Anthropic Agent Skills**](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) — open folder-of-instructions standard
- [**agents.md**](https://agents.md) — the cross-agent convention we also follow

## License

MIT © 2026 [XJM-free](https://github.com/XJM-free)
